.PHONY: setup verify test series series2 t7 replay langsmith deepeval rescore human
setup:     ## venv + packages + checks
	./setup_env.sh
verify:    ## environment checks
	. .venv/bin/activate && python scripts/verify_env.py
test:      ## 15 tests on the replay stub — no key, no network
	. .venv/bin/activate && pytest -q
series:    ## T0→T7 on the writer, k=3
	. .venv/bin/activate && python scripts/run_conditions.py 3
series2:   ## T0→T7 on both writers (the T1 identical-sentence check)
	. .venv/bin/activate && python scripts/run_conditions.py 3 --two-writers
t7:        ## one full T7 run, with the approval pause and the verifier
	. .venv/bin/activate && python scripts/run_one.py sunidhi T7 --verify
replay:    ## classroom replay of the latest T7 run → data/runs/replay_T7.json
	. .venv/bin/activate && python scripts/export_replay.py T7
langsmith: ## LangSmith experiment across all conditions
	. .venv/bin/activate && python scripts/eval_langsmith.py
deepeval:  ## DeepEval over the saved runs (+ --judge for the judged metric)
	. .venv/bin/activate && python scripts/eval_deepeval.py
rescore:   ## re-score the latest series from its saved raw answers — no model calls
	. .venv/bin/activate && python scripts/rescore.py
human:     ## open the review sheet — your verdict is the final call
	@echo "data/runs/human_review.csv"
