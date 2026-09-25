import sys; sys.path.insert(0, "src")
from salesagent import config
from salesagent.stores.memory import load_cases, past_decisions

def test_cases_from_seed_file_without_postgres(monkeypatch):
    monkeypatch.setattr(config, "POSTGRES_URI", "")
    cases, source = load_cases()
    assert source == "seed file" and [c["id"] for c in cases] == ["D1", "D2", "D3", "D4"]

def test_unreachable_postgres_falls_back_to_seed_file(monkeypatch):
    monkeypatch.setattr(config, "POSTGRES_URI", "postgresql://nobody:x@127.0.0.1:1/none")
    cases, source = load_cases()
    assert len(cases) == 4 and source.startswith("seed file (postgres unreachable")

def test_past_decisions_filters_by_pain(monkeypatch):
    monkeypatch.setattr(config, "POSTGRES_URI", "")
    assert [c["id"] for c in past_decisions(["payroll consolidation"])] == ["D3"]
