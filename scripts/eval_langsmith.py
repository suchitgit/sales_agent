"""LangSmith experiment: a dataset of the seed prospects, the spine as the target, our checks as
evaluators. Every run is traced; the experiment view compares runs over time and across models.
Usage: python scripts/eval_langsmith.py [experiment-prefix]"""
import sys, os
sys.path.insert(0, "src")
from salesagent.evals import tracing
assert tracing.enable(), "LANGSMITH_API_KEY missing in .env"
from langsmith import Client
from salesagent import config
from salesagent.evals.suite import run_once
from salesagent.stores.context import load_prospects
from salesagent.evals.checks import CHECKS

client = Client()
DATASET = "sales-agent-seed-prospects"
prospects = load_prospects()
if not client.has_dataset(dataset_name=DATASET):
    ds = client.create_dataset(dataset_name=DATASET, description="Seed prospects incl. the null case; the known winning line for Sunidhi")
    client.create_examples(dataset_id=ds.id,
        inputs=[{"prospect_id": pid} for pid in prospects],
        outputs=[{"expect": p["expect"], "known_winner": "3 new states, one payroll run, before your first joiner's salary date" if pid == "sunidhi" else None} for pid, p in prospects.items()])

def target(inputs: dict) -> dict:
    run = run_once(inputs["prospect_id"], f"ls-{inputs['prospect_id']}-{os.getpid()}")
    return {"winner": run["winner"]["text"] if run.get("winner") else None, "declined": run.get("declined", False),
            "died": [(c["id"], c.get("died_at")) for c in run.get("candidates", [])], "run": {k: run.get(k) for k in ("winner", "candidates", "trace", "declined", "prompt")}}

def make_evaluator(name, fn):
    def ev(inputs, outputs, reference_outputs):
        p = prospects[inputs["prospect_id"]]
        return {"key": name, "score": 1.0 if fn(p, outputs["run"]) else 0.0}
    ev.__name__ = name
    return ev

def guard_known_winner(inputs, outputs, reference_outputs):
    """The known winning line must not be rejected by the reader — if it is, the checks are wrong."""
    if inputs["prospect_id"] != "sunidhi": return {"key": "known_winner_clears", "score": None}
    return {"key": "known_winner_clears", "score": 1.0 if outputs["winner"] else 0.0}

prefix = sys.argv[1] if len(sys.argv) > 1 else f"reader-{config.MODEL_SMALL}"
res = client.evaluate(target, data=DATASET, evaluators=[make_evaluator(n, f) for n, f in CHECKS.items()] + [guard_known_winner],
                      experiment_prefix=prefix, metadata={"writer": config.MODEL_MEDIUM, "reader": config.MODEL_SMALL, "stub": config.USE_STUB})
print("experiment:", getattr(res, "experiment_name", prefix))
