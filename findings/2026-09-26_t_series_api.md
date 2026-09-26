# T-series on the API — Claude Fable 5.1, k = 3

**Date:** 26 Sep 2026 · **Branch:** `t-series-runtime` · **Prospect:** Sunidhi (VP HR, LogiTrans)
**Writer:** `claude-fable-5-1` (thinking always on; no temperature — the model rejects it) · **Command:** `make series`, then
`scripts/rescore.py` after the line-extraction fix (no new model calls). Table: `2026-09-26_t_series_fable_k3.conditions.json`.
Review sheet: `2026-09-26_t_series_fable_k3_human_review.csv` — **the human verdict column is the final call; everything
below is the proxy.**

The golden-prompt test passes: every block the runtime rebuilt from the source systems equals the experiment's (B0–B5, B7).

## The table

| Cond. | Proxy verdicts (3 runs) | Reproduces experiment | Line, run 1 |
|---|---|---|---|
| T0 | A A A | 3/3 | Multi-state payroll compliance for LogiTrans — one platform, fewer manual checks |
| T1 | A A A | 3/3 | 3 new states, 120 open roles — one payroll system, Sunidhi? |
| T2 | A A A | 3/3 | Three new states, one payroll process — before the 120 hires land |
| T3 | A A A | 3/3 | Three new states, 120 open roles — one payroll process for all of it? |
| T4 | A **I** A | 3/3 (either accepted) | 3 new states, 3 new payroll rulebooks — LogiTrans' compliance setup before the 120 hires land |
| T5 | A A A | 3/3 | Three new states — three more payroll processes for LogiTrans? |
| T5a | A A A | 3/3 | Three new states — three more payroll processes to reconcile? |
| T5b | A A A | 3/3 | Three new states — does LogiTrans' payroll need three more regional processes? |
| **T7** | A **I** A | **1/3** | 3 new states, 120 hires — one payroll run, not three more regional reconciliations |

A = AUTOMATION, I = INTELLIGENCE, by `verdict_proxy`: intelligence only if the line carries a deadline clause
("before/by/ahead of" + salary/pay/payroll/joiner/cycle/run/first). All 27 lines are in the review sheet.

**T7, all three runs** — the procedure was followed every time (`procedure_adherence` 3/3: three candidates, checks in
order, stopped at the first failure, survivor passed all six):

