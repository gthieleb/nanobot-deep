# Ticket #12: Unit Tests

**Status**: Pending  
**Priority**: HIGH  
**Phase**: Phase 3 - User Features  
**Branch**: `tests/agent-subagent-config`  
**Dependencies**: Ticket #8 (Human-in-the-Loop)  
**Estimated Effort**: 8-12 hours  
**Target Release**: v0.5.0

---

## Objective

Implement comprehensive unit tests for agent-subagent configuration, ensuring all configuration paths, middleware, and tools are properly tested with mock-based testing (no live LLM calls).

---

## Background

### Current State
- Some unit tests exist
- Coverage gaps in configuration loading
- No tests for middleware
- No tests for tools
- No tests for A2A configuration
- Inconsistent test patterns

### Desired State
- Comprehensive unit test coverage (>90%)
- Tests for all configuration paths
- Tests for all middleware
- Tests for all tools
- Tests for A2A configuration
- Consistent test patterns
- Mock-based testing (no live LLM)
- CI integration with coverage reporting

### Context from Planning Session
- **Decision**: Mock-based unit tests for all components
  - Rationale: Fast, reliable, no API costs
  - Alternative: Integration tests (rejected - slow, expensive)
- **Priority**: Phase 3 (parallel with other user features)
- **Coverage**: Target 90%+ coverage

---

## Technical Approach

### Testing Strategy
- **Mocking**: Use `unittest.mock` and `pytest-mock`
- **Fixtures**: Shared test fixtures in `conftest.py`
- **Patterns**: Arrange-Act-Assert (AAA)
- **Coverage**: pytest-cov with HTML reports
- **CI**: GitHub Actions with coverage badges

### Test Categories
1. **Configuration Tests**: Config loading, validation, defaults
2. **Middleware Tests**: All middleware with mocked dependencies
3. **Tool Tests**: All tools with mocked LLM calls
4. **A2A Tests**: Agent communication with mocked agents
5. **Utility Tests**: Helper functions and utilities
6. **Integration Tests**: Component interactions (still mocked)

### Implementation Strategy
1. **Setup Phase**: Configure pytest, coverage, mocking
2. **Config Tests**: Test all configuration paths
3. **Middleware Tests**: Test all middleware
4. **Tool Tests**: Test all tools
5. **A2A Tests**: Test agent communication
6. **Utility Tests**: Test utilities
7. **CI Integration**: Add coverage to CI

---

## Tasks

### 1. Test Infrastructure
- [ ] Task 1.1: Configure pytest
  - File: `pyproject.toml` pytest config
  - Settings: Markers, fixtures, coverage
  - Acceptance: pytest configured

- [ ] Task 1.2: Create shared fixtures
  - File: `tests/conftest.py`
  - Fixtures: Mock LLM, mock config, mock tools
  - Acceptance: Shared fixtures available

- [ ] Task 1.3: Configure coverage
  - File: `pyproject.toml` coverage config
  - Settings: Minimum coverage, exclude patterns
  - Acceptance: Coverage configured

- [ ] Task 1.4: Add test commands
  - Commands: `pytest`, `pytest --cov`, `pytest -m unit`
  - File: `Makefile` or `pyproject.toml` scripts
  - Acceptance: Test commands documented

### 2. Configuration Tests
- [ ] Task 2.1: Test config loading
  - File: `tests/unit/test_config_loading.py`
  - Scenarios: Valid config, invalid config, missing config
  - Acceptance: Config loading tests complete

- [ ] Task 2.2: Test config validation
  - File: `tests/unit/test_config_validation.py`
  - Scenarios: Schema validation, type checking, required fields
  - Acceptance: Config validation tests complete

- [ ] Task 2.3: Test config defaults
  - File: `tests/unit/test_config_defaults.py`
  - Scenarios: Missing fields get defaults
  - Acceptance: Config defaults tests complete

- [ ] Task 2.4: Test environment overrides
  - File: `tests/unit/test_config_env.py`
  - Scenarios: Env vars override config
  - Acceptance: Environment override tests complete

