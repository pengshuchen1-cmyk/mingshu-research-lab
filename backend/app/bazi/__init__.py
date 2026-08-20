"""Backend-owned deterministic Bazi calculation and rule package.

This package is a runtime boundary of the FastAPI backend. It must remain
independently deployable and must not import from the legacy Streamlit app.
"""
