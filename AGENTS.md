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

### Telegram E2E Tests (Requires Real Account)

Telegram E2E tests use Telethon to test from a real user account perspective.

**Test Modes:**

**Local Development (DM mode - default):**
```bash
source ~/env/ai/nanobot/ci  # Sets TELEGRAM_LOCAL_MODE="dm" by default
pytest tests/e2e/test_telegram*.py -m live -v
```
- Tests run in DM (direct message) mode
- Test user sends direct messages to bot
- For local development and testing

**CI/Production (Group mode):**
```bash
source ~/env/ai/nanobot/ci
TELEGRAM_LOCAL_MODE=group pytest tests/e2e/test_telegram*.py -m live -v
```
- Tests run in nanobot-deep-ci group
- Test user sends messages to group (you can control the group!)
- For CI and production testing

**Setup:**
1. Get API credentials: https://my.telegram.org/apps
2. Set environment variables:
```bash
export TELEGRAM_API_ID=12345
export TELEGRAM_API_HASH=abc123...
export TEST_USER_PHONE=+49...
export TELEGRAM_BOT_USERNAME=@your_bot

# For CI/Group mode:
export TELEGRAM_CI_GROUP_ID=-1001234567890  # nanobot-deep-ci group (set this!)
```

**Run tests:**
```bash
# Local development (DM):
pytest tests/e2e/test_telegram*.py -m live -v

# CI (Group):
TELEGRAM_LOCAL_MODE=group pytest tests/e2e/test_telegram*.py -m live -v
```

**Test files:**
- `test_telegram_basic.py` - Basic commands (/ping, /help, /new, /stop)
- `test_telegram_messages.py` - Message flow and conversation
- `test_telegram_errors.py` - Error handling and edge cases

**⚠️ IMPORTANT - STOP immediately on authentication or flood exceptions:**
- **FloodWaitError**: Telegram has rate-limited the phone number. WAIT 15-30 minutes before retrying.
- **PhoneCodeInvalidError**: The verification code was already used or is invalid. Get a NEW code from Telegram.
- **ApiIdInvalidError**: The API_ID/API_HASH combination is invalid. Verify credentials from my.telegram.org/apps.
- **CONSEQUENCES**: Continuing after these exceptions may lead to **account blocking** by Telegram.

