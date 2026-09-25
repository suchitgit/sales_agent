"""Context — volatile, per request. Read from the prospect record; held in graph state; never stored."""
from __future__ import annotations
import json
from .. import config

MAX_TRIGGER_AGE_DAYS = 30  # the freshness rule: older than this is no trigger


def load_prospects() -> dict:
    return {p["id"]: p for p in json.load(open(config.SEED / "prospects.json"))}


def get_context(prospect_id: str) -> dict:
    p = load_prospects()[prospect_id]
    ctx = dict(p["context"])
    age = ctx.get("trigger_age_days")
    fresh = ctx["trigger"] is not None and age is not None and age <= MAX_TRIGGER_AGE_DAYS
    return {"prospect": {k: p[k] for k in ("id", "name", "role", "company", "industry")},
            "trigger": ctx["trigger"] if fresh else None, "facts": ctx["facts"] if fresh else [],
            "new_states": ctx["new_states"], "open_roles": ctx["open_roles"],
            "derived": p["derived"], "has_live_trigger": fresh}
