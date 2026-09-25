.PHONY: setup verify test guard run evals seed up down clean
setup:      ## full setup
	./setup_env.sh
verify:     ## the checks only
	. .venv/bin/activate && python scripts/verify_env.py
test:       ## pytest on the stub model (no key needed)
	. .venv/bin/activate && pytest -q
guard:      ## the reader must clear the known winning line, pass^3, ON THE API (reader = MODEL_SMALL in .env)
	. .venv/bin/activate && API_TESTS=1 pytest -q tests/test_spine.py::test_reader_clears_the_known_winning_line
run:        ## one prospect, with approval prompt  (make run P=arun)
	. .venv/bin/activate && python scripts/run_one.py $(or $(P),sunidhi) --export data/synthetic/$(or $(P),sunidhi)_trace.json
evals:      ## pass^k suite, exports sales.eval.v1
	. .venv/bin/activate && python scripts/run_evals.py 5 data/synthetic/eval.json
seed:       ## reseed Postgres + graph
	. .venv/bin/activate && python scripts/seed_postgres.py && python scripts/seed_graph.py
up:
	docker compose up -d
down:
	docker compose down
clean:
	docker compose down -v
