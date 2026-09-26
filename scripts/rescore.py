"""Re-score the latest series from its saved runs — no model calls. Use it when the line extraction or a check
changes: every run keeps the writer's raw answer, so the table can be rebuilt without paying for the series again.
Usage: python scripts/rescore.py        (rewrites the saved runs' line/checks, conditions_latest.json, human_review.csv)"""
import sys, json, glob
sys.path.insert(0, "src")
from salesagent import config
from salesagent.models import extract_line
from salesagent.evals.checks import score
from salesagent.evals.runner import table_row, mark_identical, print_table, save_table

latest = json.load(open(config.RUNS / "conditions_latest.json"))
cutoff = latest["createdAt"] / 1000 + 1
saved = []
for f in sorted(glob.glob(str(config.RUNS / f"*_T*_{latest['prospect']}_w*.json"))):
    r = json.load(open(f)); r["_file"] = f
    if r.get("at", 0) <= cutoff: saved.append(r)
rows = []
for old in latest["rows"]:
    mine = [r for r in saved if r["condition_id"] == old["condition"] and ((r.get("usage") or {}).get("model") or "").endswith(old["writer"]) or
            (r["condition_id"] == old["condition"] and old["stub"] and str((r.get("usage") or {}).get("model", "")).startswith("replay"))][-old["k"]:]
    assert len(mine) == old["k"], f"{old['condition']} {old['writer']}: found {len(mine)} saved runs, expected {old['k']}"
    for r in mine:
        if r.get("line") is not None or "survivor" not in r:  # single-line condition: re-extract from the raw answer
            r["line"] = extract_line(r.get("raw", ""))
        r["checks"] = score(r)
        f = r.pop("_file"); json.dump(r, open(f, "w"), indent=2, default=str)
    rows.append(table_row(old["condition"], old["writer"], old["stub"], [r["checks"] for r in mine]))
mark_identical(rows)
res = {**latest, "rows": rows, "rescored": True}
print_table(res); save_table(res)
print("\nre-scored from saved runs (no model calls) · rewrote conditions_latest.json and human_review.csv")
