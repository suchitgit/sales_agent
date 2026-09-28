# Sales agent — the T-series runtime (v2)

The developer landing page. Read it once, top to bottom: what the project proves, how to run it, where every
piece lives, how to change it, and how to debug it.

> **Status (28 Sep 2026):** v2 lives on branch `t-series-runtime` and is **not merged to `main`** (per
> `MIGRATION.md`). v1 is kept at tags `kit-v1` and `kit-v1.1-reader-calibration`. First API results:
> `findings/2026-09-26_t_series_api.md`. All data is synthetic.

---

## 1 · What this is

An AI agent that writes **one email subject line that earns the read** for a named sales prospect, and a runtime
that tests one claim:

> Give the model the right **data classes** and the **decision traces** (the 80%) and the model (the 20%) writes the
> line a human expert would write.

The evidence is the **T0–T7 ablation experiment**: the same task given to models, adding one class of data at a
time. Every condition before T7 produced a vendor sentence a competitor could write. **T7** — the decision traces
given as a *procedure* — produced **"3 new states, one payroll run, before your first joiner's salary date"**: a
deadline the prospect had not computed, recombined from her own numbers.

The runtime **rebuilds each condition's prompt automatically from the source systems**, runs the writer model,
checks that it followed the procedure, pauses for a human to approve the send, and records everything — so the
experiment can be re-run on demand, repeated (pass^k), and replayed for students.

**The prospects** (synthetic): **Sunidhi Rao**, VP HR at LogiTrans (expanding into 3 new states, 120 open roles) —
the full case · **Arun Deshpande**, Head of Operations at Sunrise Logistics (3 new depots) · **Nikhil Raman**, CFO at
Steady Freight — the **null case**: nothing is happening, so the right answer is to write nothing.
The seller is **HumanAITech** (payroll and HR platform, multi-state compliance, payroll consolidation, onboarding).

---

## 2 · Quick start

```bash
cd ~/fde/sales-agent
./setup_env.sh                 # .venv, packages, .env from .env.example, environment checks. No Docker needed.
source .venv/bin/activate
make test                      # 15 tests on the replay stub — no key, no network, ~1 s
```

Add to `.env` (never committed): `ANTHROPIC_API_KEY=…` and, for tracing, `LANGSMITH_API_KEY=…`. Then:

```bash
make verify                    # 8 checks, incl. one real T7 run on Fable 5.1 (a few cents)
python scripts/run_one.py sunidhi T0      # one run of one condition, printed step by step
make series                    # T0→T7, 3 runs each, on the writer — the headline table
```

**Without an API key** every command still runs: the writer becomes a **replay stub** that returns the
experiment's recorded output. It proves the pipeline, never the model, and every trace says `replay-stub`.

---

## 3 · How one run flows

A LangGraph state machine with fixed edges. The model is called at exactly one step (`write`); everything else is code.

```
input: {prospect_id, condition_id, writer_which, thread_id, query}
  │
  ├─ fetch     code   graph/nodes.py::fetch → blocks.fetch_all + blocks.build
  │                   seven source systems, each timed; B3 derived from three of them;
  │                   flagged notes (n11, the injection) set aside; no live post → declined
  ├─ assemble  code   graph/nodes.py::assemble → blocks.assemble
  │                   exactly the condition's blocks, in the experiment's order, no truncation;
  │                   golden-prompt match recorded (Sunidhi)
  ├─ write     MODEL  graph/nodes.py::write → models.get_writer
  │                   T0–T5: one call writes one line (models.extract_line strips labels)
  │                   T7:    one call runs the whole procedure, returns JSON (S1–S5, 3 candidates, R-checks, survivor)
  ├─ verify    code   graph/nodes.py::verify  (T7 only)
  │                   3 candidates · checks in order R1… · stopped at first failure · died_at matches ·
  │                   survivor passed all six. Code checks the procedure; it does not judge the line
  ├─ approve   HUMAN  graph/nodes.py::approve → guards/approval.py (interrupt)
  │                   pauses with the survivor and the rejections; only a T7 survivor that followed the procedure
  ├─ send      code   graph/nodes.py::send → guards/idempotency.py
  │                   send-once key = thread + line; label HYPOTHESIS until an outcome returns
  ▼
state: blocks, prompt, golden, line | candidates + survivor, verification, approval, sent, trace (append-only)
```

