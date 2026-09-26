# The tests exercise the pipeline, not the model: force the replay stub even when .env holds an API key,
# keep LangSmith tracing off and its key out, so a test run makes no network calls and uploads nothing.
# Must run before salesagent.config is imported; load_dotenv does not override an existing variable.
import os
os.environ["STUB_MODEL"] = "1"
os.environ["LANGSMITH_TRACING"] = "false"
os.environ["LANGSMITH_API_KEY"] = ""

import pytest


@pytest.fixture(autouse=True)
def _runs_to_tmp(tmp_path, monkeypatch):
    """Runs made by the tests are saved to a temporary folder, never into data/runs with the real series."""
    from salesagent import config
    monkeypatch.setattr(config, "RUNS", tmp_path / "runs")
