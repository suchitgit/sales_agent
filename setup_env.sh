#!/usr/bin/env bash
# Sales agent kit v2 — setup. No Docker needed.   ./setup_env.sh
set -euo pipefail
cd "$(dirname "$0")"
say(){ printf "\n\033[1;33m▶ %s\033[0m\n" "$*"; }; ok(){ printf "  \033[1;32m✓\033[0m %s\n" "$*"; }; fail(){ printf "  \033[1;31m✗ %s\033[0m\n" "$*"; exit 1; }
say "1/4 · Python"; command -v python3 >/dev/null || fail "python3 not found"; python3 -c 'import sys;sys.exit(0 if sys.version_info>=(3,10) else 1)' || fail "Python 3.10+ required"; ok "$(python3 --version)"
say "2/4 · Virtual environment"; [[ -d .venv ]] || python3 -m venv .venv; source .venv/bin/activate; python -m pip install -q --upgrade pip; ok ".venv"
say "3/4 · Packages"; pip install -q -r requirements.txt -r requirements-observability.txt; pip freeze > requirements.lock; ok "core + observability installed · requirements.lock written"
say "4/4 · Configuration"; [[ -f .env ]] || cp .env.example .env; ok ".env ready — add ANTHROPIC_API_KEY and LANGSMITH_API_KEY"
python scripts/verify_env.py
printf "\nNext:  make test  ·  make series  ·  make t7  ·  then: claude\n\n"