See [Testing](../../README.md#telegram-e2e-tests) section in main README.md for detailed instructions.

### Ticket Issue Retrieval

When someone says "ticket anschauen" (ticket open), use `gh issue view` to get **full issue details** including:

```bash
# View issue with full comments
gh issue view <issue_number>

# Example: Get issue #12 with all comments
gh issue view 12

# This retrieves:
# - Original description
# - All comments (with timestamps)
# - Current status
# - Labels and metadata
# - Commit history
```

**Important:** `gh issue list` only shows title/status, but `gh issue view` includes the complete conversation thread with all comments and updates.

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

## Ticket Documentation Standards

### Language

**All tickets MUST be in English.**

This applies to:
- GitHub issues (titles, descriptions, comments)
- Ticket documentation files (`docs/tickets/NNN-ticket-name.md`)
- Code comments and commit messages (see Conventional Commits section)

**Why English?**
- International collaboration (GitHub, opencode-skills repo)
- Consistency with existing codebase
- Standard practice for open-source projects
- Easier for AI agents to understand and process

### Style Guidelines

**Keep it loose and conversational!**

- ❌ Don't be overly formal or academic
- ✅ Use natural, conversational language
- ✅ Write like you're explaining to a colleague
- ✅ Be concise but clear

**Good examples:**
```markdown
## Overview

Let's explore adding multi-group support for Telegram E2E tests. The current setup uses a single group, which causes session conflicts when tests run in parallel.

## Problem

With one group, all tests share the same session context:
- User A sets a secret
- User B can see it
- Tests can't run in parallel
```

**Bad examples:**
```markdown
## Overview

This document provides a comprehensive analysis of the requirement to implement a multi-group testing infrastructure for the Telegram end-to-end test suite. The current architecture utilizes a solitary group configuration, which results in session contention during concurrent test execution.

## Problem

The existing single-group configuration presents several challenges:
1. Session context is shared across all test scenarios
2. Data leakage may occur between different test scenarios
3. Parallel test execution is not feasible
```

### Ticket File Format

When creating ticket documentation in `docs/tickets/`:

```markdown
# Ticket: [Title]

## Overview

[Brief description of what this ticket is about - 2-3 sentences]

## Background

[Context and current state]

## Requirements

[What needs to be done - bullet points]

## Implementation

[How to implement - technical approach]

## Deliverables

[What will be delivered]

## References

[Links to related docs, issues, or external resources]
```

### GitHub Issue Creation

When creating GitHub issues from ticket files:

```bash
gh issue create \
  --title "Ticket Title (English)" \
  --body-file docs/tickets/NNN-ticket-name.md \
  --label "enhancement" \
  --label "phase-1"
```

**Important:**
- Title MUST be in English
- Body from ticket file MUST be in English
- Use `--label` to categorize (phase, type, priority)

## Conventional Commits

When working on nanobot-deep, **always** use Conventional Commits format for all commits.

### Quick Reference

```bash
# Features (minor version bump)
feat: add streaming support to gateway
feat(telegram): implement inline approval buttons
feat(a2a): add agent-to-agent protocol integration

# Fixes (patch version bump)
fix: resolve model initialization error
fix(checkpointer): use AsyncSqliteSaver for async compatibility
fix(gateway): handle missing session history gracefully

# Documentation
docs: update README with A2A integration guide
docs(agents): document multi-agent workflows

# Tests
test: add unit tests for memory middleware
test(e2e): verify streaming flow in Telegram

# Chore
chore: update dependencies
chore(ci): configure GitHub Actions workflow
chore(docker): optimize multi-stage build

# Breaking changes (major version bump)
feat!: migrate to AsyncSqliteSaver

BREAKING CHANGE: SessionCheckpointer removed, use AsyncSqliteSaver directly
```

### Why Conventional Commits?

1. **Automated Versioning**: Semantic versions generated automatically
   - `feat:` → minor bump (0.1.0 → 0.2.0)
   - `fix:` → patch bump (0.1.0 → 0.1.1)
   - `feat!:` or `BREAKING CHANGE:` → major bump (0.1.0 → 1.0.0)

2. **Clear History**: Easy to understand what changed
   ```bash
   git log --oneline
   # a1b2c3d feat(memory): add conversation context middleware
   # d4e5f6g fix(gateway): resolve AsyncSqliteSaver compatibility
   # g7h8i9j docs: update README with conventional commits guide
   ```

3. **Automated Changelogs**: Release notes generated from commits
   - Features grouped together
   - Fixes grouped together
   - Breaking changes highlighted

4. **Team Communication**: Clear intent in commit messages
   - Instantly see if commit adds feature or fixes bug
   - Scope indicates which component changed
   - Body provides detailed context

### Enforcement

The CI/CD pipeline uses these commits for:
- **Version calculation**: `paulhatch/semantic-version` action
- **Changelog generation**: Grouped by type
- **Docker tags**: Images tagged with semantic versions
- **GitHub releases**: Auto-created with version tags

### Validation

Before pushing, validate your commit message:
```bash
# Check last commit message format
git log -1 --pretty=%B | grep -E '^(feat|fix|docs|style|refactor|perf|test|chore|ci)(\(.+\))?: .+'

# If it doesn't match, amend the commit
git commit --amend -m "feat: correct commit message"
```

### Multi-Agent Workflows

When spawning multiple agents or working across features:

1. **Use consistent scopes**:
   ```bash
   feat(memory): add middleware
   feat(skills): add frontmatter support
   feat(mcp): integrate langchain-mcp-adapters
   ```

2. **Reference related commits**:
   ```bash
   feat(a2a): add client implementation
   
   Related to feat(a2a): add server implementation
   Part of A2A integration (Phase 1, Ticket #5)
   ```

3. **Link to issues/tickets**:
   ```bash
   fix(gateway): resolve startup error
   
   Fixes startup error with AsyncSqliteSaver initialization.
   Closes #0 (Ticket #0: Commit & Merge + CI/CD Setup)
   ```

### Common Scopes

Use these standard scopes for consistency:

| Scope | Component |
|-------|-----------|
| `memory` | Memory middleware |
| `skills` | Skills middleware |
| `mcp` | MCP integration |
| `a2a` | Agent-to-agent protocol |
| `streaming` | Streaming support |
| `docker` | Docker/containerization |
| `gateway` | Gateway/message handling |
| `agent` | DeepAgent implementation |
| `checkpointer` | Session checkpointing |
| `config` | Configuration schemas |
| `ci` | CI/CD workflows |
| `test` | Testing infrastructure |

### Full Documentation

See `README.md` Developer Guide section for complete documentation on:
- Commit format specification
- Breaking change syntax
- Examples for each commit type
- CI/CD integration details

## Task Delegation

**Always spawn tasks to subagents** for complex, multi-step, or parallel work. Prefer the `@ai-*` agents available in the opencode-skills repository.

### Available Agents

| Agent | Use For |
|-------|---------|
| `@ai-developer` | Development: LangGraph, DeepAgents, nanobot, LangChain |
| `@ai-tester` | Testing: pytest, mocking, E2E, coverage |
| `@ai-product-owner` | Product: Issue/PR tracking, curated tickets |

### When to Spawn

- **Complex tasks**: Multi-file changes, new features
- **Parallel work**: Independent tasks that can run simultaneously
- **Specialized work**: Testing, documentation, research
- **Phase 3+ work**: All Phase 3 tickets can be spawned in parallel

### Spawning Pattern

```bash
# Use Task tool with appropriate agent type
Task(description="Add memory tests", prompt="...", subagent_type="general")

# For testing tasks, use ai-tester
Task(description="Write E2E tests", prompt="...", subagent_type="general")
```

### Agent Location

Agents are defined in the [opencode-skills](https://github.com/gthieleb/opencode-skills) repository:
- `nanobot-deep/agents/ai-developer.md`
- `nanobot-deep/agents/ai-tester.md`
- `nanobot-deep/agents/ai-product-owner.md`
