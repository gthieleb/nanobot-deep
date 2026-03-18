# Ticket #19: Lightweight Gateway Architecture (Subclassing)

**Status**: Pending  
**Priority**: HIGH  
**Phase**: Phase 2 - Features  
**Branch**: `refactor/lightweight-gateway`  
**Dependencies**: Ticket #8 (Human-in-the-Loop)  
**Estimated Effort**: 10-14 hours  
**Target Release**: v0.4.0

---

## Objective

Refactor `DeepGateway` to subclass from upstream nanobot's `BaseChannel` or compose with existing gateway components, reducing code duplication and ensuring maintainability as upstream evolves.

---

## Background

### Current State
- `nanobot_deep/gateway.py` is a standalone implementation (~240 lines)
- Duplicates message bus, channel manager, signal handling from upstream
- No inheritance from upstream `BaseChannel` or gateway patterns
- Changes in upstream require manual synchronization
- ~40% code overlap with upstream patterns

### Desired State
- Gateway subclasses from or composes with upstream components
- Minimal code duplication
- Automatic inheritance of upstream improvements
- Clear separation: upstream base vs nanobot-deep extensions
- All Phase 3 gateway features build on this foundation

### Context from Upstream Analysis
- **BaseChannel** (`nanobot/channels/base.py`): Abstract class with `start()`, `stop()`, `send()`, `transcribe_audio()`
- **TelegramChannel** (`nanobot/channels/telegram.py`): Full Telegram implementation (~816 lines)
- **ChannelManager** (`nanobot/channels/manager.py`): Manages multiple channels
- **MessageBus** (`nanobot/bus/`): Event-driven messaging

### Decision: Hybrid Approach (Recommended)
After analyzing the codebase, a **hybrid approach** is most maintainable:

1. **Inherit BaseChannel** for channel interface (`start`, `stop`, `send`)
2. **Compose ChannelManager** for multi-channel support (reuse upstream)
3. **Compose MessageBus** (reuse upstream)
4. **Override only**: `process_message` (DeepAgent-specific)

This minimizes code while maximizing flexibility.

---

## Technical Approach

### Architecture Decision

```
                    ┌─────────────────┐
                    │   BaseChannel   │ (upstream)
                    └────────┬────────┘
                             │ inherits
                    ┌────────▼────────┐
                    │  DeepChannel    │ (nanobot-deep)
                    │  - process()    │ overrides message processing
                    │  - DeepAgent    │ adds LangGraph agent
                    └────────┬────────┘
                             │ uses
              ┌──────────────┼──────────────┐
              │              │              │
     ┌────────▼───┐  ┌──────▼──────┐  ┌────▼────┐
     │ MessageBus │  │ChannelMgr   │  │DeepAgent│
     │ (upstream) │  │(upstream)   │  │(ours)   │
     └────────────┘  └─────────────┘  └─────────┘
```

### Code Reuse Strategy

| Component | Strategy | Rationale |
|-----------|----------|-----------|
| `BaseChannel` | Inherit | Standard channel interface |
| `MessageBus` | Compose | No modification needed |
| `ChannelManager` | Compose | Multi-channel support |
| `transcribe_audio()` | Inherit | Groq Whisper already works |
| Signal handling | Copy minimal | Platform-specific |
| DeepAgent integration | New code | Our extension |

### Implementation Strategy
1. **Analysis Phase**: Map all duplicated code
2. **Design Phase**: Define subclass/compose boundaries
3. **Refactor Phase**: Create `DeepChannel` subclassing `BaseChannel`
4. **Integration Phase**: Update gateway entry point
5. **Testing Phase**: Verify all features still work
6. **Documentation Phase**: Document architecture

---

## Tasks

### 1. Analysis Phase
- [ ] Task 1.1: Map duplicated code between DeepGateway and upstream
  - Files: `gateway.py` vs `nanobot/channels/*.py`
  - Output: List of reusable vs custom code
  - Acceptance: Complete code overlap analysis

- [ ] Task 1.2: Identify reusable upstream components
  - Components: BaseChannel, MessageBus, ChannelManager
  - Acceptance: Document which components to reuse

- [ ] Task 1.3: Identify nanobot-deep specific code
  - Code: DeepAgent integration, checkpointer, session management
  - Acceptance: Document custom code to preserve

### 2. Design Phase
- [ ] Task 2.1: Design DeepChannel class
  - Inherit: `BaseChannel`
  - Override: `start()`, `stop()`, `send()`, `_handle_message()`
  - Add: `process_with_agent()` method
  - Acceptance: Class design documented

- [ ] Task 2.2: Design gateway entry point
  - Entry: `run_gateway()` function
  - Composition: ChannelManager, MessageBus
  - Acceptance: Entry point design documented

