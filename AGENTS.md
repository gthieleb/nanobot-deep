# AGENTS.md

Configuration and testing guide for AI agents working on nanobot-deep.

## Environment Variables

### NANOBOT_CONFIG_PATH
Path to the nanobot configuration file. Used by tests to load model and API key.

```bash
export NANOBOT_CONFIG_PATH=~/.nanobot/config.json
pytest tests/e2e/ -m live -v
```

Default: `~/.nanobot/config.json`

### NANOBOT_TEST_MODEL
Override the model for tests. Takes precedence over config file.

```bash
NANOBOT_TEST_MODEL=gpt-5-mini pytest tests/e2e/ -m live -v
```

### NANOBOT_TEST_API_KEY
Override the API key for tests. Takes precedence over config file.

```bash
NANOBOT_TEST_API_KEY=sk-xxx pytest tests/e2e/ -m live -v
```

## Running Tests

### Unit Tests
```bash
pytest tests/ -v
```

### E2E Tests (Live LLM)
```bash
# Recommended: Use existing config
export NANOBOT_CONFIG_PATH=~/.nanobot/config.json
pytest tests/e2e/ -m live -v

# Or override model
NANOBOT_TEST_MODEL=gpt-5-mini pytest tests/e2e/ -m live -v
```

## Model Configuration

The model is configured in `~/.nanobot/config.json`:

```json
{
  "agents": {
    "defaults": {
      "model": "gpt-5-mini",
      "provider": "openai"
    }
  },
  "providers": {
    "openai": {
      "api_key": "sk-xxx"
    }
  }
}
```

## Code Style

- No comments unless explicitly requested
- Follow existing patterns in the codebase
- Run lint/typecheck after changes if available
