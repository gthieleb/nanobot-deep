# Ticket #6: Streaming Support

**Status**: Pending  
**Priority**: HIGH  
**Phase**: Phase 2 - Features  
**Branch**: `feature/streaming-support`  
**Dependencies**: Ticket #5 (A2A Integration)  
**Estimated Effort**: 12-16 hours  
**Target Release**: v0.4.0

---

## Objective

Implement progressive message streaming from LLM to Telegram/Slack, providing real-time feedback as the agent generates responses instead of waiting for complete responses.

---

## Background

### Current State
- No streaming support in nanobot-deep
- Users wait for complete LLM response before seeing any output
- Poor UX for long-running tasks
- No typing indicators or progress feedback
- Gateway waits for full response before sending

### Desired State
- Progressive streaming of LLM responses to Telegram/Slack
- Real-time updates as agent generates content
- Typing indicators during processing
- Message updates (edit existing message) vs new messages
- Graceful handling of stream interruptions
- Configuration for streaming behavior
- Unit tests for streaming logic
- E2E tests for streaming UX
- Documentation explaining streaming architecture

### Context from Planning Session
- **Decision**: Stream to Telegram/Slack with message edits
  - Rationale: Best UX, no message spam
  - Alternative: Chunk-based new messages (rejected - spammy)
- **Integration Point**: Gateway message handler
- **Priority**: First item in Phase 2 (highest UX impact)
- **Telegram API**: Use `editMessageText` for updates

---

## Technical Approach

### Architecture
- **Stream Source**: LangChain streaming callback or async iterator
- **Stream Buffer**: Accumulate chunks until threshold
- **Update Strategy**: Edit existing message at intervals
- **Rate Limiting**: Respect Telegram/Slack API rate limits
- **Error Recovery**: Handle stream interruptions gracefully

### Implementation Strategy
1. **Research Phase**: Study LangChain streaming and Telegram/Slack APIs
2. **Design Phase**: Define streaming protocol and update strategy
3. **Core Phase**: Implement streaming infrastructure
4. **Integration Phase**: Connect streaming to gateway
5. **Polish Phase**: Add typing indicators and progress feedback
6. **Testing Phase**: Unit + E2E tests for streaming
7. **Documentation Phase**: Streaming architecture docs

### Key Decisions
- **Update Method**: Edit existing message (not create new)
- **Update Interval**: Every 500ms or 100 characters (configurable)
- **Rate Limiting**: Respect API limits (Telegram: 30 edits/sec)
- **Fallback**: Non-streaming mode for unsupported models
- **Content Strategy**: Accumulate until meaningful chunk

---

## Tasks

### 1. Analysis & Research
- [ ] Task 1.1: Study LangChain streaming API
  - Focus: `astream`, `astream_events`, callback handlers
  - Acceptance: Understand LangChain streaming patterns

- [ ] Task 1.2: Research Telegram streaming approach
  - API: `editMessageText`, rate limits, best practices
  - Focus: Message update strategy, error handling
  - Acceptance: Document Telegram streaming patterns

- [ ] Task 1.3: Research Slack streaming approach
  - API: `chat.update`, rate limits, best practices
  - Focus: Message update strategy, error handling
  - Acceptance: Document Slack streaming patterns

- [ ] Task 1.4: Analyze deepagents streaming support
  - Focus: How DeepAgent handles streaming
  - File: `deepagents` source code
  - Acceptance: Understand deepagents streaming integration

### 2. Design Phase
- [ ] Task 2.1: Define streaming protocol
  - Fields: chunk_type, content, is_final, metadata
  - File: `src/streaming/protocol.py`
  - Acceptance: Pydantic model for stream chunks

- [ ] Task 2.2: Design update strategy
  - Rules: When to update, how much content, rate limiting
  - File: `src/streaming/strategy.py`
  - Acceptance: Update strategy with configuration

- [ ] Task 2.3: Design error recovery
  - Scenarios: Connection loss, API errors, timeout
  - File: `src/streaming/recovery.py`
  - Acceptance: Error recovery strategy documented

### 3. Core Streaming Implementation
- [ ] Task 3.1: Create stream buffer
  - Features: Accumulate chunks, threshold detection, flush
  - File: `src/streaming/buffer.py`
  - Acceptance: Stream buffer with configurable thresholds

