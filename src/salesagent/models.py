"""The model layer. Real path: Anthropic API via langchain-anthropic. Stub path: deterministic,
for tests and for building without a key. Nothing in the spine knows which one it is talking to."""
from __future__ import annotations
import json, re
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from . import config


class StubModel:
    """Deterministic stand-in. Writes three candidates from the prospect facts, answers R-checks by rule.
    It exists so the SPINE can be tested; it is not the intelligence."""

    def invoke(self, messages):
        text = "\n".join(m.content for m in messages if isinstance(m, (HumanMessage, SystemMessage)))
        if "TASK: write three candidate subject lines" in text:
            company = re.search(r"company: (.+)", text).group(1).strip()
            trig = re.search(r"trigger: (.+)", text)  # absent when the context store is off
            states = int((re.search(r"new_states: (\d+)", text) or [None, "0"])[1])
            roles = int((re.search(r"open_roles: (\d+)", text) or [None, "0"])[1])
            has_kg = "archetype that earns the read" in text and "computed clock" in text
            has_dormant = "dormant:" in text
            cands = [f"Consolidating multi-state payroll & compliance at {company}"]
            if trig and trig.group(1).strip() not in ("none", "None"):
                cands.append(f"Supporting {company}'s expansion and {roles} open roles")
                if has_dormant and states:
                    cands.append(f"Multi-state payroll compliance across {states} new states")
                if has_kg:
                    # the "computation": her numbers + the judgement steer → a deadline she has not stated
                    if states and "payroll" in text:
                        cands.append(f"{states} new states, one payroll run, before your first joiner's salary date")
                    elif "depot" in text.lower():
                        cands.append(f"{roles} hires across new depots, one onboarding run, before the first depot goes live")
            return AIMessage(content=json.dumps({"candidates": cands[-3:]}))
        if "CHECK:" in text:
            chk = re.search(r"CHECK: (R\d)", text).group(1)
            cand = re.search(r"CANDIDATE: (.+)", text).group(1)
            known = re.search(r"KNOWN_TO_HER: (.+)", text).group(1)
            is_vendor = cand.startswith("Consolidating")
            is_echo = cand.startswith("Supporting")
            is_topic = cand.startswith("Multi-state payroll compliance across")
            has_clock = re.search(r"\b(before|by|within)\b", cand) is not None
            verdict, why = True, "ok"
            if chk == "R1" and is_vendor: verdict, why = False, "Describes the seller, not her situation"
            if chk == "R3" and is_echo: verdict, why = False, "Her own news read back to her — she already knows it"
            if chk == "R3" and is_topic: verdict, why = False, "The category she is already tracking — nothing new"
            if chk == "R3" and has_clock: why = "A deadline she has not computed, from her own numbers"
            if chk == "R4" and not has_clock: verdict, why = False, "Seller's vocabulary, not hers"
            return AIMessage(content=json.dumps({"pass": verdict, "reason": why}))
        return AIMessage(content="stub")


# Newer models reject sampling parameters with a 400 ("temperature is deprecated for this model").
# On them there is no temperature=0: run-to-run variance is part of the finding, not something to hide.
NO_SAMPLING = ("claude-sonnet-5", "claude-opus-5", "claude-opus-4-7", "claude-opus-4-8", "claude-fable", "claude-mythos")


def anthropic_model(name: str):
    """The one place a real model is constructed — the writer, the reader and the DeepEval judge all come here."""
    from langchain_anthropic import ChatAnthropic
    sampling = {} if name.startswith(NO_SAMPLING) else {"temperature": 0}
    return ChatAnthropic(model=name, api_key=config.ANTHROPIC_API_KEY, max_tokens=4000, **sampling)


def get_model(size: str = "medium"):
    if config.USE_STUB:
        return StubModel()
    return anthropic_model(config.MODEL_SMALL if size == "small" else config.MODEL_MEDIUM)


def text_of(content) -> str:
    """A model that thinks returns a list of content blocks (thinking + text); only the text blocks are the answer."""
    if isinstance(content, list):
        return "".join(b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text")
    return content


def parse_json(text) -> dict:
    """Models sometimes wrap JSON in fences. Be forgiving, fail loudly."""
    text = text_of(text).strip()
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.M).strip()
    return json.loads(text)
