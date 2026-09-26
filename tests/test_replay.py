import sys; sys.path.insert(0, "src")
from salesagent.evals.runner import run_one
from salesagent.replay import build_replay
def test_replay_has_eight_stops():
    r = run_one("sunidhi", "T7", approve=True); rp = build_replay(r)
    assert rp["kind"] == "sales.replay.v1" and [s["n"] for s in rp["stops"]] == list(range(1, 9))
    assert rp["stops"][1]["sources"] and rp["stops"][2]["golden"]
