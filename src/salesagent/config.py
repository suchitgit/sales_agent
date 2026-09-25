"""Settings, read from .env. Nothing here needs a model."""
from __future__ import annotations
import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

SEED = ROOT / "data" / "seed"
SYNTH = ROOT / "data" / "synthetic"
INDEX = ROOT / "data" / "index"

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
MODEL_SMALL = os.getenv("MODEL_SMALL", "claude-haiku-4-5-20251001")
MODEL_MEDIUM = os.getenv("MODEL_MEDIUM", "claude-sonnet-5")
USE_STUB = os.getenv("STUB_MODEL", "").lower() in ("1", "true") or not ANTHROPIC_API_KEY

POSTGRES_URI = os.getenv("POSTGRES_URI", "")
NEO4J_URI = os.getenv("NEO4J_URI", "")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")
KUZU_DIR = Path(os.getenv("KUZU_DIR", str(ROOT / "data" / "kuzu")))

# token budget — share of the assembled prompt per store; tuned by ablation (Context Eval)
PROPORTION = {"context": 0.35, "retrieval": 0.25, "memory": 0.10, "kg": 0.30}
PROMPT_BUDGET_CHARS = int(os.getenv("PROMPT_BUDGET_CHARS", "1600"))  # enforced in assemble
SEND_APPROVAL_REQUIRED = True
