"""Environment checks for the T-series runtime. Each does real work."""
import os, sys, json
from pathlib import Path
sys.path.insert(0, "src")
try:
    from dotenv import load_dotenv; load_dotenv(Path(__file__).resolve().parents[1] / ".env")
except Exception: pass
R = []
def check(name):
    def w(fn):
        try: d = fn() or ""; R.append((name, "SKIP" if str(d).startswith("skipped") else "PASS", d))
        except Exception as e: R.append((name, "FAIL", f"{type(e).__name__}: {str(e).splitlines()[0][:110]}"))
        return fn
    return w
HAS_KEY = bool(os.getenv("ANTHROPIC_API_KEY"))

@check("Source systems · 8 files present")
def _():
    from salesagent import config
    n = len(list(config.SOURCES.rglob("*.json"))); assert n >= 8, n; return f"{n} source files"
@check("Golden prompt · blocks rebuilt = experiment")
def _():
    from salesagent.blocks import fetch_all, build, golden
    g = golden(build(fetch_all("sunidhi"))); assert all(g.values()), g; return "B0 B1 B2 B3 B4 B5 B7 all match"
@check("LangGraph · spine compiles")
def _():
    from salesagent.graph.spine import build; return type(build()).__name__
@check("T-series on the replay stub · verdicts reproduce")
def _():
    os.environ["STUB_MODEL"] = "1"
    import importlib; from salesagent import config; importlib.reload(config)
    from salesagent.evals import runner; importlib.reload(runner)
    res = runner.run_conditions("sunidhi", k=1); bad = [r["condition"] for r in res["rows"] if r["reproduces_experiment_passk"] != 1]
    assert not bad, bad; return f"{len(res['rows'])} conditions reproduce"
@check("T7 · procedure verified · null prospect declines")
def _():
    from salesagent.evals.runner import run_one
    r = run_one("sunidhi", "T7"); n = run_one("nikhil", "T7")
    assert r["verification"]["adherence"] and n.get("declined"); return "adherence ✓ · nikhil declined"
@check("Writer · Fable 5.1 via API · one real T7 run")
def _():
    if not HAS_KEY: return "skipped (no ANTHROPIC_API_KEY)"
    os.environ.pop("STUB_MODEL", None)
    import importlib; from salesagent import config; importlib.reload(config)
    from salesagent import models; importlib.reload(models)
    from salesagent.graph import nodes; importlib.reload(nodes)
    from salesagent.graph import spine; importlib.reload(spine)
    from salesagent.evals import runner; importlib.reload(runner)
    r = runner.run_one("sunidhi", "T7")
    return f"{config.MODEL_WRITER} → “{(r['checks']['line'] or 'no survivor')[:60]}” · procedure {r['verification'].get('adherence') if r.get('verification') else 'n/a'}"
@check("LangSmith · key and connection")
def _():
    if not os.getenv("LANGSMITH_API_KEY"): return "skipped (no LANGSMITH_API_KEY)"
    from langsmith import Client; next(iter(Client().list_projects(limit=1)), None); return f"project {os.getenv('LANGSMITH_PROJECT')}"
@check("DeepEval · import")
def _():
    import deepeval; return f"v{deepeval.__version__}"

try:
    from rich.console import Console; from rich.table import Table
    t = Table(title="Sales agent kit v2 · T-series runtime"); [t.add_column(c) for c in ("Check", "Status", "Detail")]
    for n, s, d in R: t.add_row(n, {"PASS": "[green]PASS[/]", "SKIP": "[yellow]SKIP[/]"}.get(s, f"[red]{s}[/]"), str(d))
    Console().print(t)
except Exception:
    for n, s, d in R: print(f"{s:5} {n:52} {d}")
p = sum(s == "PASS" for _, s, _ in R); k = sum(s == "SKIP" for _, s, _ in R); print(f"\n{p}/{len(R)-k} passing" + (f" · {k} skipped" if k else ""))
