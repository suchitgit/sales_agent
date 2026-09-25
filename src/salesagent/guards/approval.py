"""The send is irreversible. The rep clears it. interrupt() needs a checkpointer; on resume the node
re-runs from the top, so nothing before the interrupt may have side effects."""
from langgraph.types import interrupt

def request_approval(payload: dict) -> dict:
    decision = interrupt(payload)
    return decision if isinstance(decision, dict) else {"approved": bool(decision)}
