"""Load the knowledge graph into Neo4j (if configured) or Kùzu (embedded)."""
import sys, json, shutil
sys.path.insert(0, "src")
from salesagent import config
g = json.load(open(config.SEED / "knowledge_graph.json")); traces = json.load(open(config.SEED / "traces.json"))
use_neo4j = False
if config.NEO4J_URI and config.NEO4J_PASSWORD:
    try:
        from neo4j import GraphDatabase
        drv = GraphDatabase.driver(config.NEO4J_URI, auth=(config.NEO4J_USER, config.NEO4J_PASSWORD))
        drv.verify_connectivity(); use_neo4j = True
    except Exception as e:  # noqa: BLE001
        print(f"neo4j configured but unreachable ({type(e).__name__}) — using Kùzu")
if use_neo4j:
    with drv.session() as s:
        s.run("MATCH (n) DETACH DELETE n")
        for a in g["archetypes"]: s.run("CREATE (:Archetype {id:$id,label:$label,weight:$w,roles:$r})", id=a["id"], label=a["label"], w=a["weight"], r=a["earns_read_from"])
        for m in g["trigger_pain"]: s.run("MERGE (t:Trigger {name:$t}) MERGE (p:Pain {name:$p}) MERGE (t)-[:CAUSES {priority:$pr}]->(p)", t=m["trigger"], p=m["pain"], pr=m["priority"])
        for kind in ("reader", "seller"):
            for i, st in enumerate(traces[kind]): s.run("CREATE (:Check {trace:$k,id:$id,order:$o,q:$q})", k=kind, id=st["id"], o=i, q=st["q"])
        n = s.run("MATCH (n) RETURN count(n)").single()[0]
    drv.close(); print(f"neo4j seeded: {n} nodes")
else:
    import kuzu
    shutil.rmtree(config.KUZU_DIR, ignore_errors=True)
    c = kuzu.Connection(kuzu.Database(str(config.KUZU_DIR)))
    c.execute("CREATE NODE TABLE Trigger(name STRING, PRIMARY KEY(name))"); c.execute("CREATE NODE TABLE Pain(name STRING, PRIMARY KEY(name))")
    c.execute("CREATE REL TABLE CAUSES(FROM Trigger TO Pain, priority INT64)")
    for m in g["trigger_pain"]:
        c.execute(f"MERGE (:Trigger {{name:'{m['trigger']}'}})"); c.execute(f"MERGE (:Pain {{name:'{m['pain']}'}})")
        c.execute(f"MATCH (t:Trigger),(p:Pain) WHERE t.name='{m['trigger']}' AND p.name='{m['pain']}' CREATE (t)-[:CAUSES {{priority:{m['priority']}}}]->(p)")
    n = c.execute("MATCH (t:Trigger)-[r:CAUSES]->(p:Pain) RETURN count(r)").get_next()[0]
    print(f"kùzu seeded at {config.KUZU_DIR}: {n} trigger→pain edges (Neo4j not in use)")
