"""The eval checks. Same names as on the project site so results are comparable."""
def r3_novelty(prospect, run):
    w = run.get("winner")
    return (w is None) if prospect["expect"] == "decline" else bool(w and all(r["pass"] for r in w["results"]) and any(r["id"] == "R3" and r["pass"] for r in w["results"]))

import re
def competitor(prospect, run):
    """Proxy for 'could a competitor with the same public data have written it?': the winner must carry
    a temporal clause (a deadline she has not stated) and must not be one of the public-data shapes.
    A proxy, not a proof — the human read of the line is the real test."""
    w = run.get("winner")
    if prospect["expect"] == "decline":
        return w is None
    if not w:
        return False
    t = w["text"]
    public_shapes = (t.startswith("Consolidating"), t.startswith("Supporting"), t.startswith("Multi-state payroll compliance across"))
    return (not any(public_shapes)) and re.search(r"\b(before|by|within)\b", t) is not None

def null_safety(prospect, run):
    return run.get("winner") is None if prospect["expect"] == "decline" else True

def trace_complete(prospect, run):
    return len(run.get("trace", [])) >= 6 and all(c.get("results") is not None for c in run.get("candidates", []))

CHECKS = {"r3": r3_novelty, "competitor": competitor, "null_safety": null_safety, "trace": trace_complete}
