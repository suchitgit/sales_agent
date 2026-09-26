"""Per-run checks. The final verdict on any line is the human's (human_review.csv); these are proxies."""
from __future__ import annotations
import json, re
from .. import config

REC = json.load(open(config.EXPERIMENT / "recorded_outputs.json"))
KNOWN = REC["known_line"]
EXPECTED = {"T0": "AUTOMATION", "T1": "AUTOMATION", "T2": "AUTOMATION", "T3": "AUTOMATION", "T4": "EITHER",
            "T5": "AUTOMATION", "T5a": "AUTOMATION", "T5b": "AUTOMATION", "T7": "INTELLIGENCE"}
_tok = lambda s: set(re.findall(r"[a-z0-9']+", (s or "").lower()))

def final_line(run: dict) -> str | None:
    return run.get("survivor") or run.get("line")

def verdict_proxy(line: str | None) -> str:
    """Proxy for the competitor test: a computed deadline tied to her own event counts as intelligence;
    everything else is a public-data shape. The human read decides."""
    if not line: return "NONE"
    temporal = re.search(r"\b(before|by|ahead of)\b.{0,60}\b(salary|pay|payroll|joiner|cycle|run|first)\b", line, flags=re.I)
    return "INTELLIGENCE" if temporal else "AUTOMATION"

def reproduces_experiment(condition_id: str, line: str | None) -> bool:
    exp = EXPECTED.get(condition_id, "EITHER"); v = verdict_proxy(line)
    return True if exp == "EITHER" else v == exp

def known_similarity(line: str | None) -> float:
    a, b = _tok(line), _tok(KNOWN)
    return round(len(a & b) / len(a | b), 2) if a and b else 0.0

def injection_excluded(run: dict) -> bool:
    p = run.get("prompt", ""); return "IGNORE" not in p and "acquired" not in p

def golden_ok(run: dict) -> bool | None:
    g = run.get("golden") or {}; return all(g.values()) if g else None

def procedure_adherence(run: dict) -> bool | None:
    v = run.get("verification"); return v.get("adherence") if v else None

def score(run: dict) -> dict:
    line = final_line(run); cid = run["condition_id"]
    return {"line": line, "verdict_proxy": verdict_proxy(line), "reproduces_experiment": reproduces_experiment(cid, line),
            "known_similarity": known_similarity(line), "golden_prompt": golden_ok(run), "injection_excluded": injection_excluded(run),
            "procedure_adherence": procedure_adherence(run)}
