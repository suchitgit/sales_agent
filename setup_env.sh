#!/usr/bin/env bash
# Sales agent kit — setup (macOS / Linux / WSL2).  ./setup_env.sh   or   ./setup_env.sh --no-docker
set -euo pipefail
USE_DOCKER=1; [[ "${1:-}" == "--no-docker" ]] && USE_DOCKER=0
say(){ printf "\n\033[1;33m▶ %s\033[0m\n" "$*"; }; ok(){ printf "  \033[1;32m✓\033[0m %s\n" "$*"; }; fail(){ printf "  \033[1;31m✗ %s\033[0m\n" "$*"; exit 1; }
cd "$(dirname "$0")"
say "1/7 · Prerequisites"
command -v python3 >/dev/null || fail "python3 not found — install Python 3.10+"
python3 -c 'import sys;sys.exit(0 if sys.version_info>=(3,10) else 1)' || fail "Python 3.10+ required"
ok "$(python3 --version)"
if [[ $USE_DOCKER -eq 1 ]]; then
  command -v docker >/dev/null || fail "docker not found — install Docker Desktop, or rerun with --no-docker"
  docker info >/dev/null 2>&1 || fail "Docker is installed but not running"; ok "Docker running"; fi
say "2/7 · Virtual environment"; [[ -d .venv ]] || python3 -m venv .venv; source .venv/bin/activate; python -m pip install -q --upgrade pip; ok "$(python --version) in .venv"
say "3/7 · Packages"; pip install -r requirements.txt; pip freeze > requirements.lock; ok "core packages installed · requirements.lock written (optional extras: requirements-optional.txt)"
say "4/7 · Configuration"; [[ -f .env ]] || cp .env.example .env; mkdir -p data/synthetic data/index; ok ".env ready — add ANTHROPIC_API_KEY to use the API; empty key = stub model"
if [[ $USE_DOCKER -eq 1 ]]; then
  say "5/7 · Services"; docker compose up -d
  for c in sales-neo4j sales-postgres; do printf "  waiting for $c"; for _ in $(seq 1 60); do docker inspect -f '{{.State.Health.Status}}' $c 2>/dev/null | grep -q healthy && break; printf "."; sleep 3; done; echo; done
  ok "Neo4j → http://localhost:7474 · Postgres → localhost:5432"
  sed -i.bak -e 's/^# POSTGRES_URI=/POSTGRES_URI=/' -e 's/^# NEO4J_URI=/NEO4J_URI=/' .env && rm -f .env.bak
  ok "service URIs enabled in .env"
  say "6/7 · Seeding"; python scripts/seed_postgres.py; python scripts/seed_graph.py
else
  say "5/7 · Skipping Docker — Kùzu embedded graph, in-memory checkpointer"; say "6/7 · Seeding"; python scripts/seed_graph.py; fi
say "7/7 · Verification"; python scripts/verify_env.py
printf "\n\033[1;32mDone.\033[0m Try:  python scripts/run_one.py sunidhi --auto     then:  claude\n\n"
