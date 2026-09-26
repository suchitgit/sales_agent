"""The verifier catches a writer that does not follow the procedure."""
import sys; sys.path.insert(0, "src")
from salesagent.graph import nodes

def _state(cands, surv):
    return {"condition_id": "T7", "candidates": cands, "survivor": surv}

def test_out_of_order_and_no_stop_are_caught():
    bad = [{"text": "a", "died_at": "R2", "checks": [{"id": "R2", "pass": False}]},
           {"text": "b", "died_at": "R1", "checks": [{"id": "R1", "pass": False}, {"id": "R2", "pass": True}]},
           {"text": "c", "died_at": None, "checks": [{"id": f"R{i}", "pass": True} for i in range(1, 7)]}]
    v = nodes.verify(_state(bad, "c"))["verification"]
    assert not v["adherence"] and len(v["issues"]) >= 2

def test_survivor_must_pass_all_six():
    c = [{"text": "x", "died_at": None, "checks": [{"id": f"R{i}", "pass": True} for i in range(1, 5)]}] * 3
    assert not nodes.verify(_state(c, "x"))["verification"]["adherence"]
