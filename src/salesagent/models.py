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


def get_writer(condition_id: str, which: int = 1):
    if config.USE_STUB:
        return ReplayStub(condition_id, "b" if which == 1 else "a")
    from langchain_anthropic import ChatAnthropic
    name = config.MODEL_WRITER if which == 1 else config.MODEL_WRITER_2
    return ChatAnthropic(model=name, api_key=config.ANTHROPIC_API_KEY, max_tokens=2500)


def get_reader():
    if config.USE_STUB:
        return None
    from langchain_anthropic import ChatAnthropic
    return ChatAnthropic(model=config.MODEL_READER, api_key=config.ANTHROPIC_API_KEY, temperature=0, max_tokens=300)


def parse_json(text: str) -> dict:
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    m = re.search(r"\{.*\}", text, flags=re.S)
    return json.loads(m.group(0) if m else text)


def usage(msg) -> dict:
    u = getattr(msg, "usage_metadata", None) or {}
    return {"input_tokens": u.get("input_tokens"), "output_tokens": u.get("output_tokens"),
            "model": (getattr(msg, "response_metadata", {}) or {}).get("model") or (getattr(msg, "response_metadata", {}) or {}).get("model_name")}
