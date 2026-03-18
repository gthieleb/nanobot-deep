# Ticket #8: Human-in-the-Loop (HITL) Integration

**Status**: Pending  
**Priority**: HIGH  
**Phase**: Phase 2 - Features  
**Branch**: `feature/human-in-the-loop`  
**Dependencies**: Ticket #7 (Backends & Sandboxes)  
**Estimated Effort**: 14-18 hours  
**Target Release**: v0.4.0

---

## Objective

Implement human-in-the-loop (HITL) approval flows for tool execution, enabling agents to request user confirmation before executing sensitive operations via Telegram/Slack inline buttons.

---

## Background

### Current State
- No HITL support in nanobot-deep
- All tool execution happens automatically
- No approval mechanism for sensitive operations
- No inline button support in Telegram/Slack handlers
- No pending action queue or timeout handling

### Desired State
- HITL approval flows for tool execution
- Inline buttons in Telegram/Slack for approve/deny
- Configurable approval requirements per tool
- Pending action queue with timeout handling
- Approval/timeout notifications
- Unit tests for HITL logic
- E2E tests for approval flows
- Documentation explaining HITL architecture

### Context from Planning Session
- **Decision**: Implement HITL with Telegram/Slack inline buttons
  - Rationale: Native UX, no external services
  - Alternative: Web-based approval (rejected - unnecessary complexity)
- **Integration Point**: Tool execution layer, Telegram/Slack handlers
- **Priority**: Last item in Phase 2 (completes core UX features)
- **Use Case**: Approve code execution, file writes, API calls

---

## Technical Approach

### Architecture
- **HITL Manager**: Coordinate approval requests and responses
- **Pending Queue**: Track pending approval requests
- **Inline Buttons**: Telegram/Slack approve/deny buttons
- **Timeout Handler**: Handle expired approval requests
- **Notification System**: Alert on approval/denial/timeout

### Implementation Strategy
1. **Research Phase**: Study HITL patterns and Telegram/Slack APIs
2. **Design Phase**: Define HITL protocol and configuration
3. **Core Phase**: Implement HITL manager and pending queue
4. **Telegram Phase**: Implement Telegram inline buttons
5. **Slack Phase**: Implement Slack inline buttons
6. **Integration Phase**: Connect HITL to tool execution
7. **Testing Phase**: Unit + E2E tests for HITL
8. **Documentation Phase**: HITL architecture docs

### Key Decisions
- **Approval UX**: Inline buttons with approve/deny
- **Timeout**: Default 5 minutes, configurable per tool
- **Fallback**: Deny on timeout (safe default)
- **Queue**: In-memory pending queue (no persistence)
- **Configuration**: Per-tool approval requirements

---

## Tasks

### 1. Analysis & Research
- [ ] Task 1.1: Study HITL patterns
  - Focus: Approval flows, pending actions, timeouts
  - Sources: LangGraph HITL, LangChain callbacks, custom implementations
  - Acceptance: Document recommended HITL patterns

- [ ] Task 1.2: Research Telegram inline buttons
  - API: `InlineKeyboardMarkup`, `CallbackQueryHandler`
  - Focus: Button layout, callback handling, edit messages
  - Acceptance: Document Telegram inline button patterns

- [ ] Task 1.3: Research Slack interactive components
  - API: Block Kit, interactive components, action handlers
  - Focus: Button layout, action handling, message updates
  - Acceptance: Document Slack interactive component patterns

- [ ] Task 1.4: Analyze deepagents HITL support
  - Focus: How DeepAgent handles human feedback
  - File: `deepagents` source code
  - Acceptance: Understand deepagents HITL integration

### 2. Design Phase
- [ ] Task 2.1: Define HITL protocol
  - Fields: action_id, tool_name, tool_args, timeout, status
  - File: `src/hitl/protocol.py`
  - Acceptance: Pydantic model for HITL requests

- [ ] Task 2.2: Define HITL configuration schema
  - Fields: require_approval, timeout, auto_approve_safe_tools
  - File: `src/hitl/config.py`
  - Acceptance: Pydantic model for HITL configuration

- [ ] Task 2.3: Design pending queue
  - Features: Add, remove, timeout, cleanup
  - File: `src/hitl/queue.py`
  - Acceptance: Pending queue design document

### 3. Core HITL Implementation
- [ ] Task 3.1: Create HITL manager
  - Features: Request approval, handle response, handle timeout
  - File: `src/hitl/manager.py`
  - Acceptance: HITL manager implementation

- [ ] Task 3.2: Create pending queue
  - Features: Thread-safe queue, timeout tracking, cleanup
  - File: `src/hitl/queue.py`
  - Acceptance: Pending queue implementation

