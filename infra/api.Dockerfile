# Build context: repository root.
FROM python:3.12-slim AS base

COPY --from=ghcr.io/astral-sh/uv:0.8 /uv /bin/uv

ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app
COPY pyproject.toml uv.lock ./

# Tooling image used by `make lint` and `make test` (repository mounted at /app).
FROM base AS dev
RUN uv sync --locked
COPY . .
CMD ["pytest"]

# Image that serves the API.
FROM base AS runtime
RUN uv sync --locked --no-dev
COPY api/ api/
COPY engine/ engine/
COPY llm/ llm/
COPY rag/ rag/
RUN useradd --create-home app
USER app
EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
