"""LangSmith experiment: a dataset of the seed prospects, the spine as the target, our checks as
evaluators, each prospect run k times. Two experiment-level columns, from one guard pass:
  known_winner_clears — the guard: every known-good line (data/seed/known_winners.json, written by a person),
                        scored by the active reader, must clear all six checks k times out of k (= `make guard`)
  verdict_consistency — on the API: the same known line, the same reader, the same verdict k of k
  path_consistency    — on the stub instead: one step path per prospect across its k runs
Usage: python scripts/eval_langsmith.py [experiment-prefix] [--k 3]"""
import sys, uuid
sys.path.insert(0, "src")
from salesagent.evals import tracing
assert tracing.enable(), "LANGSMITH_API_KEY missing in .env"
from langsmith import Client
from salesagent import config
from salesagent.evals.suite import run_once, guard, KNOWN_WINNER
from salesagent.stores.context import load_prospects
from salesagent.evals.checks import CHECKS

args = sys.argv[1:]
k = int(args[args.index("--k") + 1]) if "--k" in args else 3
prefix = next((a for a in args if not a.startswith("--") and not a.isdigit()), f"reader-{config.MODEL_SMALL}")
prospects = load_prospects()
READER = "stub" if config.USE_STUB else config.MODEL_SMALL


def target(inputs: dict) -> dict:
    run = run_once(inputs["prospect_id"], f"ls-{inputs['prospect_id']}-{uuid.uuid4().hex[:8]}")
    return {"winner": run["winner"]["text"] if run.get("winner") else None, "declined": run.get("declined", False),
            "died": [(c["id"], c.get("died_at")) for c in run.get("candidates", [])],
            "steps": [s["step"] for s in run.get("trace", [])],
            "run": {key: run.get(key) for key in ("winner", "candidates", "trace", "declined", "prompt")}}


def make_evaluator(name, fn):
    def ev(inputs, outputs, reference_outputs):
        return {"key": name, "score": 1.0 if fn(prospects[inputs["prospect_id"]], outputs["run"]) else 0.0}
    ev.__name__ = name
    return ev


_guards = {}


def _guard_all() -> dict:
    """One guard pass per experiment, shared by both columns — the known lines are not scored twice."""
    if not _guards:
        _guards.update({pid: guard(pid, k) for pid in KNOWN_WINNER})
    return _guards


def known_winner_clears(inputs, outputs):
    """The guard: if the reader rejects a known-correct line, the checks are wrong, not the line."""
    g = _guard_all()
    notes = [f"{pid} {sum(v == 'clears' for v in r['verdicts'])}/{k}" + "".join(f" · {x['died_at']}: {x['reason']}" for x in r["runs"] if x["died_at"])
             for pid, r in g.items()]
    return {"key": "known_winner_clears", "score": 1.0 if all(r["clears"] for r in g.values()) else 0.0,
            "comment": f"reader {READER} · " + " | ".join(notes)}


def consistency(inputs, outputs):
    """Stub: one step path per prospect over k runs. API: different candidates legitimately take different paths,
    so consistency is the verdict on each known line — same line, same reader, same verdict, k of k."""
    if config.USE_STUB:
        paths = {}
        for i, o in zip(inputs, outputs):
            paths.setdefault(i["prospect_id"], set()).add("|".join(o.get("steps", [])))
        split = [pid for pid, ps in paths.items() if len(ps) > 1]
        return {"key": "path_consistency", "score": 0.0 if split else 1.0,
                "comment": ("paths differ for " + ", ".join(split)) if split else f"one path per prospect over {k} runs"}
    g = _guard_all()
    return {"key": "verdict_consistency", "score": 1.0 if all(r["consistent"] for r in g.values()) else 0.0,
            "comment": " | ".join(f"{pid}: {', '.join(r['verdicts'])}" for pid, r in g.items())}


if __name__ == "__main__":
    client = Client()
    DATASET = "sales-agent-seed-prospects"
    if not client.has_dataset(dataset_name=DATASET):
        ds = client.create_dataset(dataset_name=DATASET, description="Seed prospects incl. the null case; the known winning line for Sunidhi")
        client.create_examples(dataset_id=ds.id,
            inputs=[{"prospect_id": pid} for pid in prospects],
            outputs=[{"expect": p["expect"], "known_winner": KNOWN_WINNER.get(pid)} for pid, p in prospects.items()])
    print(f"tracing: {tracing.status()} · writer {config.MODEL_MEDIUM} · reader {READER} · k={k}")
    res = client.evaluate(target, data=DATASET, evaluators=[make_evaluator(n, f) for n, f in CHECKS.items()],
                          summary_evaluators=[known_winner_clears, consistency], num_repetitions=k,
                          experiment_prefix=prefix, metadata={"writer": config.MODEL_MEDIUM, "reader": READER, "k": k, "stub": config.USE_STUB})
    print("experiment:", getattr(res, "experiment_name", prefix))
