from __future__ import annotations
from typing import TypedDict, Annotated
import operator

class Step(TypedDict):
    step: str; detail: str; actor: str; ms: float

class RunState(TypedDict, total=False):
    prospect_id: str; condition_id: str; writer_which: int; thread_id: str; query: str
    fetch: dict            # per-source: system, ms, summary
    blocks: dict
    golden: dict
    prompt: str; spans: list
    raw: str; usage: dict; write_ms: float
    line: str | None       # single-line conditions
    candidates: list; seller: dict; survivor: str | None
    verification: dict
    declined: bool
    approval: dict; sent: dict
    trace: Annotated[list[Step], operator.add]