- [ ] Task 2.3: Define extension points
  - Extensions: DeepAgent, checkpointer, middleware
  - Acceptance: Extension points documented

### 3. Refactor Phase
- [ ] Task 3.1: Create DeepChannel base class
  - File: `src/channels/deep_channel.py`
  - Inherit: `BaseChannel` from nanobot
  - Acceptance: DeepChannel class created

- [ ] Task 3.2: Move DeepAgent integration to DeepChannel
  - Method: `process_with_agent(msg) -> OutboundMessage`
  - Acceptance: Agent processing in DeepChannel

- [ ] Task 3.3: Refactor gateway.py to use DeepChannel
  - Use: ChannelManager with DeepChannel
  - Keep: Signal handling, entry point
  - Acceptance: Gateway uses new architecture

- [ ] Task 3.4: Remove duplicated code
  - Remove: Duplicated message bus, channel code
  - Keep: Only nanobot-deep specific code
  - Acceptance: Code duplication <10%

### 4. Integration Phase
- [ ] Task 4.1: Update imports
  - Import: `BaseChannel`, `MessageBus`, `ChannelManager` from nanobot
  - Acceptance: Clean imports from upstream

- [ ] Task 4.2: Update entry points
  - Entry: `python -m nanobot_deep.gateway`
  - Acceptance: Entry points work

- [ ] Task 4.3: Update CLI if needed
  - Check: `nanobot_deep/__main__.py`
  - Acceptance: CLI works with new architecture

### 5. Testing Phase
- [ ] Task 5.1: Unit tests for DeepChannel
  - File: `tests/unit/test_deep_channel.py`
  - Coverage: Inheritance, composition, processing
  - Acceptance: 90%+ coverage

- [ ] Task 5.2: Integration tests for gateway
  - File: `tests/integration/test_gateway_refactor.py`
  - Coverage: Full message flow
  - Acceptance: All tests pass

- [ ] Task 5.3: E2E tests for Telegram/Slack
  - File: `tests/e2e/test_gateway_channels.py`
  - Mark: `@pytest.mark.live`
  - Acceptance: Live channel tests pass

### 6. Documentation Phase
- [ ] Task 6.1: Document architecture decision
  - File: `docs/architecture/gateway-design.md`
  - Content: Why hybrid approach, class diagram
  - Acceptance: Architecture documented

- [ ] Task 6.2: Update README with architecture
  - Section: Gateway architecture, extension points
  - Acceptance: README updated

- [ ] Task 6.3: Update AGENTS.md
  - Section: Gateway extension guide
  - Acceptance: AGENTS.md updated

---

## Deliverables

### Code
- `src/channels/__init__.py` - Module exports
- `src/channels/deep_channel.py` - DeepChannel class (~100 lines, down from 240)
- `src/gateway.py` - Refactored entry point (~50 lines)

### Tests
- `tests/unit/test_deep_channel.py`
- `tests/integration/test_gateway_refactor.py`

### Documentation
- `docs/architecture/gateway-design.md`
- Updated `README.md`
- Updated `AGENTS.md`

---

## Acceptance Criteria

### Functional Requirements
- [ ] Gateway subclasses BaseChannel
- [ ] MessageBus composed from upstream
- [ ] ChannelManager composed from upstream
- [ ] DeepAgent integration preserved
- [ ] All existing features work

### Non-Functional Requirements
- [ ] Code reduction: ~40% fewer lines
- [ ] Code duplication: <10% with upstream
- [ ] No breaking changes to API
- [ ] Upstream updates easy to integrate

### Quality Requirements
- [ ] Unit test coverage >= 90%
- [ ] Integration tests pass
- [ ] All code passes linting
- [ ] All code passes type checking

---

## Implementation Notes

### Key Decisions
1. **Hybrid Approach**: Inherit BaseChannel, compose MessageBus/ChannelManager
2. **Minimal Override**: Only override what's truly different (agent processing)
3. **Extension Points**: Clear hooks for future features

### Pitfalls to Avoid
- **Tight Coupling**: Don't depend on upstream internals
- **Overriding Too Much**: Only override necessary methods
- **Breaking Upstream**: Don't modify upstream classes

### Integration Points
- **BaseChannel**: `nanobot.channels.base.BaseChannel`
- **MessageBus**: `nanobot.bus.queue.MessageBus`
- **ChannelManager**: `nanobot.channels.manager.ChannelManager`

---

## Related Tickets
- **Depends on**: #8 (Human-in-the-Loop) - Phase 2 in progress
- **Blocks**: #20-24 (Phase 3 gateway features)
- **Related**: All gateway-dependent features

---

Last updated: 2026-03-18
