# Ticket #3: MCP Integration (Model Context Protocol)

**Status**: Pending  
**Priority**: HIGH  
**Phase**: Phase 1 - Core Middleware  
**Branch**: `feature/mcp-integration`  
**Dependencies**: Ticket #2 (Skills Middleware)  
**Estimated Effort**: 12-16 hours  
**Target Release**: v0.3.0

---

## Objective

Migrate from nanobot's custom MCP implementation (`nanobot/tools/mcp.py`) to deepagents' native `langchain-mcp-adapters` package, configure MCP servers in `config.json`, and provide a migration guide comparing the two approaches.

---

## Background

### Current State
- nanobot has custom MCP implementation: `nanobot/tools/mcp.py`
- No MCP servers configured in nanobot-deep
- `langchain-mcp-adapters` package not installed
- No MCP configuration in `deepagents.json` or `config.json`
- Unknown: What MCP servers are available/needed?

### Desired State
- `langchain-mcp-adapters` package installed and integrated
- MCP servers configured in `config.json` (not deepagents.json)
- MCP tools available to DeepAgent
- Migration guide documenting differences between nanobot and deepagents MCP
- Unit tests for MCP configuration loading
- E2E tests for MCP tool execution
- Documentation explaining MCP setup and available servers

### Context from Planning Session
- **Decision**: Use deepagents `langchain-mcp-adapters` (not nanobot custom MCP)
  - Rationale: Official LangChain integration, better maintained
  - Alternative: Port nanobot/tools/mcp.py (rejected - duplication)
- **Configuration Location**: MCP servers in `config.json` (provider-level), not `deepagents.json`
- **Migration Strategy**: Document both approaches, provide comparison table
- **Priority**: Phase 1 after Skills middleware

---

## Technical Approach

### Architecture
- **MCP Client**: `langchain-mcp-adapters` package
- **MCP Servers**: External processes (stdio or HTTP)
- **Configuration**: `config.json` with MCP server definitions
- **Integration Point**: DeepAgent tool binding (LangGraph tools)

### Implementation Strategy
1. **Research Phase**: Study langchain-mcp-adapters documentation and API
2. **Installation Phase**: Add package to pyproject.toml
3. **Configuration Phase**: Define MCP server config schema
4. **Integration Phase**: Bind MCP tools to DeepAgent
5. **Comparison Phase**: Analyze nanobot vs deepagents MCP approaches
6. **Testing Phase**: Unit + E2E tests
7. **Documentation Phase**: Migration guide and MCP setup docs

### Key Decisions
- **Package**: Use `langchain-mcp-adapters` (official LangChain MCP integration)
- **Server Protocol**: Support both stdio and HTTP MCP servers
- **Configuration Schema**: JSON schema for MCP server definitions
- **Error Handling**: Graceful degradation if MCP server unavailable

---

## Tasks

### 1. Analysis & Research
- [ ] Task 1.1: Read langchain-mcp-adapters documentation
  - URL: https://github.com/langchain-ai/langchain-mcp-adapters
  - Focus: Installation, configuration, server types, API usage
  - Acceptance: Understand how to configure and use MCP servers

- [ ] Task 1.2: Analyze nanobot/tools/mcp.py
  - File: `nanobot/tools/mcp.py`
  - Focus: What features does it provide?
  - Questions: Server types supported, configuration format, tool binding
  - Acceptance: Document current nanobot MCP capabilities

- [ ] Task 1.3: Research available MCP servers
  - Examples: filesystem, brave-search, github, postgres
  - Sources: MCP server registry, langchain docs
  - Acceptance: List of recommended MCP servers for nanobot-deep

### 2. Package Installation
- [ ] Task 2.1: Add langchain-mcp-adapters to dependencies
  - File: `pyproject.toml`
  - Add: `langchain-mcp-adapters = "^0.1.0"` (check latest version)
  - Run: `poetry lock && poetry install`
  - Acceptance: Package installs without conflicts

- [ ] Task 2.2: Verify imports work
  - Test: `from langchain_mcp_adapters import MCPClient`
  - Test: Import in Python REPL
  - Acceptance: No import errors

### 3. Configuration Schema
- [ ] Task 3.1: Define MCP server configuration schema
  - File: `nanobot_deep/config/schema.py`
  - Add: `MCPServerConfig` class
  - Fields:
    ```python
    class MCPServerConfig(BaseModel):
        name: str
        type: Literal["stdio", "http"]
        command: Optional[str] = None  # For stdio
        url: Optional[str] = None      # For HTTP
        env: Optional[Dict[str, str]] = None
        enabled: bool = True
    ```
  - Validation: Command required if type=stdio, URL required if type=http

