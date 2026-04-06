# nanobot-deep

LangGraph/DeepAgents integration for nanobot.

## Docker Compose

Use the bundled `docker-compose.yml` to run the gateway:

```bash
# Start or recreate (if config changed)
docker compose up -d

# Recreate container (after config changes)
docker compose recreate

# View logs
docker compose logs -f nanobot-deep
```

The compose file uses `ghcr.io/gthieleb/nanobot-deep:latest`. Pin a specific
version by editing the image tag.

**Config file permissions**: If using Docker, ensure config files in `~/.nanobot/`
are readable by the container. Add the container user to your group or set
files to world-readable:

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

# After onboard: configure model/provider in ~/.deepagents/config.toml (required)
# Configure Langfuse/DeepAgent runtime in ~/.nanobot/deepagents.json (optional)

# Optional: create deepagents.json for advanced DeepAgent settings
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
| `config` | Create/view optional deepagents.json | N/A |
| `deep` | Check DeepAgent availability | N/A |
| `status` | Show nanobot status | nanobot |
| `onboard` | Initialize configuration | nanobot |
| `channels` | Manage channels | nanobot |
| `provider` | Manage providers | nanobot |

## Usage

```bash
# Check DeepAgent availability
nanobot-deep deep

# Create/view optional deepagents.json config
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
| `SessionCheckpointer` | SQLite-based session persistence |
| `DeepAgentsConfig` | Configuration schema for optional deepagents.json |

## Configuration Overview

nanobot-deep reads configuration from two required files and one optional file.
Model/provider settings live in deepagents-cli config; channels and workspace
settings live in nanobot config; DeepAgent runtime tuning is optional.

| File | Required | Purpose |
|------|----------|---------|
| `~/.nanobot/config.json` | Yes | Channels, workspace, agent defaults, tool exec settings (created by `nanobot onboard`, does NOT include model/provider - see below) |
| `~/.deepagents/config.toml` | Yes | Model/provider config for deepagents-cli (configure manually after onboard) |
| `~/.nanobot/deepagents.json` | Optional | DeepAgent runtime tuning (middleware, summarization, task routing, subagents, checkpointer, backend, Langfuse) |

### MCP Tools (DeepAgents CLI)

nanobot-deep uses DeepAgents CLI MCP discovery via `.mcp.json` files. The nanobot
config `tools.mcp_servers` is ignored in nanobot-deep.

Discovery order (lowest to highest priority):

1. `~/.deepagents/.mcp.json`
2. `<project>/.deepagents/.mcp.json`
3. `<project>/.mcp.json`

DeepAgents merges these configs by `mcpServers` name. For project-level stdio
servers, the CLI enforces trust (fingerprinted in `~/.deepagents/config.toml`).
If you run non-interactive, prefer user-level config or pre-trust the project.

CLI overrides:

- `--mcp-config PATH` to load an explicit MCP config (highest precedence)
- `--no-mcp` to disable MCP loading entirely

Docs: https://docs.langchain.com/oss/python/deepagents/cli/mcp-tools

### Required: nanobot config (channels + defaults)

Minimal example (add your channels and API keys as needed):

```json
{
  "agents": {
    "defaults": {
      "model": "anthropic/claude-opus-4-5",
      "max_tokens": 8192,
      "temperature": 0.7
    }
  },
  "providers": {
    "anthropic": {
      "api_key": "sk-..."
    }
  },
  "channels": {
    "telegram": {
      "enabled": true,
      "token": "123:abc"
    }
  }
}
```

Note: DeepAgent model/provider selection does not come from this file. It comes
from `~/.deepagents/config.toml`. The `agents.defaults.model` value is still
used by non-deep nanobot commands.

### Required: deepagents-cli config (model/provider)

Minimal example:

```toml
[models.defaults]
model = "litellm:anthropic/claude-opus-4-5"