The graph is wired in `graph/spine.py`; the state fields are in `graph/state.py`. Every node appends to `trace`
as it runs, with timings.

- **Nikhil (null case)** has no live post: `fetch` marks the run declined, `assemble` writes no prompt, the model is
  never called, nothing is sent.
- **T0–T5** have no survivor, so `approve` is skipped and nothing is sent — the table is about the line.
- After the run, `scripts/run_one.py --verify` scores the final line with the **independent verifier** (§7).

---

## 4 · Repository map

```
data/
  experiment/            the experiment, as reference — never read to build a prompt
    blocks_verbatim.json     the seven blocks a human assembled by hand (the golden-prompt reference)
    conditions.json          every condition by its blocks and mode; the shared T0–T5 task sentence
    recorded_outputs.json    every recorded line and verdict; the known line; feeds the replay stub
  sources/               the source systems (files standing in for CRM, feeds, graph, system of record)
    crm_accounts.json        CRM · account master          → B0
    social_feed.json         social feed (posts, age)      → B1 (30-day freshness rule)
    jobs_feed.json           jobs feed (open roles)        → B1
    crm_notes.json           CRM · activity notes          → B2 (tags feed B3; her_experience feeds the verifier)
    knowledge_graph/
      judgement_rules.json   judgement                     → B4
      traces.json            the reader R1–R6 and seller S1–S5 traces, verbatim → B7
      reader_calibrated.json the verifier's wording only (never shown to the writer)
    system_of_record/
      decision_cases.json    past decisions with outcomes  → B5
  runs/                  outputs (git-ignored): every saved run, tables, review sheet, replay, DeepEval

src/salesagent/
  config.py              settings from .env; paths; models; freshness rule
  models.py              THE ONLY place a model is built: chat(), get_writer(), get_reader(), ReplayStub,
                         text_of(), extract_line(), parse_json(), usage()
  blocks.py              fetch_all() · build() the blocks from sources · assemble() a condition · golden()
  sources/adapters.py    one adapter per source system (timed); crm_notes() sets flagged notes aside
  sources/derive.py      B3 signals, computed at run time — no source system of its own
  graph/spine.py         the LangGraph graph: nodes and edges
  graph/nodes.py         fetch · assemble · write · verify · approve · send
  graph/state.py         RunState — the fields passed between nodes
  guards/sanitize.py     instruction-like text → flagged, kept as data, never in a prompt
  guards/approval.py     interrupt() for the human approval
  guards/idempotency.py  send-once (memory; Postgres when POSTGRES_URI is set)
  evals/checks.py        per-run proxy checks (§7)
  evals/runner.py        run_one · run_conditions · save_run · table / print / save helpers
  evals/verifier.py      independent reader: known_to_her() · verify_line() — evidence, never the gate
  evals/judge.py         DeepEval judge (Anthropic-backed)
  evals/tracing.py       LangSmith on/off from env
  replay.py              the classroom replay, sales.replay.v1 (eight stops)

scripts/                 command-line entry points (§6)
tests/                   15 tests; conftest.py forces the stub, no tracing, runs to a temp folder
findings/                results written up, and the evidence behind them (committed)
CLAUDE.md                rules for Claude Code working in this repo
HANDOFF.md · MIGRATION.md   how v2 was handed over and brought into this repo
```

---

## 5 · The data: the 80%

Each block of the prompt comes from a different source system; the orchestrator fetches from each and assembles.

