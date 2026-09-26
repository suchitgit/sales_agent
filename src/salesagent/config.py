"""Settings from .env. The writer is the model under test; everything else is the 80%."""
from __future__ import annotations
import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")
SOURCES = ROOT / "data" / "sources"
EXPERIMENT = ROOT / "data" / "experiment"
RUNS = ROOT / "data" / "runs"

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
MODEL_WRITER = os.getenv("MODEL_WRITER", "claude-fable-5-1")        # T7 parity: the experiment's best line came from Fable 5.1
MODEL_WRITER_2 = os.getenv("MODEL_WRITER_2", "claude-sonnet-5")      # second writer, for the cross-model checks (T1)
MODEL_READER = os.getenv("MODEL_READER", "claude-sonnet-5")          # independent verifier only — never the gate
USE_STUB = os.getenv("STUB_MODEL", "").lower() in ("1", "true") or not ANTHROPIC_API_KEY

POSTGRES_URI = os.getenv("POSTGRES_URI", "")
SEND_APPROVAL_REQUIRED = os.getenv("SEND_APPROVAL_REQUIRED", "true").lower() == "true"
TRIGGER_MAX_AGE_DAYS = 30
