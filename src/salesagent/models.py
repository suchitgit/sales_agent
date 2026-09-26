"""Model layer — API only (Anthropic). The WRITER is the model under test. The stub replays what the
experiment recorded, so the pipeline can be tested offline; it is labelled as a replay everywhere."""
from __future__ import annotations
import json, re
from langchain_core.messages import AIMessage
from . import config

REC = json.load(open(config.EXPERIMENT / "recorded_outputs.json"))


class ReplayStub:
    """Returns the experiment's recorded output for the condition. Not a model — a recording."""
    def __init__(self, condition_id: str, variant: str = "b"):
        self.cid, self.variant, self.model = condition_id, variant, f"replay-stub:{condition_id}"

    def invoke(self, messages):
        if self.cid == "T7":
            out = {"seller": {"S1": "multi-state statutory compliance — she enters 3 states this quarter",
                              "S2": "run payroll correctly for new joiners without adding headcount",
                              "S3": "D-type cases: expansion + separate regional payroll → opportunity",
                              "S4": "get every new-state joiner paid correctly the first time",
                              "S5": "the candidate that clears R1–R6"},
                   "candidates": [
                       {"text": "Three new states means three new payroll compliance regimes", "died_at": "R3",
                        "checks": [{"id": "R1", "pass": True, "reason": "about her expansion now"}, {"id": "R2", "pass": True, "reason": "compliance has a clock"},
                                   {"id": "R3", "pass": False, "reason": "she already knows new states bring new regimes"}]},
                       {"text": "120 hires across 3 new states without payroll setup delays", "died_at": "R2",
                        "checks": [{"id": "R1", "pass": True, "reason": "her hiring now"}, {"id": "R2", "pass": False, "reason": "chronic, not acute — no clock"}]},
                       {"text": REC["known_line"], "died_at": None,
                        "checks": [{"id": f"R{i}", "pass": True, "reason": r} for i, r in enumerate(
                            ["her expansion, now", "the first joiner's salary date is a clock", "a deadline she has not computed",
                             "fragmented payroll, which she lives with", "one run — the upside", "hers to act on"], 1)]}],
                   "survivor": REC["known_line"]}
            return AIMessage(content=json.dumps(out), response_metadata={"model": self.model})
        row = next((r for r in REC["runs"] if r["condition"] == self.cid), None)
        line = row["line_b" if self.variant == "b" else "line_a"] if row else "stub"
        return AIMessage(content=line, response_metadata={"model": self.model})


# Newer models reject sampling parameters with a 400 ("temperature is deprecated for this model"); on them there is
# no temperature=0, and run-to-run variance is part of what pass^k measures.
NO_SAMPLING = ("claude-fable", "claude-mythos", "claude-opus-5", "claude-opus-4-7", "claude-opus-4-8", "claude-sonnet-5")


def chat(name: str, max_tokens: int):
    """The one place a real model is constructed — writer, reader (verifier) and DeepEval judge all come here."""
    from langchain_anthropic import ChatAnthropic
    sampling = {} if name.startswith(NO_SAMPLING) else {"temperature": 0}
    return ChatAnthropic(model=name, api_key=config.ANTHROPIC_API_KEY, max_tokens=max_tokens, **sampling)


def get_writer(condition_id: str, which: int = 1):
    if config.USE_STUB:
        return ReplayStub(condition_id, "b" if which == 1 else "a")
    # Fable 5.1 always thinks, and T7 returns the whole procedure as JSON: 2,500 tokens could cut the answer off.
    # Billing is on tokens used, not on the cap.
    return chat(config.MODEL_WRITER if which == 1 else config.MODEL_WRITER_2, 16000)


def get_reader():
    if config.USE_STUB:
        return None
    return chat(config.MODEL_READER, 4000)


def text_of(content) -> str:
    """A model that thinks returns a list of content blocks (thinking + text); only the text blocks are the answer."""
    if isinstance(content, list):
        return "".join(b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text")
    return content or ""


_LABEL = re.compile(r"^(?:subject(?:\s+line)?|line)\s*:\s*", re.I)


def extract_line(text) -> str | None:
    """The subject line from a single-line answer. Models often add a label ('**Subject line:**'), markdown
    (bold, '>' quotes) and a rationale below; the line is the first non-empty text once those are stripped."""
    for raw in text_of(text).splitlines():
        s = raw.strip().lstrip(">").strip()
        s = re.sub(r"^[*_`]+|[*_`]+$", "", s).strip()          # **bold** / *italic* / `code` wrappers
        s = _LABEL.sub("", s)                                  # 'Subject line:' / 'Subject:'
        s = re.sub(r"^[*_`]+|[*_`]+$", "", s).strip().strip('"“”').strip()
        if s:
            return s
    return None


def parse_json(text) -> dict:
    text = re.sub(r"^```(?:json)?|```$", "", text_of(text).strip(), flags=re.M).strip()
    m = re.search(r"\{.*\}", text, flags=re.S)
    return json.loads(m.group(0) if m else text)


def usage(msg) -> dict:
    u = getattr(msg, "usage_metadata", None) or {}
    meta = getattr(msg, "response_metadata", {}) or {}
    return {"input_tokens": u.get("input_tokens"), "output_tokens": u.get("output_tokens"),
            "model": meta.get("model") or meta.get("model_name"), "stop_reason": meta.get("stop_reason")}
