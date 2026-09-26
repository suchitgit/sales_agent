# Sales agent kit v2 — the T-series runtime

Read this once, top to bottom. Everything needed to run, extend and debug the kit without asking.

## 1 · What this proves

**The claim:** give the model the right data classes and the decision traces — the 80% — and the model — the 20% — produces a subject line a human expert would write: one that earns the read.

**The evidence it rests on** is the T0–T7 ablation: the same task given to models, adding one class of data at a time. Every class before T7 left the line a vendor sentence a competitor could write. T7 — the decision traces given as a procedure — produced **"3 new states, one payroll run, before your first joiner's salary date"**: a deadline the prospect had not computed, recombined from her own numbers.

**What this kit adds:** a runtime that **assembles each condition's prompt automatically from the source systems**, runs the model, verifies the procedure, and shows the whole run end to end — so the experiment can be re-run on demand, repeated (pass^k), and replayed for students.

## 2 · T7, exactly

| | |
|---|---|
| Blocks | **B0 + B1 + B2 + B3 + B7.** B4 (judgement) was *replaced* by B7. B5 (decision cases) was **not** in T7 |
| Who did what | **One model call did everything:** ran S1–S5, wrote three candidates, scored each against R1–R6 in order, stopped at the first failure and named it, chose the survivor |
| Models, one run each | Gemini and DeepSeek (run 1): the method ran, lines split. **Fable 5.1 and DeepSeek 4.1: intelligence** — Fable wrote the best line, and rejected a candidate at R2 as "chronic, not acute" |
| What was not yet shown | Repeat consistency. T7 was one run per model. **This kit establishes it** — `make series` runs k=3 |

The full reference is in `data/experiment/`: the blocks verbatim (`blocks_verbatim.json`), every condition by its blocks (`conditions.json`), and every recorded line and verdict (`recorded_outputs.json`).

## 3 · The 80% — where each block comes from at run time

In production each block comes from a different system. Each file in `data/sources/` stands in for one system; the orchestrator fetches from each and assembles.

| Block | Class | Source system | File | Built by |
|---|---|---|---|---|
| B0 | Basic | CRM · account master | `crm_accounts.json` | `blocks.build` |
| B1 | Current context | Social feed + Jobs feed | `social_feed.json`, `jobs_feed.json` | `blocks.build` (30-day freshness rule) |
| B2 | Dormant | CRM · activity notes | `crm_notes.json` | `blocks.build` — injection-like notes flagged and excluded |
| B3 | Derived | **None — computed at run time** | — | `sources/derive.py`, deterministic rules |
| B4 | Judgement | Knowledge graph | `knowledge_graph/judgement_rules.json` | `blocks.build` |
| B5 | Decision | System of record | `system_of_record/decision_cases.json` | `blocks.build` |
| B7 | Decision traces | Knowledge graph | `knowledge_graph/traces.json` | `blocks.build` — the experiment's wording, verbatim |

**The golden-prompt test** checks that every block the runtime rebuilds from these sources is identical to the block a human assembled by hand in the experiment. It passes for all seven. That is the runtime demonstration in one test.

## 4 · The 20% — the writer

`MODEL_WRITER=claude-fable-5-1` — T7 parity. `MODEL_WRITER_2=claude-sonnet-5` for the cross-model checks. Anthropic API only.
- **T0–T5:** one call, writes one subject line.
- **T7:** one call runs the whole procedure and returns JSON — seller steps, three candidates with their R-checks in order, the survivor. The JSON format is a runtime addition appended *after* B7; the experiment's blocks are untouched.

**Without a key**, the writer is a **replay stub**: it returns the experiment's recorded output for each condition. It proves the pipeline, never the model. Every trace says `replay-stub` when it is in use.

## 5 · The flow of one run

