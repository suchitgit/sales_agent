# The tests exercise the spine, not the model: force the stub even when .env holds an API key.
# Must run before salesagent.config is imported; load_dotenv does not override an existing variable.
import os
os.environ["STUB_MODEL"] = "1"