| Block | Class | Source system | File | Built by |
|---|---|---|---|---|
| B0 | Basic — who she is, what we sell | CRM · account master | `crm_accounts.json` | `blocks.build` |
| B1 | Current context — this week | Social feed + Jobs feed | `social_feed.json`, `jobs_feed.json` | `blocks.build` (30-day freshness rule) |
| B2 | Dormant — private facts already held | CRM · activity notes | `crm_notes.json` | `blocks.build` — injection-like notes flagged and excluded |
| B3 | Derived signals | **none — computed at run time** | — | `sources/derive.py`, deterministic rules |
| B4 | Judgement — how the best salesperson weighs it | Knowledge graph | `knowledge_graph/judgement_rules.json` | `blocks.build` |
| B5 | Decision — past cases with outcomes | System of record | `system_of_record/decision_cases.json` | `blocks.build` (B5a = without D4) |
| B7 | Decision traces — the procedure | Knowledge graph | `knowledge_graph/traces.json` | `blocks.build` — the experiment's wording, verbatim |

**The golden-prompt test** (`tests/test_golden_prompt.py`) checks that every block rebuilt from these sources equals
the block a human assembled by hand in the experiment (`blocks_verbatim.json`), whitespace normalised. It passes for
all seven. That is the runtime's central demonstration in one test.

### The conditions

Defined only in `data/experiment/conditions.json` — never in Python.

| Condition | Blocks | Mode |
|---|---|---|
| T0 | B0 | one line |
| T1 | B0 B1 | one line |
| T2 | B0 B1 B2 | one line |
| T3 | B0 B1 B2 B3 | one line |
| T4 | B0 B1 B2 B3 B4 | one line |
| T5 | B0 B1 B2 B3 B4 B5 | one line |
| T5a | B0 B1 B2 B3 B4 B5a | one line — judgement restored, D4 dropped |
| T5b | B0 B1 B2 B3 B5a B4 | one line — as T5a, decision block above judgement |
| **T7** | **B0 B1 B2 B3 B7** | **procedure** — B4 replaced by B7, B5 absent, exactly as the experiment |

T0–T5b share one task sentence (`task_single_line`, reconstructed — the original wording was not preserved). T7's
task is part of B7, verbatim. T7 also gets an OUTPUT FORMAT block after B7 (a runtime addition asking for JSON).

---

## 6 · Commands

| Command | What it does | Model calls |
|---|---|---|
| `make test` | 15 tests on the replay stub | none |
| `make verify` | 8 environment checks; one real T7 on the writer if a key is set | 1 |
| `make series` | T0→T7 on the writer, k=3 → `conditions_latest.json`, `human_review.csv` | 27 |
| `make series2` | T0→T7 on both writers — the T1 identical-sentence check | 54 |
| `make t7` | one full T7 run: approval pause (asks y/N), verifier, run saved | 1 + 6 |
| `make replay` | classroom replay of the latest saved T7 run → `replay_T7.json` | none |
| `make langsmith` | LangSmith experiment over all conditions (+ Nikhil T7) | ~10 |
| `make deepeval` | DeepEval over the saved API runs; `--judge` adds the judged novelty metric | 0 (or 1 per run) |
| `make rescore` | re-score the latest series from its saved raw answers | none |

Scripts, with their options:

```bash
python scripts/run_one.py [prospect] [condition] [--writer 2] [--auto] [--verify]   # default: sunidhi T7
python scripts/run_conditions.py [k] [--only T0,T7] [--two-writers] [--prospect sunidhi]
python scripts/rescore.py                        # after changing extract_line or a check — no API calls
python scripts/export_replay.py [condition] [out.json]
python scripts/eval_deepeval.py [--judge] [--include-stub]
python scripts/eval_langsmith.py [experiment-prefix]
```

`--auto` approves without asking and is labelled `rep (--auto)` in the trace; the send is simulated — nothing leaves
the machine. `run_conditions.py --only T0` rewrites `human_review.csv` with only those rows.

---

## 7 · Models and evaluation

