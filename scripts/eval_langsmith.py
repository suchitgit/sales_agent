"""A LangSmith experiment across conditions: dataset = (prospect, condition); target = the runtime;
evaluators = the checks. Compare experiments per writer model in the LangSmith UI.
Usage: python scripts/eval_langsmith.py [prefix]"""
import sys, os
sys.path.insert(0, "src")
from salesagent.evals import tracing
assert tracing.enable(), "LANGSMITH_API_KEY missing in .env"
from langsmith import Client
from salesagent import config
from salesagent.evals.runner import run_one, ALL
client = Client(); DS = "sales-agent-t-series"
if not client.has_dataset(dataset_name=DS):
    ds = client.create_dataset(dataset_name=DS, description="T0–T7 conditions for Sunidhi, plus T7 for the null prospect")
    ex = [{"prospect_id": "sunidhi", "condition_id": c} for c in ALL] + [{"prospect_id": "nikhil", "condition_id": "T7"}]
    client.create_examples(dataset_id=ds.id, inputs=ex, outputs=[{"condition": e["condition_id"]} for e in ex])
config.SEND_APPROVAL_REQUIRED = False
def target(inputs): r = run_one(inputs["prospect_id"], inputs["condition_id"]); return {"checks": r["checks"], "declined": r.get("declined")}
def ev(name):
    def f(inputs, outputs, reference_outputs):
        v = outputs["checks"].get(name); return {"key": name, "score": None if v is None else (float(v) if isinstance(v, (int, float, bool)) else (1.0 if v == "INTELLIGENCE" else 0.0))}
    f.__name__ = name; return f
res = client.evaluate(target, data=DS, evaluators=[ev(n) for n in ("reproduces_experiment", "known_similarity", "golden_prompt", "injection_excluded", "procedure_adherence", "verdict_proxy")],
                      experiment_prefix=sys.argv[1] if len(sys.argv) > 1 else f"writer-{config.MODEL_WRITER}", metadata={"writer": config.MODEL_WRITER, "stub": config.USE_STUB})
print("experiment:", getattr(res, "experiment_name", "done"))
