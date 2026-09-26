"""fetch → assemble(condition) → write → verify → approve → send.
The orchestrator's job is to assemble exactly the condition's blocks from the source systems. The WRITER
does the rest; code only verifies the writer followed the procedure."""
from __future__ import annotations
import json, time
from langchain_core.messages import HumanMessage
from .. import config
from ..blocks import fetch_all, build, assemble as assemble_prompt, golden
from ..models import get_writer, parse_json, usage
from ..guards.approval import request_approval
from ..guards.idempotency import send_key, send_once

CONDITIONS = {c["id"]: c for c in json.load(open(config.EXPERIMENT / "conditions.json"))["conditions"]}
T = lambda step, detail, actor="code", ms=0.0: {"step": step, "detail": detail, "actor": actor, "ms": ms}


def fetch(state):
    f = fetch_all(state["prospect_id"])
    notes = f["notes"]["data"]
    summary = {
        "account": {"system": f["account"]["system"], "ms": f["account"]["ms"], "returned": f"{f['account']['data']['account']['name']} · {f['account']['data']['account']['role']}"},
        "post": {"system": f["post"]["system"], "ms": f["post"]["ms"], "returned": (f["post"]["data"] or {}).get("text", "no live post")},
        "jobs": {"system": f["jobs"]["system"], "ms": f["jobs"]["ms"], "returned": f"{f['jobs']['data']['open_roles']} open roles"},
        "notes": {"system": f["notes"]["system"], "ms": f["notes"]["ms"], "returned": f"{len(notes['notes'])} notes" + (f" · flagged and excluded: {', '.join(n['id'] for n in notes['flagged'])}" if notes["flagged"] else "")},
        "cases": {"system": f["cases"]["system"], "ms": f["cases"]["ms"], "returned": f"{len(f['cases']['data']['cases'])} past decisions"},
        "judgement": {"system": f["judgement"]["system"], "ms": f["judgement"]["ms"], "returned": f"{len(f['judgement']['data']['rules'])} rules"},
        "traces": {"system": f["traces"]["system"], "ms": f["traces"]["ms"], "returned": "reader R1–R6 · seller S1–S5 · task"},
    }
    blocks = build(f)
    tr = [T(f"fetch · {v['system']}", v["returned"], ms=v["ms"]) for v in summary.values()]
    tr.append(T("derive · B3", "signals computed from feed + jobs + notes (no source system)"))
    return {"fetch": summary, "blocks": blocks, "declined": not f["post"]["data"], "trace": tr}


def assemble(state):
    cond = CONDITIONS[state["condition_id"]]
    if state.get("declined"):
        return {"prompt": "", "spans": [], "golden": {}, "trace": [T("assemble", "no live trigger — nothing to write; the agent declines")]}
    prompt, spans = assemble_prompt(state["blocks"], cond)
    g = golden(state["blocks"]) if state["prospect_id"] == "sunidhi" else {}
    used = [b for b in cond["blocks"]]
    gtxt = ("golden match: " + ", ".join(f"{b} {'✓' if g.get(b if b != 'B5a' else 'B5', True) else '✗'}" for b in used)) if g else "no experiment reference for this prospect"
    return {"prompt": prompt, "spans": spans, "golden": g,
            "trace": [T("assemble", f"condition {cond['id']} · blocks {' + '.join(used)} · {len(prompt)} chars, no truncation · {gtxt}")]}


def write(state):
    if state.get("declined"):
        return {}
    cid = state["condition_id"]; w = get_writer(cid, state.get("writer_which", 1))
    t = time.perf_counter(); msg = w.invoke([HumanMessage(content=state["prompt"])]); ms = round((time.perf_counter() - t) * 1000, 1)
    u = usage(msg); model = getattr(w, "model", None) or getattr(w, "model_name", None) or u.get("model")
    out = {"raw": msg.content, "usage": {**u, "model": model}, "write_ms": ms}
    if CONDITIONS[cid]["mode"] == "single":
        line = msg.content.strip().strip('"').splitlines()[0].strip().strip('"')
        out.update(line=line, trace=[T("write", f"{model} → “{line}”", actor="model", ms=ms)])
    else:
        try:
            j = parse_json(msg.content)
            out.update(candidates=j.get("candidates", []), seller=j.get("seller", {}), survivor=j.get("survivor"))
            out["trace"] = [T("write · procedure", f"{model} ran S1–S5, wrote {len(out['candidates'])} candidates, scored R1–R6, chose “{out['survivor']}”", actor="model", ms=ms)]
        except Exception as e:  # noqa: BLE001
            out.update(candidates=[], survivor=None, trace=[T("write · procedure", f"{model} output was not valid JSON ({type(e).__name__}) — recorded as a procedure failure", actor="model", ms=ms)])
    return out


def verify(state):
    """Code checks the writer's own procedure — it does not re-judge the line."""
    if state.get("declined") or CONDITIONS[state["condition_id"]]["mode"] != "procedure":
        return {}
    cands, surv, issues = state.get("candidates", []), state.get("survivor"), []
    if len(cands) != 3: issues.append(f"{len(cands)} candidates, expected 3")
    for c in cands:
        ids = [x.get("id") for x in c.get("checks", [])]
        if ids != [f"R{i}" for i in range(1, len(ids) + 1)]: issues.append(f"“{c.get('text','')[:30]}…” checks out of order: {ids}")
        fails = [x for x in c.get("checks", []) if not x.get("pass")]
        if fails and c.get("checks", [])[-1] is not fails[0]: issues.append(f"“{c.get('text','')[:30]}…” did not stop at its first failure")
        if fails and c.get("died_at") != fails[0].get("id"): issues.append(f"“{c.get('text','')[:30]}…” died_at does not match its first failure")
    surv_c = next((c for c in cands if c.get("text") == surv), None)
    if not surv_c: issues.append("survivor is not one of the candidates")
    elif len(surv_c.get("checks", [])) != 6 or not all(x.get("pass") for x in surv_c["checks"]): issues.append("survivor did not pass all six")
    v = {"adherence": not issues, "issues": issues, "killed": [(c.get("text"), c.get("died_at")) for c in cands if c.get("died_at")]}
    return {"verification": v, "trace": [T("verify", "procedure followed: checks in order, stopped at first failure, survivor all-pass" if not issues else "procedure issues: " + "; ".join(issues))]}


def approve(state):
    ok_to_send = state.get("survivor") and state.get("verification", {}).get("adherence")
    if state.get("declined") or not ok_to_send or not config.SEND_APPROVAL_REQUIRED:
        return {"approval": {"approved": bool(ok_to_send) and not config.SEND_APPROVAL_REQUIRED, "skipped": not ok_to_send}}
    d = request_approval({"line": state["survivor"], "rejected": [{"text": t, "died_at": d} for t, d in state["verification"]["killed"]]})
    return {"approval": d, "trace": [T("approve", f"rep decision: {d}", actor="human")]}


def send(state):
    if not state.get("approval", {}).get("approved"):
        return {"sent": {"status": "not_sent"}, "trace": [T("send", "nothing left the system")]}
    key = send_key(state.get("thread_id", "t"), state["survivor"])
    r = send_once(key, lambda: {"line": state["survivor"]})
    return {"sent": r, "trace": [T("send", f"{r['status']} · key {key} · label HYPOTHESIS until the outcome returns")]}
