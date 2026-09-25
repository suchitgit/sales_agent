"""Create the system-of-record tables and load the seed; set up the checkpointer and store."""
import sys, json
sys.path.insert(0, "src")
from salesagent import config
import psycopg
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.store.postgres import PostgresStore
assert config.POSTGRES_URI, "POSTGRES_URI missing in .env"
with psycopg.connect(config.POSTGRES_URI, autocommit=True) as conn, conn.cursor() as cur:
    cur.execute("CREATE TABLE IF NOT EXISTS prospects (id text primary key, record jsonb)")
    cur.execute("CREATE TABLE IF NOT EXISTS decision_cases (id text primary key, record jsonb)")
    cur.execute("CREATE TABLE IF NOT EXISTS outcomes (id serial primary key, prospect text, line text, outcome jsonb, at timestamptz default now())")
    for p in json.load(open(config.SEED / "prospects.json")):
        cur.execute("INSERT INTO prospects VALUES (%s,%s) ON CONFLICT (id) DO UPDATE SET record=excluded.record", (p["id"], json.dumps(p)))
    for c in json.load(open(config.SEED / "decision_cases.json")):
        cur.execute("INSERT INTO decision_cases VALUES (%s,%s) ON CONFLICT (id) DO UPDATE SET record=excluded.record", (c["id"], json.dumps(c)))
with PostgresSaver.from_conn_string(config.POSTGRES_URI) as cp: cp.setup()
with PostgresStore.from_conn_string(config.POSTGRES_URI) as st:
    st.setup(); st.put(("rep", "rep-suchit"), "profile", json.load(open(config.SEED / "rep_profile.json")))
print("postgres seeded: prospects, decision_cases, outcomes · checkpointer + store set up · rep profile written")
