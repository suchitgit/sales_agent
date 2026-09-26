"""DeepEval over the latest conditions table: deterministic metrics from the saved runs, plus an optional
judged novelty metric (Anthropic-backed; never OpenAI). Usage: python scripts/eval_deepeval.py [--judge]"""
import sys, json, glob
sys.path.insert(0, "src")
from salesagent import config
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

runs = [json.load(open(f)) for f in sorted(glob.glob(str(config.RUNS / "*_T*_*.json")))]
cases = []
for r in runs:
    line = r["checks"]["line"] or "(declined)"
    tc = LLMTestCase(input=f"What she already knows: {r['blocks'].get('B1','')}", actual_output=line, metadata={"checks": r["checks"]})
    tc.name = f"{r['condition_id']}·{r['prospect_id']}"; cases.append(tc)
metrics = [Flag("reproduces_experiment", "Reproduces the experiment"), Flag("golden_prompt", "Golden prompt"), Flag("injection_excluded", "Injection excluded"), Flag("procedure_adherence", "Procedure adherence (T7)")]
if "--judge" in sys.argv and not config.USE_STUB:
    from salesagent.evals.judge import AnthropicJudge
    metrics.append(GEval(name="Novelty (judged)", criteria="INPUT is what the prospect already knows. Score high only if ACTUAL_OUTPUT adds a deadline, consequence or number she has not worked out, about her situation now.",
                         evaluation_params=[SingleTurnParams.INPUT, SingleTurnParams.ACTUAL_OUTPUT], model=AnthropicJudge(), threshold=0.7))
evaluate(test_cases=cases, metrics=metrics)