### 3. Middleware Tests
- [ ] Task 3.1: Test memory middleware
  - File: `tests/unit/test_middleware_memory.py`
  - Mocks: LLM responses, conversation history
  - Acceptance: Memory middleware tests complete

- [ ] Task 3.2: Test skills middleware
  - File: `tests/unit/test_middleware_skills.py`
  - Mocks: Skill loading, skill execution
  - Acceptance: Skills middleware tests complete

- [ ] Task 3.3: Test MCP middleware
  - File: `tests/unit/test_middleware_mcp.py`
  - Mocks: MCP server connections, tool calls
  - Acceptance: MCP middleware tests complete

- [ ] Task 3.4: Test A2A middleware
  - File: `tests/unit/test_middleware_a2a.py`
  - Mocks: Agent communication, task routing
  - Acceptance: A2A middleware tests complete

- [ ] Task 3.5: Test backend middleware
  - File: `tests/unit/test_middleware_backend.py`
  - Mocks: Backend execution, resource limits
  - Acceptance: Backend middleware tests complete

- [ ] Task 3.6: Test HITL middleware
  - File: `tests/unit/test_middleware_hitl.py`
  - Mocks: Approval requests, responses
  - Acceptance: HITL middleware tests complete

### 4. Tool Tests
- [ ] Task 4.1: Test web search tool
  - File: `tests/unit/test_tool_websearch.py`
  - Mocks: Search API responses
  - Acceptance: WebSearch tool tests complete

- [ ] Task 4.2: Test delegate tool
  - File: `tests/unit/test_tool_delegate.py`
  - Mocks: Sub-agent execution, result aggregation
  - Acceptance: Delegate tool tests complete

- [ ] Task 4.3: Test todo tools
  - File: `tests/unit/test_tool_todo.py`
  - Mocks: Todo store operations
  - Acceptance: Todo tool tests complete

- [ ] Task 4.4: Test generate image tool
  - File: `tests/unit/test_tool_generate_image.py`
  - Mocks: DALL-E API responses
  - Acceptance: Generate image tool tests complete

### 5. A2A Tests
- [ ] Task 5.1: Test A2A protocol
  - File: `tests/unit/test_a2a_protocol.py`
  - Scenarios: Message creation, parsing, validation
  - Acceptance: A2A protocol tests complete

- [ ] Task 5.2: Test A2A router
  - File: `tests/unit/test_a2a_router.py`
  - Scenarios: Task routing, capability matching
  - Acceptance: A2A router tests complete

- [ ] Task 5.3: Test A2A server
  - File: `tests/unit/test_a2a_server.py`
  - Mocks: Task execution, result aggregation
  - Acceptance: A2A server tests complete

- [ ] Task 5.4: Test A2A client
  - File: `tests/unit/test_a2a_client.py`
  - Mocks: Task reception, execution, response
  - Acceptance: A2A client tests complete

### 6. Backend Tests
- [ ] Task 6.1: Test local backend
  - File: `tests/unit/test_backend_local.py`
  - Scenarios: Execution, error handling
  - Acceptance: Local backend tests complete

- [ ] Task 6.2: Test local sandbox
  - File: `tests/unit/test_backend_local_sandbox.py`
  - Scenarios: Isolation, resource limits, timeout
  - Acceptance: Local sandbox tests complete

- [ ] Task 6.3: Test backend manager
  - File: `tests/unit/test_backend_manager.py`
  - Scenarios: Selection, initialization, switching
  - Acceptance: Backend manager tests complete

### 7. Streaming Tests
- [ ] Task 7.1: Test streaming buffer
  - File: `tests/unit/test_streaming_buffer.py`
  - Scenarios: Accumulation, thresholds, flush
  - Acceptance: Streaming buffer tests complete

- [ ] Task 7.2: Test streaming manager
  - File: `tests/unit/test_streaming_manager.py`
  - Mocks: Stream chunks, rate limiter
  - Acceptance: Streaming manager tests complete

- [ ] Task 7.3: Test rate limiter
  - File: `tests/unit/test_streaming_rate_limiter.py`
  - Scenarios: Token bucket, backoff
  - Acceptance: Rate limiter tests complete

