# Sales agent kit — README

Everything an engineer (or Claude Code) needs to understand, run, extend and debug this system
without asking anyone. Read top to bottom once; then use the section headings as a lookup.

---

## 1 · What this is

A runnable implementation of one AI agent: it writes **the subject line that earns the read** for a
named sales prospect, from what the company already knows about her, and shows its reasoning step by
step. It is the runtime of the architecture taught on Day 4 of the FDE programme — the six-block
diagram (context, retrieval, memory, knowledge graph, orchestrator, feedback) — built as a
LangGraph state machine with the Anthropic API as the model.

It exists for two audiences at once:
- **students**, who watched the architecture being derived by hand from an experiment and now see it
  run — so the demo must reproduce the experiment's result, and visibly;
- **Claude Code**, which will harden it, run it on the API, and extend it — so every design decision
  that is not obvious from the code is written down here.

Everything runs on **synthetic data only**. No real people, companies or CRM records anywhere.

---

## 2 · Why — the problem behind the build

The problem, as framed by the domain expert (a VP of sales at a payroll/HR software company):

> Once a prospect opens and reads a message, her chance of moving from prospect to customer rises by
> about 50%. Only about 10% of messages are read. So the read rate, not the send volume, is the
> number that matters. Only about 5% of salespeople can write the subject line that earns the read.
> Help the other 95% write it.

The one job, then, is not "write a good email". It is: **write one line the reader will open**,
for one prospect, using material the company holds and a competitor does not.

The prospect used throughout is **Sunidhi Rao, VP HR at LogiTrans** (a mid-size logistics company,
synthetic; the original experiment used a placeholder company name, replaced here so nothing in the kit names a real company). Last week she posted that LogiTrans is expanding into three new states; it has 120 open
roles. The seller is **HumanAITech** — multi-state statutory compliance, payroll consolidation,
onboarding at scale.

---

## 3 · The experiment this build must reproduce

Before any code, the architecture was derived by an **ablation experiment** (called T0–T7): the same
task was given to models repeatedly, adding one class of data at a time, and the resulting subject
line was judged each time by one test — *could a competitor holding the same public data have
written this line?* If yes, it is automation. If no, it is intelligence.

| Run | Data added | What came out | Verdict |
|---|---|---|---|
| T0 | Basic — who she is, what we sell | "Consolidating multi-state payroll & compliance at LogiTrans" — a vendor describing itself | Automation |
| T1 | + Current context — her post, 120 roles | Two different models wrote the **identical** sentence | Automation |
| T2 | + Dormant data — six private CRM facts | All six cited in the reasoning; none reached the line | Automation |
| T3 | + Derived signals — expansion HIGH, fragmentation MED-HIGH… | Same sentence again — the signals were **inert** | Automation |
| T4 | + Judgement — how the best salesperson weighs it | The line addressed *her* for the first time — but held only **3 of 6** repeats | Unstable |
| T5 | + Decision data — past cases with outcomes | Went backwards to a topic statement | Automation |
| T7 | + Two decision traces, as a procedure | Every model ran the method; one found a **deadline she had not computed** | **Intelligence** |

The winning line: **"3 new states, one payroll run, before your first joiner's salary date."**

The finding, stated once: every data class before T7 supplied *material to reason about*; only the
judgement and the traces supplied *a procedure to reason with*, and only those moved the sentence.
Material is necessary; procedure is what changes the output.

This is why the orchestrator is the hero of the architecture, and why this kit's spine is code
that runs the procedure rather than a model that decides what to do.

---

## 4 · The points this build has to prove

These are the claims made to students. The kit is only finished when each can be shown, not argued.

