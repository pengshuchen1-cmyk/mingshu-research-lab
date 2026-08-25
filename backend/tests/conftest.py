"""Set explicit isolated service URLs before application modules are imported."""

import os

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["REDIS_URL"] = "redis://127.0.0.1:1/15"
os.environ["AI_PROVIDER"] = "local"
os.environ["AI_API_KEY"] = ""