- [ ] Task 3.3: Create timeout handler
  - Features: Periodic cleanup, timeout notifications
  - File: `src/hitl/timeout.py`
  - Acceptance: Timeout handler implementation

- [ ] Task 3.4: Create notification system
  - Features: Notify on approval, denial, timeout
  - File: `src/hitl/notifications.py`
  - Acceptance: Notification system implementation

### 4. Telegram HITL Integration
- [ ] Task 4.1: Create Telegram approval handler
  - Features: Send approval request, handle callback, update message
  - File: `src/hitl/handlers/telegram.py`
  - Acceptance: Telegram approval handler

- [ ] Task 4.2: Add inline buttons
  - Buttons: Approve, Deny (optional: Approve All, Deny All)
  - Layout: Inline keyboard with buttons
  - Acceptance: Inline buttons for approval

- [ ] Task 4.3: Handle callback queries
  - Handler: `CallbackQueryHandler` for button clicks
  - Features: Update message, notify HITL manager
  - Acceptance: Callback query handling

- [ ] Task 4.4: Add approval notifications
  - Messages: "Approved by user", "Denied by user", "Timeout"
  - Acceptance: Approval notification messages

### 5. Slack HITL Integration
- [ ] Task 5.1: Create Slack approval handler
  - Features: Send approval request, handle action, update message
  - File: `src/hitl/handlers/slack.py`
  - Acceptance: Slack approval handler

- [ ] Task 5.2: Add interactive buttons
  - Buttons: Approve, Deny (using Block Kit)
  - Layout: Action block with buttons
  - Acceptance: Interactive buttons for approval

- [ ] Task 5.3: Handle interactive actions
  - Handler: Slack action handler for button clicks
  - Features: Update message, notify HITL manager
  - Acceptance: Interactive action handling

- [ ] Task 5.4: Add approval notifications
  - Messages: "Approved by user", "Denied by user", "Timeout"
  - Acceptance: Approval notification messages

### 6. Tool Execution Integration
- [ ] Task 6.1: Add HITL middleware to tools
  - Integration: Intercept tool execution, request approval
  - File: `src/tools/hitl_middleware.py`
  - Acceptance: HITL middleware for tools

- [ ] Task 6.2: Add tool approval configuration
  - Config: Per-tool approval requirements
  - File: `config.json` schema update
  - Acceptance: Tool approval configuration

- [ ] Task 6.3: Add safe tool auto-approval
  - Config: Auto-approve safe tools (read-only operations)
  - Acceptance: Auto-approval for safe tools

### 7. Gateway Integration
- [ ] Task 7.1: Add HITL to gateway
  - Integration: Enable HITL in message handler
  - File: `src/gateway/__init__.py`
  - Acceptance: Gateway supports HITL

- [ ] Task 7.2: Add HITL configuration
  - Config: Enable/disable HITL, default timeout
  - File: `config.json` schema update
  - Acceptance: HITL configuration in config.json

- [ ] Task 7.3: Add HITL to callback handlers
  - Integration: Telegram callback, Slack action handlers
  - Acceptance: Callback handlers support HITL

### 8. Testing
- [ ] Task 8.1: Unit tests for HITL protocol
  - File: `tests/unit/test_hitl_protocol.py`
  - Coverage: Request parsing, validation, serialization
  - Acceptance: 90%+ coverage for protocol module

- [ ] Task 8.2: Unit tests for HITL manager
  - File: `tests/unit/test_hitl_manager.py`
  - Coverage: Approval flow, timeout, notifications
  - Acceptance: 90%+ coverage for manager

- [ ] Task 8.3: Unit tests for pending queue
  - File: `tests/unit/test_hitl_queue.py`
  - Coverage: Add, remove, timeout, cleanup
  - Acceptance: 90%+ coverage for queue

- [ ] Task 8.4: E2E tests for Telegram HITL
  - File: `tests/e2e/test_hitl_telegram.py`
  - Mark: `@pytest.mark.live`
  - Scenario: Request approval, approve/deny/timeout
  - Acceptance: Live Telegram HITL works

- [ ] Task 8.5: E2E tests for Slack HITL
  - File: `tests/e2e/test_hitl_slack.py`
  - Mark: `@pytest.mark.live`
  - Scenario: Request approval, approve/deny/timeout
  - Acceptance: Live Slack HITL works

### 9. Documentation
- [ ] Task 9.1: Write HITL architecture docs
  - File: `docs/hitl-architecture.md`
  - Content: Protocol, handlers, integration, configuration
  - Acceptance: Complete HITL architecture documentation

