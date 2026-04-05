# syntax=docker/dockerfile:1.4

# Builder stage
FROM python:3.12-slim AS builder

WORKDIR /build

# Install uv for fast dependency resolution
RUN pip install --no-cache-dir uv

# Copy dependency files
COPY pyproject.toml README.md constraints.txt ./

# Install dependencies in virtual environment
RUN uv venv /build/.venv && \
    . /build/.venv/bin/activate && \
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
    && xargs -r -a /tmp/nanobot-deps.txt uv pip install --no-cache -c constraints.txt \
    && uv pip install --no-cache -e . --no-deps \
    && uv pip install --no-cache --no-deps "$(cat /tmp/deepagents-cli-spec.txt)" \
    && python - <<'PY'
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
    && xargs -r -a /tmp/deepagents-cli-deps.txt uv pip install --no-cache -c constraints.txt

# Runtime stage
FROM python:3.12-slim

# Create non-root user
RUN useradd -m -u 1000 -s /bin/bash nanobot && \
    mkdir -p /home/nanobot/.nanobot/workspace && \
    chown -R nanobot:nanobot /home/nanobot

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /build/.venv /app/.venv

# Copy application code
COPY --chown=nanobot:nanobot nanobot_deep /app/nanobot_deep
COPY --chown=nanobot:nanobot templates /app/templates

# Set up environment
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    NANOBOT_WORKSPACE=/home/nanobot/.nanobot/workspace

# Switch to non-root user
USER nanobot

# Health check (assuming gateway runs on default port)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Default command (can be overridden)
CMD ["python", "-m", "nanobot_deep.gateway"]
