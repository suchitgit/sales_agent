"""Knowledge graph — judgement made durable: archetypes, trigger->pain mappings, and the two traces.
Neo4j when configured; Kùzu embedded otherwise; the seed file is the source of truth for both."""
from __future__ import annotations
import json
from .. import config


class KnowledgeGraph:
    def __init__(self):
        self.g = json.load(open(config.SEED / "knowledge_graph.json"))
        self.traces = json.load(open(config.SEED / "traces.json"))
        self.rules = json.load(open(config.SEED / "judgement_rules.json"))

    def pains_for(self, triggers: list[str]) -> list[dict]:
        hits = [m for m in self.g["trigger_pain"] if any(t in m["trigger"] for t in triggers)]
        return sorted(hits, key=lambda m: m["priority"])

    def top_archetype(self, role: str, industry: str) -> dict:
        cands = [a for a in self.g["archetypes"] if any(x in (role + " " + industry) for x in a["earns_read_from"])]
        if not cands:  # say so; falling back to the highest weight would put a false archetype in the trace
            return {"id": "none", "label": "no archetype matches this role — nothing earns the read here", "weight": 0}
        return max(cands, key=lambda a: a["weight"])

    def reader_trace(self) -> list[dict]:
        return self.traces["reader"]

    def seller_trace(self) -> list[dict]:
        return self.traces["seller"]