| Run | Survivor | Rejected (by Fable's own R-checks) | Proxy |
|---|---|---|---|
| 1 | 3 new states, 120 hires — one payroll run, not three more regional reconciliations | "Transform LogiTrans HR with AI" @R1 · "New-state payroll registration deadlines your 120 hires will trigger" @R5 (only a warning) | A |
| 2 | 3 new states, 120 hires: payroll registration lands before hire #1 — one reconciliation cycle, not four | "Three new states means three more payroll processes to reconcile — unless they're one" @R3 · "How LogiTrans can transform HR with AI…" @R2 | I |
| 3 | Three new states shouldn't mean three more payroll reconciliations | "120 open roles: onboarding at scale without adding HR headcount" @R3 · "Statutory payroll exposure in your three new states" @R4 | A |

The first real T7 run (`make verify`, not in the table) survived with *"Three new states, 120 hires — without three more
payroll reconciliations"* — procedure followed, proxy A.

## Where the API matched the experiment

- **T7 ran the method, every time.** Seller steps grounded in the dormant data (webinar, separate regional payroll, the
  reconciliation discussion), three candidates, R-checks in order, stops named, a survivor that clears all six. Four of
  four T7 runs on Fable followed the procedure. Its own rejections are the experiment's kind: a generic AI line at R1/R2,
  a known fact at R3, "only a warning" at R5, a seller's word ("exposure") at R4.
- **T7 run 2 is structurally the known line**: her numbers (3 states, 120 hires), a deadline she has not computed
  ("before hire #1"), and the consolidation ("one reconciliation cycle, not four").
- **T0 is a vendor sentence** ("one platform"), as in the experiment.

## Where it did not

- **T7 reproduces 1/3 on the proxy, not 3/3.** Runs 1 and 3 name a *consequence* (three more reconciliations) instead of a
  *deadline*. The proxy calls them automation; whether a human does is the open question — they recombine the expansion
  with the reconciliation pain from her own history, which no competitor holds.
- **T1–T5 on Fable are already stronger than the experiment's T1–T5.** From T1 on, Fable names the consolidation angle
  ("one payroll system / process for all of it"), and T2 run 1 and T4 runs 1–2 carry a deadline clause ("before the 120
  hires land", "before the first hire lands"). The experiment's T1 was the vendor-flat "Supporting LogiTrans's 3-state
  expansion and 120 open roles" — identical from two models. The gap between T0–T5 and T7 is narrower on Fable 5.1 than
  in the experiment. The README anticipates this ("models change … it would weaken the claim"); recorded, not adjusted.
- **The proxy is narrow.** It only recognises a deadline clause with a pay word after it: "before the 120 hires land"
  (T2, T4 run 1) reads as AUTOMATION, "before the first hire lands" (T4 run 2) as INTELLIGENCE. The human column settles it.

## What was fixed to get here (all on `t-series-runtime`)

- Tests forced to the replay stub with tracing off and no LangSmith key (they would otherwise run Fable on the API).
- One model constructor; no `temperature` on Sonnet 5 (the verifier and judge 400'd); text blocks read from thinking
  models; writer `max_tokens` 16000 (was 2500); stop reason recorded.
- **Line extraction:** Fable prefixes most single-line answers with `**Subject line:**` and a rationale; the delivered
  parser recorded the label as the line for T4–T5b. Fixed and re-scored from the saved raw answers — no series re-run.

## Not yet run

`make series2` (both writers; the T1 identical-sentence check), `make t7` + `make replay`, `make langsmith`,
`make deepeval`. The independent verifier (`--verify`) has not been run on these lines.

## Decisions, 26 Sep (Suchit)

1. **Human verdict = the proxy verdict** for all 27 lines (review sheet filled accordingly). So on the human column:
   T0–T5 are automation in 23 of 24 runs (T4 run 2 is intelligence: "Three new states — payroll compliance before the
   first hire lands"); **T7 is intelligence in 1 of 3** (run 2, "before hire #1"), automation in 2 of 3.
2. **Verifier wording:** keep v2's `reader_calibrated.json` — including its reworded R4 and the Indian-HR-English
   persona — over the repo's 25 Sep wording (MIGRATION.md's "repo wins" read literally would have undone them).
3. **Verifier knowledge:** B1 plus the CRM notes marked `her_experience` only (n2, n3); never n1, n6 or n11.
4. **No server-side model fallback on Fable.** A refusal would otherwise be answered silently by another model inside
   the experiment; a refusal or a cut-off stays in the run as data (`stop_reason` in the trace).

## Full T7 runs with the independent verifier (`make t7`, after decisions 2–3)

Approval by `--auto` (labelled so in the trace); the send is simulated.

| Run | Survivor | Rejected by Fable | Proxy | Verifier (calibrated reader, all six) |
|---|---|---|---|---|
| A | 3 new states, 120 open roles: get each state's payroll registered before the first offer letter lands | "Consolidating LogiTrans's regional payroll processes into one run" @R2 · "Multi-state payroll compliance: a follow-up to the session your HR ops team joined" @R3 | I | R1–R6 pass |
| B | Before LogiTrans's first payroll in 3 new states: one process, not 3 more to reconcile | "Onboarding 120 hires across new states without adding HR headcount" @R3 · "How AI is transforming HR at logistics companies" @R1 | I | R1–R6 pass |

Both followed the procedure; both carry a computed deadline tied to her own event; the verifier — told only B1 and her
own experiences (n2, n3) — cleared both on all six checks. Run B's classroom replay (`sales.replay.v1`, eight stops,
with approval, verifier and a LangSmith trace link) is `2026-09-26_replay_T7_fable.json`. Across all six real T7 runs on
Fable today the procedure was followed six times; the proxy reads intelligence in three (series run 2, A, B).
