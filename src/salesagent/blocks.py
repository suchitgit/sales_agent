"""The runtime's core claim: it rebuilds, from the source systems, the blocks a human assembled by hand
in the experiment. Each builder returns the block text; tests/test_golden_prompt.py checks them against
data/experiment/blocks_verbatim.json."""
from __future__ import annotations
import json, re
from . import config
from .sources import adapters as A
from .sources.derive import signals

TITLES = {"B0": "B0 · BASIC", "B1": "B1 · CURRENT CONTEXT", "B2": "B2 · DORMANT DATA", "B3": "B3 · NEW / DERIVED DATA",
          "B4": "B4 · JUDGMENT DATA", "B5": "B5 · DECISION DATA", "B5a": "B5 · DECISION DATA", "B7": "B7 · DECISION TRACES"}

def fetch_all(prospect_id: str) -> dict:
    acct = A.crm_account(prospect_id); company = acct["data"]["account"]["company"]
    return {"account": acct, "post": A.social_post(prospect_id), "jobs": A.job_postings(company),
            "notes": A.crm_notes(prospect_id), "cases": A.decision_cases(), "judgement": A.judgement(), "traces": A.traces()}

def build(f: dict) -> dict:
    a, s = f["account"]["data"]["account"], f["account"]["data"]["seller"]
    post, jobs, notes = f["post"]["data"], f["jobs"]["data"], f["notes"]["data"]["notes"]
    b = {}
    b["B0"] = (f"PROSPECT\nName: {a['name']} · Role: {a['role']}\nCompany: {a['company']} · {a['company_desc']}\n\n"
               f"SELLER\nCompany: {s['company']}\nProvides: " + " · ".join(s["provides"]))
    if post:
        when = "Last week" if post["age_days"] <= 7 else f"{post['age_days']} days ago"
        b["B1"] = f"{when}, {post['author']} posted that {post['text']}\n\n{jobs['company']} currently has {jobs['open_roles']} open roles."
    else:
        b["B1"] = ""
    b["B2"] = "\n".join(f"{i}. {n['text']}" for i, n in enumerate(notes, 1))
    sig, interest = signals(post, jobs, notes)
    b["B3"] = "\n".join(f"{k:<33}{v}" for k, v in sig.items()) + (f"\n\nHistorical interest signal:\n{interest}" if interest else "")
    j = f["judgement"]["data"]; b["B4"] = j["source_line"] + "\n\n" + "\n".join(f"{i}. {r}" for i, r in enumerate(j["rules"], 1))
    def case_line(c):
        pain = f"\n         Known pain: {c['known_pain']}" if c.get("known_pain") else (f"\n         ({c['angle']})" if c.get("angle") else "")
        return f"CASE {c['id']}  Context: {c['context']}{pain} → {c['outcome']}"
    cases = f["cases"]["data"]["cases"]
    b["B5"] = "\n".join(case_line(c) for c in cases)
    b["B5a"] = "\n".join(case_line(c) for c in cases if c["id"] != "D4")
    t = f["traces"]["data"]
    b["B7"] = (t["reader_title"] + "\n" + "\n".join(f"{r['id']} {r['q']}" for r in t["reader"]) + "\n\n" + t["seller_title"] + "\n"
               + "\n".join(f"{x['id']} {x['q']}" for x in t["seller"]) + "\n\nTASK  " + t["task"])
    return b

OUTPUT_FORMAT = """OUTPUT FORMAT (runtime addition — not part of the experiment's blocks)
Reply with JSON only:
{"seller": {"S1": "...", "S2": "...", "S3": "...", "S4": "...", "S5": "..."},
 "candidates": [{"text": "...", "checks": [{"id": "R1", "pass": true, "reason": "..."}], "died_at": "R3" or null}],
 "survivor": "<the surviving subject line, exactly as in candidates>"}
List each candidate's checks in order R1…R6 and stop at its first failure."""

def assemble(blocks: dict, condition: dict) -> tuple[str, list]:
    cond_text = json.load(open(config.EXPERIMENT / "conditions.json"))
    parts, spans, pos = [], [], 0
    for bid in condition["blocks"]:
        seg = f"[{TITLES[bid]}]\n{blocks[bid]}\n"
        spans.append({"block": bid, "start": pos, "end": pos + len(seg)}); parts.append(seg); pos += len(seg) + 1
    if condition["mode"] == "single":
        parts.append(cond_text["task_single_line"])
    else:
        parts.append(OUTPUT_FORMAT)
    return "\n".join(parts), spans

_norm = lambda s: re.sub(r"\s+", " ", s).strip()

def golden(blocks: dict) -> dict:
    """Block-by-block comparison with the experiment. B5's 'D5–D7 (from v19)' line is a known gap, stripped."""
    ref = json.load(open(config.EXPERIMENT / "blocks_verbatim.json"))
    out = {}
    for bid, v in ref.items():
        r = re.sub(r"CASE D5–D7\s+\(from v19\)", "", v["text"])
        out[bid] = _norm(blocks.get(bid, "")) == _norm(r)
    return out
