"""LangSmith tracing. LangGraph traces every node and model call automatically once these env
vars are set — nothing in the spine changes. Call `enable()` early, or just set the vars in .env."""
import os
from .. import config  # loads .env


def enable(project: str | None = None) -> bool:
    if not os.getenv("LANGSMITH_API_KEY"):
        return False
    os.environ.setdefault("LANGSMITH_TRACING", "true")
    os.environ.setdefault("LANGSMITH_PROJECT", project or os.getenv("LANGSMITH_PROJECT", "sales-agent"))
    return True


def status() -> str:
    if not os.getenv("LANGSMITH_API_KEY"): return "off — no LANGSMITH_API_KEY"
    return f"on — project {os.getenv('LANGSMITH_PROJECT', 'sales-agent')}"
