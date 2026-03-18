# Ticket #4: WebSearch Tool Configuration

**Status**: Pending  
**Priority**: MEDIUM  
**Phase**: Phase 1 - Tool Integration  
**Branch**: `feature/websearch-tool`  
**Dependencies**: Ticket #3 (MCP Integration)  
**Estimated Effort**: 6-8 hours  
**Target Release**: v0.3.0

---

## Objective

Configure web search tool for DeepAgent, decide between nanobot's custom `tools/web.py` and deepagents/MCP alternatives, configure API keys, and test web search activation in Telegram/Slack.

---

## Background

### Current State
- nanobot has custom web search implementation: `nanobot/tools/web.py`
- No web search configured in nanobot-deep
- Unknown: What search API does nanobot/tools/web.py use?
- MCP brave-search server available (from Ticket #3)
- No API keys configured for web search

### Desired State
- Web search tool configured and working
- API key configured in config.json (environment variable)
- Decision documented: Use nanobot tools/web.py OR migrate to deepagents/MCP
- Web search works via Telegram/Slack commands
- Unit tests for web search configuration
- E2E tests for web search execution
- Documentation explaining web search setup and usage

### Context from Planning Session
- **Decision Needed**: Evaluate nanobot vs deepagents/MCP web search
  - Option A: Use nanobot/tools/web.py (existing, proven)
  - Option B: Use MCP brave-search (from Ticket #3)
  - Option C: Use deepagents native web search (if exists)
- **Configuration**: API key in config.json, not hardcoded
- **Priority**: Medium priority (after core middleware)

---

## Technical Approach

### Architecture
- **Search Provider**: TBD (Brave, Google, Bing, SerpAPI, etc.)
- **Implementation**: TBD (nanobot custom vs MCP vs deepagents)
- **Configuration**: API key in config.json with environment variable
- **Integration Point**: LangGraph tool binding

### Implementation Strategy
1. **Analysis Phase**: Review nanobot/tools/web.py implementation
2. **Comparison Phase**: Compare nanobot vs MCP vs deepagents web search
3. **Decision Phase**: Choose implementation approach
4. **Configuration Phase**: Add API key config to schema
5. **Integration Phase**: Wire web search tool to DeepAgent
6. **Testing Phase**: Unit + E2E tests
7. **Documentation Phase**: Setup guide and usage examples

### Key Decisions
- **Search Provider**: TBD (depends on cost, API limits, quality)
- **Implementation**: TBD (nanobot vs MCP vs deepagents)
- **API Key Storage**: Environment variable referenced in config.json
- **Search Limits**: Rate limiting, result count limits

---

## Tasks

### 1. Analysis & Research
- [ ] Task 1.1: Analyze nanobot/tools/web.py
  - File: `nanobot/tools/web.py`
  - Questions:
    - What search API does it use? (Brave, Google, SerpAPI, etc.)
    - How is it configured? (API key, parameters)
    - What features does it provide? (basic search, image search, etc.)
  - Acceptance: Document nanobot web search capabilities

- [ ] Task 1.2: Review MCP brave-search server
  - MCP Server: `@modelcontextprotocol/server-brave-search`
  - API: Brave Search API (https://brave.com/search/api/)
  - Features: Web search, news, images
  - Pricing: Free tier available, paid tiers for higher volume
  - Acceptance: Understand MCP brave-search capabilities

- [ ] Task 1.3: Research deepagents web search
  - Check: Does deepagents have native web search tool?
  - Sources: deepagents docs, LangChain web search tools
  - Alternatives: LangChain SerpAPI, Google Search, DuckDuckGo
  - Acceptance: List all available web search options

### 2. Comparison & Decision
- [ ] Task 2.1: Create comparison matrix
  - Criteria: Cost, API limits, quality, ease of setup, maintenance
  - Options: nanobot custom, MCP brave-search, deepagents/LangChain tools
  - Example matrix:
    ```markdown
    | Feature | Nanobot Custom | MCP Brave | LangChain SerpAPI |
    |---------|---------------|-----------|-------------------|
    | Cost | TBD | Free tier | Paid only |
    | Setup | Port code | Configure MCP | Install package |
    | Maintenance | Manual | MCP upstream | LangChain upstream |
    | Features | TBD | Web, news, images | Web, news, images |
    ```
  - Acceptance: Clear comparison for decision making

- [ ] Task 2.2: Make implementation decision
  - Consider: User preference, maintenance burden, cost
  - Decision factors:
    - Ease of setup (favor MCP if already integrated)
    - API cost (favor free tier options)
    - Feature completeness
    - Long-term maintenance
  - Document: Decision rationale in this ticket
  - Acceptance: Clear decision documented

### 3. Configuration
- [ ] Task 3.1: Add web search config to schema
  - File: `nanobot_deep/config/schema.py`
  - Add (if using MCP): No changes (use MCP config from Ticket #3)
  - Add (if using custom): `WebSearchConfig` class
    ```python
    class WebSearchConfig(BaseModel):
        provider: Literal["brave", "google", "serpapi", "duckduckgo"]
        api_key: Optional[str] = None  # For paid APIs
        max_results: int = 10
        enabled: bool = True
    ```

- [ ] Task 3.2: Add API key to config.json
  - File: User's `~/.nanobot/config.json`
  - Example (if using MCP brave-search):
    ```json
    {
      "mcp_servers": [
        {
          "name": "brave-search",
          "type": "stdio",
          "command": "npx -y @modelcontextprotocol/server-brave-search",
          "env": {
            "BRAVE_API_KEY": "${BRAVE_API_KEY}"
          },
          "enabled": true
        }
      ]
    }
    ```
  - Example (if using custom tool):
    ```json
    {
      "web_search": {
        "provider": "brave",
        "api_key": "${BRAVE_API_KEY}",
        "max_results": 10
      }
    }
    ```

- [ ] Task 3.3: Document API key setup
  - File: `docs/WEBSEARCH_SETUP.md`
  - Steps:
    1. Get API key from provider (e.g., Brave Search API)
    2. Set environment variable: `export BRAVE_API_KEY=xxx`
    3. Add to config.json (as shown above)
    4. Restart gateway
  - Include: Links to API key signup pages

### 4. Implementation
- [ ] Task 4.1: Implement web search integration (depends on decision)
  - **If MCP brave-search chosen**:
    - No code changes (already done in Ticket #3)
    - Just enable brave-search MCP server in config
  
  - **If nanobot tools/web.py chosen**:
    - Create: `nanobot_deep/tools/web_search.py`
    - Port: Logic from `nanobot/tools/web.py`
    - Adapt: Use config from config.json
    - Bind: To DeepAgent as LangChain tool
  
  - **If LangChain tool chosen**:
    - Install: Package (e.g., `langchain-community`)
    - Import: Web search tool (e.g., SerpAPIWrapper)
    - Configure: API key from config
    - Bind: To DeepAgent

- [ ] Task 4.2: Add error handling
  - Handle: API key missing or invalid
  - Handle: API rate limit exceeded
  - Handle: Search API downtime
  - Handle: Invalid search queries
  - Acceptance: Graceful error messages to user

### 5. Testing
- [ ] Task 5.1: Write unit tests
  - File: `tests/unit/test_web_search.py`
  - Test cases:
    1. `test_web_search_config_loading()`: Verify config parses
    2. `test_api_key_expansion()`: Verify ${VAR} expansion works
    3. `test_missing_api_key()`: Handle missing API key gracefully
    4. `test_search_tool_binding()`: Verify tool binds to agent
    5. `test_search_result_parsing()`: Verify results parse correctly
  - Mock: Search API responses
  - Coverage: 80%+

- [ ] Task 5.2: Write E2E tests
  - File: `tests/e2e/test_web_search.py`
  - Test scenarios:
    1. Send Telegram message: "Search for Python tutorials"
    2. Verify: Web search tool executes
    3. Verify: Response contains search results (titles, URLs)
    4. Test: Rate limiting (multiple searches in quick succession)
  - Note: May need to mock search API for CI (avoid costs)
  - Acceptance: E2E tests pass with real or mock API

### 6. Documentation
- [ ] Task 6.1: Update README.md
  - Section: Add "Web Search" section
  - Content:
    - What web search does
    - How to get API key
    - How to configure web search
    - Telegram/Slack usage examples
  - Include: Configuration examples

- [ ] Task 6.2: Create web search setup guide
  - File: `docs/WEBSEARCH_SETUP.md`
  - Sections:
    - API key acquisition (step-by-step with screenshots)
    - Environment variable setup
    - Configuration examples
    - Testing web search
    - Troubleshooting
  - Include: Links to provider docs (Brave, Google, etc.)

---

## Deliverables

### Code Deliverables
- [ ] `nanobot_deep/config/schema.py`: WebSearchConfig (if custom tool)
- [ ] `nanobot_deep/tools/web_search.py`: Web search tool (if custom)
- [ ] User's `~/.nanobot/config.json`: Web search configuration
- [ ] `pyproject.toml`: Dependencies (if needed, e.g., langchain-community)

### Test Deliverables
- [ ] `tests/unit/test_web_search.py`: Unit tests
- [ ] `tests/e2e/test_web_search.py`: E2E tests

### Documentation Deliverables
- [ ] `docs/WEBSEARCH_SETUP.md`: Setup guide with API key instructions
- [ ] README.md: Web Search section
- [ ] Decision document: Implementation choice rationale (in this ticket)

---

## Acceptance Criteria

### Functional Requirements
1. ✅ Web search API key configured in config.json
   - Verification: Cat config.json, see API key (environment variable)
   - Test: `test_api_key_configured()`

2. ✅ Web search tool executes successfully
   - Verification: Ask agent to search, get results
   - Test: `test_web_search_execution()`

3. ✅ Search results returned to user
   - Verification: Telegram response contains URLs and titles
   - Test: `test_search_results_format()`

4. ✅ Implementation decision documented
   - Verification: This ticket has decision rationale section filled
   - Test: Manual review

### Non-Functional Requirements
1. ✅ Performance: Search results returned within 5 seconds
2. ✅ Security: API key not logged or exposed
3. ✅ Cost: Stay within free tier limits (if applicable)

### Testing Requirements
- ✅ Unit test coverage ≥ 80%
- ✅ All E2E tests passing
- ✅ CI/CD pipeline passing (with mocked API)

---

## Testing Strategy

### Unit Tests
**File**: `tests/unit/test_web_search.py`

**Test Cases**:
1. `test_web_search_config_loading()`:
   - Load config.json with web search config
   - Verify WebSearchConfig object created (or MCP config)
   - Check provider, API key, max_results

2. `test_api_key_env_expansion()`:
   - Set: `export BRAVE_API_KEY=test-key`
   - Config: `"api_key": "${BRAVE_API_KEY}"`
   - Verify: Expands to "test-key"

3. `test_missing_api_key_handling()`:
   - Config: API key not set
   - Start gateway
   - Verify: Warning logged, search tool disabled (or uses fallback)

4. `test_search_result_parsing()`:
   - Mock API response: 5 search results
   - Parse results
   - Verify: Titles, URLs, snippets extracted

**Mock Strategy**:
- Mock HTTP requests to search API
- Mock environment variable expansion
- Don't mock config parsing (test real behavior)

### E2E Tests
**File**: `tests/e2e/test_web_search.py`

**Test Scenarios**:
1. **Basic web search**:
   - Send Telegram message: "Search for 'Python asyncio tutorial'"
   - Verify: Agent uses web search tool
   - Verify: Response contains at least 3 results with URLs

2. **Search result quality**:
   - Send: "What is the capital of France?"
   - Verify: Search results mention Paris
   - Verify: Agent synthesizes answer from search results

3. **Rate limiting**:
   - Send 10 search queries rapidly
   - Verify: All succeed (or graceful rate limit handling)
   - Verify: No API key ban

**Verification Steps**:
1. Check gateway logs for web search tool execution
2. Verify Telegram response format (titles, URLs)
3. Check API usage metrics (if available)

---

## Configuration

### Configuration Files
**File**: `~/.nanobot/config.json`

**Option A: MCP Brave Search**
```json
{
  "mcp_servers": [
    {
      "name": "brave-search",
      "type": "stdio",
      "command": "npx -y @modelcontextprotocol/server-brave-search",
      "env": {
        "BRAVE_API_KEY": "${BRAVE_API_KEY}"
      },
      "enabled": true
    }
  ]
}
```

**Option B: Custom Web Search Tool**
```json
{
  "web_search": {
    "provider": "brave",
    "api_key": "${BRAVE_API_KEY}",
    "max_results": 10,
    "safe_search": true,
    "enabled": true
  }
}
```

**Environment Variable**:
```bash
export BRAVE_API_KEY=your-api-key-here
```

**Configuration Options** (if custom tool):
- `provider`: Search provider
  - Type: string
  - Valid values: "brave", "google", "serpapi", "duckduckgo"
  - Required: yes
  - Description: Which search API to use

- `api_key`: API key
  - Type: string
  - Required: depends on provider (Brave requires it, DuckDuckGo doesn't)
  - Description: Search API key (supports ${VAR} expansion)

- `max_results`: Maximum results
  - Type: integer
  - Default: 10
  - Valid range: 1-100
  - Description: Max number of search results to return

- `safe_search`: Safe search filter
  - Type: boolean
  - Default: true
  - Description: Filter explicit content

- `enabled`: Enable web search
  - Type: boolean
  - Default: true
  - Description: Toggle web search on/off

---

## Documentation Updates

### README.md
**Section**: Web Search (after MCP Integration section)

**Content**:
```markdown
## Web Search

Web search enables the agent to search the internet for information.

### Setup

#### 1. Get API Key

Get a Brave Search API key:
1. Visit https://brave.com/search/api/
2. Sign up for free tier (2,000 queries/month)
3. Copy your API key

#### 2. Configure

Set environment variable:
\`\`\`bash
export BRAVE_API_KEY=your-api-key-here
\`\`\`

Add to `~/.nanobot/config.json`:
\`\`\`json
{
  "mcp_servers": [
    {
      "name": "brave-search",
      "type": "stdio",
      "command": "npx -y @modelcontextprotocol/server-brave-search",
      "env": {
        "BRAVE_API_KEY": "${BRAVE_API_KEY}"
      }
    }
  ]
}
\`\`\`

#### 3. Restart Gateway

\`\`\`bash
python -m nanobot_deep.gateways.telegram
\`\`\`

### Usage Example (Telegram)

\`\`\`
User: Search for "Python asyncio best practices"
Bot: I found these resources:
     
     1. Real Python - Async IO in Python: A Complete Walkthrough
        https://realpython.com/async-io-python/
     
     2. Python Docs - Asyncio Official Documentation
        https://docs.python.org/3/library/asyncio.html
     
     3. ...

User: What is the capital of France?
Bot: [Searches web] The capital of France is Paris.
\`\`\`

### Alternative: DuckDuckGo (No API Key)

For testing without API key, use DuckDuckGo:
\`\`\`json
{
  "web_search": {
    "provider": "duckduckgo",
    "max_results": 10
  }
}
\`\`\`

Note: DuckDuckGo has rate limits and may be less reliable than Brave.

### Troubleshooting

- **API key invalid**: Check environment variable is set correctly
- **Rate limit exceeded**: Wait or upgrade to paid tier
- **No results**: Check internet connectivity, API status
- **Slow searches**: Normal (web search takes 2-5 seconds)

For detailed setup, see `docs/WEBSEARCH_SETUP.md`.
```

---

## Implementation Notes

### Key Decisions
1. **Decision**: TBD - Implementation approach (to be decided in Task 2.2)
   - **Options**: nanobot custom vs MCP brave-search vs LangChain tool
   - **Recommendation**: MCP brave-search (if Ticket #3 complete, minimizes new code)
   - **Rationale**: Reuse MCP infrastructure, less maintenance
   - **Alternative**: Custom tool if MCP has limitations

2. **Decision**: Use environment variable for API key (confirmed)
   - **Rationale**: Secure, don't commit secrets to config file
   - **Pattern**: `"api_key": "${BRAVE_API_KEY}"`
   - **Tradeoffs**: User must set env var, but better security

3. **Decision**: Brave Search API as default provider
   - **Rationale**: Free tier available, good quality, official MCP server
   - **Alternative**: DuckDuckGo (no API key, but unreliable)
   - **Alternative**: SerpAPI (excellent quality, but paid only)

### Important Considerations
- **API Costs**: Monitor usage to stay within free tier
- **Rate Limits**: Brave free tier = 2,000 queries/month (~67/day)
- **Search Quality**: Brave quality is good, but may need fallbacks
- **Privacy**: Brave doesn't track searches (privacy-friendly)
- **Caching**: Consider caching search results to reduce API calls

### Potential Pitfalls
- **API Key Exposure**: Never log API key, don't commit to git
- **Rate Limit Bans**: Implement rate limiting on client side
- **API Key Not Set**: Gateway should start (degraded mode) if API key missing
- **Search Timeouts**: Set reasonable timeout (5-10 seconds)
- **Result Formatting**: Ensure results are human-readable in Telegram/Slack

---

## Dependencies

### Blocked By
- Ticket #3: MCP Integration (if using MCP brave-search)

### Blocks
- None

### Parallel Work
- Can work in parallel with Ticket #5 (A2A Integration)

---

## Related Documentation

### Internal Docs
- Analysis: `docs/tickets/001-deepagents-integration-analysis.md`
- MCP ticket: `docs/tickets/006-mcp-integration.md`
- Roadmap: `docs/ROADMAP.md`

### External References
- [Brave Search API Docs](https://brave.com/search/api/)
- [MCP Brave Search Server](https://github.com/modelcontextprotocol/servers/tree/main/src/brave-search)
- [LangChain Search Tools](https://python.langchain.com/docs/integrations/tools/)
- [SerpAPI Documentation](https://serpapi.com/search-api)

---

## Questions & Clarifications

### Open Questions
1. **Question**: Which search provider to use?
   - **Options**: Brave (free tier), Google (paid), SerpAPI (paid), DuckDuckGo (free, unreliable)
   - **Recommendation**: Brave (free tier + good quality)
   - **Action**: Decide in Task 2.2

2. **Question**: Should we cache search results?
   - **Context**: Reduce API calls, improve performance
   - **Options**:
     - A: Cache results for 1 hour
     - B: No caching (always fresh results)
   - **Recommendation**: Future enhancement, start without caching

3. **Question**: How to handle rate limits?
   - **Options**:
     - A: Client-side rate limiting (queue requests)
     - B: Fail gracefully, inform user
   - **Recommendation**: Fail gracefully for now, add queuing later

### Decisions Needed
1. **Implementation approach**: Decide in Task 2.2 (nanobot vs MCP vs LangChain)
2. **Search provider**: Brave (recommended, pending user approval)

---

## Success Metrics

### Measurable Outcomes
- API key configured correctly: 100% of time (if set)
- Web search tool executes successfully: >95%
- Search result quality: >3 relevant results per query
- Search latency: <5 seconds per query

### Verification Methods
- Unit test pass rate
- E2E test pass rate
- User feedback on search quality
- API usage metrics (stay within free tier)

---

## Rollback Plan

### If Something Goes Wrong
1. Disable web search in config:
   - MCP: Set `"enabled": false` for brave-search server
   - Custom: Set `"web_search": {"enabled": false}`
2. Restart gateway
3. Agent works without web search (graceful degradation)
4. Investigate web search errors in logs

### Monitoring
- Watch for API key errors at startup
- Monitor API rate limit warnings
- Check search tool execution success rate
- Warning signs: 401 Unauthorized, 429 Rate Limit, search timeouts

---

## Timeline

### Estimated Breakdown
- Analysis & Research: 2 hours
- Comparison & Decision: 1 hour
- Configuration: 1 hour
- Implementation: 2 hours
- Testing: 2 hours
- Documentation: 1 hour
- **Total**: 6-8 hours

### Milestones
- [ ] Day 1: Analysis complete, decision made
- [ ] Day 2: Implementation done, tests passing
- [ ] Day 3: Documentation complete, PR ready

---

## Post-Completion

### Follow-up Tasks
- [ ] Monitor API usage (stay within free tier)
- [ ] Gather user feedback on search quality
- [ ] Optimize search result formatting
- [ ] Consider adding search result caching
- [ ] Evaluate alternative search providers if needed

### Future Enhancements
- **Image Search**: Add image search capabilities
- **News Search**: Dedicated news search
- **Search Caching**: Cache results to reduce API calls
- **Multi-Provider Fallback**: Try alternative provider if primary fails
- **Search Analytics**: Track which queries are most common