- [ ] Task 9.2: Write HITL configuration guide
  - File: `docs/hitl-configuration.md`
  - Content: Enable/disable, per-tool config, timeouts
  - Acceptance: HITL configuration guide

- [ ] Task 9.3: Update README with HITL section
  - Section: HITL support, configuration, UX
  - Acceptance: README includes HITL overview

---

## Deliverables

### Code
- `src/hitl/` directory with:
  - `__init__.py` - Module exports
  - `protocol.py` - HITL request schemas
  - `config.py` - HITL configuration
  - `manager.py` - HITL manager
  - `queue.py` - Pending queue
  - `timeout.py` - Timeout handler
  - `notifications.py` - Notification system
  - `handlers/` - Platform handlers
    - `__init__.py`
    - `telegram.py` - Telegram handler
    - `slack.py` - Slack handler
- `src/tools/hitl_middleware.py` - HITL middleware for tools

### Tests
- `tests/unit/test_hitl_protocol.py`
- `tests/unit/test_hitl_manager.py`
- `tests/unit/test_hitl_queue.py`
- `tests/e2e/test_hitl_telegram.py`
- `tests/e2e/test_hitl_slack.py`

### Documentation
- `docs/hitl-architecture.md` - Architecture documentation
- `docs/hitl-configuration.md` - Configuration guide
- Updated `README.md` - HITL section

### Configuration
- Updated `config.json` schema with HITL section

---

## Acceptance Criteria

### Functional Requirements
- [ ] Tools can request approval before execution
- [ ] Telegram inline buttons show approve/deny options
- [ ] Slack interactive buttons show approve/deny options
- [ ] Approval triggers tool execution
- [ ] Denial prevents tool execution
- [ ] Timeout denies by default
- [ ] Notifications sent on approval/denial/timeout
- [ ] Per-tool approval configuration works

### Non-Functional Requirements
- [ ] Approval request sent within 100ms
- [ ] Timeout handled within configured time
- [ ] Queue cleanup prevents memory leaks
- [ ] Logging captures HITL events
- [ ] Configuration validated on startup

### Quality Requirements
- [ ] Unit test coverage >= 90%
- [ ] E2E tests pass with live platforms
- [ ] All code passes linting (ruff)
- [ ] All code passes type checking (pyright)
- [ ] Documentation is complete and accurate

---

## Testing Strategy

### Unit Tests
- **Protocol**: Request parsing, validation, serialization
- **Manager**: Approval flow, timeout, notifications
- **Queue**: Add, remove, timeout, cleanup
- **Handlers**: Platform-specific button handling

### E2E Tests
- **Telegram Approval**: Request, approve, verify execution
- **Telegram Denial**: Request, deny, verify no execution
- **Telegram Timeout**: Request, wait, verify denial
- **Slack Approval**: Request, approve, verify execution
- **Slack Denial**: Request, deny, verify no execution
- **Slack Timeout**: Request, wait, verify denial

### Verification Steps
1. Run unit tests: `pytest tests/unit/test_hitl*.py -v`
2. Run E2E tests: `pytest tests/e2e/test_hitl*.py -m live -v`
3. Check coverage: `pytest --cov=src/hitl tests/unit/test_hitl*.py`
4. Verify linting: `ruff check src/hitl`
5. Verify types: `pyright src/hitl`

---

## Implementation Notes

### Key Decisions
1. **Inline Buttons**: Native platform buttons for best UX
2. **Timeout**: 5 minutes default, deny on timeout
3. **Auto-Approve**: Safe tools (read-only) auto-approved
4. **Queue**: In-memory, no persistence across restarts

### Pitfalls to Avoid
- **Deadlocks**: Don't block on approval indefinitely
- **Queue Overflow**: Limit pending queue size
- **Stale Approvals**: Handle session changes
- **Race Conditions**: Thread-safe queue operations

### Integration Points
- **Tools**: `src/tools/` HITL middleware
- **Gateway**: `src/gateway/__init__.py` callback handlers
- **Configuration**: `config.json` HITL section

### Dependencies
- `python-telegram-bot` - Telegram inline buttons
- `slack-sdk` - Slack interactive components
- `asyncio` - Async execution
- `pydantic` - Configuration validation

---

## Related Tickets
- **Depends on**: #7 (Backends & Sandboxes) - Phase 2 in progress
- **Enables**: #9-12 (Phase 3) - HITL for parallel agent work
- **Related**: #6 (Streaming Support) - UX during approval

---

## Questions?
- See `AGENTS.md` for ticket workflow
- See `ROADMAP.md` for phase overview
- See `docs/hitl-architecture.md` (after completion) for details

---

Last updated: 2026-03-18