### Three model roles — keep them separate

| Role | Setting | Default | Where |
|---|---|---|---|
| **Writer** — the model under test | `MODEL_WRITER` | `claude-fable-5-1` (T7 parity) | `graph/nodes.py::write` |
| Second writer — cross-model checks | `MODEL_WRITER_2` | `claude-sonnet-5` | `--writer 2`, `make series2` |
| **Verifier** — independent reader, never the gate | `MODEL_READER` | `claude-sonnet-5` | `evals/verifier.py` |
| **Judge** — DeepEval novelty metric | `MODEL_READER` | `claude-sonnet-5` | `evals/judge.py` |

Anthropic API only; `models.chat()` is the only constructor. Newer models reject `temperature` (a 400), so it is sent
only where accepted — there is no temperature 0 on Fable or Sonnet 5, and run-to-run variance is what pass^k measures.
Fable 5.1 always thinks: the writer gets `max_tokens=16000` (billed on use) and only the text blocks of an answer are
read. The stop reason is recorded; `max_tokens` or `refusal` shows in the trace and is kept as data. There is no
automatic model fallback: a refusal is never answered silently by another model inside the experiment.

### Per-run checks (`evals/checks.py`) — proxies; the human verdict is final

| Check | Meaning |
|---|---|
| `verdict_proxy` | INTELLIGENCE if the line carries a deadline clause tied to her event (before/by/ahead of + salary, pay, payroll, joiner, cycle, run, first); else AUTOMATION |
| `reproduces_experiment` | the proxy verdict matches the experiment's for this condition (T4 accepts either — it was unstable) |
| `known_similarity` | token overlap with the known line |
| `golden_prompt` | the assembled blocks equal the experiment's |
| `injection_excluded` | note n11 never reached the prompt |
| `procedure_adherence` | T7: the writer followed the procedure |
| `identical_across_writers` | two writers, same line — the T1 finding (`make series2`) |
| pass^k | `reproduces_experiment` across k repeats |

**The human verdict** goes in `human_review.csv` (column `HUMAN_VERDICT`). It is the final call on every line.

### The independent verifier

`evals/verifier.py` scores a final line against the **calibrated** reader wording
(`knowledge_graph/reader_calibrated.json`), all six checks, no break — evidence, never the gate. It is told only what
she would know: **B1 plus the CRM notes marked `"her_experience": true`** (n2, n3 for Sunidhi) — not the rest of B2,
never flagged notes (`known_to_her()`). The DeepEval judge is told the same.

### Monitoring

- **LangSmith** — set `LANGSMITH_API_KEY`; every run is traced to project `LANGSMITH_PROJECT`
  (`sales-agent-t-series`), tagged with its condition. A run paused for approval appears as two traces (run, resume);
  verifier calls appear as separate traces. `make langsmith` builds dataset `sales-agent-t-series` and an experiment
  per writer. Trace pages show the account owner — check before sharing links with students.
- **DeepEval** — `make deepeval` scores the saved API runs → `data/runs/deepeval_latest.json`. Never set
  `OPENAI_API_KEY`; the judge is Anthropic-backed. Telemetry is off (`DEEPEVAL_TELEMETRY_OPT_OUT=YES`).
- **Replay** — `make replay` writes `sales.replay.v1`: eight stops, query to line — the fetches with timings, the
  assembled prompt with its golden match, the model's run with tokens and latency, the verification, the eval, the
  approval, and the T0→T7 strip. Import it on the sales agent site.

---

## 8 · Configuration (`.env`)

| Variable | Purpose |
|---|---|
| `ANTHROPIC_API_KEY` | empty → the replay stub |
| `MODEL_WRITER`, `MODEL_WRITER_2`, `MODEL_READER` | §7 |
| `STUB_MODEL=1` | force the stub even with a key |
| `SEND_APPROVAL_REQUIRED` | `true` → a T7 survivor pauses for approval |
| `LANGSMITH_API_KEY`, `LANGSMITH_TRACING`, `LANGSMITH_PROJECT` | tracing |
| `DEEPEVAL_TELEMETRY_OPT_OUT=YES` | no usage telemetry |
| `POSTGRES_URI` | optional — durable send-once record across restarts (`docker compose up -d`) |

