# Handoff — v2, the T-series runtime

**One line:** the runtime rebuilds the experiment's T7 prompt from the source systems — all seven blocks match the hand-assembled originals — and runs it on Fable 5.1 so the claim can be tested on demand, repeated, and replayed for students.

## Ten minutes
```bash
./setup_env.sh && make test && make series
```
Then add `ANTHROPIC_API_KEY` (and `LANGSMITH_API_KEY`) to `.env`, `make verify`, `make series`.

## What ran before handover (replay stub, no Docker, no key)
- 11/11 tests · golden prompt 7/7 blocks match the experiment
- T0→T7 reproduces the experiment's verdicts; T1 identical across writers, as recorded
- T7: procedure verified, survivor = the known line, approval paused and resumed, sent once; Nikhil declined before the model
- Replay export: eight stops written
- **Not run here:** Fable on the API, LangSmith. Your first `make series` on the API is the real test.

## Done, first milestone
T0→T7 on Fable at k=3, the table in `findings/`, the replay imported on the site, and the human review sheet marked.
