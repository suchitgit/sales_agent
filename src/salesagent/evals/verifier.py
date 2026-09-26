"""Independent reader — a VERIFIER, not the gate. Scores the final line against the calibrated R1–R6 wording,
all six checks (diagnostic mode, no break), so every check is read. API only; skipped on the stub."""
from __future__ import annotations
from langchain_core.messages import SystemMessage, HumanMessage
from ..models import get_reader, parse_json
from ..sources.adapters import reader_calibrated, crm_notes


def known_to_her(prospect_id: str, b1: str) -> str:
    """What the reader, playing her, already knows: this week's context (B1) and what she has been through — the CRM
    notes marked her_experience in the data (n2, n3 for Sunidhi). Not the rest of B2 (a colleague's webinar, a message
    she ignored); flagged notes never arrive — crm_notes() sets them aside before this."""
    lived = [n["text"] for n in crm_notes(prospect_id)["data"]["notes"] if n.get("her_experience")]
    return b1 + ("\nWhat I have been through: " + " ".join(lived) if lived else "")

def verify_line(line: str, known_to_her: str) -> list | None:
    llm = get_reader()
    if llm is None or not line: return None
    cal = reader_calibrated(); out = []
    for c in cal["reader"]:
        msg = llm.invoke([SystemMessage(content=f"You are the prospect reading a subject line in two seconds. {cal['reader_persona']} Reply with JSON only: {{\"pass\": true|false, \"reason\": \"...\"}}."),
                          HumanMessage(content=f"CHECK {c['id']}: {c['q']}\nWHAT I ALREADY KNOW: {known_to_her}\nSUBJECT LINE: {line}")])
        v = parse_json(msg.content); out.append({"id": c["id"], "pass": bool(v.get("pass")), "reason": v.get("reason", "")})
    return out
