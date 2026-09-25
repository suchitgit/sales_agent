# The tests exercise the spine, not the model: force the stub even when .env holds an API key,
# and keep LangSmith tracing off so stub runs are not uploaded as traces.
# Must run before salesagent.config is imported; load_dotenv does not override an existing variable.
# API_TESTS=1 lets a test run on the real models (make guard) — paid calls, opt-in only, traced if configured.
import os
if os.environ.get("API_TESTS") != "1":
    os.environ["STUB_MODEL"] = "1"
    os.environ["LANGSMITH_TRACING"] = "false"
