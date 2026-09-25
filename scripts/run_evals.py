"""Run the suite at pass^k and export sales.eval.v1. Usage: python scripts/run_evals.py [k] [out.json]"""
import sys, json
sys.path.insert(0, "src")
from salesagent.evals.suite import run_suite
k = int(sys.argv[1]) if len(sys.argv) > 1 else 3
res = run_suite(k)
for s in res["scenarios"]:
    print(f"{s['id']:10} pass^{k} {s['passes']}/{s['runs']}  " + "  ".join(f"{c}={'ok' if v else 'FAIL'}" for c, v in s["checks"].items()))
out = sys.argv[2] if len(sys.argv) > 2 else "data/synthetic/eval.json"
json.dump(res, open(out, "w"), indent=2); print("exported", out)
