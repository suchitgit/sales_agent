from __future__ import annotations
from langgraph.graph import StateGraph, START, END
from .state import RunState
from . import nodes

def build(checkpointer=None, store=None):
    g = StateGraph(RunState)
    for n in ("fetch", "assemble", "write", "verify", "approve", "send"):
        g.add_node(n, getattr(nodes, n))
    g.add_edge(START, "fetch"); g.add_edge("fetch", "assemble"); g.add_edge("assemble", "write")
    g.add_edge("write", "verify"); g.add_edge("verify", "approve"); g.add_edge("approve", "send"); g.add_edge("send", END)
    return g.compile(checkpointer=checkpointer, store=store)
