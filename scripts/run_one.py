"""One run, full path including the approval pause. Usage:
  python scripts/run_one.py [prospect] [condition] [--writer 2] [--auto] [--verify]
  default: sunidhi T7"""
import sys, json
sys.path.insert(0, "src")
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command
from salesagent import config
from salesagent.graph.spine import build
from salesagent.evals import tracing
from salesagent.evals.checks import score
args = [a for a in sys.argv[1:] if not a.startswith("--")]
pid = args[0] if args else "sunidhi"; cid = args[1] if len(args) > 1 else "T7"
w = int(sys.argv[sys.argv.index("--writer") + 1]) if "--writer" in sys.argv else 1
tracing.enable()
app = build(checkpointer=InMemorySaver()); cfg = {"configurable": {"thread_id": f"one-{cid}-{pid}"}, "tags": [cid], "metadata": {"condition": cid}}
print(f"writer: {'REPLAY STUB (no key) — recorded experiment output' if config.USE_STUB else (config.MODEL_WRITER if w == 1 else config.MODEL_WRITER_2)} · condition {cid} · tracing {tracing.status()}")
from langchain_core.tracers.context import collect_runs
with collect_runs() as cb:  # the root run id, so the replay can link to its LangSmith trace
    out = app.invoke({"prospect_id": pid, "condition_id": cid, "writer_which": w, "thread_id": f"one-{cid}-{pid}", "query": f"Write a subject line for {pid}"}, cfg)
    if "__interrupt__" in out:
        p = out["__interrupt__"][0].value
        print("\n=== APPROVAL NEEDED ===\nline:", p["line"]); [print(f"  rejected at {r['died_at']}: {r['text']}") for r in p["rejected"]]
        ok = True if "--auto" in sys.argv else input("approve? [y/N] ").lower().startswith("y")
        out = app.invoke(Command(resume={"approved": ok, "by": "rep" if "--auto" not in sys.argv else "rep (--auto)"}), cfg)
    run_id = str(cb.traced_runs[0].id) if cb.traced_runs else None
out = dict(out); out["run_id"] = run_id
if "--verify" in sys.argv and (out.get("survivor") or out.get("line")):
    from salesagent.evals.verifier import verify_line, known_to_her
    out["verifier"] = verify_line(out.get("survivor") or out.get("line"), known_to_her(pid, out["blocks"]["B1"]))
from salesagent.evals.runner import save_run
save_run(out)  # data/runs — what make replay reads
print("\n=== TRACE ===")
for s in out["trace"]: print(f"  [{s['actor']:5}] {s['step']:38} {s['detail'][:150]}  {s['ms']} ms")
print("\n=== CHECKS ===", json.dumps(score(out), indent=1))
if out.get("verifier"): print("=== VERIFIER (calibrated reader, all six) ===", [(v["id"], v["pass"]) for v in out["verifier"]])