| # | Claim | How the kit shows it | Where |
|---|---|---|---|
| 1 | The stores hold material; the orchestrator holds the method | Same stores, different procedure → different line. The spine's plan is a constant in code | `graph/nodes.py::plan`, `data/seed/traces.json` |
| 2 | Material does not move the sentence; procedure does | `scripts/ablation.py`: stores removed one at a time; the line is flat through T5 and moves only when the knowledge graph arrives. Ran on the stub; the API run is build item 3 | `scripts/ablation.py` |
| 3 | The reader decides in order and stops at the first failure | The scorer is a loop with a `break`; every candidate's death is recorded with the check that killed it | `graph/nodes.py::score` |
| 4 | R3 — "something I had not already thought of" — is the check that matters | On Sunidhi, two of three candidates die at R3; the survivor carries a computed clock | `scripts/run_one.py sunidhi` |
| 5 | Same request, same stores → same path, same rejections, same winner | The eval suite records the step path per run and fails consistency if paths differ | `evals/suite.py`, `tests/test_spine.py::test_same_path_every_run` |
| 6 | The model is the 20% | It is called at exactly two points: once to write three candidates, once per reader check. Everything else is code | `graph/nodes.py::generate`, `::score` |
| 7 | The send is irreversible, so a human clears it | `interrupt()` pauses the run with the line and the rejections; nothing leaves without the rep | `guards/approval.py`, `graph/nodes.py::approve` |
| 8 | Declining is sometimes the right answer | Nikhil, the null prospect, has no live trigger; the agent writes nothing, and that is a pass | `data/seed/prospects.json`, `evals/checks.py::null_safety` |
| 9 | Text from stores is evidence, never instructions | CRM note n11 is an injection on purpose; it is flagged and never reaches the prompt | `guards/sanitize.py`, `stores/retrieval.py` |
| 10 | Memory is three different things | Session state (checkpointer), rep habits and history (Store, namespaced), past decisions with outcomes (system of record) | `stores/memory.py`, `scripts/seed_postgres.py` |
| 11 | Retrieval is stable truth; context is this week's truth | Context has a 30-day freshness rule; retrieval has none | `stores/context.py` |
| 12 | The knowledge graph is the only store whose contents *are* the method | The traces and the archetypes live there and nowhere else | `stores/graph.py`, `data/seed/knowledge_graph.json` |
| 13 | Feedback is the only source of Rung-2 truth | A line is HYPOTHESIS until the outcome returns; `record_outcome.py` relabels it TESTED | `scripts/record_outcome.py` |
| 14 | A deterministic spine beats a self-planning agent when the procedure is known | The deep-agents sibling kit builds the same agent on the harness; the comparison is on identical data and evals | `deepagent-sales-sandbox` (separate kit) |

---

## 5 · Data classes — what goes where, and why

The four Data Liquidity classes, plus the two that frame them. Each is a file in `data/seed/`.

| Class | T-block | File | Store | Why that store |
|---|---|---|---|---|
| Basic | T0 | `prospects.json` (identity fields), `capability_catalogue.json` | Retrieval / context | Stable identity; what we sell |
| Current context | T1 | `prospects.json → context` | **Context** — graph state, per run | Volatile. True this week, stale next month. A 30-day freshness rule decides whether a trigger is live |
| Derived | T3 | `prospects.json → derived` | Context | Computed from the current context; found **inert** in the experiment, so excluded from the prompt |
| Dormant | T2 | `crm_notes.json` | **Retrieval** — BM25 index | Private facts a competitor lacks; stable; searched by exact terms |
| Decision | T5 | `decision_cases.json` | **Memory** — system of record | Past choices with outcomes **and the choice set** (without the choice set the class carries a confound) |
| Judgement | T4 | `judgement_rules.json` | **Knowledge graph** | How the best salesperson weighs competing problems |
| Procedure | T7 | `traces.json` | **Knowledge graph** → the orchestrator | The reader trace R1–R6 and the seller trace S1–S5. Not data the model reads — the method the code runs |
| Archetypes | — | `knowledge_graph.json` | Knowledge graph | Which opener shapes earn replies from which roles; trigger → pain mappings with priority |
| Rep profile | — | `rep_profile.json` | Memory — Store, namespace `("rep", rep_id)` | The rep's editing habits, cross-thread |

**The prospects:**
- **Sunidhi** — the full case; expected verdict *intelligence*.
- **Arun** (Head of Ops, Sunrise Logistics, three new depots) — a second live case; expected *intelligence*.
- **Nikhil** (CFO, Steady Freight, nothing happening) — the **null case**; expected *decline*.

---

## 6 · Components

