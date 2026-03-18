# Ticket #25: ACP Support (Agent Client Protocol)

**Status**: Pending  
**Priority**: MEDIUM  
**Phase**: Phase 3 - User Features  
**Branch**: `feature/acp-support`  
**Dependencies**: Ticket #19 (Lightweight Gateway)  
**Estimated Effort**: 12-16 hours  
**Target Release**: v0.5.0

---

## Objective

Implement Agent Client Protocol (ACP) support to enable nanobot-deep integration with ACP-compatible editors and IDEs (Zed, JetBrains, Avante.nvim, CodeCompanion.nvim).

---

## Background

### What is ACP?

**Agent Client Protocol (ACP)** is an open protocol that standardizes communication between code editors/IDEs and AI coding agents. It enables any ACP-compatible editor to use any ACP-compatible agent.

**Key Characteristics**:
- **Transport**: JSON-RPC over stdio
- **Architecture**: Agent runs as subprocess, editor communicates via stdin/stdout
- **Standard**: Open specification at [agentclientprotocol.com](https://agentclientprotocol.com)
- **Editor Support**: Zed, JetBrains IDEs, Avante.nvim, CodeCompanion.nvim

### Current State
- No ACP support in nanobot-deep
- Agents only accessible via Telegram/Slack channels
- No IDE integration capability
- Limited to chat-based interfaces

### Desired State
- ACP server implementation (`nanobot-deep acp` command)
- Integration with Zed, JetBrains, Neovim plugins
- Full feature parity with terminal-based usage
- Configuration for ACP-specific settings

### Context from OpenCode
OpenCode implements ACP via `opencode acp` command:
- Starts agent as ACP-compatible subprocess
- Communicates via JSON-RPC over stdio
- Supports all tools, MCP servers, custom commands
- Slash commands like `/undo`, `/redo` not yet supported

---

## Technical Approach

### Architecture

```
┌─────────────────┐     JSON-RPC      ┌──────────────────┐
│   Zed / JetBrains │◄──────────────►│  nanobot-deep    │
│   Avante.nvim    │     stdio       │  ACP Server      │
│   CodeCompanion  │                  │                  │
└─────────────────┘                  └────────┬─────────┘
                                              │
                                     ┌────────▼─────────┐
                                     │   DeepAgent      │
                                     │   (LangGraph)    │
                                     └────────┬─────────┘
                                              │
                              ┌───────────────┼───────────────┐
                              │               │               │
                     ┌────────▼───┐   ┌───────▼──────┐   ┌────▼─────┐
                     │   Tools    │   │  Middleware  │   │   MCP    │
                     │   (fs, etc)│   │  (memory)    │   │ Servers  │
                     └────────────┘   └──────────────┘   └──────────┘
```

### ACP vs A2A Comparison

| Aspect | ACP (Agent Client Protocol) | A2A (Agent-to-Agent) |
|--------|----------------------------|----------------------|
| **Purpose** | Editor ↔ Agent communication | Agent ↔ Agent delegation |
| **Standard** | Open protocol ([agentclientprotocol.com](https://agentclientprotocol.com)) | DeepAgents internal pattern |
| **Transport** | JSON-RPC over stdio | In-process / network |
| **Clients** | IDEs: Zed, JetBrains, Neovim | Sub-agents, specialized workers |
| **Use Case** | IDE integration, editor tooling | Multi-agent workflows, task delegation |
| **Direction** | External (human-facing) | Internal (agent-facing) |
| **State** | Stateless per request | Context-aware across agents |
| **Discovery** | Editor discovers agents | Agents discover capabilities |
| **Scope** | Single agent per editor session | Multiple concurrent sub-agents |
| **Maturity** | Emerging standard (2025) | Established pattern (LangGraph) |

### Recommendation

**Implement BOTH protocols** - they serve complementary purposes:

1. **ACP for External Integration**: Enables IDE integration, reaching developers in their workflow
2. **A2A for Internal Orchestration**: Enables multi-agent workflows and task delegation

**Priority Order**:
- Phase 1: A2A (already planned) - Foundation for multi-agent
- Phase 3: ACP - IDE integration after gateway refactoring

**Why Both**:
- ACP is the entry point for developers (IDE-first experience)
- A2A is the engine for complex workflows (multi-agent orchestration)
- Together they provide a complete developer experience

### Implementation Strategy

1. **Research Phase**: Study ACP specification and OpenCode implementation
2. **Protocol Phase**: Implement JSON-RPC server with ACP methods
3. **Bridge Phase**: Connect ACP to DeepAgent
4. **Tool Phase**: Ensure all tools work via ACP
5. **Testing Phase**: Test with multiple editors
6. **Documentation Phase**: Editor-specific setup guides

---

## Tasks

### 1. Research Phase
- [ ] Task 1.1: Study ACP specification
  - Source: [agentclientprotocol.com](https://agentclientprotocol.com)
  - Focus: JSON-RPC methods, message format, lifecycle
  - Acceptance: Document ACP protocol details

- [ ] Task 1.2: Analyze OpenCode ACP implementation
  - Source: OpenCode source code
  - Focus: `opencode acp` command, JSON-RPC handling
  - Acceptance: Understand implementation patterns

- [ ] Task 1.3: Research editor configurations
  - Editors: Zed, JetBrains, Avante.nvim, CodeCompanion.nvim
  - Focus: Configuration format, command structure
  - Acceptance: Document editor setup patterns

### 2. Protocol Implementation
- [ ] Task 2.1: Implement JSON-RPC server
  - File: `src/acp/server.py`
  - Methods: `initialize`, `shutdown`, `message`, `cancel`
  - Acceptance: JSON-RPC server with ACP methods

- [ ] Task 2.2: Define ACP message schemas
  - File: `src/acp/protocol.py`
  - Schemas: Request, Response, Error, Notification
  - Acceptance: Pydantic models for ACP messages

- [ ] Task 2.3: Implement stdio transport
  - File: `src/acp/transport.py`
  - Transport: stdin/stdout JSON-RPC
  - Acceptance: Stdio transport working

### 3. DeepAgent Bridge
- [ ] Task 3.1: Create ACP-to-DeepAgent adapter
  - File: `src/acp/adapter.py`
  - Methods: Convert ACP messages to DeepAgent invocations
  - Acceptance: ACP messages trigger DeepAgent

- [ ] Task 3.2: Handle streaming responses
  - Feature: Stream agent responses back to editor
  - Acceptance: Streaming works via ACP

- [ ] Task 3.3: Implement tool execution
  - Feature: Tools work via ACP
  - Acceptance: File operations, terminal commands work

### 4. CLI Integration
- [ ] Task 4.1: Add `acp` command to CLI
  - File: `src/cli.py` or `src/__main__.py`
  - Command: `nanobot-deep acp`
  - Acceptance: CLI starts ACP server

- [ ] Task 4.2: Configure ACP settings
  - Config: `~/.nanobot/deepagents.json`
  - Settings: enabled, model override, tool restrictions
  - Acceptance: ACP configuration working

### 5. Editor Integration
- [ ] Task 5.1: Create Zed configuration example
  - File: `docs/acp/zed.md`
  - Content: `settings.json` configuration
  - Acceptance: Zed integration documented

- [ ] Task 5.2: Create JetBrains configuration example
  - File: `docs/acp/jetbrains.md`
  - Content: `acp.json` configuration
  - Acceptance: JetBrains integration documented

- [ ] Task 5.3: Create Neovim configuration examples
  - File: `docs/acp/neovim.md`
  - Content: Avante.nvim, CodeCompanion.nvim configs
  - Acceptance: Neovim integrations documented

### 6. Testing
- [ ] Task 6.1: Unit tests for ACP protocol
  - File: `tests/unit/test_acp_protocol.py`
  - Coverage: Message parsing, validation, serialization
  - Acceptance: 90%+ coverage

- [ ] Task 6.2: Integration tests for ACP server
  - File: `tests/integration/test_acp_server.py`
  - Coverage: JSON-RPC handling, DeepAgent bridge
  - Acceptance: Integration tests pass

- [ ] Task 6.3: E2E tests with mock editor
  - File: `tests/e2e/test_acp_e2e.py`
  - Scenario: Simulate editor → ACP → DeepAgent flow
  - Acceptance: E2E flow works

### 7. Documentation
- [ ] Task 7.1: Write ACP architecture docs
  - File: `docs/acp-architecture.md`
  - Content: Protocol, server, bridge, tools
  - Acceptance: Complete ACP architecture documentation

- [ ] Task 7.2: Write editor setup guides
  - Files: `docs/acp/*.md`
  - Content: Zed, JetBrains, Neovim setup
  - Acceptance: Step-by-step setup guides

- [ ] Task 7.3: Update README with ACP section
  - Section: IDE integration, ACP support
  - Acceptance: README includes ACP overview

---

## Deliverables

### Code
- `src/acp/` directory with:
  - `__init__.py` - Module exports
  - `server.py` - JSON-RPC server
  - `protocol.py` - Message schemas
  - `transport.py` - Stdio transport
  - `adapter.py` - DeepAgent bridge
- CLI command: `nanobot-deep acp`

### Tests
- `tests/unit/test_acp_protocol.py`
- `tests/integration/test_acp_server.py`
- `tests/e2e/test_acp_e2e.py`

### Documentation
- `docs/acp-architecture.md` - Architecture documentation
- `docs/acp/zed.md` - Zed setup guide
- `docs/acp/jetbrains.md` - JetBrains setup guide
- `docs/acp/neovim.md` - Neovim setup guides
- Updated `README.md` - ACP section

---

## Acceptance Criteria

### Functional Requirements
- [ ] `nanobot-deep acp` starts ACP server
- [ ] JSON-RPC communication works over stdio
- [ ] DeepAgent processes ACP messages
- [ ] Tools work via ACP (file operations, terminal)
- [ ] Streaming responses reach editor
- [ ] MCP servers work via ACP

### Non-Functional Requirements
- [ ] ACP overhead is <50ms for message processing
- [ ] Memory overhead is minimal
- [ ] Error handling prevents editor crashes
- [ ] Logging provides ACP traceability

### Quality Requirements
- [ ] Unit test coverage >= 90%
- [ ] Integration tests pass
- [ ] All code passes linting (ruff)
- [ ] All code passes type checking (pyright)
- [ ] Documentation is complete and accurate

---

## Testing Strategy

### Unit Tests
- **Protocol**: Message parsing, validation, serialization
- **Server**: JSON-RPC handling, method routing
- **Adapter**: ACP-to-DeepAgent conversion

### Integration Tests
- **Server + Adapter**: Full message flow
- **Tool Execution**: Tools via ACP
- **Streaming**: Response streaming

### E2E Tests
- **Mock Editor**: Simulate editor communication
- **Real Editors**: Manual testing with Zed, JetBrains

### Verification Steps
1. Run unit tests: `pytest tests/unit/test_acp*.py -v`
2. Run integration tests: `pytest tests/integration/test_acp*.py -v`
3. Test with Zed: Configure and verify messages
4. Test with JetBrains: Configure and verify messages

---

## Implementation Notes

### Key Decisions
1. **JSON-RPC over stdio**: Standard ACP transport
2. **Streaming Support**: Essential for UX
3. **Tool Compatibility**: All tools must work via ACP
4. **Configuration**: Per-user ACP settings

### Pitfalls to Avoid
- **Blocking I/O**: Use async stdio handling
- **Buffer Overflow**: Handle large messages
- **Incomplete Responses**: Ensure streaming completes
- **Editor Compatibility**: Test with multiple editors

### Integration Points
- **DeepAgent**: `src/deep_agent.py`
- **Tools**: `src/tools/`
- **MCP**: `src/mcp/`
- **CLI**: `src/cli.py` or `src/__main__.py`

### Dependencies
- `jsonrpc-base` or custom JSON-RPC implementation
- `pydantic` - Data validation
- `asyncio` - Async stdio

---

## Related Tickets
- **Depends on**: #19 (Lightweight Gateway) - Gateway refactoring complete
- **Related**: #5 (A2A Integration) - Complementary protocol
- **Enables**: IDE integration for all features

---

## Editor Configuration Examples

### Zed (`~/.config/zed/settings.json`)
```json
{
  "agent_servers": {
    "nanobot-deep": {
      "command": "nanobot-deep",
      "args": ["acp"]
    }
  }
}
```

### JetBrains (`acp.json`)
```json
{
  "agent_servers": {
    "nanobot-deep": {
      "command": "/path/to/nanobot-deep",
      "args": ["acp"]
    }
  }
}
```

### Avante.nvim
```lua
{
  acp_providers = {
    ["nanobot-deep"] = {
      command = "nanobot-deep",
      args = { "acp" }
    }
  }
}
```

---

## Questions?
- See `AGENTS.md` for ticket workflow
- See `ROADMAP.md` for phase overview
- See [agentclientprotocol.com](https://agentclientprotocol.com) for protocol spec

---

Last updated: 2026-03-18
