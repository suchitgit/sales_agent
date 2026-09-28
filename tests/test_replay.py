import sys; sys.path.insert(0, "src")
from salesagent.evals.runner import run_one
from salesagent.replay import build_replay
def test_replay_has_eight_stops():
    r = run_one("sunidhi", "T7", approve=True); rp = build_replay(r)
    assert rp["kind"] == "sales.replay.v1" and [s["n"] for s in rp["stops"]] == list(range(1, 9))
    assert rp["stops"][1]["sources"] and rp["stops"][2]["golden"]

def test_rewriting_the_review_sheet_keeps_human_verdicts():
    import csv
    from salesagent import config
    from salesagent.evals.runner import save_table
    res = {"rows": [{"condition": "T1", "writer": "w", "lines": ["a line"], "verdicts": ["AUTOMATION"]}]}
    save_table(res)
    sheet = config.RUNS / "human_review.csv"
    rows = list(csv.reader(open(sheet, encoding="utf-8"))); rows[1][5], rows[1][6] = "intelligence", "mine"
    csv.writer(open(sheet, "w", newline="", encoding="utf-8")).writerows(rows)
    save_table(res)
    assert list(csv.DictReader(open(sheet, encoding="utf-8")))[0]["HUMAN_VERDICT (automation/intelligence)"] == "intelligence"
