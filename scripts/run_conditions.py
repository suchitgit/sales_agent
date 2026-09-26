"""The T-series, live. Usage: python scripts/run_conditions.py [k] [--two-writers] [--only T1,T7] [--prospect sunidhi]
Writes data/runs/conditions_latest.json and data/runs/human_review.csv"""
import sys
sys.path.insert(0, "src")
from salesagent import config
from salesagent.evals.runner import run_conditions, print_table, save_table
k = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 1
only = sys.argv[sys.argv.index("--only") + 1].split(",") if "--only" in sys.argv else None
pid = sys.argv[sys.argv.index("--prospect") + 1] if "--prospect" in sys.argv else "sunidhi"
writers = (1, 2) if "--two-writers" in sys.argv else (1,)
res = run_conditions(pid, only, k, writers)
print_table(res)
save_table(res)
print("\nwrote data/runs/conditions_latest.json and data/runs/human_review.csv — the human verdict column is the final call")
