"""Run a condition (or all), k repeats, one or two writers. Saves every run; returns the table."""
from __future__ import annotations
import json, time, uuid
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command
from .. import config
from ..graph.spine import build
from .checks import score
from . import tracing

ALL = [c["id"] for c in json.load(open(config.EXPERIMENT / "conditions.json"))["conditions"]]

def run_one(prospect_id: str, condition_id: str, writer_which: int = 1, approve: bool = True) -> dict:
    tracing.enable()
    thread = f"{condition_id}-{prospect_id}-{uuid.uuid4().hex[:6]}"
    app = build(checkpointer=InMemorySaver())
    cfg = {"configurable": {"thread_id": thread}, "tags": [condition_id, f"writer{writer_which}"],
           "metadata": {"condition": condition_id, "prospect": prospect_id, "writer": config.MODEL_WRITER if writer_which == 1 else config.MODEL_WRITER_2, "stub": config.USE_STUB}}
    inp = {"prospect_id": prospect_id, "condition_id": condition_id, "writer_which": writer_which, "thread_id": thread,
           "query": f"Write a subject line for {prospect_id}"}
    run_id = None
    try:
        from langchain_core.tracers.context import collect_runs
        with collect_runs() as cb:
            out = app.invoke(inp, cfg)
            if "__interrupt__" in out: out = app.invoke(Command(resume={"approved": approve, "by": "runner"}), cfg)
            run_id = str(cb.traced_runs[0].id) if cb.traced_runs else None
    except ImportError:
        out = app.invoke(inp, cfg)
        if "__interrupt__" in out: out = app.invoke(Command(resume={"approved": approve, "by": "runner"}), cfg)
    out = dict(out); out["run_id"] = run_id; out["checks"] = score(out); out["at"] = int(time.time())
    config.RUNS.mkdir(parents=True, exist_ok=True)
    json.dump(out, open(config.RUNS / f"{int(time.time()*1000)}_{condition_id}_{prospect_id}_w{writer_which}.json", "w"), indent=2, default=str)
    return out

def run_conditions(prospect_id="sunidhi", conditions=None, k=1, writers=(1,)) -> dict:
    rows = []
    prev = config.SEND_APPROVAL_REQUIRED; config.SEND_APPROVAL_REQUIRED = False  # the table is about the line, not the send
    try:
        for cid in conditions or ALL:
            for w in writers:
                checks = [run_one(prospect_id, cid, w)["checks"] for _ in range(k)]
                rows.append(table_row(cid, config.MODEL_WRITER if w == 1 else config.MODEL_WRITER_2, config.USE_STUB, checks))
        mark_identical(rows)
    finally:
        config.SEND_APPROVAL_REQUIRED = prev
    return {"kind": "sales.conditions.v1", "prospect": prospect_id, "createdAt": int(time.time() * 1000), "rows": rows}


def table_row(cid: str, writer: str, stub: bool, checks: list[dict]) -> dict:
    """One row of the conditions table from the k runs' checks."""
    return {"condition": cid, "writer": writer, "stub": stub, "k": len(checks),
            "lines": [c["line"] for c in checks], "verdicts": [c["verdict_proxy"] for c in checks],
            "reproduces_experiment_passk": sum(c["reproduces_experiment"] for c in checks), "known_similarity_max": max(c["known_similarity"] for c in checks),
            "procedure_adherence": [c["procedure_adherence"] for c in checks], "golden_prompt": checks[0]["golden_prompt"]}


def mark_identical(rows: list[dict]) -> None:
    """The T1 finding: with two writers, does a condition produce the same line from both?"""
    by = {}
    for r in rows: by.setdefault(r["condition"], []).append(r)
    for rs in by.values():
        if len(rs) > 1:
            same = rs[0]["lines"][0] == rs[1]["lines"][0]
            for r in rs: r["identical_across_writers"] = same


def print_table(res: dict) -> None:
    print(f"{'COND':6} {'WRITER':22} {'VERDICT(proxy)':16} {'EXP?':5} {'KNOWN~':6} LINE")
    for r in res["rows"]:
        print(f"{r['condition']:6} {('replay-stub' if r['stub'] else r['writer']):22} {','.join(r['verdicts']):16} {r['reproduces_experiment_passk']}/{r['k']}  {r['known_similarity_max']:<6} {r['lines'][0][:80] if r['lines'][0] else '—'}"
              + (f"   [identical across writers: {r['identical_across_writers']}]" if "identical_across_writers" in r else "")
              + (f"   [procedure: {r['procedure_adherence']}]" if r['condition'] == 'T7' else ""))


def save_table(res: dict) -> None:
    """data/runs/conditions_latest.json and human_review.csv — the human verdict column is the final call."""
    import csv
    config.RUNS.mkdir(parents=True, exist_ok=True)
    json.dump(res, open(config.RUNS / "conditions_latest.json", "w"), indent=2)
    with open(config.RUNS / "human_review.csv", "w", newline="") as f:
        wr = csv.writer(f); wr.writerow(["condition", "writer", "run", "line", "proxy_verdict", "HUMAN_VERDICT (automation/intelligence)", "HUMAN_NOTE"])
        for r in res["rows"]:
            for i, (l, v) in enumerate(zip(r["lines"], r["verdicts"])): wr.writerow([r["condition"], r["writer"], i + 1, l, v, "", ""])
