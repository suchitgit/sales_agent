"""Memory is three things. Session state -> the checkpointer (not here). Rep habits and prospect
history -> the LangGraph Store, namespaced. Past decisions with outcomes -> the system of record:
the decision_cases table in Postgres when it is reachable and seeded, the seed file otherwise."""
from __future__ import annotations
import json
from langgraph.store.base import BaseStore
from .. import config


def load_cases() -> tuple[list[dict], str]:
    """All past decisions, and where they came from — the trace names the source."""
    if config.POSTGRES_URI:
        try:
            import psycopg
            with psycopg.connect(config.POSTGRES_URI, connect_timeout=3) as conn:
                rows = conn.execute("SELECT record FROM decision_cases ORDER BY id").fetchall()
            if rows:
                return [r[0] for r in rows], "postgres"
            source = "seed file (decision_cases table empty — run make seed)"
        except Exception as e:  # noqa: BLE001 — the file path must keep working
            source = f"seed file (postgres unreachable: {type(e).__name__})"
    else:
        source = "seed file"
    return json.load(open(config.SEED / "decision_cases.json")), source


def past_decisions(pains: list[str], cases: list[dict] | None = None) -> list[dict]:
    cases = cases if cases is not None else load_cases()[0]
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
