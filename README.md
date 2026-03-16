# nanobot-deep

LangGraph/DeepAgents integration for nanobot.

## Summary

**nanobot-deep** provides a LangGraph-based agent backend for nanobot, replacing the default LiteLLM-based `AgentLoop` with `DeepAgent`. This enables:

- **State machine agent**: LangGraph's compiled state graph instead of simple while loops
- **Session persistence**: SQLite-based checkpointing for conversation history
- **Skills framework**: Loadable skill modules from `SKILL.md` files
- **Subagent delegation**: Task tool for spawning specialized subagents
- **Reply context**: Enhanced handling of reply-to messages with context extraction

### AgentLoop vs DeepAgent

| Aspect | AgentLoop (nanobot) | DeepAgent (nanobot-deep) |
|--------|--------------------|-----------------------|
| Framework | Custom while loop | LangGraph state graph |
| LLM calls | LiteLLM direct | langchain chat models |
| Sessions | JSON files | SQLite checkpointer |
| Subagents | SubagentManager | Task tool + subagent config |
| Skills | Simple loading | Full skills framework |

## Installation

```bash
pip install nanobot-deep
```

Or with uv:

```bash
uv tool install nanobot-deep
```

## Try It

### Quick Start

```bash
# Initialize nanobot configuration (if not done already)
nanobot-deep onboard

# Create deepagents config
nanobot-deep config

# Start the gateway with DeepAgent backend
nanobot-deep gateway

# Or chat directly with DeepAgent
nanobot-deep agent -m "Hello, who are you?"
```

### Gateway Mode

Start a channel gateway that uses DeepAgent:

```bash
# Start gateway (listens on Telegram, Slack, Discord, etc.)
nanobot-deep gateway

# With options
nanobot-deep gateway --verbose --workspace ~/my-workspace
```

### Direct Chat Mode

Chat directly with DeepAgent from the command line:

```bash
# Single message
nanobot-deep agent -m "What can you do?"

# With session persistence
nanobot-deep agent -m "Remember my name is Alice" -s my-session

# With logs visible
nanobot-deep agent -m "Hello" --logs
```

### Commands

| Command | Description | Agent Backend |
|---------|-------------|---------------|
| `gateway` | Start channel gateway | DeepAgent ✅ |
| `agent` | Direct CLI chat | DeepAgent ✅ |
| `config` | Manage deepagents.json | N/A |
| `deep` | Check DeepAgent availability | N/A |
| `status` | Show nanobot status | nanobot |
| `onboard` | Initialize configuration | nanobot |
| `channels` | Manage channels | nanobot |
| `provider` | Manage providers | nanobot |

## Usage

```bash
# Check DeepAgent availability
nanobot-deep deep

# Create/view deepagents.json config
nanobot-deep config

# Start gateway with DeepAgent backend
nanobot-deep gateway

# Chat directly with DeepAgent
nanobot-deep agent -m "Your message here"
```

## What's Included

This package provides **glue code** that integrates:

- **nanobot-ai**: Multi-channel AI assistant framework
- **deepagents**: LangGraph-based agent framework
- **LangGraph**: State management and checkpointing

### Key Components

| Module | Purpose |
|--------|---------|
| `DeepAgent` | Wrapper around `deepagents.create_deep_agent()` |
| `LangGraphBridge` | Translates messages between nanobot and LangGraph |
| `get_session_history()` | Utility to extract session messages from checkpointer |
| `DeepAgentsConfig` | Configuration schema for deepagents.json |

## Configuration

Create `~/.nanobot/deepagents.json`:

```json
{
  "recursion_limit": 500,
  "skills": ["~/.nanobot/workspace/skills"],
  "subagents": [
    {
      "name": "reply-handler",
      "description": "Handles replies to messages"
    }
  ],
  "interrupt_on": {
    "edit_file": false,
    "execute": false
  }
}
```

## Limitations

### SQLite Checkpointer Concurrency

The default `SqliteSaver` checkpointer is suitable for single-process deployments. SQLite uses database-level locking, which means:

- ✅ **Same process**: Multiple async tasks/threads share one connection - works fine
- ❌ **Multiple processes**: Concurrent writes will cause "database is locked" errors

For multi-gateway or multi-process deployments, consider:

| Backend | Package | Concurrency | Latency | Best For |
|---------|---------|-------------|---------|----------|
| SQLite | built-in | ❌ Single writer | Low | Dev, single-instance |
| Redis | `langgraph-checkpoint-redis` | ✅ Multi-writer | Very low | Multi-process, fast |
| Postgres | `langgraph-checkpoint-postgres` | ✅ Multi-writer | Medium | Production, ACID |
| MongoDB | `langgraph-checkpoint-mongodb` | ✅ Multi-writer | Medium | Production, flexible |

See [Issue #5](https://github.com/gthieleb/nanobot-deep/issues/5) for migration script from legacy JSONL sessions.

## Dependencies

- `nanobot-ai>=0.1.4.post4,<0.2.0` (from PyPI)
- `deepagents>=0.4.0`
- `langgraph>=0.2.0`
- `langchain-core>=0.3.0`
- `langchain-mcp-adapters>=0.1.0`
- `aiosqlite>=0.20.0`

## Testing

### Unit Tests

```bash
pytest tests/ -v
```

### E2E Tests (Live LLM Calls)

E2E tests require a nanobot config with API keys:

```bash
NANOBOT_TEST_CONFIG=~/.nanobot/config.json pytest tests/e2e/ -m live -v
```

**Note:** E2E tests use a minimal config (`tests/e2e/deepagents.test.json`) to reduce token usage:

- `max_tokens: 500` (vs 20000 in production)
- Most middleware disabled (todolist, summarization, skills, memory, subagents)
- Only filesystem middleware enabled for file operation tests

To use your own deepagents config for tests:

```bash
NANOBOT_TEST_DEEPAGENTS_CONFIG=~/.nanobot/deepagents.json pytest tests/e2e/ -m live -v
```

For faster/cheaper testing, use a smaller model in your nanobot config:

```bash
# Create test config with GPT-4o-mini
cat ~/.nanobot/config.json | sed 's/anthropic\/claude-sonnet-4-5/openai\/gpt-4o-mini/g' > /tmp/test_config.json
NANOBOT_TEST_CONFIG=/tmp/test_config.json pytest tests/e2e/ -m live -v
```

## License

MIT
