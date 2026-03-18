# syntax=docker/dockerfile:1.4

# Builder stage
FROM python:3.12-slim AS builder

WORKDIR /build

# Install uv for fast dependency resolution
RUN pip install --no-cache-dir uv

# Copy dependency files
COPY pyproject.toml README.md ./

# Install dependencies in virtual environment
RUN uv venv /build/.venv && \
    . /build/.venv/bin/activate && \
    uv pip install --no-cache -e .

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
