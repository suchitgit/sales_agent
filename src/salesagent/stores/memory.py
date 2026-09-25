"""Memory is three things. Session state -> the checkpointer (not here). Rep habits and prospect
history -> the LangGraph Store, namespaced. Past decisions with outcomes -> the system of record,
read here from seed (Postgres when seeded)."""
from __future__ import annotations
import json
from langgraph.store.base import BaseStore
from .. import config


def past_decisions(pains: list[str]) -> list[dict]:
    cases = json.load(open(config.SEED / "decision_cases.json"))
    return [c for c in cases if any(p.split()[0] in (c["context"] + " " + c["pain"]) for p in pains)] or cases[:2]


def rep_profile(store: BaseStore | None, rep_id: str) -> dict:
    if store is not None:
        item = store.get(("rep", rep_id), "profile")
        if item:
            return item.value
    prof = json.load(open(config.SEED / "rep_profile.json"))
    if store is not None:
        store.put(("rep", rep_id), "profile", prof)
    return prof


def write_outcome(store: BaseStore, rep_id: str, prospect_id: str, outcome: dict):
    store.put(("rep", rep_id, "outcomes"), prospect_id, outcome)
