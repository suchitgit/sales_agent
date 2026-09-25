# Reader calibration — same procedure, two readers, the winning line rejected

**Date:** 25 Sep 2026 · **Prospect:** Sunidhi (VP HR, LogiTrans) · **Writer:** `claude-sonnet-5` (every run)
**Procedure:** `data/seed/traces.json` as shipped in `kit-v1` — the reader checks at that point:

| Check | `q` | `kill` (read by the model as the failure rule) |
|---|---|---|
| R1 | Is this about my situation now? | Anything about last quarter is gone. |
| R2 | Does it need me now, or can it wait? Is there a clock on it? | No clock, no urgency. |
| R3 | Is there something I had not already thought of? | A fact I already know earns nothing. |

R4–R6 unchanged throughout. Each check is one reader call; the loop stops at the first failure.

## Before the wording change

### Table 1 — reader `claude-haiku-4-5-20251001` (temperature 0) · 0 of 3 runs produced a winner

| Run | Cand. | Line (written by Sonnet 5) | Died at |
|---|---|---|---|
| 0 | A | Your 45-day window before multi-state payroll risk | R1 |
| 0 | B | 3 new states, one compliance clock now running | R1 |
| 0 | C | Before payroll runs in state #1: a compliance check | R1 |
| 1 | A | Your 30-day window for multi-state statutory compliance | R1 |
| 1 | B | 120 open roles, 3 payroll systems — one compliance clock | R1 |
| 1 | C | Before the first paycheck: multi-state payroll readiness | R1 |
| 2 | A | 120 open roles, 3 new states: your compliance clock starts now | R3 |
| 2 | B | Statutory filings for 3 states are due before your first payroll run | R1 |
| 2 | C | 30 days to register payroll in 3 new states—are you covered? | R3 |

**7 of 9 died at R1, 2 at R3.** Run 0's full trace, with every reason, is
`2026-09-25_before_haiku_run0.trace.json` (`sales.trace.v1`, importable on the site). A typical R1 reason:
*"focuses on a future risk scenario ('45-day window before') rather than addressing her current situation"* —
the reader treated a forward-looking line as failing "about my situation now". Reasons for runs 1–2 were not
captured (only the death point was printed).

### Table 2 — reader `claude-sonnet-5` (no temperature: the model rejects it) · 0 of 3 runs produced a winner

| Run | Cand. | Line (written by Sonnet 5) | Died at | Reason (as returned, trimmed) |
|---|---|---|---|---|
| 0 | A | 30-Day Compliance Window Before Your First Payroll Run | R1 | references a compliance deadline tied to a first payroll run, not the known context of expanding into three new states or 120 open roles |
| 0 | B | 3 States, 1 Payroll Deadline: Are You Registered? | R3 | Merely restates the known expansion-into-three-states fact and infers an obvious payroll registration concern |
| 0 | C | Before Onboarding 120 Roles Across 3 States, This Comes First | R3 | Just restates known facts (120 roles, 3 states) framed as urgency without revealing a new insight |
| 1 | A | 3-State Payroll Compliance: 30-Day Countdown Starts Now | R3 | Just restates known expansion news with a generic urgency hook |
| 1 | B | 120 Hires, 3 States — One Payroll Clock Ticking | R3 | 'payroll clock ticking' is a vague implication, not a genuinely new fact or angle |
| 1 | C | Statutory Deadline for New-State Payroll: 30 Days Out | R3 | a generic statutory deadline reminder doesn't reveal anything new |
| 2 | A | 30 Days to Statutory Compliance in Your Newest States | R3 | Just restates the known expansion news (new states) |
| 2 | B | One Payroll System, Three New State Rules—Ready? | R2 | No explicit deadline or time pressure indicated |
| 2 | C | 120 Roles to Fill Before Compliance Clock Runs Out | R3 | Just restates known facts (120 open roles, expansion implies compliance pressure) |

**1 died at R1, 1 at R2, 7 at R3.**

### Table 3 — the known winning line, scored directly (no generation), two runs per reader

Line: **"3 new states, one payroll run, before your first joiner's salary date"** (the T7 result of the experiment).

| Reader | Run 0 | Run 1 | Reason |
|---|---|---|---|
| Haiku 4.5 | R1 | R1 | "mentions 'before your first joiner's salary date' which is forward-looking/future-oriented, but fails the check requirement that 'anything about last quarter is gone'" |
| Sonnet 5 | R3 | R3 | "Just restates the known fact (3 new states) plus a generic payroll/compliance angle she'd already assume" · "a mirror of her own LinkedIn post—nothing new is surfaced" |

## What it shows

- **Same procedure, two readers, the known-correct line rejected — at different checks, for different reasons.**
  Haiku read R1's `kill` text literally as a rule the line breaks. Sonnet read R3 as "fails if it mentions
  anything she knows", ignoring the computed deadline the line adds.
- A reader that rejects the known-correct answer cannot produce a winner, however good the writer is.
  **Measure the reader before you trust it.**
- A single run would have hidden this or blamed the writer; three runs per reader, plus the known-good line,
  located it. This is the argument for pass^k.
- Second-order, not yet addressed: Sonnet's deadlines are generic ("30 days", "compliance clock") rather than
  built from her own numbers the way "first joiner's salary date" is.

## After the wording change (commit b7cdc44) — the guard, `make guard`, pass^3 per reader

R1 and R3 reworded in `traces.json` (see that commit); R2, R4, R5, R6 unchanged. The guard scores the known
winning line three times with the active reader and requires all six checks cleared every time.

| Reader | Guard | R1 | R2 | R3 | Died at |
|---|---|---|---|---|---|
| Haiku 4.5 | **0/3** | pass ×3 | pass ×3 | pass ×3 | **R4 ×3** |
| Sonnet 5 | **0/3** | pass ×3 | pass ×3 | pass ×3 | **R4 ×3** |

The R4 check, unchanged since `kit-v1`: *"Does it name a pain I have actually been through?"* — kill:
*"In the words I would use, not the seller's."* Reasons, as returned:

- Haiku: *"uses seller's jargon ('joiner's salary date') rather than the prospect's natural language … there's no
  evidence she's actually experienced the specific pain … this is assumed pain, not validated pain in her own words."*
- Sonnet: *"a pain she's articulated in her own words. She posted about expansion and open roles as facts/announcements,
  not as a complaint about payroll complexity across states or joiner salary timing."*

**What it shows**

- The rewording did what it was meant to: both readers now pass R1 and R3 on the known-correct line, and they fail
  it at the same place for the same reason — a disagreement between readers became agreement.
- Fixing one check exposed the next. The guard moved from R1/R3 to R4 — the loop stops at the first failure, so R4
  was never reached before.
- R4 asks about a pain she has *been through*, but the reader is told only what she knows **this week**
  (`KNOWN_TO_HER` = trigger + current facts, `nodes.py::score`). The evidence of her lived pain is in the dormant
  CRM notes — n2 *separate payroll processes across regions*, n3 *manual reconciliation between regional payroll
  teams* — and the reader never sees them. Both readers say, in effect, "no evidence she has lived this".
- "Joiner" is the prospect's own register (Indian HR usage; the expansion is into states); Haiku calls it seller's
  jargon. The reader has no signal for whose words are whose.

Not changed: R4, and what the reader is shown. Both are decisions on the procedure. Neither reader clears the
guard, so the reader stays on the kit default (Haiku 4.5), the cheaper one; the full Sunidhi runs were not repeated
since the guard already fails.
