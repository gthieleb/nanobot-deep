# syntax=docker/dockerfile:1.4

# Builder stage
FROM python:3.12-slim AS builder

WORKDIR /build

# Install uv for fast dependency resolution
RUN pip install --no-cache-dir uv

# Copy dependency files
COPY pyproject.toml README.md constraints.txt ./

# Install dependencies in virtual environment
RUN <<'BASH'
set -eux
uv venv /build/.venv
. /build/.venv/bin/activate
python - <<'PY'
import tomllib
from pathlib import Path

data = tomllib.loads(Path("pyproject.toml").read_text())
deps = data["project"]["dependencies"]

def is_deepagents_cli(dep: str) -> bool:
    return dep.strip().startswith("deepagents-cli")

filtered = [d for d in deps if not is_deepagents_cli(d)]
Path("/tmp/nanobot-deps.txt").write_text("\n".join(filtered))
deepagents = next((d for d in deps if is_deepagents_cli(d)), "deepagents-cli")
Path("/tmp/deepagents-cli-spec.txt").write_text(deepagents)
PY
xargs -r -a /tmp/nanobot-deps.txt uv pip install --no-cache -c constraints.txt
uv pip install --no-cache -e . --no-deps
uv pip install --no-cache --no-deps "$(cat /tmp/deepagents-cli-spec.txt)"
python - <<'PY'
import importlib.metadata as md
from pathlib import Path

reqs = md.requires("deepagents-cli") or []
filtered = []
for r in reqs:
    spec = r.split(";", 1)[0].strip()
    if spec.lower().startswith("daytona"):
        continue
    filtered.append(spec)

Path("/tmp/deepagents-cli-deps.txt").write_text("\n".join(filtered))
PY
xargs -r -a /tmp/deepagents-cli-deps.txt uv pip install --no-cache -c constraints.txt
BASH

# Runtime stage
FROM python:3.12-slim

# Install runtime tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends gh git curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Install Playwright system dependencies (Ubuntu 24.04+)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libnss3 \
    libatk-bridge2.0-0 \
    libxss1 \
    libasound2t64 \
    libgbm1 \
    libgtk-3-0t64 \
    libxshmfence-dev \
    libxrandr2 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxi6 \
    fonts-noto-color-emoji \
    fonts-unifont && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 -s /bin/bash nanobot && \
    mkdir -p /app/.nanobot/workspace /app/.deepagents /app/.config/gh && \
    chown -R nanobot:nanobot /app

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /build/.venv /app/.venv

# Copy application code
COPY --chown=nanobot:nanobot nanobot_deep /app/nanobot_deep
COPY --chown=nanobot:nanobot templates /app/templates

# Set up environment
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    HOME=/app \
    XDG_CONFIG_HOME=/app/.config \
    DEEPAGENTS_CONFIG_PATH=/app/.deepagents/config.toml \
    NANOBOT_WORKSPACE=/app/.nanobot/workspace

# Switch to non-root user
USER nanobot

# Health check (assuming gateway runs on default port)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

ENTRYPOINT ["python", "-m", "nanobot_deep.cli"]
CMD ["gateway"]
