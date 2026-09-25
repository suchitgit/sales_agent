import sys; sys.path.insert(0, "src")
from salesagent.stores.graph import KnowledgeGraph

def test_cfo_gets_no_archetype():
    a = KnowledgeGraph().top_archetype("CFO", "freight")
    assert a["id"] == "none" and a["weight"] == 0

def test_vp_hr_in_logistics_gets_the_clock_archetype():
    assert KnowledgeGraph().top_archetype("VP HR", "mid-size logistics")["id"] == "computed_clock"