```
src/salesagent/
  config.py          settings from .env · the token proportion per store · approval flag
  models.py          get_model("medium"|"small") → ChatAnthropic via the API · StubModel when no key
  stores/
    context.py       get_context(prospect_id) — freshness rule, live trigger, derived signals
    retrieval.py     Retrieval.search(query, prospect_id) — BM25 over CRM notes; sanitises results
    memory.py        past_decisions(pains) · rep_profile(store, rep_id) · write_outcome(...)
    graph.py         KnowledgeGraph — pains_for(triggers), top_archetype(role, industry), the traces
  graph/
    state.py         SalesState — the TypedDict every node reads and returns; trace is append-only
    nodes.py         plan · fetch · assemble · generate · score · approve · send
    spine.py         build(checkpointer, store) → the compiled StateGraph, edges fixed
  guards/
    sanitize.py      instruction-like text → flagged, kept as data
    approval.py      request_approval(payload) → interrupt()
    idempotency.py   send_key(thread, line) · send_once(key, fn)
  evals/
    checks.py        r3_novelty · competitor · null_safety · trace_complete
    suite.py         run_once · run_suite(k) → pass^k + path consistency · export_trace
  data/              (empty) synthetic generators — build item 5
scripts/
  run_one.py         one prospect, approval prompt, optional --export
  run_evals.py       the suite at pass^k, exports sales.eval.v1
  seed_postgres.py   tables + seed + checkpointer.setup() + store.setup() + rep profile
  seed_graph.py      Neo4j when configured, else Kùzu embedded
  record_outcome.py  the feedback write
  verify_env.py      eleven checks, each doing real work
tests/
  test_seed.py       seed integrity
  test_spine.py      behaviour: clock line, order, null decline, injection, path consistency
```

### The model layer, precisely
`models.py` is the **only** file that constructs a model.
- With `ANTHROPIC_API_KEY` set: `ChatAnthropic(model=MODEL_MEDIUM)` writes candidates;
  `ChatAnthropic(model=MODEL_SMALL)` answers each check. Temperature 0. **API only — no local models.**
- Without a key (or `STUB_MODEL=1`): `StubModel`, a deterministic stand-in that writes candidates from
  the prompt's facts and answers checks by rule. It exists so the *spine* can be tested and the build
  can proceed offline. It is not the intelligence and must not be made to look like it.

### The stores, precisely
- **Context** is not a database. It is a function that reads the prospect record and returns this
  week's facts, or nothing if the trigger is older than `MAX_TRIGGER_AGE_DAYS`.
- **Retrieval** is BM25 (`rank-bm25`), which needs no model. Vector retrieval, if wanted, goes through
  the Voyage embeddings API (`langchain-voyageai`) — never a downloaded embedding model.
- **Memory** — three places by design. Do not merge them: session state disappears with the thread;
  the Store is cross-thread and namespaced; past decisions are business rows that analytics and the
  confound guard must be able to query.
- **Knowledge graph** — reads `knowledge_graph.json` and `traces.json` today; `seed_graph.py` loads
  the same into Neo4j (or Kùzu). Build item 2 makes the Neo4j path live.

---

## 7 · The stack

| Layer | What it holds | Built with |
|---|---|---|
| 5 · Governance | approval before the send · sanitised tool text · idempotent send · evals, traces | `guards/`, `evals/`, pytest |
| 4 · Orchestration | S1–S5 as a constant plan · R1–R6 as a loop with a break · token proportion | LangGraph `StateGraph`, `interrupt`, `Command` |
| 3 · Model | candidates (medium) · six checks (small) | `langchain-anthropic` → Anthropic API |
| 2 · Decision | the two traces · judgement rules · archetypes · READ / HYPOTHESIS / TESTED labels | seed JSON → knowledge graph |
| 1 · Data | context · retrieval · memory · knowledge graph · feedback | graph state · BM25 · Postgres (checkpointer, Store, tables) · Neo4j/Kùzu |

Services (`docker-compose.yml`): **Postgres 16** (`sales-postgres`, 5432) backs the checkpointer, the
Store and the system of record; **Neo4j 5** (`sales-neo4j`, 7474/7687) is the knowledge graph.
Without Docker: in-memory checkpointer and store, Kùzu embedded graph. The service URIs are commented out in `.env.example`; `setup_env.sh` enables them only when the Docker services come up, and every script falls back to the local option if a configured service is unreachable.

---

