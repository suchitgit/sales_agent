# Seed data — the experiment's own blocks, as files

| File | T-block | Store it feeds |
|---|---|---|
| prospects.json | B0 basic + B1 current context + B3 derived signals | Context (per run) + system of record |
| crm_notes.json | B2 dormant facts (n1–n6 for Sunidhi) — includes one injection note, n11, on purpose | Retrieval (BM25 index) |
| capability_catalogue.json | B0 what we sell, keyed by the pains each capability answers | Retrieval |
| decision_cases.json | B5 decisions with outcomes — and the choice set, not only the winner | Memory · system of record |
| judgement_rules.json | B4 how the best salesperson weighs it | Knowledge graph |
| traces.json | B7 the reader trace R1–R6 and the seller trace S1–S5 — the procedure, as data | Knowledge graph → the orchestrator |
| knowledge_graph.json | archetypes and trigger→pain mappings | Knowledge graph |
| rep_profile.json | the rep's editing habits | Memory (Store, namespaced by rep) |
| known_winners.json | known-good lines, one per prospect, **written by a person — never by the model under test** | The guard (`make guard`): the reader must clear each k/k |

All synthetic. Nikhil is the null prospect: no trigger, and declining to write is the correct answer.
