"""Run the spine on every seed prospect k times and score each run with the DeepEval metrics.
Deterministic metrics always run; the judged novelty metric runs only with an API key and --judge.
Usage: python scripts/eval_deepeval.py [k] [--judge]
Results also land in LangSmith when tracing is on."""
import sys, json, time
sys.path.insert(0, "src")
from salesagent.evals import tracing; tracing.enable()
from salesagent import config
from salesagent.evals.suite import run_once
from salesagent.stores.context import load_prospects
from salesagent.evals.deepeval_metrics import DETERMINISTIC, novelty_geval, case_from_run
from deepeval import evaluate

k = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 3
use_judge = "--judge" in sys.argv and not config.USE_STUB
metrics = [m() for m in DETERMINISTIC]
if use_judge:
    from salesagent.evals.judge import AnthropicJudge
    metrics.append(novelty_geval(AnthropicJudge()))
print(f"tracing: {tracing.status()} · model: {'STUB' if config.USE_STUB else config.MODEL_MEDIUM} · judge: {'on' if use_judge else 'off'}")

cases = []
for pid, p in load_prospects().items():
    for i in range(k):
        run = run_once(pid, f"de-{pid}-{i}")
        tc = case_from_run(p, run); tc.name = f"{pid}#{i}"
        cases.append(tc)
res = evaluate(test_cases=cases, metrics=metrics)
# a flat summary the site and the deck can use
summary = {"kind": "sales.deepeval.v1", "k": k, "createdAt": int(time.time() * 1000), "judge": use_judge, "rows": []}
for tr in res.test_results:
    summary["rows"].append({"case": tr.name, "success": tr.success,
                            "metrics": [{"name": m.name, "score": m.score, "success": m.success, "reason": m.reason} for m in (tr.metrics_data or [])]})
out = "data/synthetic/deepeval.json"; json.dump(summary, open(out, "w"), indent=2)
print(f"\n{sum(r['success'] for r in summary['rows'])}/{len(summary['rows'])} cases passed all metrics · exported {out}")
