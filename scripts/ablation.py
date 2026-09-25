"""The Day 4 demo: run one prospect with stores removed one at a time and watch the line collapse
toward the T0 sentence. Usage: python scripts/ablation.py [prospect_id]"""
import sys
sys.path.insert(0, "src")
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore
from langgraph.types import Command
from salesagent.graph.spine import build
from salesagent import config

pid = sys.argv[1] if len(sys.argv) > 1 else "sunidhi"
config.SEND_APPROVAL_REQUIRED = False  # the demo is about the line, not the send
CONFIGS = [
    ("T0 · basic only",        {"context": False, "retrieval": False, "memory": False, "kg": False}),
    ("T1 · + context",         {"context": True,  "retrieval": False, "memory": False, "kg": False}),
    ("T2 · + retrieval",       {"context": True,  "retrieval": True,  "memory": False, "kg": False}),
    ("T5 · + memory",          {"context": True,  "retrieval": True,  "memory": True,  "kg": False}),
    ("T7 · + knowledge graph", {"context": True,  "retrieval": True,  "memory": True,  "kg": True}),
    ("no context · kg only",   {"context": False, "retrieval": False, "memory": False, "kg": True}),
]
print(f"{'RUN':26} {'LINE':70} {'REJECTED':28} VERDICT")
for label, on in CONFIGS:
    app = build(checkpointer=InMemorySaver(), store=InMemoryStore())
    out = app.invoke({"prospect_id": pid, "rep_id": "rep-suchit", "thread_id": f"abl-{label}", "stores_on": on},
                     {"configurable": {"thread_id": f"abl-{label}"}})
    w = out.get("winner"); died = ", ".join(f"{c['id']}@{c['died_at']}" for c in out.get("candidates", []) if c.get("died_at")) or "—"
    scored = any(c.get("results") for c in out.get("candidates", []))
    verdict = "declined" if out.get("declined") else ("intelligence" if (w and scored) else ("automation" if w else "nothing survived"))
    print(f"{label:26} {(w['text'] if w else verdict):70} {died if scored else 'unscored — no reader trace':28} {verdict}")
print("\nRead it top to bottom: material alone does not move the line; the knowledge graph does.")
