"""HTTP API for browser frontends.

The backend is intentionally process-local in phase 1. Importing it never opens
the profile database; public deployments therefore remain session-only.
"""

from backend.main import app, create_app

__all__ = ["app", "create_app"]
