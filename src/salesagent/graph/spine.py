"""One StateGraph. Same request, same stores -> same path, same rejections, same winner."""
from __future__ import annotations
from langgraph.graph import StateGraph, START, END
from .state import SalesState
from . import nodes


def build(checkpointer=None, store=None):
    g = StateGraph(SalesState)
    g.add_node("plan", nodes.plan)
    g.add_node("fetch", nodes.fetch)
    g.add_node("assemble", nodes.assemble)
    g.add_node("generate", nodes.generate)
    g.add_node("score", nodes.score)
    g.add_node("approve", nodes.approve)
    g.add_node("send", nodes.send)
    g.add_edge(START, "plan"); g.add_edge("plan", "fetch"); g.add_edge("fetch", "assemble")
    g.add_edge("assemble", "generate"); g.add_edge("generate", "score"); g.add_edge("score", "approve")
    g.add_edge("approve", "send"); g.add_edge("send", END)
    return g.compile(checkpointer=checkpointer, store=store)
