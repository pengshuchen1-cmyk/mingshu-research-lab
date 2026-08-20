# syntax=docker/dockerfile:1
# Migrations run in the separate `migrate` Compose service so the web process
# can remain a non-root process.
FROM python:3.11-slim

# Override this build argument on hosts where the default PyPI route is slow.
ARG PIP_INDEX_URL=https://pypi.org/simple

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Keep third-party installation in its own cacheable layer. Update this file
# together with pyproject.toml when production dependencies change.
COPY requirements-prod.txt ./
RUN python -m venv /opt/venv \
    && pip install --index-url "$PIP_INDEX_URL" --upgrade pip \
    && pip install --index-url "$PIP_INDEX_URL" -r requirements-prod.txt

COPY alembic.ini ./
COPY alembic ./alembic
COPY app ./app

RUN addgroup --system app \
    && adduser --system --ingroup app --home /app app \
    && chown -R app:app /app

USER app
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
