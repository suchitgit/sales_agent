"""pass^k over the seed prospects, plus tool-path consistency. Exports sales.eval.v1."""
from __future__ import annotations
import json, time
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore
from langgraph.types import Command
from ..graph.spine import build
from ..graph import nodes
from ..stores.context import load_prospects
from .checks import CHECKS

# The experiment's T7 result. A known-good case the reader must not flip: if this line fails a check,
# the check is wrong, not the line.
KNOWN_WINNER = {"sunidhi": "3 new states, one payroll run, before your first joiner's salary date"}


def score_line(prospect_id: str, text: str) -> dict:
    """Score one given line against the reader trace with the active reader. No generation."""
    st = {"prospect_id": prospect_id, "rep_id": "rep-suchit"}
    st.update(nodes.fetch(st))
    st.update(nodes.assemble(st))
    st["candidates"] = [{"id": "K", "text": text, "results": [], "died_at": None, "reason": None}]
    return nodes.score(st)["candidates"][0]


def run_once(prospect_id: str, thread: str, auto_approve: bool = True) -> dict:
    app = build(checkpointer=InMemorySaver(), store=InMemoryStore())
    cfg = {"configurable": {"thread_id": thread}}
    out = app.invoke({"prospect_id": prospect_id, "rep_id": "rep-suchit", "thread_id": thread}, cfg)
    if "__interrupt__" in out and auto_approve:
        out = app.invoke(Command(resume={"approved": True, "by": "eval"}), cfg)
    return out


def run_suite(k: int = 3) -> dict:
    prospects = load_prospects()
    scen = []
    for pid, p in prospects.items():
        passes, agg, paths = 0, {c: True for c in CHECKS}, set()
        for i in range(k):
            run = run_once(pid, f"{pid}-{i}")
            paths.add("|".join(s["step"] for s in run["trace"]))
            res = {c: fn(p, run) for c, fn in CHECKS.items()}
            if all(res.values()): passes += 1
            for c, ok in res.items():
                if not ok: agg[c] = False
        agg["consistency"] = len(paths) == 1
        scen.append({"id": pid, "title": f"{p['name']} · {p['role']}, {p['company']}", "passes": passes if agg["consistency"] else 0, "runs": k, "checks": agg})
    return {"kind": "sales.eval.v1", "k": k, "createdAt": int(time.time() * 1000), "source": "local app", "scenarios": scen}


def export_trace(run: dict, prospect: dict, stores=("context", "retrieval", "memory", "kg")) -> dict:
    return {"kind": "sales.trace.v1", "prospect": prospect["id"], "prospectName": f"{prospect['name']} · {prospect['role']}, {prospect['company']}",
            "stores": list(stores), "verdict": "declined" if run.get("declined") else ("intelligence" if run.get("winner") else "none"),
            "createdAt": int(time.time() * 1000),
            "candidates": [{"id": c["id"], "text": c["text"], "needs": list(stores), "died_at": c.get("died_at"), "reason": c.get("reason"), "results": [{"id": r["id"], "ok": r["pass"], "why": r["reason"]} for r in c.get("results", [])]} for c in run.get("candidates", [])],
            "winner": {"id": run["winner"]["id"], "text": run["winner"]["text"]} if run.get("winner") else None,
            "steps": [{"step": s["step"], "detail": s["detail"], "actor": s["actor"], "label": s["label"]} for s in run.get("trace", [])]}
