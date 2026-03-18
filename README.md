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
| `SessionCheckpointer` | SQLite-based session persistence |
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

**Commit Format**:
```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types**:
- `feat:` - New feature (triggers minor version bump)
- `fix:` - Bug fix (triggers patch version bump)
- `docs:` - Documentation only changes
- `style:` - Code style changes (formatting, etc.)
- `refactor:` - Code refactoring (no feature/fix)
- `perf:` - Performance improvements
- `test:` - Adding or updating tests
- `chore:` - Build process, tooling, dependencies
- `ci:` - CI/CD configuration changes

**Breaking Changes**:

Add `BREAKING CHANGE:` in footer or `!` after type to trigger major version bump:
```
feat!: remove support for Python 3.11

BREAKING CHANGE: Minimum Python version is now 3.12
```

**Examples**:
```bash
# Feature (minor bump: 0.1.0 → 0.2.0)
git commit -m "feat: add A2A agent-to-agent protocol support"

# Fix (patch bump: 0.1.0 → 0.1.1)
git commit -m "fix: resolve AsyncSqliteSaver compatibility issue"

# Multiple changes
git commit -m "feat(memory): add conversation context middleware

- Integrate deepagents memory middleware
- Configure memory storage in deepagents.json
- Add E2E tests for context retention"
```

**CI/CD Integration**:
- Semantic versioning automatically generates version numbers from commits
- GitHub releases include auto-generated changelogs
- Docker images tagged with semantic versions

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

### Code Quality

```bash
# Format code
ruff format nanobot_deep/

# Check linting
ruff check nanobot_deep/

# Fix auto-fixable issues
ruff check --fix nanobot_deep/
```

## License

MIT
