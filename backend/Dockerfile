# syntax=docker/dockerfile:1.7
# API de Hotel Kawari. Contexto de construcción: RAÍZ del repositorio (necesita pyproject.toml y uv.lock).
#   docker build -f backend/Dockerfile -t kawari-api .

# --- Etapa 1: dependencias con uv (lockfile congelado, sin grupo dev) ---
FROM ghcr.io/astral-sh/uv:0.13.7 AS uv
FROM python:3.12-slim AS builder
COPY --from=uv /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/opt/venv
WORKDIR /src
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# --- Etapa 2: imagen final mínima, usuario sin privilegios ---
FROM python:3.12-slim AS runtime
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_ENV=production \
    UPLOAD_DIR=/data/uploads \
    PRIVATE_UPLOAD_DIR=/data/private
RUN groupadd --system app && useradd --system --gid app --no-create-home app \
    && mkdir -p /data/uploads /data/private \
    && chown -R app:app /data
WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY backend/__init__.py backend/__init__.py
COPY backend/app backend/app
COPY backend/scripts backend/scripts

USER app
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"]

# Un solo proceso por contenedor: el scheduler de expiración corre dentro de la API (ver CLAUDE.md 8.1),
# así que para escalar se agregan réplicas con SCHEDULER_ENABLED=false, no --workers.
# El access log lo emite RequestContextMiddleware (con request-id y duración).
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--no-access-log"]
