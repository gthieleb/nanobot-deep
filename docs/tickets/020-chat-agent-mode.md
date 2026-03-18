# Ticket #20: Chat vs Agent Mode Toggle

**Status**: Pending  
**Priority**: MEDIUM  
**Phase**: Phase 3 - User Features  
**Branch**: `feature/chat-agent-mode`  
**Dependencies**: Ticket #19 (Lightweight Gateway)  
**Estimated Effort**: 6-8 hours  
**Target Release**: v0.5.0

---

## Objective

Implement a toggle between Chat mode (simple Q&A, no tools) and Agent mode (full tool execution), allowing users to switch modes per conversation or session.

---

## Background

### Current State
- Agent always runs in full mode with all tools
- No way to disable tools for simple conversations
- Higher latency and cost for simple Q&A
- No mode indicator in UI

### Desired State
- Chat mode: Fast Q&A, no tools, lower cost
- Agent mode: Full tool execution, all capabilities
- Toggle via command or config
- Mode persistence per session
- Mode indicator in responses

### Use Cases
1. **Quick Questions**: User wants fast answer without tool overhead
2. **Privacy Sensitive**: User doesn't want tool execution for sensitive topics
3. **Cost Control**: Reduce API costs for simple queries
4. **Development**: Test agent behavior with/without tools

---

## Technical Approach

### Architecture
- **Mode Enum**: `ChatMode` (chat, agent)
- **Session Store**: Track mode per session
- **Tool Filter**: Conditionally include tools based on mode
- **Toggle Command**: `/mode chat` or `/mode agent`

### Implementation Strategy
1. **Define Modes**: Create mode enum and configuration
2. **Session Tracking**: Store mode per session
3. **Tool Filtering**: Filter tools based on mode
4. **Command Handler**: Add toggle command
5. **UI Indicators**: Show mode in responses

---

## Tasks

### 1. Define Modes
- [ ] Task 1.1: Create ChatMode enum
  - File: `src/modes/types.py`
  - Values: CHAT, AGENT
  - Acceptance: Mode enum created

- [ ] Task 1.2: Create mode configuration
  - File: `src/modes/config.py`
  - Settings: default_mode, allowed_modes, persistence
  - Acceptance: Mode config schema

### 2. Session Tracking
- [ ] Task 2.1: Add mode to session state
  - File: `src/session/state.py`
  - Field: `chat_mode: ChatMode`
  - Acceptance: Mode in session state

- [ ] Task 2.2: Create mode persistence
  - Storage: SQLite session store
  - Acceptance: Mode persists across restarts

### 3. Tool Filtering
- [ ] Task 3.1: Create tool filter middleware
  - File: `src/middleware/tool_filter.py`
  - Logic: Filter tools based on mode
  - Acceptance: Tools filtered in chat mode

- [ ] Task 3.2: Update DeepAgent to use filter
  - Integration: Apply filter before tool binding
  - Acceptance: Agent respects mode

### 4. Command Handler
- [ ] Task 4.1: Add `/mode` command
  - Command: `/mode [chat|agent]`
  - Response: Confirm mode change
  - Acceptance: Command works

- [ ] Task 4.2: Add mode status command
  - Command: `/mode` (no args shows current)
  - Acceptance: Status shows current mode

### 5. UI Indicators
- [ ] Task 5.1: Add mode indicator to responses
  - Indicator: "[Chat]" or "[Agent]" prefix
  - Acceptance: Mode shown in responses

### 6. Testing
- [ ] Task 6.1: Unit tests for mode logic
  - File: `tests/unit/test_modes.py`
  - Acceptance: 90%+ coverage

- [ ] Task 6.2: E2E tests for mode toggle
  - File: `tests/e2e/test_modes.py`
  - Acceptance: Mode toggle works live

### 7. Documentation
- [ ] Task 7.1: Document modes in README
  - Section: Chat vs Agent mode
  - Acceptance: Documentation complete

---

## Deliverables

### Code
- `src/modes/` - Mode management module
- `src/middleware/tool_filter.py` - Tool filtering

### Tests
- `tests/unit/test_modes.py`
- `tests/e2e/test_modes.py`

### Documentation
- Updated `README.md`

---

## Acceptance Criteria

### Functional Requirements
- [ ] Chat mode disables all tools
- [ ] Agent mode enables all tools
- [ ] Toggle works via command
- [ ] Mode persists per session
- [ ] Mode indicator shows

### Quality Requirements
- [ ] Unit test coverage >= 90%
- [ ] E2E tests pass
- [ ] No performance regression

---

## Related Tickets
- **Depends on**: #19 (Lightweight Gateway)
- **Related**: #11 (Human-in-the-Loop) - HITL only in agent mode

---

Last updated: 2026-03-18
