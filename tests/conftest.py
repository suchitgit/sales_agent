# The tests exercise the spine, not the model: force the stub even when .env holds an API key.
# Must run before salesagent.config is imported; load_dotenv does not override an existing variable.
# API_TESTS=1 lets a test run on the real models (make guard) — paid calls, opt-in only.
import os
if os.environ.get("API_TESTS") != "1":
    os.environ["STUB_MODEL"] = "1"
