# Ticket #22: Cronjob Support Integration

**Status**: Pending  
**Priority**: MEDIUM  
**Phase**: Phase 3 - User Features  
**Branch**: `feature/cronjob-support`  
**Dependencies**: Ticket #19 (Lightweight Gateway)  
**Estimated Effort**: 8-10 hours  
**Target Release**: v0.5.0

---

## Objective

Integrate upstream nanobot's CronService into nanobot-deep, enabling scheduled agent tasks with support for one-time, interval, and cron-expression schedules.

---

## Background

### Current State
- No cronjob support in nanobot-deep
- Agent only responds to incoming messages
- No scheduled task execution

### Upstream Implementation
- **File**: `nanobot/cron/service.py` (~376 lines)
- **Types**: `nanobot/cron/types.py` (~59 lines)
- **Storage**: JSON file at `~/.nanobot/runtime/cron/jobs.json`

### Schedule Types (All Idempotent)
| Type | Example | Use Case |
|------|---------|----------|
| `at` | Run once at timestamp | One-time reminder |
| `every` | Run every N ms | Periodic checks |
| `cron` | Cron expression | Complex schedules |

### Idempotency Guarantees
- Jobs have unique IDs (UUID)
- State persisted to JSON on every change
- Next run time computed on load
- Safe to restart: jobs resume from where they left
- One-shot jobs (`at` type) disable after execution

### Desired State
- CronService integrated with DeepAgent
- Job management via commands or API
- Persistent job storage
- Support all three schedule types
- Job delivery to configured channels

---

## Technical Approach

### Architecture
```
CronService (upstream)
     │
     │ on_job callback
     ▼
DeepAgent.process()
     │
     ▼
ChannelManager.deliver()
```

### Integration Strategy
1. **Reuse Upstream**: Import `CronService`, `CronJob`, `CronSchedule` from nanobot
2. **Connect to DeepAgent**: Pass `on_job` callback
3. **Connect to Channels**: Deliver to configured channel
4. **Job Management**: Add/remove jobs via commands

---

## Tasks

### 1. Analysis Phase
- [ ] Task 1.1: Analyze upstream CronService
  - Files: `nanobot/cron/service.py`, `nanobot/cron/types.py`
  - Focus: Callbacks, storage, idempotency
  - Acceptance: Understand integration points

- [ ] Task 1.2: Verify idempotency
  - Test: Restart gateway during job execution
  - Verify: Jobs resume correctly
  - Acceptance: Idempotency confirmed

### 2. Integration Phase
- [ ] Task 2.1: Import CronService
  - Import: `from nanobot.cron import CronService, CronJob, CronSchedule`
  - File: `src/cron/manager.py`
  - Acceptance: Service imported

- [ ] Task 2.2: Create on_job callback
  - Callback: Execute job payload via DeepAgent
  - File: `src/cron/callbacks.py`
  - Acceptance: Callback connects to agent

- [ ] Task 2.3: Add cron to gateway lifecycle
  - Integration: Start/stop with gateway
  - File: `src/gateway.py`
  - Acceptance: Cron lifecycle managed

### 3. Job Management
- [ ] Task 3.1: Add `/cron` command handler
  - Commands: `/cron list`, `/cron add`, `/cron remove`
  - File: `src/commands/cron.py`
  - Acceptance: Commands work

- [ ] Task 3.2: Add job creation command
  - Command: `/cron add "name" "schedule" "message"`
  - Parse: Natural language or structured
  - Acceptance: Jobs created via command

### 4. Configuration Phase
- [ ] Task 4.1: Add cron config schema
  - File: `src/config/schema.py`
  - Fields: enabled, store_path
  - Acceptance: Config schema defined

- [ ] Task 4.2: Add cron to deepagents.json
  - Example config with defaults
  - Acceptance: Config documented

### 5. Testing
- [ ] Task 5.1: Unit tests for cron integration
  - File: `tests/unit/test_cron.py`
  - Mock: CronService, DeepAgent
  - Acceptance: 90%+ coverage

- [ ] Task 5.2: Integration tests for cron
  - File: `tests/integration/test_cron.py`
  - Scenario: Job executes at scheduled time
  - Acceptance: Integration tests pass

- [ ] Task 5.3: Idempotency tests
  - Scenario: Restart during job execution
  - Verify: Jobs resume correctly
  - Acceptance: Idempotency tests pass

### 6. Documentation
- [ ] Task 6.1: Document cron usage
  - File: `docs/features/cron.md`
  - Content: Schedule types, commands, examples
  - Acceptance: Documentation complete

- [ ] Task 6.2: Update README
  - Section: Cronjob support
  - Acceptance: README updated

---

## Deliverables

### Code
- `src/cron/__init__.py` - Module exports
- `src/cron/manager.py` - Cron manager (~50 lines)
- `src/cron/callbacks.py` - Callbacks (~30 lines)
- `src/commands/cron.py` - Command handler (~100 lines)
- Updated `src/gateway.py` - Lifecycle integration

### Tests
- `tests/unit/test_cron.py`
- `tests/integration/test_cron.py`

### Documentation
- `docs/features/cron.md`
- Updated `README.md`

---

## Acceptance Criteria

### Functional Requirements
- [ ] CronService starts with gateway
- [ ] Jobs execute at scheduled times
- [ ] All schedule types work (at, every, cron)
- [ ] Jobs persist across restarts
- [ ] Jobs deliver to configured channels
- [ ] Commands for job management

### Idempotency Requirements
- [ ] Jobs resume after restart
- [ ] No duplicate executions
- [ ] State persisted on every change

### Quality Requirements
- [ ] Reuses upstream CronService (no duplication)
- [ ] Unit test coverage >= 90%
- [ ] Integration tests pass

---

## Implementation Notes

### Key Decisions
1. **Reuse Upstream**: Import CronService, don't reimplement
2. **JSON Storage**: Use upstream's JSON file storage
3. **Callback Pattern**: Use `on_job` callback for execution

### Cron Expression Examples
```bash
# Every day at 9am
0 9 * * *

# Every Monday at 9am
0 9 * * 1

# Every hour
0 * * * *
```

### Command Examples
```bash
/cron add "daily_standup" "0 9 * * *" "Time for standup!"
/cron list
/cron remove abc123
```

### Related Upstream Code
- `nanobot/cron/service.py` - Main service
- `nanobot/cron/types.py` - Types and schemas

---

## Related Tickets
- **Depends on**: #19 (Lightweight Gateway)
- **Related**: #21 (Heartbeat Mode) - Similar scheduling pattern

---

Last updated: 2026-03-18
