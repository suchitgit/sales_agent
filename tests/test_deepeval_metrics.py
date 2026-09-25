"""The deterministic metrics agree with the eval suite's checks — no API needed."""
import sys; sys.path.insert(0, "src")
from salesagent.evals.suite import run_once
from salesagent.stores.context import load_prospects
from salesagent.evals.deepeval_metrics import DETERMINISTIC, case_from_run

def _scores(pid):
    p = load_prospects()[pid]; run = run_once(pid, f"tm-{pid}")
    tc = case_from_run(p, run)
    return {m.__name__: m.measure(tc) for m in (M() for M in DETERMINISTIC)}

def test_sunidhi_all_deterministic_metrics_pass():
    assert all(v == 1.0 for v in _scores("sunidhi").values())

def test_nikhil_null_metrics_pass():
    s = _scores("nikhil"); assert s["Null safety"] == 1.0 and s["R3 novelty (from trace)"] == 1.0

def test_injection_guard_scores_from_trace():
    assert _scores("sunidhi")["Injection guard"] == 1.0
