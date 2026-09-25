"""Run one prospect through the spine. Pauses for approval; --auto approves for you.
Usage: python scripts/run_one.py sunidhi [--auto] [--export out.json]"""
import sys, json
sys.path.insert(0, "src")
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore
from langgraph.types import Command
from salesagent import config
from salesagent.graph.spine import build
from salesagent.stores.context import load_prospects
from salesagent.evals.suite import export_trace

pid = sys.argv[1] if len(sys.argv) > 1 else "sunidhi"
auto = "--auto" in sys.argv
checkpointer, store = InMemorySaver(), InMemoryStore()
persistence = "in-memory"
if config.POSTGRES_URI:
    try:
        from langgraph.checkpoint.postgres import PostgresSaver
        from langgraph.store.postgres import PostgresStore
        cp_ctx, st_ctx = PostgresSaver.from_conn_string(config.POSTGRES_URI), PostgresStore.from_conn_string(config.POSTGRES_URI)
        checkpointer, store = cp_ctx.__enter__(), st_ctx.__enter__()
        checkpointer.setup(); store.setup(); persistence = "postgres"
    except Exception as e:  # noqa: BLE001
        print(f"postgres configured but unreachable ({type(e).__name__}) — falling back to in-memory persistence")
        checkpointer, store = InMemorySaver(), InMemoryStore()
app = build(checkpointer=checkpointer, store=store)
cfg = {"configurable": {"thread_id": f"run-{pid}"}}
print(f"model: {'STUB (no ANTHROPIC_API_KEY)' if config.USE_STUB else config.MODEL_MEDIUM + ' / ' + config.MODEL_SMALL} · persistence: {persistence}")
out = app.invoke({"prospect_id": pid, "rep_id": "rep-suchit", "thread_id": f"run-{pid}"}, cfg)
if "__interrupt__" in out:
    payload = out["__interrupt__"][0].value
    print("\n=== APPROVAL NEEDED ===\nline:", payload["line"])
    for r in payload["rejected"]: print(f"  rejected {r['id']} at {r['died_at']}: {r['text']} — {r['reason']}")
    ans = "y" if auto else input("approve? [y/N] ")
    out = app.invoke(Command(resume={"approved": ans.lower().startswith("y"), "by": "rep"}), cfg)
print("\n=== TRACE ===")
for s in out["trace"]: print(f"  [{s['actor']:5}] {s['step']:32} {s['detail']}  ({s['label']})")
print("\nlabel:", out.get("label"), "| sent:", out.get("sent"))
if "--export" in sys.argv:
    path = sys.argv[sys.argv.index("--export") + 1]
    json.dump(export_trace(out, load_prospects()[pid]), open(path, "w"), indent=2); print("exported", path)