### 8. HITL Tests
- [ ] Task 8.1: Test HITL manager
  - File: `tests/unit/test_hitl_manager.py`
  - Mocks: Approval requests, responses
  - Acceptance: HITL manager tests complete

- [ ] Task 8.2: Test HITL queue
  - File: `tests/unit/test_hitl_queue.py`
  - Scenarios: Add, remove, timeout, cleanup
  - Acceptance: HITL queue tests complete

### 9. Media Tests
- [ ] Task 9.1: Test image processor
  - File: `tests/unit/test_media_image.py`
  - Mocks: Vision model responses
  - Acceptance: Image processor tests complete

- [ ] Task 9.2: Test audio processor
  - File: `tests/unit/test_media_audio.py`
  - Mocks: Whisper API responses
  - Acceptance: Audio processor tests complete

- [ ] Task 9.3: Test document processors
  - File: `tests/unit/test_media_documents.py`
  - Mocks: File parsing libraries
  - Acceptance: Document processor tests complete

### 10. CI Integration
- [ ] Task 10.1: Add coverage to CI
  - File: `.github/workflows/ci-cd.yml`
  - Features: Run tests, report coverage, fail on low coverage
  - Acceptance: Coverage in CI pipeline

- [ ] Task 10.2: Add coverage badge
  - Badge: Coverage percentage in README
  - Acceptance: Coverage badge in README

- [ ] Task 10.3: Add coverage artifacts
  - Artifacts: HTML coverage report
  - Acceptance: Coverage artifacts uploaded

### 11. Documentation
- [ ] Task 11.1: Write testing guide
  - File: `docs/testing-guide.md`
  - Content: How to run tests, write tests, patterns
  - Acceptance: Testing guide complete

- [ ] Task 11.2: Update README with testing section
  - Section: How to run tests, coverage requirements
  - Acceptance: README includes testing info

---

## Deliverables

### Tests
- `tests/unit/test_config_*.py` - Configuration tests
- `tests/unit/test_middleware_*.py` - Middleware tests
- `tests/unit/test_tool_*.py` - Tool tests
- `tests/unit/test_a2a_*.py` - A2A tests
- `tests/unit/test_backend_*.py` - Backend tests
- `tests/unit/test_streaming_*.py` - Streaming tests
- `tests/unit/test_hitl_*.py` - HITL tests
- `tests/unit/test_media_*.py` - Media tests
- `tests/conftest.py` - Shared fixtures

### Documentation
- `docs/testing-guide.md` - Testing guide
- Updated `README.md` - Testing section

### CI Integration
- Updated `.github/workflows/ci-cd.yml` - Coverage in CI

---

## Acceptance Criteria

### Coverage Requirements
- [ ] Overall coverage >= 90%
- [ ] Configuration coverage >= 95%
- [ ] Middleware coverage >= 90%
- [ ] Tool coverage >= 90%
- [ ] A2A coverage >= 85%
- [ ] No uncovered branches in critical paths

### Quality Requirements
- [ ] All tests pass
- [ ] No flaky tests
- [ ] Mock-based (no live API calls)
- [ ] Fast execution (<30 seconds total)
- [ ] Clear test names and descriptions

### CI Requirements
- [ ] Coverage runs in CI
- [ ] CI fails on coverage drop
- [ ] Coverage badge in README
- [ ] Coverage artifacts uploaded

---

## Implementation Notes

### Key Decisions
1. **Mocking**: Use pytest-mock for all external dependencies
2. **Fixtures**: Shared fixtures for common test setup
3. **Coverage**: 90% minimum, 95% for critical paths
4. **Speed**: All tests must complete in <30 seconds

### Pitfalls to Avoid
- **Live API Calls**: Never call real APIs in unit tests
- **Flaky Tests**: Use deterministic mocks
- **Slow Tests**: Keep tests fast
- **Coverage Gaming**: Don't skip complex scenarios

---

## Related Tickets
- **Depends on**: #8 (Human-in-the-Loop) - Phase 2 complete
- **Parallel with**: #9, #10, #11 (Phase 3)
- **Related**: All tickets - tests validate all features

---

Last updated: 2026-03-18
