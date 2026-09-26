# Rules for Claude Code — sales agent kit v2 (T-series runtime)

Read README.md first. It explains the claim, T7 exactly, and every component.

## The goal — do not drift from it
Test one claim: **the right data classes plus the decision traces (the 80%) let the model (the 20%) write the
line a human expert would write.** The runtime assembles each T-condition from the source systems, runs the
writer, verifies the procedure, and shows the run end to end. It is **not** a reader-calibration project;
the independent reader is a verifier only.

## What to do, in order
1. `make test` and `make verify` — 11 tests and the checks, on the replay stub.
2. Add `ANTHROPIC_API_KEY`, rerun `make verify` — the Fable check runs one real T7.
3. `make series` — T0→T7 on Fable, k=3. Save the table. **This is the headline result.**
4. `make series2` — both writers. The T1 identical-sentence check and cross-model T7.
5. `make t7` then `make replay` — one full run with the approval pause, and its classroom replay.
6. `make langsmith` and `make deepeval` — the same runs, in the monitoring and eval tools.
7. Write `findings/<date>_t_series_api.md`: the table, where the API matched the experiment and where it didn't.
   Hand `data/runs/human_review.csv` to Suchit — his verdict column is the final call.

## Rules
- **Conditions are data.** `data/experiment/conditions.json` defines every run by its blocks. Never hard-code a condition in Python.
- **T7 = B0+B1+B2+B3+B7.** B4 is replaced by B7; B5 is absent. As in the experiment.
- **No truncation, no budget** in `assemble`. The experiment had none; a token budget is a later tuning experiment.
- **The writer sees the experiment's verbatim traces** (`knowledge_graph/traces.json`). The calibrated wording in `reader_calibrated.json` is for the verifier only. Never swap them.
- **The golden-prompt test must stay green.** If you change a source file or a builder, the rebuilt block must still equal the experiment's.
- **Code verifies the procedure; it does not judge the line.** The human does.
- **API only.** The stub is a replay of recorded outputs and is labelled as such.
- **Keep failures.** A T7 run that breaks the procedure, a T0–T5 line that looks intelligent, a writer that disagrees with the experiment — record all of it.
- Small steps, `make test` after each, ask before installing. Synthetic data only.

## Next, only after step 7
- Durable approval on Postgres (`requirements-optional.txt`, `docker compose up -d`).
- Neo4j and Postgres adapters behind `sources/adapters.py`, with a test that each returns the same records as the file adapters.
- Token-budget experiment: does trimming any block change the T7 result?
- More prospects, generated in the shape of the sources.
