FROM ghcr.io/astral-sh/uv:0.9.17-python3.13-bookworm-slim AS builder

ARG MCS_NAME=auth

WORKDIR /app

ENV UV_SYSTEM_PYTHON=0

COPY commons /commons

RUN --mount=type=bind,source=${MCS_NAME}/pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=${MCS_NAME}/uv.lock,target=uv.lock \
    uv sync --frozen --no-dev --no-install-project

COPY ${MCS_NAME} .

RUN --mount=type=bind,source=${MCS_NAME}/pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=${MCS_NAME}/uv.lock,target=uv.lock \
    uv sync --frozen --no-dev

RUN rm -f /app/.venv/bin/python*

FROM python:3.13-slim-bookworm

ARG MCS_NAME

RUN groupadd -r appuser && useradd -r -g appuser appuser

ENV PYTHONPATH=/app
ENV MCS_NAME=${MCS_NAME}

WORKDIR /app

COPY --from=builder --chown=appuser:appuser /app/.venv/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder --chown=appuser:appuser /app/.venv/include/site/python3.13/ /usr/local/include/python3.13/
COPY --from=builder --chown=appuser:appuser /app/.venv/bin /usr/local/bin
COPY --from=builder --chown=appuser:appuser /app /app
COPY --from=builder --chown=appuser:appuser /commons /commons

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health', timeout=5)" || exit 1

CMD sh -c "python -m uvicorn --host 0.0.0.0 --port 8000 --workers 1 --factory ${MCS_NAME}.api:create_app"