[models.providers.litellm.params]
api_key = "sk-..."
```

### Optional: deepagents.json (DeepAgent runtime tuning)

Only needed if you want to tune DeepAgent runtime behavior. If the file is
absent, nanobot-deep uses defaults. This file is not read by deepagents-cli.

Settings you can tune here include:
- backend type (`filesystem` or `local_shell`) and execution settings
- middleware toggles (summarization, memory, prompt caching, skills, subagents)
- summarization settings
- task routing and delegate threshold
- subagent definitions
- interrupt_on behavior
- checkpointer type/path

Example:

```json
{
  "recursion_limit": 500,
  "backend": {
    "type": "filesystem",
    "exec_timeout": 60,
    "path_append": ""
  },
  "checkpointer": {
    "type": "sqlite",
    "path": "~/.nanobot/sessions.db"
  },
  "middleware": {
    "enable_summarization": true,
    "enable_memory": true
  },
  "summarization": {
    "enabled": true,
    "keep_messages": 20
  },
  "task_routing": {
    "delegate_threshold_tokens": 1000
  },
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

For shell execution with `local_shell` backend:

```json
{
  "backend": {
    "type": "local_shell",
    "exec_timeout": 120,
    "path_append": "/usr/local/bin",
    "restrict_to_workspace": true
  },
  "interrupt_on": {
    "execute": true
  }
}
```

### Human-in-the-Loop (HITL) Interrupts

nanobot-deep supports Human-in-the-Loop (HITL) interrupts via the `interrupt_on` configuration. When enabled, the agent pauses before executing certain tools and waits for user approval via Telegram inline buttons.

#### Configuration

Add to `~/.nanobot/deepagents.json`:

```json
{
  "interrupt_on": {
    "edit_file": false,
    "write_file": false,
    "execute": false,
    "all_tools": false,
    "auto_reject_timeout": 60.0
  }
}
```

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `edit_file` | bool | false | Pause before editing files |
| `write_file` | bool | false | Pause before writing files |
| `execute` | bool/null | null | Pause before shell execution (auto-enabled for `local_shell` backend) |
| `all_tools` | bool | false | Pause before ALL tool calls |
| `auto_reject_timeout` | float | 60.0 | Seconds to wait before auto-rejecting |

#### How It Works

1. Agent attempts to execute a protected tool (e.g., `execute rm -rf`)
2. Execution pauses, interrupt is stored
3. Telegram message sent with inline buttons:
   - **Approve**: Allow the action
   - **Edit**: Modify the action (not yet implemented)
   - **Reject**: Block the action
4. User clicks a button
5. Decision fed back to agent, execution resumes or action is rejected

#### Example Telegram Message

```
⚠️ Action requires approval

Tool: execute

Command:
rm -rf /important/files

Auto-reject after 60s

[✅ Approve] [❌ Reject]
```

#### Shell Execution Security

When using `local_shell` backend, `execute` is automatically protected:

```json
{
  "backend": {
    "type": "local_shell",
    "exec_timeout": 120
  },
  "interrupt_on": {
    "execute": true
  }
}
```

### LiteLLM Notes (including z.ai)

These notes apply to `~/.deepagents/config.toml` model/provider settings.

When using DeepAgents with the `litellm` provider in `~/.deepagents/config.toml`:

- Use `zai/` model names for z.ai (for example `litellm:zai/glm-4.5`).
- A provider-level `api_key` under `[models.providers.litellm.params]` can be used as a global default key.
- You are not limited to one key overall. For multi-provider setups, use provider-specific env vars (for example `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `ZAI_API_KEY`) and/or per-model `params` overrides.
- A LiteLLM proxy is optional. Use it for centralized routing/policies/logging, not because multiple keys are otherwise impossible.

## Langfuse Observability

nanobot-deep supports Langfuse for observability and tracing of agent execution.
Langfuse is **only for tracing/observability** — it does NOT provide model or
provider settings. Model/provider config comes from `~/.deepagents/config.toml`.

You can configure Langfuse via environment variables or the optional
`~/.nanobot/deepagents.json` file. Note: `nanobot onboard` does not support
Langfuse or provider/LLM configuration — edit `~/.nanobot/deepagents.json`
and `~/.deepagents/config.toml` manually after running onboard.

### Configuration

Add to the optional `~/.nanobot/deepagents.json`:

```json
{
  "langfuse": {
    "enabled": true,
    "public_key": "pk-lf-...",
    "secret_key": "sk-lf-...",
    "host": "http://localhost:3000",
    "environment": "development"
  }
}
```

### Environment Variables

Environment variables take precedence over config file:

```bash
export LANGFUSE_PUBLIC_KEY="pk-lf-..."
export LANGFUSE_SECRET_KEY="sk-lf-..."
export LANGFUSE_HOST="http://localhost:3000"
```

### Self-Hosted Langfuse

Use the docker-compose setup from [litellm-setup](https://github.com/gthieleb/litellm-setup):

```bash
# Clone and start Langfuse stack
git clone https://github.com/gthieleb/litellm-setup
cd litellm-setup
docker compose -f docker-compose.yml -f docker-compose.langfuse.yml up -d

# Access Langfuse UI at http://localhost:3000
```

### OTEL Telemetry

OpenTelemetry is supported via environment variables:

```bash
export OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4317"
export OTEL_SERVICE_NAME="nanobot-deep"
```

## Dependencies

- `nanobot-ai>=0.1.4.post4,<0.2.0` (from PyPI)
- `deepagents>=0.4.0`
- `langgraph>=0.2.0`
- `langchain-core>=0.3.0`
- `langchain-mcp-adapters>=0.1.0`
- `aiosqlite>=0.20.0`

## Developer Guide

### Conventional Commits

This project uses [Conventional Commits](https://www.conventionalcommits.org/) for semantic versioning and automated releases.

**Types**: `feat:`, `fix:`, `docs:`, `style:`, `refactor:`, `perf:`, `test:`, `chore:`, `ci:`

**Breaking changes**: Add `!` after type or `BREAKING CHANGE:` in footer (triggers major version bump).

**Quick examples**:
```bash
git commit -m "feat: add A2A agent-to-agent protocol support"
git commit -m "fix: resolve AsyncSqliteSaver compatibility issue"
git commit -m "feat!: remove support for Python 3.11"
```

See `AGENTS.md#conventional-commits` for full documentation including scopes, validation, and CI/CD integration.

### Development Workflow

1. **Create feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make changes and commit with conventional format**:
   ```bash
   git commit -m "feat: add your feature"
   ```

3. **Push and create PR**:
   ```bash
   git push -u origin feature/your-feature-name
   gh pr create --base main
   ```

4. **CI pipeline runs automatically**:
   - Tests with coverage (80% minimum)
   - Linting (ruff check + format)
   - Docker build
   - Auto-merge if all checks pass

5. **Release process** (automatic on main):
   - Semantic version calculated from commits
   - Docker image published to ghcr.io
   - GitHub release created with changelog

### Running Tests

```bash
# Install dev dependencies
uv pip install -e ".[dev]"

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=nanobot_deep --cov-report=term

# Run specific test file
pytest tests/test_deepagents_config.py -v
```

### Dependency Constraints (CI)
CI installs dependencies using `constraints.txt` to avoid resolver conflicts between
`nanobot-ai` and `deepagents-cli`.

Current pinning includes `websockets==16.0.0`. `deepagents-cli` depends on `daytona`,
which requires `websockets<16`, so installs that include `deepagents-cli` will fail
until upstream relaxes the constraint. Track updates in
https://github.com/gthieleb/nanobot-deep/issues/70.

### Streaming Output Notes
`astream_events` event `name` values are runnable names and can change when graphs or
nodes are renamed. We capture final output based on `messages`/state output instead of
hard-coding event names to keep streaming resilient. Details in
https://github.com/gthieleb/nanobot-deep/issues/71.

### DeepAgents CLI Interactive Commands
DeepAgents CLI supports slash commands like `/model`, `/threads`, and `/clear` in
interactive mode. See the upstream overview for the full list:
https://docs.langchain.com/oss/python/deepagents/cli/overview#interactive-mode.
Telegram command routing is not implemented yet; tracked in
https://github.com/gthieleb/nanobot-deep/issues/65.

### Code Quality

```bash
# Format code
ruff format nanobot_deep/

# Check linting
ruff check nanobot_deep/

# Fix auto-fixable issues
ruff check --fix nanobot_deep/
```

### Telegram E2E Tests

See `AGENTS.md#telegram-e2e-tests-requires-real-account` for the full guide including test modes (DM vs group), environment variables, and important safety notes.

### Customisation

nanobot-deep supports the same customisation options as [LangChain's Deep Agents](https://docs.langchain.com/oss/javascript/deepagents/customization). Configuration is driven through `~/.nanobot/deepagents.json`.

#### Currently Supported via `deepagents.json`

| Feature | Config Path | Description |
|---------|-------------|-------------|
| Middleware toggles | `middleware.*` | Enable/disable summarization, memory, skills, subagents, prompt caching |
| Subagents | `subagents` | Define specialized subagents with custom system prompts and tools |
| Skills paths | `skills` | Paths to skill directories (SKILL.md files) |
| Memory paths | `memory` | Paths to AGENTS.md memory files |
| Interrupt on | `interrupt_on.*` | Human-in-the-loop approval for file/execute operations |
| Summarization | `summarization.*` | Trigger threshold and message retention |
| Task routing | `task_routing.*` | Control commands and delegate threshold |
| Checkpointer | `checkpointer.*` | SQLite or memory persistence |
| Backend type | `backend.type` | `filesystem` (default) or `local_shell` |
| Backend settings | `backend.*` | Exec timeout, path append, workspace restriction |
| Langfuse | `langfuse.*` | Observability and tracing |

#### Planned Customisation Options

| Feature | Config Path | Status |
|---------|-------------|--------|
| Custom system prompt | `system_prompt` | Not implemented - currently hardcoded in `deep_agent.py` |
| Custom tools | `tools` | `_build_custom_tools()` returns empty - extend for your tools |
| Daytona sandbox | `backend.type: "daytona"` | Enable by installing `langchain-daytona` |
| Composite/Store backends | `backend.type` | Planned - route different paths to different backends |
| Structured output | `response_format` | Not implemented |

#### Adding Custom Tools

Extend `_build_custom_tools()` in `nanobot_deep/agent/deep_agent.py`:

```python
def _build_custom_tools(self) -> list[Any]:
    """Build nanobot-specific custom tools."""
    from langchain_core.tools import tool
    import z

    @tool
    def get_weather(city: str) -> str:
        """Get weather for a city."""
        return f"Weather in {city}: sunny, 22°C"

    return [get_weather]
```

#### Adding Custom Middleware

Custom middleware can be added to `_create_agent()` in `deep_agent.py`. See [LangChain middleware docs](https://docs.langchain.com/oss/javascript/langchain/middleware/overview) for the middleware API.

#### Backend Types

nanobot-deep supports two backend types configured via `backend.type` in `deepagents.json`:

| Type | File Operations | Execute Tool | Use Case |
|------|---------------|-------------|----------|
| `filesystem` (default) | ✅ | ❌ | Safe, read/write only |
| `local_shell` | ✅ | ✅ | Full shell execution |

**FilesystemBackend** (default):
```json
{
  "backend": {
    "type": "filesystem"
  }
}
```

**LocalShellBackend** (with shell execution):
```json
{
  "backend": {
    "type": "local_shell",
    "exec_timeout": 60,
    "path_append": "/usr/local/bin"
  },
  "interrupt_on": {
    "execute": true
  }
}
```

**Security note:** When using `local_shell`, the `execute` tool is automatically protected by HITL (human-in-the-loop) approval unless explicitly disabled. This prevents the agent from running arbitrary commands without review.

For production with untrusted code, consider **Daytona sandbox** backends which provide isolated container execution. See [LangChain's backend docs](https://docs.langchain.com/oss/javascript/deepagents/backends).

## License

MIT