## 8 · The sequence — one request, start to finish

```
1  invoke({"prospect_id", "rep_id", "thread_id"}, config={"configurable": {"thread_id"}})
2  plan       code    S1–S5 loaded from the knowledge graph as a constant. The model decides nothing.
3  fetch      code    Context (trigger, roles, derived) · Retrieval (BM25, sanitised) ·
                      Memory (past decisions, rep profile from the Store) · Knowledge graph (pains,
                      archetype, rules, the reader trace). Four reads, no model.
4  assemble   code    If no live trigger → declined=True, stop writing. Else: MATERIAL ONLY — facts,
                      trigger→pain mappings, archetype, judgement rules — never the deadline; each
                      store cut to its share of PROMPT_BUDGET_CHARS; derived signals excluded as inert.
5  generate   MODEL   call 1 — the medium model writes three candidates. Nothing chosen.
6  score      MODEL   for each candidate, for R1..R6 in order: one small call → pass/fail + reason;
              + code  break at the first failure. The loop is code; only the verdict is the model.
                      (Knowledge graph off → no reader trace → best candidate ships unscored: T0–T5.)
7  select     code    the first candidate that cleared all six. No model.
8  approve    HUMAN   interrupt() with the line and the rejections. Needs a checkpointer.
                      On resume the node re-runs from its start — nothing before it has side effects.
9  send       code    send_once(key = thread + line). A resumed approval cannot send twice.
                      Label: HYPOTHESIS.
10 feedback   later   record_outcome.py — opened / replied / ignored → Store + system of record.
                      Label: TESTED.
```

Every node appends to `state["trace"]` **during execution** (the reducer is `operator.add`), so the
trace is a by-product of the run, never a summary written afterwards.

**A mistake this order corrects, so it is not reintroduced:** an earlier slide showed the scoring
happening *before* the model was called. Nothing can be scored until the model has written the
candidates, and each score is itself a model call. `tests/test_spine.py` enforces the order.

---

## 9 · Evaluation

`scripts/run_evals.py k` runs every seed prospect `k` times and reports **pass^k** — a prospect passes
only if every run passes every check — plus **path consistency** (the step sequence must be
identical across runs). Exported as `sales.eval.v1`.

| Check | Passes when |
|---|---|
| `r3` | the winner cleared all six checks including R3 (novelty); for the null prospect, there is no winner |
| `competitor` | proxy: the winner carries a temporal clause and is not a public-data shape (vendor intro, echo, category). The human read is the real test |
| `null_safety` | the null prospect produced no winner |
| `trace` | at least six trace steps and every candidate carries its check results |
| `consistency` | one step path across all k runs |

On the **stub**, the suite scores 3/3 on every prospect — by construction. On the **API**, expect that
to drop, and record where: that drop is the finding about model variance, not a bug to hide.

---

## 10 · The front end

**Not in this zip.** The site is a published page (a claude.ai artifact link held by the project owner) and the Deep Agents sibling kit is a separate zip; both are handed over alongside this one. The kit has no UI of its own. Its outputs are designed to land on **the sales agent project site**
(published separately), which has:
- a reference implementation of the same spine in the browser, on the same seed data, with a
  **gate strip** showing every candidate's R1–R6 results and where it died;
- an **ablation** view (the T0–T7 sequence run automatically);
- **evals** with publish and download; **traces** for every run;
- **"Your local app"** — an import control that accepts `sales.trace.v1` and `sales.eval.v1` JSON.

So the loop is: run here → export (`--export`, `run_evals.py`) → import on the site → the real
runtime sits beside the browser reference. Build item 6 adds a FastAPI layer (`/write`, `/approve`,
`/runs`, `/outcome`) for a live console; until then, files are the bridge.

