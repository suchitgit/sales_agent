"""The spine, node by node. Code owns the order. The model is called at exactly two points:
generate (once) and score (once per check). Every node appends to the trace as it runs."""
from __future__ import annotations
import json
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.store.base import BaseStore
from .. import config
from ..models import get_model, parse_json
from ..stores.context import get_context
from ..stores.retrieval import Retrieval
from ..stores.memory import load_cases, past_decisions, rep_profile
from ..stores.graph import KnowledgeGraph
from ..guards.approval import request_approval
from ..guards.idempotency import send_key, send_once

_ret, _kg = Retrieval(), KnowledgeGraph()
T = lambda step, detail, actor="code", label="READ": {"step": step, "detail": detail, "actor": actor, "label": label}


def plan(state):
    steps = [s["id"] for s in _kg.seller_trace()]
    return {"plan": steps, "trace": [T("plan", "S1–S5 loaded from the knowledge graph as a constant; the model decides nothing here")]}


def fetch(state, *, store: BaseStore = None):
    on = state.get("stores_on") or {"context": True, "retrieval": True, "memory": True, "kg": True}
    ctx = get_context(state["prospect_id"])
    if not on["context"]:
        ctx = {**ctx, "trigger": None, "facts": [], "has_live_trigger": True, "new_states": ctx["new_states"], "open_roles": ctx["open_roles"]}
    triggers = []
    if ctx["has_live_trigger"]:
        if ctx["new_states"]: triggers.append("new states")
        if ctx["open_roles"] >= 50: triggers.append("open roles")
        if "depot" in (ctx["trigger"] or "").lower(): triggers.append("new depots")
    pains = _kg.pains_for(triggers)
    query = " ".join([p["pain"] for p in pains] + ["payroll", "reconciliation", "onboarding"])
    retrieved = _ret.search(query, state["prospect_id"]) if on["retrieval"] else []
    flagged = [r for r in retrieved if r["flagged"]]
    all_cases, cases_from = load_cases()
    mem = {"cases": past_decisions([p["pain"] for p in pains], all_cases), "rep": rep_profile(store, state.get("rep_id", "rep-suchit"))}
    kg = {"pains": pains if on["kg"] else [], "archetype": _kg.top_archetype(ctx["prospect"]["role"], ctx["prospect"]["industry"]) if on["kg"] else {"label": "none", "id": "none"},
          "rules": _kg.rules if on["kg"] else [], "reader": _kg.reader_trace()}
    if not on["memory"]:
        mem = {"cases": [], "rep": {"habits": []}}
    tr = [T("fetch · context", f"trigger={'none' if not ctx['has_live_trigger'] else ctx['trigger']} · roles={ctx['open_roles']}"),
          T("fetch · retrieval", f"{len(retrieved) - len(flagged)} dormant facts" + (f" · {len(flagged)} note(s) flagged as instruction-like: {', '.join(f['id'] for f in flagged)} — kept as data, excluded from the prompt" if flagged else "")),
          T("fetch · memory", f"{len(mem['cases'])} past decisions with outcomes, from {cases_from} · rep habits loaded"),
          T("fetch · knowledge graph", f"{len(pains)} trigger→pain mappings · archetype: {kg['archetype']['label']}")]
    return {"context": ctx, "retrieved": retrieved, "memory": mem, "kg": kg, "trace": tr}


def _cut(text: str, budget: int) -> str:
    return text if len(text) <= budget else text[: max(0, budget - 1)].rstrip() + "…"


def assemble(state):
    """Hands the model MATERIAL only — facts, mappings, rules, the archetype. Never the answer.
    The deadline is the model's to compute from her numbers; that is the R3 test. Each store's text is
    cut to its share of the character budget (config.PROPORTION), so the proportion is enforced."""
    ctx, kg = state["context"], state["kg"]
    if not ctx["has_live_trigger"]:
        return {"prompt": "", "declined": True, "trace": [T("assemble", "No live trigger inside the freshness window — the agent declines to write")]}
    B = config.PROMPT_BUDGET_CHARS
    on = state.get("stores_on") or {"context": True, "retrieval": True, "memory": True, "kg": True}
    sections = {}
    # basic (T0) is not a store and not a toggle: who she is and what we sell always reach the prompt
    basic = "\n".join([f"company: {ctx['prospect']['company']}", f"prospect: {ctx['prospect']['name']}, {ctx['prospect']['role']}, {ctx['prospect']['industry']}",
                        "seller: HumanAITech — multi-state statutory compliance, payroll consolidation, onboarding at scale"])
    sections["context"] = "\n".join([f"trigger: {ctx['trigger']}", f"facts: {' | '.join(ctx['facts'])}", f"new_states: {ctx['new_states']}", f"open_roles: {ctx['open_roles']}"]) if on["context"] else ""
    facts = [r["text"] for r in state["retrieved"] if not r["flagged"]]
    sections["retrieval"] = ("dormant: " + " | ".join(facts)) if (on["retrieval"] and facts) else ""
    cases = state["memory"]["cases"]
    sections["memory"] = ("past decisions: " + " | ".join(f"{c['id']} {c['context']} → {c['pain']} → {c['outcome']}" for c in cases) + f"\nrep habits: {', '.join(state['memory']['rep']['habits'])}") if on["memory"] else ""
    sections["kg"] = ("\n".join([f"trigger→pain: " + " | ".join(f"{m['trigger']} → {m['pain']} (priority {m['priority']})" for m in kg["pains"]),
                                 f"archetype that earns the read from {ctx['prospect']['role']} in {ctx['prospect']['industry']}: {kg['archetype']['label']}",
                                 "judgement: " + " ".join(kg["rules"][:3])])) if on["kg"] else ""
    cut = {k: _cut(v, int(B * config.PROPORTION[k])) for k, v in sections.items()}
    prompt = "\n".join([basic] + [v for v in cut.values() if v])
    used = {k: len(v) for k, v in cut.items()}
    return {"prompt": prompt, "declined": False,
            "trace": [T("assemble", f"material only, no deadline supplied · budget {B} chars · used {used} · derived signals excluded as inert")]}


