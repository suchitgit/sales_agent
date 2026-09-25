# Handoff — the sales agent kit, to Claude Code

A working skeleton, not an empty one. Everything below ran before packaging.

## In ten minutes
```bash
chmod +x setup_env.sh && ./setup_env.sh        # or make setup · or ./setup_env.sh --no-docker
python scripts/run_one.py sunidhi --auto        # the whole spine on the stub model
make test                                       # 11 tests
python scripts/ablation.py sunidhi               # the Day 4 demo, on the stub
```
Then add `ANTHROPIC_API_KEY` to `.env` and run `make verify` — the last two checks make real API calls, including a full run on Sunidhi. Then `claude`.

## What is in the kit
| | |
|---|---|
| `data/seed/` | The T0–T7 blocks as files: prospects (Sunidhi, Arun, and Nikhil the null case), six dormant CRM notes plus one deliberate injection, the capability catalogue, D1–D4 with choice sets, the judgement rules, both traces, archetypes and trigger→pain mappings, the rep profile |
| `src/salesagent/graph/` | The spine: 7 nodes, order enforced by a test |
| `src/salesagent/stores/` | Context (with a freshness rule), Retrieval (BM25), Memory (Store + system of record), Knowledge graph (Kùzu / Neo4j) |
| `src/salesagent/guards/` | Sanitise, approval interrupt, send-once |
| `src/salesagent/evals/` | Five checks, pass^k, `sales.trace.v1` and `sales.eval.v1` exporters |
| `src/salesagent/models.py` | Anthropic API via `ChatAnthropic`; a deterministic stub when the key is empty |
| `scripts/` | `run_one` (with approval prompt), `run_evals`, `seed_postgres`, `seed_graph`, `record_outcome`, `verify_env` |
| `tests/` | Seed integrity and spine behaviour |

## What ran before handover (stub model, no Docker)
- 11/11 tests · Sunidhi → the clock line computed by the (stub) model from material only, two candidates rejected at R3, approved, sent once · Nikhil → declined · the ablation flat through T5 and moving at T7 · injection note n11 visible in the trace and absent from the prompt · Kùzu seeded
- **Not run here:** Neo4j and Postgres (need Docker), and the API model checks (need a key). Your first `make verify` with services and a key is the real test.

## The demo
1. `python scripts/run_one.py sunidhi` — watch the approval prompt list the rejections, approve, see the trace.
2. `make evals` on the API — the number that matters is how far below 3/3 it lands and where.
3. `python scripts/ablation.py sunidhi` on the API: the line collapsing toward the T0 sentence as stores are removed — the Day 4 slide, running. Compare with the stub table in the README.

## Done, first milestone
- `make verify` all green with services and a key · a Sunidhi run on the API with a candidate dying at R3 · the eval export imported on the sales agent site beside the browser reference · Postgres holding the checkpoint through an approval pause and a restart
