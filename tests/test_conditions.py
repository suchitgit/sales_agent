import sys, json; sys.path.insert(0, "src")
from salesagent import config
from salesagent.evals.runner import run_one, run_conditions

def test_conditions_use_exactly_their_blocks():
    conds = {c["id"]: c for c in json.load(open(config.EXPERIMENT / "conditions.json"))["conditions"]}
    assert conds["T7"]["blocks"] == ["B0", "B1", "B2", "B3", "B7"], "T7 = B4 replaced by B7, B5 absent"
    r = run_one("sunidhi", "T7", approve=False)
    assert "[B4 · JUDGMENT DATA]" not in r["prompt"] and "[B5 · DECISION DATA]" not in r["prompt"] and "[B7 · DECISION TRACES]" in r["prompt"]

def test_t7_procedure_verified_and_known_line():
    r = run_one("sunidhi", "T7", approve=True)
    assert r["verification"]["adherence"] and r["survivor"] == r["checks"]["line"]
    assert r["checks"]["verdict_proxy"] == "INTELLIGENCE" and r["sent"]["status"] in ("sent", "already_sent")

def test_series_reproduces_the_experiment_on_replay():
    res = run_conditions("sunidhi", k=1)
    bad = [r["condition"] for r in res["rows"] if r["reproduces_experiment_passk"] != r["k"]]
    assert not bad, f"conditions not reproducing the experiment's verdict: {bad}"

def test_null_prospect_declines_before_the_model():
    r = run_one("nikhil", "T7", approve=True)
    assert r.get("declined") and not r.get("survivor") and r["sent"]["status"] == "not_sent"

def test_spine_order():
    r = run_one("sunidhi", "T7", approve=True)
    steps = [s["step"].split(" ·")[0] for s in r["trace"]]
    assert steps.index("assemble") < steps.index("write") < steps.index("verify") < steps.index("send")
