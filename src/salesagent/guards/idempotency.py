"""Send-once. The key is thread + line. The record lives in Postgres when configured (survives a
restart — the resumed approval cannot send twice); in memory otherwise."""
import hashlib
from .. import config
_sent: set[str] = set()

def send_key(thread_id: str, line: str) -> str:
    return hashlib.sha256(f"{thread_id}|{line}".encode()).hexdigest()[:16]

def _pg():
    if not config.POSTGRES_URI:
        return None
    try:
        import psycopg
        conn = psycopg.connect(config.POSTGRES_URI, autocommit=True, connect_timeout=3)
        conn.execute("CREATE TABLE IF NOT EXISTS sent_keys (key text primary key, at timestamptz default now())")
        return conn
    except Exception:  # noqa: BLE001
        return None

def send_once(key: str, do_send) -> dict:
    conn = _pg()
    if conn is not None:
        with conn:
            row = conn.execute("SELECT 1 FROM sent_keys WHERE key=%s", (key,)).fetchone()
            if row:
                return {"status": "already_sent", "key": key, "record": "postgres"}
            result = do_send()
            conn.execute("INSERT INTO sent_keys (key) VALUES (%s) ON CONFLICT DO NOTHING", (key,))
            return {"status": "sent", "key": key, "record": "postgres", **result}
    if key in _sent:
        return {"status": "already_sent", "key": key, "record": "memory"}
    result = do_send(); _sent.add(key)
    return {"status": "sent", "key": key, "record": "memory", **result}