- [ ] Task 3.2: Add MCP to main config schema
  - File: `nanobot_deep/config/schema.py`
  - Update: `NanobotConfig` class
  - Add field: `mcp_servers: List[MCPServerConfig] = []`
  - Acceptance: Config validates MCP server definitions

- [ ] Task 3.3: Create example MCP configuration
  - File: User's `~/.nanobot/config.json`
  - Add example servers:
    ```json
    {
      "mcp_servers": [
        {
          "name": "filesystem",
          "type": "stdio",
          "command": "npx -y @modelcontextprotocol/server-filesystem ~/.nanobot/workspace",
          "enabled": true
        },
        {
          "name": "brave-search",
          "type": "stdio",
          "command": "npx -y @modelcontextprotocol/server-brave-search",
          "env": {
            "BRAVE_API_KEY": "${BRAVE_API_KEY}"
          },
          "enabled": false
        }
      ]
    }
    ```

### 4. MCP Client Integration
- [ ] Task 4.1: Create MCP client wrapper
  - File: `nanobot_deep/mcp/client.py`
  - Class: `MCPClientManager`
  - Methods:
    - `__init__(config: List[MCPServerConfig])`
    - `async def start_servers()`
    - `async def stop_servers()`
    - `def get_tools() -> List[BaseTool]`
  - Acceptance: Client can start/stop MCP servers and retrieve tools

- [ ] Task 4.2: Integrate MCP tools into DeepAgent
  - File: `nanobot_deep/agent/deep_agent.py`
  - Update: `__init__` method
  - Load MCP tools: `mcp_tools = mcp_client.get_tools()`
  - Bind tools: Pass to LangGraph agent
  - Acceptance: MCP tools available to agent

- [ ] Task 4.3: Add error handling
  - Handle: MCP server startup failures
  - Handle: Tool execution errors
  - Handle: Server crashes (auto-restart?)
  - Acceptance: Graceful degradation if MCP server unavailable

### 5. Migration Guide & Comparison
- [ ] Task 5.1: Document nanobot MCP approach
  - File: `docs/MCP_MIGRATION.md`
  - Section: "Nanobot Custom MCP"
  - Content: How nanobot/tools/mcp.py works
  - Include: Code examples, configuration format

- [ ] Task 5.2: Document deepagents MCP approach
  - File: `docs/MCP_MIGRATION.md`
  - Section: "Deepagents langchain-mcp-adapters"
  - Content: How langchain-mcp-adapters works
  - Include: Code examples, configuration format

- [ ] Task 5.3: Create comparison table
  - File: `docs/MCP_MIGRATION.md`
  - Table columns: Feature, Nanobot, Deepagents, Recommendation
  - Rows: Server types, Configuration, Tool binding, Error handling, Maintenance
  - Acceptance: Clear comparison for migration decisions

### 6. Testing
- [ ] Task 6.1: Write unit tests
  - File: `tests/unit/test_mcp_client.py`
  - Test cases:
    1. `test_mcp_config_loading()`: Verify config parses correctly
    2. `test_mcp_client_initialization()`: Create MCPClientManager
    3. `test_stdio_server_config()`: Validate stdio server config
    4. `test_http_server_config()`: Validate HTTP server config
    5. `test_invalid_mcp_config()`: Handle malformed config
    6. `test_mcp_tools_binding()`: Verify tools bind to agent
  - Mock: MCP server processes, langchain-mcp-adapters client
  - Coverage: 85%+

- [ ] Task 6.2: Write E2E tests
  - File: `tests/e2e/test_mcp_integration.py`
  - Test scenarios:
    1. Start gateway with MCP filesystem server
    2. Use Telegram to ask: "List files in workspace"
    3. Verify: MCP tool executes, returns file list
    4. Test: Multiple MCP servers simultaneously
  - Note: May need mock MCP servers for CI
  - Acceptance: E2E tests pass with real or mock MCP servers

### 7. Documentation
- [ ] Task 7.1: Update README.md
  - Section: Add "MCP Integration" section
  - Content:
    - What is MCP (Model Context Protocol)
    - How to configure MCP servers
    - Example MCP servers (filesystem, brave-search)
    - How to use MCP tools in Telegram/Slack
  - Include: Configuration examples

- [ ] Task 7.2: Create MCP setup guide
  - File: `docs/MCP_SETUP.md`
  - Sections:
    - Installation (npx, npm packages)
    - Server types (stdio vs HTTP)
    - Environment variables (API keys)
    - Testing MCP servers
    - Troubleshooting
  - Acceptance: User can set up MCP server from guide

---

## Deliverables

