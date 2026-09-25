from __future__ import annotations
from typing import TypedDict, Annotated
import operator

class Candidate(TypedDict, total=False):
    id: str; text: str; results: list; died_at: str | None; reason: str | None

class Step(TypedDict):
    step: str; detail: str; actor: str; label: str

class SalesState(TypedDict, total=False):
    prospect_id: str; rep_id: str; thread_id: str
    stores_on: dict
    plan: list[str]
    context: dict; retrieved: list[dict]; her_history: list[dict]; memory: dict; kg: dict
    prompt: str
    candidates: list[Candidate]
    winner: Candidate | None
    declined: bool
    approval: dict
    sent: dict
    trace: Annotated[list[Step], operator.add]
    label: str
