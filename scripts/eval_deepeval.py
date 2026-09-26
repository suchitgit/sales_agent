"""DeepEval over the saved runs: deterministic metrics from each run's checks, plus an optional judged novelty
metric (Anthropic-backed; never OpenAI). Real API runs only unless --include-stub.
Usage: python scripts/eval_deepeval.py [--judge] [--include-stub]
Writes data/runs/deepeval_latest.json (one row per run, every metric's score and reason)."""
import sys, json, glob, time
sys.path.insert(0, "src")
from salesagent import config
from salesagent.evals.verifier import known_to_her
from deepeval import evaluate
from deepeval.metrics import BaseMetric, GEval
from deepeval.test_case import LLMTestCase, SingleTurnParams

class Flag(BaseMetric):
    def __init__(self, key, label): self.key, self.label, self.threshold = key, label, 1.0
    @property
    def __name__(self): return self.label
    def measure(self, tc, *a, **k):
        v = tc.metadata["checks"].get(self.key)
        self.score = 1.0 if v in (True, None) else (v if isinstance(v, float) else 0.0); self.success = self.score >= self.threshold
        self.reason = f"{self.key}={v}"; return self.score
    async def a_measure(self, tc, *a, **k): return self.measure(tc)
    def is_successful(self): return bool(self.success)

is_stub = lambda r: str((r.get("usage") or {}).get("model") or "").startswith("replay") or r.get("declined")
runs = [json.load(open(f)) for f in sorted(glob.glob(str(config.RUNS / "*_T*_*.json")))]
runs = [r for r in runs if "--include-stub" in sys.argv or not is_stub(r)]
cases = []
for r in runs:
    line = r["checks"]["line"] or "(declined)"
    # the judge is told what the verifier is told: this week's context and her own experiences (decision 3, 26 Sep)
    tc = LLMTestCase(input=f"What she already knows: {known_to_her(r['prospect_id'], r['blocks'].get('B1', ''))}", actual_output=line,
                     metadata={"checks": r["checks"]})
    tc.name = f"{r['condition_id']}·{r['prospect_id']}·{r['at']}"; cases.append(tc)
metrics = [Flag("reproduces_experiment", "Reproduces the experiment"), Flag("golden_prompt", "Golden prompt"), Flag("injection_excluded", "Injection excluded"), Flag("procedure_adherence", "Procedure adherence (T7)")]
judge = "--judge" in sys.argv and not config.USE_STUB
if judge:
    from salesagent.evals.judge import AnthropicJudge
    metrics.append(GEval(name="Novelty (judged)", criteria="INPUT is what the prospect already knows. Score high only if ACTUAL_OUTPUT adds a deadline, consequence or number she has not worked out, about her situation now.",
                         evaluation_params=[SingleTurnParams.INPUT, SingleTurnParams.ACTUAL_OUTPUT], model=AnthropicJudge(), threshold=0.7))
print(f"DeepEval over {len(cases)} saved {'runs' if '--include-stub' in sys.argv else 'API runs'} · judge: {config.MODEL_READER if judge else 'off'}")
res = evaluate(test_cases=cases, metrics=metrics)
by_name = {tc.name: (r, tc) for r, tc in zip(runs, cases)}
rows = []
for tr in res.test_results:
    r, tc = by_name[tr.name]
    rows.append({"condition": r["condition_id"], "prospect": r["prospect_id"], "writer": (r.get("usage") or {}).get("model"), "at": r["at"],
                 "line": tc.actual_output, "success": tr.success,
                 "metrics": {m.name: {"score": m.score, "success": m.success, "reason": m.reason} for m in (tr.metrics_data or [])}})
rows.sort(key=lambda x: x["at"])
out = {"kind": "sales.deepeval.v2", "createdAt": int(time.time() * 1000), "judge": config.MODEL_READER if judge else None, "rows": rows}
json.dump(out, open(config.RUNS / "deepeval_latest.json", "w"), indent=2)
print(f"\n{sum(r['success'] for r in rows)}/{len(rows)} runs passed every metric · wrote {config.RUNS / 'deepeval_latest.json'}")