### Code Deliverables
- [ ] `pyproject.toml`: langchain-mcp-adapters dependency added
- [ ] `nanobot_deep/config/schema.py`: MCPServerConfig class
- [ ] `nanobot_deep/mcp/client.py`: MCPClientManager class
- [ ] `nanobot_deep/agent/deep_agent.py`: MCP tools integration
- [ ] User's `~/.nanobot/config.json`: Example MCP server configs

### Test Deliverables
- [ ] `tests/unit/test_mcp_client.py`: Unit tests for MCP client
- [ ] `tests/e2e/test_mcp_integration.py`: E2E tests for MCP tools

### Documentation Deliverables
- [ ] `docs/MCP_MIGRATION.md`: Nanobot vs Deepagents MCP comparison
- [ ] `docs/MCP_SETUP.md`: MCP server setup guide
- [ ] README.md: MCP Integration section

---

## Acceptance Criteria

### Functional Requirements
1. ✅ langchain-mcp-adapters package installed successfully
   - Verification: `poetry show langchain-mcp-adapters`
   - Test: `test_mcp_package_installed()`

2. ✅ MCP servers configured in config.json
   - Verification: Cat config.json, see mcp_servers array
   - Test: `test_mcp_config_valid()`

3. ✅ MCP tools available to DeepAgent
   - Verification: Agent can execute MCP tool (e.g., list files)
   - Test: `test_mcp_tool_execution()`

4. ✅ Migration guide documents nanobot vs deepagents MCP
   - Verification: `docs/MCP_MIGRATION.md` exists with comparison table
   - Test: Manual review of documentation

### Non-Functional Requirements
1. ✅ Performance: MCP server startup < 5 seconds
2. ✅ Reliability: Graceful degradation if MCP server fails
3. ✅ Security: Environment variables expanded securely

### Testing Requirements
- ✅ Unit test coverage ≥ 85%
- ✅ All E2E tests passing (with mock or real MCP servers)
- ✅ CI/CD pipeline passing

---

## Testing Strategy

### Unit Tests
**File**: `tests/unit/test_mcp_client.py`

**Test Cases**:
1. `test_mcp_config_loading()`:
   - Load config.json with mcp_servers
   - Verify MCPServerConfig objects created
   - Check name, type, command/url fields

2. `test_mcp_client_initialization()`:
   - Mock langchain-mcp-adapters.MCPClient
   - Create MCPClientManager with config
   - Verify client.start_servers() called

3. `test_stdio_server_validation()`:
   - Config: type=stdio, command present
   - Verify: Validation passes
   - Config: type=stdio, command missing
   - Verify: Validation error raised

4. `test_http_server_validation()`:
   - Config: type=http, url present
   - Verify: Validation passes
   - Config: type=http, url missing
   - Verify: Validation error raised

5. `test_mcp_tools_retrieval()`:
   - Mock MCP server returning 3 tools
   - Call `mcp_client.get_tools()`
   - Verify: 3 LangChain tools returned

**Mock Strategy**:
- Mock subprocess for stdio servers
- Mock HTTP client for HTTP servers
- Mock langchain-mcp-adapters.MCPClient

### E2E Tests
**File**: `tests/e2e/test_mcp_integration.py`

**Test Scenarios**:
1. **Filesystem MCP server**:
   - Configure: MCP filesystem server
   - Start gateway
   - Send Telegram message: "List files in workspace"
   - Verify: Agent uses MCP filesystem tool
   - Verify: Response contains file names

2. **Multiple MCP servers**:
   - Configure: filesystem + brave-search
   - Send message: "Search for Python tutorials and save results to workspace"
   - Verify: Both MCP tools used (search + filesystem)

3. **MCP server failure handling**:
   - Configure: Invalid MCP server (bad command)
   - Start gateway
   - Verify: Gateway starts (degraded mode)
   - Verify: Other tools still work

**Verification Steps**:
1. Check gateway logs for MCP server startup
2. Verify Telegram responses mention file operations
3. Check actual filesystem changes (if applicable)

---

## Configuration