- [ ] Task 3.2: Create stream manager
  - Features: Start stream, handle chunks, finalize, error handling
  - File: `src/streaming/manager.py`
  - Acceptance: Stream manager with lifecycle hooks

- [ ] Task 3.3: Create rate limiter
  - Features: Token bucket, configurable rate, backoff
  - File: `src/streaming/rate_limiter.py`
  - Acceptance: Rate limiter for API compliance

- [ ] Task 3.4: Create content formatter
  - Features: Markdown escaping, truncation, formatting
  - File: `src/streaming/formatter.py`
  - Acceptance: Content formatter for platform compatibility

### 4. Telegram Integration
- [ ] Task 4.1: Create Telegram stream handler
  - Features: Send initial message, edit updates, finalize
  - File: `src/streaming/handlers/telegram.py`
  - Acceptance: Telegram streaming handler

- [ ] Task 4.2: Add typing indicator support
  - API: `sendChatAction` with `typing`
  - Features: Start/stop typing indicator
  - Acceptance: Typing indicator during streaming

- [ ] Task 4.3: Handle Telegram rate limits
  - Rate: 30 edits per second per chat
  - Features: Rate limiting, backoff, error handling
  - Acceptance: Graceful handling of rate limits

### 5. Slack Integration
- [ ] Task 5.1: Create Slack stream handler
  - Features: Send initial message, edit updates, finalize
  - File: `src/streaming/handlers/slack.py`
  - Acceptance: Slack streaming handler

- [ ] Task 5.2: Handle Slack rate limits
  - Rate: Varies by workspace, respect headers
  - Features: Rate limiting, backoff, error handling
  - Acceptance: Graceful handling of rate limits

- [ ] Task 5.3: Add Slack typing indicator
  - API: Using app mentions or reactions
  - Acceptance: Slack typing indicator (if supported)

### 6. Gateway Integration
- [ ] Task 6.1: Add streaming to gateway
  - File: `src/gateway/__init__.py`
  - Integration: Enable streaming mode in message handler
  - Acceptance: Gateway uses streaming for responses

- [ ] Task 6.2: Add streaming configuration
  - File: `config.json` schema
  - Config: Enable/disable, thresholds, intervals
  - Acceptance: Streaming configuration with defaults

- [ ] Task 6.3: Add fallback for non-streaming
  - Scenarios: Unsupported models, disabled streaming
  - Acceptance: Graceful fallback to non-streaming mode

### 7. Testing
- [ ] Task 7.1: Unit tests for streaming protocol
  - File: `tests/unit/test_streaming_protocol.py`
  - Coverage: Chunk parsing, validation, serialization
  - Acceptance: 90%+ coverage for protocol module

- [ ] Task 7.2: Unit tests for stream buffer
  - File: `tests/unit/test_streaming_buffer.py`
  - Coverage: Accumulation, thresholds, flush
  - Acceptance: 90%+ coverage for buffer module

- [ ] Task 7.3: Unit tests for rate limiter
  - File: `tests/unit/test_streaming_rate_limiter.py`
  - Coverage: Token bucket, backoff, rate limiting
  - Acceptance: 90%+ coverage for rate limiter

- [ ] Task 7.4: E2E tests for Telegram streaming
  - File: `tests/e2e/test_streaming_telegram.py`
  - Mark: `@pytest.mark.live`
  - Scenario: Stream response, verify updates
  - Acceptance: Live Telegram streaming works

- [ ] Task 7.5: E2E tests for Slack streaming
  - File: `tests/e2e/test_streaming_slack.py`
  - Mark: `@pytest.mark.live`
  - Scenario: Stream response, verify updates
  - Acceptance: Live Slack streaming works

### 8. Documentation
- [ ] Task 8.1: Write streaming architecture docs
  - File: `docs/streaming-architecture.md`
  - Content: Protocol, handlers, integration, rate limits
  - Acceptance: Complete streaming architecture documentation

- [ ] Task 8.2: Write streaming configuration guide
  - File: `docs/streaming-configuration.md`
  - Content: Enable/disable, thresholds, platform-specific
  - Acceptance: Streaming configuration guide

- [ ] Task 8.3: Update README with streaming section
  - Section: Streaming support, configuration, UX
  - Acceptance: README includes streaming overview

---

## Deliverables