def generate(state):
    if state.get("declined"):
        return {"candidates": []}
    llm = get_model("medium")
    msgs = [SystemMessage(content="You write subject lines for a salesperson. Reply with JSON only: {\"candidates\": [three strings]}."),
            HumanMessage(content="TASK: write three candidate subject lines for this prospect, from these facts only. Do not repeat her own news back to her. If her numbers imply a deadline she has not stated, you may compute it and use it.\n" + state["prompt"])]
    out = parse_json(llm.invoke(msgs).content)
    cands = [{"id": chr(65 + i), "text": c, "results": [], "died_at": None, "reason": None} for i, c in enumerate(out["candidates"][:3])]
    return {"candidates": cands, "trace": [T("generate", f"model call 1 → {len(cands)} candidates", actor="model", label="HYPOTHESIS")]}


def score(state):
    if state.get("declined"):
        return {"winner": None}
    on = state.get("stores_on") or {"kg": True}
    if not on.get("kg", True):
        # the six checks live in the knowledge graph; without it there is nothing to score against —
        # the best-informed candidate ships as written. This is T0–T5: a line, unscored, automation.
        cands = [dict(c, results=[], died_at=None, reason=None) for c in state["candidates"]]
        w = cands[-1] if cands else None
        return {"candidates": cands, "winner": w,
                "trace": [T("score", "no reader trace available (knowledge graph off) — best-informed candidate taken as written, unscored", label="HYPOTHESIS"),
                          T("select", f"unscored: \u201c{w['text']}\u201d" if w else "nothing to select", label="HYPOTHESIS")]}
    llm = get_model("small")
    ctx = state["context"]
    known = f"{ctx['trigger']} {' '.join(ctx['facts'])}"
    reader = state["kg"]["reader"]
    cands, tr, winner = [], [], None
    for c in state["candidates"]:
        c = dict(c); c["results"] = []
        for chk in reader:  # in order; break at first failure — the loop is code
            msgs = [SystemMessage(content="You are the prospect reading a subject line in two seconds. Reply with JSON only: {\"pass\": true|false, \"reason\": \"...\"}."),
                    HumanMessage(content=f"CHECK: {chk['id']} — {chk['q']} (fails if: {chk['kill']})\nCANDIDATE: {c['text']}\nKNOWN_TO_HER: {known}")]
            v = parse_json(llm.invoke(msgs).content)
            c["results"].append({"id": chk["id"], "pass": bool(v["pass"]), "reason": v.get("reason", "")})
            if not v["pass"]:
                c["died_at"], c["reason"] = chk["id"], v.get("reason", "")
                tr.append(T(f"score {c['id']} · rejected at {chk['id']}", f"\u201c{c['text']}\u201d — {c['reason']}", actor="model", label="HYPOTHESIS"))
                break
        else:
            tr.append(T(f"score {c['id']} · clears all six", f"\u201c{c['text']}\u201d", actor="model", label="HYPOTHESIS"))
            if winner is None:
                winner = c
        cands.append(c)
    tr.append(T("select", f"survivor: \u201c{winner['text']}\u201d" if winner else "no candidate cleared all six", label="HYPOTHESIS"))
    return {"candidates": cands, "winner": winner, "trace": tr}


def approve(state):
    if state.get("declined") or not state.get("winner"):
        return {"approval": {"approved": False, "skipped": True}}
    if not config.SEND_APPROVAL_REQUIRED:
        return {"approval": {"approved": True, "auto": True}}
    decision = request_approval({"line": state["winner"]["text"],
                                 "rejected": [{"id": c["id"], "text": c["text"], "died_at": c["died_at"], "reason": c["reason"]} for c in state["candidates"] if c["died_at"]]})
    return {"approval": decision, "trace": [T("approve", f"rep decision: {decision}", actor="human", label="READ")]}


def send(state):
    if not state.get("approval", {}).get("approved"):
        return {"sent": {"status": "not_sent"}, "label": "DECLINED" if state.get("declined") else "NOT_APPROVED",
                "trace": [T("send", "nothing left the system")]}
    key = send_key(state.get("thread_id", "t"), state["winner"]["text"])
    result = send_once(key, lambda: {"to": state["context"]["prospect"]["name"], "line": state["winner"]["text"]})
    return {"sent": result, "label": "HYPOTHESIS", "trace": [T("send", f"{result['status']} · key {key} · label HYPOTHESIS until the outcome returns")]}