`.env` is git-ignored. `.env.example` is the template.

---

## 9 · Where outputs go

| Path | Written by | Contents |
|---|---|---|
| `data/runs/<ms>_<cond>_<prospect>_w<n>.json` | every saved run | the full run: blocks, prompt, raw answer, line/candidates, checks, trace, usage |
| `data/runs/conditions_latest.json` | `make series`, `rescore.py` | the conditions table (`sales.conditions.v1`) |
| `data/runs/human_review.csv` | same | one row per line; the human verdict column — kept for unchanged lines when the sheet is rewritten |
| `data/runs/replay_T7.json` | `make replay` | `sales.replay.v1` |
| `data/runs/deepeval_latest.json` | `make deepeval` | every run's metric scores and reasons |
| `findings/` | by hand, committed | write-ups and the evidence copied out of `data/runs` |

`data/runs/` is git-ignored; copy anything worth keeping into `findings/`.

---

## 10 · How to change things

After any change: `make test`. Then one real run to see it: `python scripts/run_one.py sunidhi T0`.

- **A condition's blocks** — edit its entry in `data/experiment/conditions.json`. Never hard-code a condition.
- **The T0–T5 task sentence** — `task_single_line` in the same file; it changes all single-line conditions at once.
- **A block's content** — edit the source file (§5), not the block text. The golden-prompt test will then fail,
  because the block no longer equals the experiment's: expected when the change is deliberate — update
  `blocks_verbatim.json` (or the test) to the new baseline in the same commit, and say so.
- **How a block is laid out** — `blocks.build`; same golden-test rule.
- **The graph** — nodes in `graph/nodes.py`, wiring in `graph/spine.py`, state fields in `graph/state.py`.
  `tests/test_conditions.py::test_spine_order` checks assemble → write → verify → send.
- **The procedure** — `knowledge_graph/traces.json` (what the T7 writer sees, verbatim). The verifier's wording is
  separate: `reader_calibrated.json`. Never swap them.
- **What the verifier knows** — the `her_experience` flag on each note in `crm_notes.json`.
- **A new prospect** — add the account, post, jobs and notes to the source files; no golden reference exists for it.
- **After changing `extract_line` or a check** — `python scripts/rescore.py` re-scores the last series for free.

---

## 11 · Tests

`tests/conftest.py` forces the replay stub, turns tracing off, blanks the LangSmith key and sends runs to a temporary
folder — `make test` never calls a model, never touches the network and never writes into `data/runs`.

| File | Covers |
|---|---|
| `test_golden_prompt.py` | every rebuilt block equals the experiment's · the injection is in no block · B3 is computed, never stored |
| `test_conditions.py` | T7 uses exactly B0 B1 B2 B3 B7 · T7 procedure verified, known line, sent · the series reproduces on replay · Nikhil declines before the model · spine order |
| `test_verify.py` | procedure breaches caught · survivor must pass all six · thinking blocks read as text · subject-line extraction from labelled answers · the verifier knows B1 + n2/n3, not n1/n6/n11 |
| `test_replay.py` | the replay has eight stops · rewriting the review sheet keeps human verdicts |

---

## 12 · Rules that must survive any change

- **Conditions are data** (`conditions.json`). **T7 = B0 + B1 + B2 + B3 + B7** — B4 replaced, B5 absent.
- **No truncation, no token budget** in `assemble`. The experiment had none.
- **The writer receives the experiment's verbatim traces** (`traces.json`); the calibrated wording is the verifier's only.
- **The golden-prompt test stays green**, or its baseline is changed on purpose, in the open.
- **Code verifies the procedure; it does not judge the line.** The verifier never gates. **The human verdict is final.**
- **API models only**; `models.py` builds every model; the stub is a labelled replay.
- **Keep failures**: a T7 run that breaks the procedure, a T0–T5 line that looks intelligent, a judge that disagrees —
  record it in `findings/`.
