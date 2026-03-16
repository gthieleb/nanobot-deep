# AGENTS.md

Guidelines for AI agents working on this codebase.

## Project Structure

```
nanobot-deep/
├── nanobot_deep/
│   ├── agent/          # DeepAgent implementation
│   ├── config/         # Configuration schema and loader
│   ├── langgraph/      # LangGraph bridge and utilities
│   └── gateway.py      # Main gateway for message processing
├── tests/
│   ├── e2e/            # End-to-end tests with live LLM calls
│   │   ├── conftest.py           # Test fixtures
│   │   ├── deepagents.test.json  # Minimal config for tests
│   │   └── test_deepagent_live.py
│   └── test_*.py       # Unit tests
└── templates/          # Config templates
```

## Running Tests

### Unit Tests

```bash
pytest tests/ -v
```

### E2E Tests

E2E tests require real API keys and use minimal configuration to reduce costs:

```bash
NANOBOT_TEST_CONFIG=~/.nanobot/config.json pytest tests/e2e/ -m live -v
```

**Test Config:** Uses `tests/e2e/deepagents.test.json` with:
- `max_tokens: 500` (reduced from 20000)
- Most middleware disabled
- Only filesystem enabled

**Custom Config:** Override with `NANOBOT_TEST_DEEPAGENTS_CONFIG`

**Cheaper Testing:** Use GPT-4o-mini or similar:

```bash
cat ~/.nanobot/config.json | sed 's/anthropic\/claude-sonnet-4-5/openai\/gpt-4o-mini/g' > /tmp/test_config.json
NANOBOT_TEST_CONFIG=/tmp/test_config.json pytest tests/e2e/ -m live -v
```

## Code Style

- No comments unless requested
- Follow existing patterns in the codebase
- Use type hints for function signatures
- Keep functions focused and concise

## Key Commands

| Command | Purpose |
|---------|---------|
| `pytest tests/ -v` | Run all unit tests |
| `pytest tests/e2e/ -m live -v` | Run E2E tests |
| `python -m nanobot_deep.cli` | Run CLI |
| `ruff check .` | Lint code |

## Configuration

- `~/.nanobot/config.json` - Main nanobot config (model, API keys)
- `~/.nanobot/deepagents.json` - DeepAgents config (middleware, limits)
- `tests/e2e/deepagents.test.json` - Minimal config for E2E tests

## Recent Changes

- Removed `SessionCheckpointer` class (Issue #4 fix)
- Now using `AsyncSqliteSaver` directly
- `get_session_history()` is now a utility function
- E2E tests use minimal config to reduce token usage
