# Observability add-on — LangSmith tracing + DeepEval evaluation

Drop these files into the kit (paths match), append `.env.additions` to `.env`, then
`pip install -r requirements-observability.txt`.

## What each does
| Piece | Role | Costs a model call? |
|---|---|---|
| `evals/tracing.py` | Turns on LangSmith tracing from env vars. LangGraph then records every node, every model call, every interrupt/resume — nothing in the spine changes | No |
| `evals/judge.py` | DeepEval's judge model, backed by the Anthropic API. A **third** model role: it grades; it never writes or scores in the spine | Only when used |
| `evals/deepeval_metrics.py` | Our five checks as DeepEval metrics, scored from the trace (deterministic, free) + one GEval "Novelty (judged)" metric | GEval only |
| `scripts/eval_deepeval.py` | Runs the spine k× per prospect, scores with DeepEval, exports `sales.deepeval.v1` | Spine runs; judge with `--judge` |
| `scripts/eval_langsmith.py` | Creates a LangSmith dataset of the seed prospects, runs the spine as the target, attaches our checks as evaluators, and the **known-winner guard** — the experiment view then compares readers over time | Spine runs |
| `tests/test_deepeval_metrics.py` | The deterministic metrics agree with the suite, on the stub | No |

## The three model roles — keep them separate
| Role | Model | Where |
|---|---|---|
| Writer | `MODEL_MEDIUM` | `nodes.py::generate` |
| Reader | `MODEL_SMALL` (or swapped) | `nodes.py::score` |
| Judge | `AnthropicJudge` (defaults to `MODEL_MEDIUM`) | DeepEval GEval only |
The judge grades the *line*, independently of the reader's verdict. When reader and judge disagree, that disagreement is a result, not noise — record it.

## Commands
```bash
make test                                   # includes the new metric tests, stub, no key
python scripts/eval_deepeval.py 3           # deterministic metrics on the API (or stub)
python scripts/eval_deepeval.py 3 --judge   # + the judged novelty metric
python scripts/eval_langsmith.py reader-haiku   # experiment, tagged with the reader in use
python scripts/eval_langsmith.py reader-sonnet  # swap MODEL_SMALL in .env first
```
Then open LangSmith → project `sales-agent` for traces; → Datasets → `sales-agent-seed-prospects` for the experiments side by side.

## What to look at first
1. In LangSmith, one Sunidhi trace end to end: 7 nodes, the two model-call points, the interrupt and the resume.
2. Two experiments, `reader-haiku` and `reader-sonnet`, on the same dataset. Each prospect runs k times (`--k`, default 3). Two experiment-level columns from one guard pass: `known_winner_clears` is the guard test — every known-good line in `data/seed/known_winners.json` (written by a person) scored by that experiment's reader, k out of k (same as `make guard`); `verdict_consistency` is the same line, same reader, same verdict k of k. On the stub the second column is `path_consistency` instead (one step path per prospect), because on the API different candidates legitimately take different paths. The per-run columns (`r3`, `competitor`, `null_safety`, `trace`) give pass^k per prospect.
3. In DeepEval's output: rows where the deterministic R3 (the reader's verdict) and the judged Novelty disagree.

## Rules
- Never set `OPENAI_API_KEY`; the judge is Anthropic-backed by design.
- Tracing is on/off by env var; the spine has no LangSmith code in it.
- The deterministic metrics must always agree with `evals/checks.py` — `test_deepeval_metrics.py` guards this.
