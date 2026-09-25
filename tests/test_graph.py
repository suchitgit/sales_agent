import sys; sys.path.insert(0, "src")
from salesagent.stores.graph import KnowledgeGraph

def test_cfo_gets_no_archetype():
    a = KnowledgeGraph().top_archetype("CFO", "freight")
    assert a["id"] == "none" and a["weight"] == 0

def test_vp_hr_in_logistics_gets_the_clock_archetype():
    assert KnowledgeGraph().top_archetype("VP HR", "mid-size logistics")["id"] == "computed_clock"

def test_graph_from_seed_file_without_neo4j(monkeypatch):
    from salesagent import config
    from salesagent.stores.graph import get_graph
    monkeypatch.setattr(config, "NEO4J_URI", "")
    assert get_graph().source == "seed file"

def test_unreachable_neo4j_falls_back_to_seed_file(monkeypatch):
    from salesagent import config
    from salesagent.stores.graph import get_graph
    monkeypatch.setattr(config, "NEO4J_URI", "bolt://127.0.0.1:1"); monkeypatch.setattr(config, "NEO4J_PASSWORD", "x")
    g = get_graph()
    assert type(g).__name__ == "KnowledgeGraph" and g.source.startswith("seed file (neo4j unreachable")
    assert g.pains_for(["new states"])[0]["pain"] == "multi-state statutory compliance"
