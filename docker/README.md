# Langfuse Self-Hosted Docker Compose

This directory contains Docker Compose configuration for running Langfuse locally for observability and tracing.

## Quick Start

```bash
# Start Langfuse stack
docker compose -f docker-compose.langfuse.yml up -d

# Wait for services to be ready (about 2-3 minutes)
# Check logs with:
docker compose -f docker-compose.langfuse.yml logs -f langfuse-web
```

Access the Langfuse UI at: **http://localhost:3000**

## First-Time Setup

1. Open http://localhost:3000
2. Create an account and organization
3. Create a project
4. Get your API keys from Project Settings

## Configuration for nanobot-deep

Add to your `~/.nanobot/deepagents.json`:

```json
{
  "langfuse": {
    "enabled": true,
    "public_key": "pk-lf-...",
    "secret_key": "sk-lf-...",
    "host": "http://localhost:3000"
  }
}
```

Or use environment variables:

```bash
export LANGFUSE_PUBLIC_KEY="pk-lf-..."
export LANGFUSE_SECRET_KEY="sk-lf-..."
export LANGFUSE_HOST="http://localhost:3000"
```

## Services

| Service | Port | Description |
|---------|------|-------------|
| langfuse-web | 3000 | Main web UI |
| langfuse-worker | 3030 | Background worker |
| postgres | 5432 | Database |
| redis | 6379 | Queue/cache |
| clickhouse | 8123/9000 | Analytics DB |
| minio | 9090/9091 | Object storage |

## Security Notes

**IMPORTANT**: Before production use, update all secrets in `docker-compose.langfuse.yml`:

```bash
# Generate secure secrets
openssl rand -hex 32  # For ENCRYPTION_KEY
openssl rand -hex 16  # For passwords

# Update these environment variables:
# - DATABASE_URL (postgres password)
# - SALT
# - ENCRYPTION_KEY
# - NEXTAUTH_SECRET
# - CLICKHOUSE_PASSWORD
# - REDIS_AUTH
# - MINIO_ROOT_PASSWORD
# - POSTGRES_PASSWORD
```

## Stopping

```bash
docker compose -f docker-compose.langfuse.yml down

# To also remove volumes (clears all data):
docker compose -f docker-compose.langfuse.yml down -v
```

## Troubleshooting

### Services not ready
Wait 2-3 minutes for all services to initialize. Check health:
```bash
docker compose -f docker-compose.langfuse.yml ps
```

### Port conflicts
If ports are in use, edit the port mappings in `docker-compose.langfuse.yml`.

### Data persistence
Data is stored in Docker volumes. To reset everything:
```bash
docker compose -f docker-compose.langfuse.yml down -v
```

## References

- [Langfuse Docker Compose Docs](https://langfuse.com/self-hosting/deployment/docker-compose)
- [Langfuse Configuration](https://langfuse.com/self-hosting/configuration)
- [LangChain DeepAgents Integration](https://langfuse.com/integrations/frameworks/langchain-deepagents)