### Code
- `src/streaming/` directory with:
  - `__init__.py` - Module exports
  - `protocol.py` - Stream chunk schemas
  - `strategy.py` - Update strategy
  - `buffer.py` - Stream buffer
  - `manager.py` - Stream manager
  - `rate_limiter.py` - Rate limiter
  - `formatter.py` - Content formatter
  - `recovery.py` - Error recovery
  - `handlers/` - Platform handlers
    - `__init__.py`
    - `telegram.py` - Telegram handler
    - `slack.py` - Slack handler

### Tests
- `tests/unit/test_streaming_protocol.py`
- `tests/unit/test_streaming_buffer.py`
- `tests/unit/test_streaming_rate_limiter.py`
- `tests/e2e/test_streaming_telegram.py`
- `tests/e2e/test_streaming_slack.py`

### Configuration
- Updated `config.json` schema with streaming section

### Documentation
- `docs/streaming-architecture.md` - Architecture documentation
- `docs/streaming-configuration.md` - Configuration guide
- Updated `README.md` - Streaming section

---

## Acceptance Criteria

### Functional Requirements
- [ ] Responses stream progressively to Telegram
- [ ] Responses stream progressively to Slack
- [ ] Message edits replace content (not spam new messages)
- [ ] Typing indicator shows during streaming
- [ ] Rate limits are respected
- [ ] Stream interruptions are handled gracefully
- [ ] Fallback to non-streaming works for unsupported models
- [ ] Configuration controls streaming behavior

### Non-Functional Requirements
- [ ] Streaming latency <500ms per update
- [ ] Rate limiting prevents API throttling
- [ ] Memory usage stays bounded during streaming
- [ ] Error recovery prevents message loss
- [ ] Logging captures streaming events

### Quality Requirements
- [ ] Unit test coverage >= 90%
- [ ] E2E tests pass with live platforms
- [ ] All code passes linting (ruff)
- [ ] All code passes type checking (pyright)
- [ ] Documentation is complete and accurate

---

## Testing Strategy

### Unit Tests
- **Protocol**: Chunk parsing, validation, serialization
- **Buffer**: Accumulation, thresholds, flush behavior
- **Rate Limiter**: Token bucket, backoff, rate limiting
- **Formatter**: Markdown escaping, truncation
- **Handlers**: Platform-specific message handling

### E2E Tests
- **Telegram Streaming**: Send message, verify progressive updates
- **Slack Streaming**: Send message, verify progressive updates
- **Rate Limiting**: Verify no throttling errors
- **Error Recovery**: Interrupt stream, verify graceful handling
- **Fallback**: Non-streaming mode works correctly

### Verification Steps
1. Run unit tests: `pytest tests/unit/test_streaming*.py -v`
2. Run E2E tests: `pytest tests/e2e/test_streaming*.py -m live -v`
3. Check coverage: `pytest --cov=src/streaming tests/unit/test_streaming*.py`
4. Verify linting: `ruff check src/streaming`
5. Verify types: `pyright src/streaming`

---

## Implementation Notes

### Key Decisions
1. **Message Edits**: Update existing message, not create new ones
2. **Update Interval**: 500ms minimum between updates
3. **Rate Limiting**: Respect platform limits strictly
4. **Typing Indicator**: Show during entire stream duration

### Pitfalls to Avoid
- **Rate Limit Violations**: Strict rate limiting required
- **Message Spam**: Don't create new messages for updates
- **Broken Markdown**: Escape content properly
- **Lost Context**: Preserve message state across edits

### Integration Points
- **Gateway**: `src/gateway/__init__.py`
- **DeepAgent**: Streaming callback or async iterator
- **Configuration**: `config.json` streaming section

### Dependencies
- `langchain-core` - LangChain streaming
- `python-telegram-bot` - Telegram API
- `slack-sdk` - Slack API
- `asyncio` - Async execution

---

## Related Tickets
- **Depends on**: #5 (A2A Integration) - Phase 1 complete
- **Enables**: #7 (Backends & Sandboxes) - Better UX for long tasks
- **Related**: #8 (Human-in-the-Loop) - Streaming during approvals

---

## Questions?
- See `AGENTS.md` for ticket workflow
- See `ROADMAP.md` for phase overview
- See `docs/streaming-architecture.md` (after completion) for details

---

Last updated: 2026-03-18
