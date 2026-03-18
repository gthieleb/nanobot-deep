# Ticket #21: Heartbeat Mode Integration

**Status**: Pending  
**Priority**: MEDIUM  
**Phase**: Phase 3 - User Features  
**Branch**: `feature/heartbeat-mode`  
**Dependencies**: Ticket #19 (Lightweight Gateway)  
**Estimated Effort**: 8-10 hours  
**Target Release**: v0.5.0

---

## Objective

Integrate upstream nanobot's HeartbeatService into nanobot-deep, enabling periodic agent wake-ups to check for tasks defined in `HEARTBEAT.md`.

---

## Background

### Current State
- No heartbeat support in nanobot-deep
- Agent only responds to incoming messages
- No periodic task checking
- No background agent activation

### Upstream Implementation
- **File**: `nanobot/heartbeat/service.py` (~185 lines)
- **Purpose**: Periodic agent wake-up to check for tasks
- **Mechanism**: Reads `HEARTBEAT.md`, LLM decides if action needed
- **Tool**: Virtual `heartbeat` tool with `skip`/`run` actions

### How It Works
1. Service wakes every N seconds (default: 30 min)
2. Reads `HEARTBEAT.md` from workspace
3. LLM decides via tool call: `skip` (nothing to do) or `run` (has tasks)
4. If `run`, executes task and optionally notifies user

### Desired State
- HeartbeatService integrated with DeepAgent
- `HEARTBEAT.md` support
- Configurable interval
- Task notification via channels
- Post-run evaluation (should notify?)

---

## Technical Approach

### Architecture
```
HeartbeatService (upstream)
       │
       │ on_execute callback
       ▼
  DeepAgent.process()
       │
       ▼
  OutboundMessage
       │
       ▼
  ChannelManager.deliver()
```

### Integration Strategy
1. **Reuse Upstream**: Import `HeartbeatService` from nanobot
2. **Connect to DeepAgent**: Pass `on_execute` callback
3. **Connect to Channels**: Pass `on_notify` callback
4. **Configuration**: Add heartbeat config to `deepagents.json`

---

## Tasks

### 1. Analysis Phase
- [ ] Task 1.1: Analyze upstream HeartbeatService
  - File: `nanobot/heartbeat/service.py`
  - Focus: Callbacks, configuration, lifecycle
  - Acceptance: Understand integration points

- [ ] Task 1.2: Identify DeepAgent integration
  - Method: How to call `agent.process()` from heartbeat
  - Acceptance: Integration pattern documented

### 2. Integration Phase
- [ ] Task 2.1: Import HeartbeatService
  - Import: `from nanobot.heartbeat import HeartbeatService`
  - File: `src/heartbeat/manager.py`
  - Acceptance: Service imported

- [ ] Task 2.2: Create on_execute callback
  - Callback: Process heartbeat task with DeepAgent
  - File: `src/heartbeat/callbacks.py`
  - Acceptance: Callback connects to agent

- [ ] Task 2.3: Create on_notify callback
  - Callback: Send result to configured channel
  - Acceptance: Notification callback works

- [ ] Task 2.4: Add heartbeat to gateway lifecycle
  - Integration: Start/stop with gateway
  - File: `src/gateway.py`
  - Acceptance: Heartbeat lifecycle managed

### 3. Configuration Phase
- [ ] Task 3.1: Add heartbeat config schema
  - File: `src/config/schema.py`
  - Fields: enabled, interval_s, notify_channel
  - Acceptance: Config schema defined

- [ ] Task 3.2: Add heartbeat config to deepagents.json
  - Example config with defaults
  - Acceptance: Config documented

### 4. Workspace Templates
- [ ] Task 4.1: Create HEARTBEAT.md template
  - Template: Example task definitions
  - File: `templates/HEARTBEAT.md`
  - Acceptance: Template created

### 5. Testing
- [ ] Task 5.1: Unit tests for heartbeat integration
  - File: `tests/unit/test_heartbeat.py`
  - Mock: HeartbeatService, DeepAgent
  - Acceptance: 90%+ coverage

- [ ] Task 5.2: Integration tests for heartbeat
  - File: `tests/integration/test_heartbeat.py`
  - Scenario: Heartbeat triggers agent execution
  - Acceptance: Integration tests pass

### 6. Documentation
- [ ] Task 6.1: Document heartbeat usage
  - File: `docs/features/heartbeat.md`
  - Content: HEARTBEAT.md format, configuration
  - Acceptance: Documentation complete

- [ ] Task 6.2: Update README
  - Section: Heartbeat mode
  - Acceptance: README updated

---

## Deliverables

### Code
- `src/heartbeat/__init__.py` - Module exports
- `src/heartbeat/manager.py` - Heartbeat manager (~50 lines)
- `src/heartbeat/callbacks.py` - Callbacks (~30 lines)
- Updated `src/gateway.py` - Lifecycle integration

### Tests
- `tests/unit/test_heartbeat.py`
- `tests/integration/test_heartbeat.py`

### Templates
- `templates/HEARTBEAT.md` - Template

### Documentation
- `docs/features/heartbeat.md`
- Updated `README.md`

---

## Acceptance Criteria

### Functional Requirements
- [ ] HeartbeatService starts with gateway
- [ ] HEARTBEAT.md is read on each tick
- [ ] LLM decides skip/run correctly
- [ ] Tasks execute via DeepAgent
- [ ] Notifications sent when appropriate

### Non-Functional Requirements
- [ ] Heartbeat interval configurable
- [ ] Graceful start/stop with gateway
- [ ] Logging for debugging

### Quality Requirements
- [ ] Reuses upstream HeartbeatService (no duplication)
- [ ] Unit test coverage >= 90%
- [ ] Integration tests pass

---

## Implementation Notes

### Key Decisions
1. **Reuse Upstream**: Import HeartbeatService, don't reimplement
2. **Callback Pattern**: Use `on_execute` and `on_notify` callbacks
3. **Config in deepagents.json**: Not config.json (agent-specific)

### HEARTBEAT.md Example
```markdown
# Heartbeat Tasks

Check for:
- Pending todo items due today
- Calendar events in next hour
- Unread important emails

Report any actionable items.
```

### Related Upstream Code
- `nanobot/heartbeat/service.py` - Main service
- `nanobot/utils/evaluator.py` - Post-run evaluation

---

## Related Tickets
- **Depends on**: #19 (Lightweight Gateway)
- **Related**: #22 (Cronjob Support) - Similar scheduling pattern

---

Last updated: 2026-03-18
