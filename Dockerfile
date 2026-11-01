# ── Stage 1: dependency builder ───────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

# Install uv (fast Python package manager)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency manifests first for layer caching
COPY pyproject.toml uv.lock* README.md ./

# Install dependencies into an isolated prefix (no editable installs)
RUN uv sync --frozen --no-dev --no-install-project

# Copy source and install the project package
COPY src/ ./src/
RUN uv sync --frozen --no-dev --no-editable

# ── Stage 2: runtime image ────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

# Security: run as a non-root user
RUN groupadd --gid 1001 plainspeak \
 && useradd --uid 1001 --gid plainspeak --shell /bin/sh --no-create-home plainspeak

WORKDIR /app

# Copy only the installed environment from the builder
COPY --from=builder --chown=plainspeak:plainspeak /build/.venv /app/.venv
COPY --from=builder --chown=plainspeak:plainspeak /build/src /app/src

# Data volume mount point — cases and uploads are stored here
RUN mkdir -p /data/cases /data/uploads \
 && chown -R plainspeak:plainspeak /data

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PLAINSPEAK_DATA_DIR=/data \
    APP_ENV=production \
    HOST=0.0.0.0 \
    PORT=8080

EXPOSE 8080

USER plainspeak

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/api/health')"

CMD ["python", "-m", "plainspeak.main"]
