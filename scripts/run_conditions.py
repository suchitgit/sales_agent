"""The T-series, live. Usage: python scripts/run_conditions.py [k] [--two-writers] [--only T1,T7] [--prospect sunidhi]
Writes data/runs/conditions_latest.json and data/runs/human_review.csv"""
import sys, json, csv
sys.path.insert(0, "src")
from salesagent import config
from salesagent.evals.runner import run_conditions
k = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 1
only = sys.argv[sys.argv.index("--only") + 1].split(",") if "--only" in sys.argv else None
pid = sys.argv[sys.argv.index("--prospect") + 1] if "--prospect" in sys.argv else "sunidhi"
writers = (1, 2) if "--two-writers" in sys.argv else (1,)
res = run_conditions(pid, only, k, writers)
print(f"{'COND':6} {'WRITER':22} {'VERDICT(proxy)':16} {'EXP?':5} {'KNOWN~':6} LINE")
for r in res["rows"]:
    print(f"{r['condition']:6} {('replay-stub' if r['stub'] else r['writer']):22} {','.join(r['verdicts']):16} {r['reproduces_experiment_passk']}/{r['k']}  {r['known_similarity_max']:<6} {r['lines'][0][:80] if r['lines'][0] else '—'}"
          + (f"   [identical across writers: {r['identical_across_writers']}]" if "identical_across_writers" in r else "")
          + (f"   [procedure: {r['procedure_adherence']}]" if r['condition'] == 'T7' else ""))
config.RUNS.mkdir(parents=True, exist_ok=True)
json.dump(res, open(config.RUNS / "conditions_latest.json", "w"), indent=2)
with open(config.RUNS / "human_review.csv", "w", newline="") as f:
    wr = csv.writer(f); wr.writerow(["condition", "writer", "run", "line", "proxy_verdict", "HUMAN_VERDICT (automation/intelligence)", "HUMAN_NOTE"])
    for r in res["rows"]:
        for i, (l, v) in enumerate(zip(r["lines"], r["verdicts"])): wr.writerow([r["condition"], r["writer"], i + 1, l, v, "", ""])
print("\nwrote data/runs/conditions_latest.json and data/runs/human_review.csv — the human verdict column is the final call")