### Configuration Files
**File**: `~/.nanobot/config.json`

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
  },
  "mcp_servers": [
    {
      "name": "filesystem",
      "type": "stdio",
      "command": "npx -y @modelcontextprotocol/server-filesystem ~/.nanobot/workspace",
      "enabled": true,
      "description": "Access files in workspace"
    },
    {
      "name": "brave-search",
      "type": "stdio",
      "command": "npx -y @modelcontextprotocol/server-brave-search",
      "env": {
        "BRAVE_API_KEY": "${BRAVE_API_KEY}"
      },
      "enabled": false,
      "description": "Web search via Brave API"
    },
    {
      "name": "github",
      "type": "stdio",
      "command": "npx -y @modelcontextprotocol/server-github",
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      },
      "enabled": false,
      "description": "GitHub repository access"
    }
  ],
  "telegram": {
    "token": "${TELEGRAM_BOT_TOKEN}"
  }
}
```

**Configuration Options**:
- `name`: Server identifier
  - Type: string
  - Required: yes
  - Description: Unique name for MCP server

- `type`: Server protocol
  - Type: string
  - Valid values: "stdio", "http"
  - Required: yes
  - Description: How to communicate with server

- `command`: Command to start server (stdio only)
  - Type: string
  - Required: if type=stdio
  - Example: "npx -y @modelcontextprotocol/server-filesystem /path"
  - Description: Shell command to execute

- `url`: Server URL (HTTP only)
  - Type: string
  - Required: if type=http
  - Example: "http://localhost:8080"
  - Description: HTTP endpoint

- `env`: Environment variables
  - Type: object (key-value pairs)
  - Required: no
  - Description: Environment variables for server process
  - Note: Supports ${VAR} expansion from system env

- `enabled`: Enable server
  - Type: boolean
  - Default: true
  - Description: Toggle server on/off

---

## Documentation Updates

### README.md
**Section**: MCP Integration (after Skills section)

**Content**:
```markdown
## MCP Integration (Model Context Protocol)

MCP (Model Context Protocol) allows the agent to use external tools and services.

### What is MCP?

MCP is a standardized protocol for connecting LLMs to external tools:
- **Filesystem**: Read/write files, list directories
- **Brave Search**: Web search capabilities
- **GitHub**: Repository access, issue management
- **Postgres**: Database queries
- And more...

### Configuration

MCP servers are configured in `~/.nanobot/config.json`:

\`\`\`json
{
  "mcp_servers": [
    {
      "name": "filesystem",
      "type": "stdio",
      "command": "npx -y @modelcontextprotocol/server-filesystem ~/.nanobot/workspace"
    }
  ]
}
\`\`\`

### Available MCP Servers

#### Filesystem
```json
{
  "name": "filesystem",
  "type": "stdio",
  "command": "npx -y @modelcontextprotocol/server-filesystem /path/to/directory"
}
```
Capabilities: read_file, write_file, list_directory, create_directory

#### Brave Search
```json
{
  "name": "brave-search",
  "type": "stdio",
  "command": "npx -y @modelcontextprotocol/server-brave-search",
  "env": {
    "BRAVE_API_KEY": "${BRAVE_API_KEY}"
  }
}
```
Requires: Brave API key (get from https://brave.com/search/api/)

#### GitHub
```json
{
  "name": "github",
  "type": "stdio",
  "command": "npx -y @modelcontextprotocol/server-github",
  "env": {
    "GITHUB_TOKEN": "${GITHUB_TOKEN}"
  }
}
```
Capabilities: create_issue, list_repos, get_file_contents, etc.

### Usage Example (Telegram)

\`\`\`
User: List files in my workspace
Bot: [Uses MCP filesystem tool]
      Files in workspace:
      - project.py
      - README.md
      - data/

User: Search for "Python asyncio tutorial"
Bot: [Uses MCP brave-search tool]
      Found these tutorials:
      1. Real Python - Asyncio Guide
      2. ...
\`\`\`

### Migration from Nanobot

See `docs/MCP_MIGRATION.md` for comparison between nanobot custom MCP and deepagents langchain-mcp-adapters.

### Troubleshooting

- **MCP server won't start**: Check command syntax, ensure npx is installed
- **Permission denied**: Ensure server has access to specified paths
- **API key errors**: Verify environment variables are set correctly

For detailed setup instructions, see `docs/MCP_SETUP.md`.
```

---

## Implementation Notes

### Key Decisions
1. **Decision**: Use langchain-mcp-adapters (official package)
   - **Rationale**: Better maintained, official LangChain support, active development
   - **Alternative**: Port nanobot/tools/mcp.py (rejected - duplication)
   - **Tradeoffs**: Dependency on external package, but better long-term maintenance

2. **Decision**: Configure in config.json (not deepagents.json)
   - **Rationale**: MCP servers are provider-level, not agent-specific
   - **Alternative**: deepagents.json (rejected - wrong abstraction level)
   - **Tradeoffs**: Two config files, but clearer separation of concerns

3. **Decision**: Support both stdio and HTTP MCP servers
   - **Rationale**: Different servers use different protocols
   - **Example**: stdio for local tools, HTTP for remote services
   - **Tradeoffs**: More complex configuration schema