```
query
 → fetch        code    seven source systems, each timed; B3 derived from three of them
 → assemble     code    exactly the condition's blocks, in the experiment's order, no truncation;
                        golden-prompt match recorded
 → write        MODEL   the writer — one call (T0–T5: a line · T7: the whole procedure)
 → verify       code    T7 only: 3 candidates · checks in order · stopped at first failure ·
                        survivor passed all six. Code checks the procedure; it does not re-judge the line
 → approve      HUMAN   interrupt() with the survivor and the rejections
 → send         code    idempotent key; label HYPOTHESIS until the outcome returns
```
A prospect with no live trigger (Nikhil) declines at `assemble` — the model is never called.

## 6 · Evaluation

Per run (`evals/checks.py`), all proxies — **your verdict in `data/runs/human_review.csv` is the final call**:

| Check | Meaning |
|---|---|
| `verdict_proxy` | INTELLIGENCE if the line carries a computed deadline tied to her event; else AUTOMATION |
| `reproduces_experiment` | the proxy verdict matches the experiment's for this condition (T4 accepts either — it was unstable) |
| `known_similarity` | token overlap with the known line (T7) |
| `golden_prompt` | the assembled blocks equal the experiment's |
| `injection_excluded` | note n11 never reached the prompt |
| `procedure_adherence` | T7: the writer followed the procedure |
| `identical_across_writers` | two writers, same line — the T1 finding |
| pass^k | `reproduces_experiment` across k repeats |

**The independent verifier** (`evals/verifier.py`, `--verify`) scores the final line against the *calibrated* reader wording, all six checks, no break. It is evidence, never the gate. Its wording lives in `knowledge_graph/reader_calibrated.json` — separate from the traces the writer sees.

## 7 · Monitoring and the classroom replay

- **LangSmith** — set `LANGSMITH_API_KEY`; every run is traced with its condition as a tag. `make langsmith` runs an experiment over all conditions; compare experiments per writer model.
- **DeepEval** — `make deepeval` scores the saved runs; `--judge` adds an Anthropic-backed novelty metric. Never set `OPENAI_API_KEY`.
- **Replay** — `make replay` writes `sales.replay.v1`: eight stops, query to line — the fetches with timings, the assembled prompt with its golden match, the model's run with tokens and latency, the verification, the eval, the approval, and the T0→T7 strip. Import it on the sales agent site.

## 8 · Commands

```bash
./setup_env.sh            # no Docker needed
make test                 # 11 tests, replay stub
make series               # T0→T7 on Fable, k=3
make series2              # both writers — the T1 check
make t7                   # one full run, approval pause, verifier
make replay               # the classroom replay
make langsmith · make deepeval
```

## 9 · Debugging guide

| Symptom | Look at |
|---|---|
| Golden-prompt test fails | A source file or `blocks.build` changed. Diff the block against `blocks_verbatim.json`; whitespace is normalised, words are not |
| T7 output not valid JSON | The writer ignored the output-format block. Recorded as a procedure failure — keep it; that's data |
| `procedure_adherence` false | Read `verification.issues`: out of order, no stop at first failure, or survivor not all-pass. This is the model not following the trace — a finding, not a bug |
| T0–T5 look like intelligence on the API | Possible — models change. Record it; it would weaken the claim, and that matters |
| Nikhil writes a line | Freshness rule bypassed — `sources/adapters.py::social_post` |
| n11 in the prompt | `sources/adapters.py::crm_notes` sanitise step |
| `replay-stub` in a trace when you expected the API | `ANTHROPIC_API_KEY` empty or `STUB_MODEL=1` |

**Rules that must survive any change:** conditions are defined by `conditions.json` only · no truncation in assemble · the writer receives the experiment's verbatim traces · the verifier never gates · the human verdict is final · API models only · synthetic data only.

## 10 · Known gaps

- **D5–D7** were in the experiment and are not recoverable; B5 has D1–D4.
- **T0–T5 task wording** is reconstructed; T7's task is verbatim (part of B7).
- The company is **LogiTrans**, a synthetic stand-in for the placeholder name in the experiment.
- The knowledge graph and system of record are files standing in for Neo4j and Postgres; the adapters are the seam where the real systems plug in.
