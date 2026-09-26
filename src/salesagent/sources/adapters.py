from __future__ import annotations
import json, time
from .. import config
from ..guards.sanitize import sanitize

S = config.SOURCES
def _load(rel): return json.load(open(S / rel, encoding="utf-8"))

def _timed(system, fn):
    t = time.perf_counter(); out = fn(); ms = round((time.perf_counter() - t) * 1000, 2)
    return {"system": system, "ms": ms, "data": out}

def crm_account(prospect_id):          # CRM · account master  → B0
    def f():
        d = _load("crm_accounts.json"); a = next(x for x in d["accounts"] if x["id"] == prospect_id)
        return {"account": a, "seller": d["seller"]}
    return _timed("CRM · account master", f)

def social_post(prospect_id):          # Social feed           → B1
    def f():
        posts = [p for p in _load("social_feed.json")["posts"] if p["prospect"] == prospect_id]
        live = [p for p in posts if p["age_days"] <= config.TRIGGER_MAX_AGE_DAYS]
        return live[0] if live else None
    return _timed("Social feed", f)

def job_postings(company):             # Jobs feed             → B1
    def f():
        return next((c for c in _load("jobs_feed.json")["companies"] if c["company"] == company), {"company": company, "open_roles": 0})
    return _timed("Jobs feed", f)

def crm_notes(prospect_id):            # CRM · activity notes   → B2 (flagged notes kept aside, never in a block)
    def f():
        clean, flagged = [], []
        for n in _load("crm_notes.json")["notes"]:
            if n["prospect"] != prospect_id: continue
            _, is_flagged = sanitize(n["text"])
            (flagged if is_flagged else clean).append(n)
        return {"notes": clean, "flagged": flagged}
    return _timed("CRM · activity notes", f)

def decision_cases():                  # System of record       → B5
    return _timed("System of record", lambda: _load("system_of_record/decision_cases.json"))

def judgement():                       # Knowledge graph        → B4
    return _timed("Knowledge graph · judgement", lambda: _load("knowledge_graph/judgement_rules.json"))

def traces():                          # Knowledge graph        → B7
    return _timed("Knowledge graph · traces", lambda: _load("knowledge_graph/traces.json"))

def reader_calibrated():               # verifier wording only
    return _load("knowledge_graph/reader_calibrated.json")