### Important Considerations
- **Server Lifecycle**: Start MCP servers on gateway startup, stop on shutdown
- **Error Handling**: MCP server failures shouldn't crash gateway
- **Environment Variables**: Securely expand ${VAR} from system environment
- **Tool Naming**: Avoid conflicts between MCP tools and built-in tools
- **Performance**: Stdio servers add process overhead, HTTP servers add network latency

### Potential Pitfalls
- **npx Dependency**: Requires Node.js/npm installed (document in setup guide)
- **Server Crashes**: MCP servers may crash, need auto-restart mechanism
- **API Key Exposure**: Don't log API keys, use environment variable expansion
- **Path Resolution**: Filesystem server paths must be absolute or properly resolved
- **Windows Compatibility**: Stdio servers may behave differently on Windows

---

## Dependencies

### Blocked By
- Ticket #2: Skills Middleware (skills and MCP tools both integrate with LangGraph tools)

### Blocks
- Ticket #4: WebSearch Tool (may use MCP brave-search instead of custom web tool)

### Parallel Work
- None (sequential Phase 1)

---

## Related Documentation

### Internal Docs
- Analysis: `docs/tickets/001-deepagents-integration-analysis.md`
- Roadmap: `docs/ROADMAP.md`
- Skills ticket: `docs/tickets/005-skills-middleware.md`

### External References
- [langchain-mcp-adapters GitHub](https://github.com/langchain-ai/langchain-mcp-adapters)
- [Model Context Protocol Spec](https://modelcontextprotocol.io/)
- [MCP Server Registry](https://github.com/modelcontextprotocol/servers)
- [LangChain Tools Documentation](https://python.langchain.com/docs/modules/tools/)

---

## Questions & Clarifications

### Open Questions
1. **Question**: Should we auto-install MCP servers (npx packages)?
   - **Options**:
     - A: Auto-install on first use (better UX)
     - B: Require manual installation (more control)
   - **Recommendation**: Manual installation, documented in setup guide

2. **Question**: Should we support MCP server auto-restart on crash?
   - **Context**: stdio servers may crash unexpectedly
   - **Options**:
     - A: Auto-restart with backoff
     - B: Manual restart only
   - **Recommendation**: Future enhancement, start with manual restart

3. **Question**: How to handle MCP tool naming conflicts?
   - **Context**: MCP filesystem has "read_file", but we might have custom read_file tool
   - **Solution**: Prefix MCP tools with server name (e.g., "filesystem.read_file")

### Decisions Needed
1. **Auto-restart policy**: TBD after initial implementation
2. **Tool naming convention**: Prefix with server name (confirmed)

---

## Success Metrics

### Measurable Outcomes
- MCP servers start successfully: 100% of time (if config valid)
- MCP tool execution success rate: >95%
- MCP server startup time: <5 seconds
- Gateway startup time increase: <15%

### Verification Methods
- Unit test pass rate
- E2E test pass rate
- Gateway log analysis (MCP startup messages)
- Performance benchmarks (startup time)

---

## Rollback Plan

### If Something Goes Wrong
1. Set `"mcp_servers": []` in config.json (disable all MCP servers)
2. Restart gateway
3. Agent works without MCP tools (graceful degradation)
4. Investigate MCP server errors in logs

### Monitoring
- Watch gateway logs for MCP server startup failures
- Monitor MCP tool execution errors
- Check MCP server process health
- Warning signs: Server crash loops, tool execution timeouts, permission errors

---

## Timeline

### Estimated Breakdown
- Analysis & Research: 3 hours
- Package Installation: 1 hour
- Configuration Schema: 2 hours
- MCP Client Integration: 4 hours
- Migration Guide: 2 hours
- Testing: 4 hours
- Documentation: 2 hours
- **Total**: 12-16 hours

### Milestones
- [ ] Day 1: Analysis complete, package installed
- [ ] Day 2: Configuration schema defined, client integration started
- [ ] Day 3: MCP client working, migration guide written
- [ ] Day 4: Testing complete, documentation done, PR ready

---

## Post-Completion

### Follow-up Tasks
- [ ] Monitor MCP server stability in production
- [ ] Gather user feedback on MCP tool usefulness
- [ ] Add more MCP servers based on user needs
- [ ] Optimize MCP server startup performance
- [ ] Implement auto-restart mechanism for crashed servers

### Future Enhancements
- **MCP Server Marketplace**: Curated list of recommended servers
- **MCP Tool Analytics**: Track which tools are most used
- **Custom MCP Servers**: Guide for creating custom MCP servers
- **MCP Server Health Dashboard**: Monitor server status, restart manually
