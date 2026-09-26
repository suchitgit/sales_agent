# Bringing v2 into the existing repo

The repo holds v1 plus a day of reader calibration. Keep all of it; do v2 on a branch.

1. **Retain v1 as it stands:** `git tag kit-v1.1-reader-calibration` on the current `main` head; push the tag.
2. **Branch:** `git checkout -b t-series-runtime`.
3. **Replace the code with v2:** copy this kit's `src/`, `scripts/`, `tests/`, `data/`, root files over the repo.
   Keep the repo's `findings/` folder and `.env` untouched.
4. **Carry forward the calibration work:** it already lives in v2 as
   `data/sources/knowledge_graph/reader_calibrated.json` (R1/R3/R4 wording, the Indian-English persona) and the
   `her_experience` flag on CRM notes n2, n3. If the repo's wording differs, the repo's version wins — copy it in.
5. `make test` → 11 green, then commit: "v2: T-series runtime — conditions as data, golden prompt, writer runs the procedure".
6. Do not merge to `main` until the first API series is recorded in `findings/`.

What changed from v1, in one table:

| v1 | v2 | Why |
|---|---|---|
| Writer writes; a separate reader scores | **One writer call runs the whole procedure (T7)**; the reader only verifies | That is what T7 did |
| Writer never saw the traces | **Writer receives B7 verbatim** | The traces are what T7 proved matters |
| Material cut to a 1,600-char budget; derived excluded | **No truncation; every block as the condition defines** | The experiment had neither |
| Seed files shaped for stores | **Source systems** + the experiment's blocks as a reference | Runtime rebuilds the blocks; golden test proves it |
| Toggle-store ablation | **Condition runner T0→T7** with controls, k repeats, two writers | The experiment's own shape |
| Reader verdict = success | **Human verdict = success**; proxies alongside | The claim is "a human-like line" |