Export formats (the site's contract):

```json
{ "kind": "sales.trace.v1", "prospect": "sunidhi", "prospectName": "...", "stores": [...],
  "verdict": "intelligence|declined|none",
  "candidates": [ { "id": "A", "text": "...", "died_at": "R3", "reason": "...", "results": [...] } ],
  "winner": { "id": "C", "text": "..." }, "steps": [ { "step": "...", "detail": "...", "actor": "code|model|human", "label": "READ|HYPOTHESIS|TESTED" } ] }

{ "kind": "sales.eval.v1", "k": 3, "scenarios": [ { "id": "sunidhi", "title": "...", "passes": 3, "runs": 3,
  "checks": { "r3": true, "competitor": true, "null_safety": true, "trace": true, "consistency": true } } ] }
```

---

## 11 · Running it

```bash
./setup_env.sh                 # or make setup · or ./setup_env.sh --no-docker
make test                      # 11 tests on the stub, ~1 s
python scripts/ablation.py sunidhi               # the T0→T7 collapse, live
python scripts/run_one.py sunidhi --auto --export data/synthetic/sunidhi_trace.json
python scripts/run_one.py nikhil --auto           # the null case declines
make evals                     # pass^5, exports data/synthetic/eval.json
make seed                      # reseed Postgres + graph
python scripts/record_outcome.py sunidhi opened   # the feedback write
```

Add `ANTHROPIC_API_KEY` to `.env` and rerun `make verify`: the last two checks make a real call and a
full run on the API. Everything before that ran on the stub.

---

## 12 · Debugging guide — for Claude Code

**Where to look first for each symptom:**

| Symptom | Likely cause | Look at |
|---|---|---|
| `NotImplementedError` from `bind_tools`, or the run stops at `generate` | The configured model does not support tool calling / structured output; or the stub is active when a real model was expected | `models.py`, `.env` (`STUB_MODEL`, `ANTHROPIC_API_KEY`) |
| Winner has no clock; `competitor` check fails on the API | The medium model did not compute a deadline from her numbers — it is given material only, by design | `nodes.py::assemble` (do NOT add the clock to the prompt); the archetype and judgement lines are the steer; record the result — this is the finding |
| A candidate that should die at R3 passes | The small model's verdict; `KNOWN_TO_HER` in the check prompt may be too thin | `nodes.py::score` — the `known` string |
| `consistency` fails | Different candidates → different rejection sequence. On the API this can be legitimate; on the stub it is a bug | compare `trace` step names across runs |
| Nikhil produces a line | The freshness rule or `has_live_trigger` was bypassed | `stores/context.py`, `nodes.py::assemble` |
| The injection note reaches the prompt | Sanitisation skipped or the `flagged` filter removed | `stores/retrieval.py::search`, `nodes.py::assemble` (`if not r["flagged"]`) |
| The run does not pause for approval | No checkpointer on the compiled graph, or `SEND_APPROVAL_REQUIRED=False` | `spine.py::build`, `config.py` |
| The line is sent twice after a resume | The send moved *before* the interrupt, or the key changed, or Postgres was down so the record was in memory | `guards/idempotency.py` (`record` field in the send result says which), `nodes.py::approve/send` |
| `interrupt()` raises inside a try/except | Interrupts propagate as exceptions; never wrap them | `guards/approval.py` |
| Postgres checks fail | Services not up, or `POSTGRES_URI` missing | `docker compose ps`, `.env`, then `python scripts/seed_postgres.py` |
| `StoreBackend`/`PostgresStore` errors about setup | `setup()` not called | `seed_postgres.py` or `run_one.py` (it calls setup when `POSTGRES_URI` is set) |

**Rules that must survive any change** (each has a test or a check):
1. The spine order: plan → fetch → assemble → generate → score → approve → send.
2. The model is created only in `models.py`, only via the API.
3. `break` at the first failed check; deaths recorded with the check id.
4. `interrupt()` before the send; the send idempotent; nothing with side effects before the interrupt.
5. Flagged tool text never reaches the prompt.
6. The null prospect declines.
7. Every node appends to the trace as it runs.

**How to add a prospect:** append to `data/seed/prospects.json` (all six fields), add CRM notes with
its id to `crm_notes.json`, set `expect` to `intelligence` or `decline`, run `make test`.

**How to change the procedure:** edit `data/seed/traces.json`, not the code. The plan and the checks
are data; the spine reads them. That is the point — changing the procedure changes behaviour
without touching the orchestrator.

---

## 13 · What is deliberately not here

- No local models, no fine-tuning, no downloaded embeddings.
- No self-planning agent on the path to the send. (The Deep Agents comparison is a separate kit.)
- No real customer data.
- No UI — the site is the front end, files are the bridge until the API layer exists.