- **Synthetic data only.**

---

## 13 · Debugging

| Symptom | Look at |
|---|---|
| Golden-prompt test fails | a source file or `blocks.build` changed — diff the block against `blocks_verbatim.json`; whitespace is normalised, words are not |
| A line reads `**Subject line:**` or starts with `Subject:` | `models.extract_line`; then `scripts/rescore.py` |
| T7 output not valid JSON | the writer ignored the output-format block, or stopped at `max_tokens` (see `usage.stop_reason`) — a procedure failure; keep it |
| `procedure_adherence` false | `verification.issues`: out of order, no stop at first failure, died_at mismatch, survivor not all-pass |
| 400 "`temperature` is deprecated for this model" | a model built outside `models.chat()`, or a new model missing from `NO_SAMPLING` |
| `replay-stub` in a trace when you expected the API | `ANTHROPIC_API_KEY` empty or `STUB_MODEL=1` |
| `make test` slow, or calls LangSmith | `tests/conftest.py` missing or edited |
| DeepEval scores stub runs | run without `--include-stub`; tests no longer write to `data/runs` |
| `make replay` shows an old run | `make t7` / `run_one.py` saves its run; replay picks the newest `*_T7_*.json` |
| Nikhil writes a line | freshness rule bypassed — `sources/adapters.py::social_post` |
| n11 in a prompt | `sources/adapters.py::crm_notes` sanitise step |
| T0–T5 look like intelligence on the API | possible — models change. Record it; it weakens the claim, and that matters |

---

## 14 · Decisions and known gaps

**Decisions, 26 Sep (Suchit)** — also in `findings/2026-09-26_t_series_api.md`:
1. Human verdict = the proxy verdict for the first Fable series (T7 intelligence 1/3).
2. The verifier keeps v2's calibrated wording, including the reworded R4 and the Indian-HR-English persona.
3. The verifier (and judge) know B1 plus `her_experience` notes only.
4. No server-side model fallback on the writer.

**Known gaps**
- D5–D7 were in the experiment and are not recoverable; B5 has D1–D4.
- T0–T5 task wording is reconstructed; T7's is verbatim (part of B7).
- The company is LogiTrans, a synthetic stand-in for the placeholder name in the experiment.
- The knowledge graph and system of record are files; `sources/adapters.py` is the seam where Neo4j and Postgres plug in.
- The DeepEval judge scores every Fable line below its 0.7 threshold, including lines the verifier passes on all six — recorded, not tuned.

---

## 15 · History

| Ref | What |
|---|---|
| tag `kit-v1` | the v1 kit as handed over (25 Sep): writer + separate reader, stores, toggle ablation |
| tag `kit-v1.1-reader-calibration` | v1 plus a day of reader calibration — the state before v2 |
| branch `t-series-runtime` | v2: the kit as delivered (commit `5b8173a`, with its original README), then the fixes below |
| branch `main` | v1; v2 merges only after the first API series is recorded (done — awaiting the merge decision) |

Changes to the delivered v2, each its own commit: tests isolated from `.env` (stub, no tracing, temp runs folder) ·
one model constructor, no `temperature` on newer models, thinking blocks read as text, writer `max_tokens` 16000,
stop reason recorded · subject-line extraction from labelled answers + `rescore.py` · the verifier told B1 +
`her_experience` notes only · `run_one.py` saves its run (so the replay shows it) · DeepEval on API runs only, judge
told what the verifier is told, results saved.

Next, from `CLAUDE.md`: `make series2`, `make langsmith`; then durable approval on Postgres, Neo4j/Postgres adapters
behind `sources/adapters.py`, a token-budget experiment, and more prospects.
