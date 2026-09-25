"""Knowledge graph — judgement made durable: archetypes, trigger->pain mappings, and the two traces.
Neo4j when configured and seeded (scripts/seed_graph.py); the seed files otherwise. The seed files are
the source of truth for both, and the judgement rules and the two traces are always read from them."""
from __future__ import annotations
import json
from .. import config

NO_ARCHETYPE = {"id": "none", "label": "no archetype matches this role — nothing earns the read here", "weight": 0}


class KnowledgeGraph:
    source = "seed file"

    def __init__(self, source: str | None = None):
        self.g = json.load(open(config.SEED / "knowledge_graph.json"))
        self.traces = json.load(open(config.SEED / "traces.json"))
        self.rules = json.load(open(config.SEED / "judgement_rules.json"))
        if source:
            self.source = source

    def pains_for(self, triggers: list[str]) -> list[dict]:
        hits = [m for m in self.g["trigger_pain"] if any(t in m["trigger"] for t in triggers)]
        return sorted(hits, key=lambda m: (m["priority"], m["trigger"], m["pain"]))  # same order as Neo4j

    def top_archetype(self, role: str, industry: str) -> dict:
        cands = [a for a in self.g["archetypes"] if any(x in (role + " " + industry) for x in a["earns_read_from"])]
        if not cands:  # say so; falling back to the highest weight would put a false archetype in the trace
            return NO_ARCHETYPE
        return max(cands, key=lambda a: a["weight"])

    def reader_trace(self) -> list[dict]:
        return self.traces["reader"]

    def seller_trace(self) -> list[dict]:
        return self.traces["seller"]


class Neo4jGraph(KnowledgeGraph):
    """pains_for and top_archetype answered by Cypher over the graph seed_graph.py loaded."""
    source = "neo4j"

    def __init__(self, driver):
        super().__init__()
        self.drv = driver

    def pains_for(self, triggers: list[str]) -> list[dict]:
        q = ("MATCH (t:Trigger)-[r:CAUSES]->(p:Pain) WHERE any(x IN $triggers WHERE t.name CONTAINS x) "
             "RETURN t.name AS trigger, p.name AS pain, r.priority AS priority ORDER BY priority, trigger, pain")
        with self.drv.session() as s:
            return [r.data() for r in s.run(q, triggers=triggers)]

    def top_archetype(self, role: str, industry: str) -> dict:
        q = ("MATCH (a:Archetype) WHERE any(x IN a.roles WHERE $who CONTAINS x) "
             "RETURN a.id AS id, a.label AS label, a.weight AS weight, a.roles AS earns_read_from "
             "ORDER BY weight DESC, id LIMIT 1")
        with self.drv.session() as s:
            rec = s.run(q, who=role + " " + industry).single()
        return rec.data() if rec else NO_ARCHETYPE


def get_graph() -> KnowledgeGraph:
    """Neo4j if it is configured, reachable and seeded; otherwise the seed files, saying why."""
    if not (config.NEO4J_URI and config.NEO4J_PASSWORD):
        return KnowledgeGraph()
    try:
        from neo4j import GraphDatabase
        drv = GraphDatabase.driver(config.NEO4J_URI, auth=(config.NEO4J_USER, config.NEO4J_PASSWORD), connection_timeout=3)
        drv.verify_connectivity()
        with drv.session() as s:
            seeded = s.run("MATCH (:Trigger)-[r:CAUSES]->(:Pain) RETURN count(r) AS n").single()["n"] > 0
        if seeded:
            return Neo4jGraph(drv)
        drv.close()
        return KnowledgeGraph(source="seed file (neo4j graph empty — run make seed)")
    except Exception as e:  # noqa: BLE001 — the file path must keep working
        return KnowledgeGraph(source=f"seed file (neo4j unreachable: {type(e).__name__})")
