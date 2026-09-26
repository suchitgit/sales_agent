"""Derived data (B3) is COMPUTED at run time from the other sources — it has no source system of its own.
Deterministic rules, no model."""
from __future__ import annotations

def signals(post, jobs, notes):
    states = (post or {}).get("new_states", 0); sites = (post or {}).get("new_sites", 0)
    roles = jobs.get("open_roles", 0)
    tags = {t for n in notes for t in n.get("tags", [])}
    level = lambda cond_hi, cond_mh=False: "HIGH" if cond_hi else ("MEDIUM-HIGH" if cond_mh else "LOW")
    frag = "payroll-fragmentation" in tags
    out = {
        "Geographic expansion signal": level(states >= 2 or sites >= 2),
        "Hiring-scale signal": level(roles >= 100, roles >= 50),
        "Payroll-fragmentation signal": "MEDIUM-HIGH" if frag else "LOW",
        "Multi-state compliance exposure": "MEDIUM-HIGH" if (states >= 1 and frag) else "LOW",
        "Onboarding-scale requirement": level(roles >= 50),
    }
    interest = None
    if {"compliance-interest", "efficiency-interest"} & tags and "generic-ai-ignored" in tags:
        interest = "Compliance and HR operational efficiency appear more relevant than generic HR transformation."
    return out, interest
