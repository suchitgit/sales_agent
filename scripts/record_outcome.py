"""The feedback write, run later.
Usage: python scripts/record_outcome.py <prospect_id> <opened|replied|ignored|edited> [--rep rep-id] [--line "..."]"""
import sys, json, time
sys.path.insert(0, "src")
from salesagent import config
args = sys.argv[1:]
pid, outcome = args[0], args[1]
rep = args[args.index("--rep") + 1] if "--rep" in args else "rep-suchit"
line = args[args.index("--line") + 1] if "--line" in args else ""
rec = {"prospect": pid, "rep": rep, "line": line, "outcome": outcome, "label": "TESTED", "at": int(time.time())}
if config.POSTGRES_URI:
    try:
        import psycopg
        from langgraph.store.postgres import PostgresStore
        with psycopg.connect(config.POSTGRES_URI, autocommit=True) as conn:
            conn.execute("INSERT INTO outcomes (prospect, line, outcome) VALUES (%s,%s,%s)", (pid, line, json.dumps(rec)))
        with PostgresStore.from_conn_string(config.POSTGRES_URI) as st:
            st.setup(); st.put(("rep", rep, "outcomes"), pid, rec)
        print("outcome written to Postgres and the Store; label moves to TESTED"); sys.exit(0)
    except Exception as e:  # noqa: BLE001
        print(f"postgres unreachable ({type(e).__name__}) —", end=" ")
print("would write:", json.dumps(rec))
