"""Build sales.replay.v1 — the classroom view of one run, eight stops, query to line.
Local data always; LangSmith enrichment (trace URL) when a key and a run id exist."""
from __future__ import annotations
import json, os
from . import config

def build_replay(run: dict, conditions_table: dict | None = None) -> dict:
    total_ms = sum(s.get("ms", 0) for s in run.get("trace", []))
    url = None
    if run.get("run_id") and os.getenv("LANGSMITH_API_KEY"):
        try:
            from langsmith import Client
            url = Client().read_run(run["run_id"]).url
        except Exception:  # noqa: BLE001
            url = None
    stops = [
        {"n": 1, "title": "The query", "body": run.get("query")},
        {"n": 2, "title": "The orchestrator fetches", "sources": list((run.get("fetch") or {}).values())},
        {"n": 3, "title": "The assembled prompt", "condition": run["condition_id"], "prompt": run.get("prompt"), "spans": run.get("spans"), "golden": run.get("golden")},
        {"n": 4, "title": "The model runs", "model": (run.get("usage") or {}).get("model"), "tokens": run.get("usage"), "ms": run.get("write_ms"),
         "line": run.get("line"), "seller": run.get("seller"), "candidates": run.get("candidates"), "survivor": run.get("survivor")},
        {"n": 5, "title": "Code checks the procedure", "verification": run.get("verification")},
        {"n": 6, "title": "The eval", "checks": run.get("checks"), "verifier": run.get("verifier")},
        {"n": 7, "title": "Approval and send", "approval": run.get("approval"), "sent": run.get("sent")},
        {"n": 8, "title": "T0 → T7 for this prospect", "table": (conditions_table or {}).get("rows")},
    ]
    return {"kind": "sales.replay.v1", "condition": run["condition_id"], "prospect": run["prospect_id"], "stub": config.USE_STUB,
            "totals": {"ms": round(total_ms, 1), "model_ms": run.get("write_ms"), "tokens": run.get("usage")},
            "langsmith_url": url, "trace": run.get("trace"), "stops": stops}
