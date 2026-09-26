"""Build the classroom replay (sales.replay.v1) from the latest saved run of a condition.
Usage: python scripts/export_replay.py [condition] [out.json]   (default T7) — run run_one or run_conditions first."""
import sys, json, glob, os
sys.path.insert(0, "src")
from salesagent import config
from salesagent.replay import build_replay
cid = sys.argv[1] if len(sys.argv) > 1 else "T7"
files = sorted(glob.glob(str(config.RUNS / f"*_{cid}_*.json")))
assert files, f"no saved run for {cid} — run scripts/run_conditions.py --only {cid} first"
run = json.load(open(files[-1]))
table = json.load(open(config.RUNS / "conditions_latest.json")) if os.path.exists(config.RUNS / "conditions_latest.json") else None
out = sys.argv[2] if len(sys.argv) > 2 else str(config.RUNS / f"replay_{cid}.json")
json.dump(build_replay(run, table), open(out, "w"), indent=2, default=str)
print("replay written:", out, "· import it on the sales agent site → Replay")
