# Ticket #5: A2A Integration (Agent-to-Agent Communication)

**Status**: Pending  
**Priority**: HIGH  
**Phase**: Phase 1 - Core Middleware  
**Branch**: `feature/a2a-integration`  
**Dependencies**: Ticket #4 (WebSearch Tool)  
**Estimated Effort**: 16-20 hours  
**Target Release**: v0.3.0

---

## Objective

Implement agent-to-agent (A2A) communication protocol based on deepagents' A2A architecture, enabling agents to delegate tasks, share context, and coordinate multi-agent workflows.

---

## Background

### Current State
- No A2A protocol implementation in nanobot-deep
- Single agent architecture (no delegation)
- No inter-agent communication
- No task routing or coordination
- No sub-agent spawning capability

### Desired State
- A2A protocol implementation following deepagents patterns
- Task delegation from main agent to specialized sub-agents
- Context sharing between agents
- Multi-agent workflow coordination
- Sub-agent spawning with isolated execution
- Configuration for agent capabilities and routing rules
- Unit tests for A2A communication
- E2E tests for multi-agent workflows
- Documentation explaining A2A architecture

### Context from Planning Session
- **Decision**: Use deepagents A2A protocol patterns
  - Rationale: Native integration with DeepAgent architecture
  - Alternative: Custom protocol (rejected - unnecessary complexity)
- **Integration Point**: DeepAgent middleware or tool layer
- **Priority**: Last item in Phase 1 (foundation for Phase 3 parallel work)
- **Use Case**: Enable Phase 3 parallel ticket work by spawning multiple agents

---

## Technical Approach

### Architecture
- **A2A Server**: Main agent that receives delegation requests
- **A2A Client**: Sub-agent that executes delegated tasks
- **Message Protocol**: Structured messages for task delegation
- **Context Passing**: Share relevant context with sub-agents
- **Result Aggregation**: Collect and merge sub-agent results

### Implementation Strategy
1. **Research Phase**: Study deepagents A2A architecture and protocol
2. **Design Phase**: Define A2A message format and routing rules
3. **Server Phase**: Implement A2A server (main agent)
4. **Client Phase**: Implement A2A client (sub-agent)
5. **Integration Phase**: Connect A2A with DeepAgent middleware
6. **Testing Phase**: Unit + E2E tests for A2A flows
7. **Documentation Phase**: A2A architecture and usage docs

### Key Decisions
- **Protocol**: Use deepagents native A2A protocol format
- **Communication**: In-process (no network overhead for single-instance)
- **Context Scope**: Full context sharing vs minimal context (configurable)
- **Error Handling**: Fallback to single-agent if A2A fails
- **Logging**: Full traceability of inter-agent communication

---

## Tasks

### 1. Analysis & Research
- [ ] Task 1.1: Study deepagents A2A architecture
  - Source: deepagents source code and documentation
  - Focus: Protocol format, server/client patterns, context passing
  - Acceptance: Understand A2A message flow and integration points

- [ ] Task 1.2: Analyze multi-agent patterns
  - Focus: Task routing, agent capabilities, result aggregation
  - Sources: LangGraph multi-agent docs, deepagents examples
  - Acceptance: Document recommended multi-agent patterns

- [ ] Task 1.3: Define A2A use cases for nanobot-deep
  - Use cases: Parallel ticket work, specialized tasks, tool execution
  - Acceptance: Clear list of A2A scenarios and requirements

### 2. Protocol Design
- [ ] Task 2.1: Define A2A message schema
  - Fields: task_type, task_payload, context, routing_rules, response_format
  - File: `src/a2a/protocol.py`
  - Acceptance: Pydantic model for A2A messages

- [ ] Task 2.2: Define agent capability registry
  - Fields: agent_id, capabilities, max_concurrent_tasks, priority
  - File: `src/a2a/registry.py`
  - Acceptance: Capability registry with registration API

- [ ] Task 2.3: Design routing rules
  - Rules: Task type → Agent capability matching
  - File: `src/a2a/router.py`
  - Acceptance: Routing logic with fallback handling

### 3. A2A Server Implementation
- [ ] Task 3.1: Create A2A server base class
  - File: `src/a2a/server.py`
  - Methods: receive_task, route_task, aggregate_results
  - Acceptance: A2A server with task routing

- [ ] Task 3.2: Implement task queue
  - Queue: Priority queue with task tracking
  - File: `src/a2a/queue.py`
  - Acceptance: Task queue with priority and status tracking

- [ ] Task 3.3: Implement result aggregation
  - Methods: collect_results, merge_contexts, handle_partial_failures
  - File: `src/a2a/aggregation.py`
  - Acceptance: Result aggregation with error handling

### 4. A2A Client Implementation
- [ ] Task 4.1: Create A2A client base class
  - File: `src/a2a/client.py`
  - Methods: register_capabilities, receive_task, execute_task, send_result
  - Acceptance: A2A client with capability registration

- [ ] Task 4.2: Implement context handling
  - Methods: receive_context, merge_with_local, validate_context
  - File: `src/a2a/context.py`
  - Acceptance: Context passing with validation

- [ ] Task 4.3: Implement task execution
  - Methods: parse_task, validate_task, execute, format_result
  - File: `src/a2a/executor.py`
  - Acceptance: Task execution with error handling

### 5. DeepAgent Integration
- [ ] Task 5.1: Create A2A middleware
  - Integration: DeepAgent middleware pattern
  - File: `src/middleware/a2a.py`
  - Acceptance: A2A middleware with lifecycle hooks

- [ ] Task 5.2: Add A2A tool for delegation
  - Tool: Delegate task to sub-agent
  - File: `src/tools/delegate.py`
  - Acceptance: Delegation tool with task routing

- [ ] Task 5.3: Configure A2A in config.json
  - Config: Agent capabilities, routing rules, timeouts
  - File: `config.json` schema update
  - Acceptance: A2A configuration with validation

### 6. Testing
- [ ] Task 6.1: Unit tests for A2A protocol
  - File: `tests/unit/test_a2a_protocol.py`
  - Coverage: Message parsing, validation, serialization
  - Acceptance: 90%+ coverage for protocol module

- [ ] Task 6.2: Unit tests for routing
  - File: `tests/unit/test_a2a_router.py`
  - Coverage: Task routing, capability matching, fallbacks
  - Acceptance: 90%+ coverage for router module

- [ ] Task 6.3: Unit tests for server/client
  - File: `tests/unit/test_a2a_server_client.py`
  - Coverage: Server routing, client execution, result aggregation
  - Acceptance: 90%+ coverage for server/client modules

- [ ] Task 6.4: E2E tests for multi-agent workflow
  - File: `tests/e2e/test_a2a_workflow.py`
  - Mark: `@pytest.mark.live`
  - Scenario: Delegate task to sub-agent, aggregate results
  - Acceptance: Live A2A communication works end-to-end

### 7. Documentation
- [ ] Task 7.1: Write A2A architecture docs
  - File: `docs/a2a-architecture.md`
  - Content: Protocol, server/client, routing, integration
  - Acceptance: Complete A2A architecture documentation

- [ ] Task 7.2: Write A2A usage guide
  - File: `docs/a2a-usage.md`
  - Content: Configuration, examples, best practices
  - Acceptance: Step-by-step A2A usage guide

- [ ] Task 7.3: Update README with A2A section
  - Section: Multi-agent workflows, A2A configuration
  - Acceptance: README includes A2A overview

---

## Deliverables

### Code
- `src/a2a/` directory with:
  - `__init__.py` - Module exports
  - `protocol.py` - Message schemas
  - `registry.py` - Capability registry
  - `router.py` - Task routing
  - `server.py` - A2A server
  - `client.py` - A2A client
  - `queue.py` - Task queue
  - `aggregation.py` - Result aggregation
  - `context.py` - Context handling
  - `executor.py` - Task execution
- `src/middleware/a2a.py` - DeepAgent middleware
- `src/tools/delegate.py` - Delegation tool

### Tests
- `tests/unit/test_a2a_protocol.py`
- `tests/unit/test_a2a_router.py`
- `tests/unit/test_a2a_server_client.py`
- `tests/e2e/test_a2a_workflow.py`

### Configuration
- Updated `config.json` schema with A2A section

### Documentation
- `docs/a2a-architecture.md` - Architecture documentation
- `docs/a2a-usage.md` - Usage guide
- Updated `README.md` - A2A section

---

## Acceptance Criteria

### Functional Requirements
- [ ] A2A server can receive and route tasks
- [ ] A2A client can execute delegated tasks
- [ ] Context is correctly passed between agents
- [ ] Results are properly aggregated
- [ ] Fallback to single-agent works if A2A fails
- [ ] Multiple sub-agents can work in parallel
- [ ] Task routing matches capabilities correctly

### Non-Functional Requirements
- [ ] A2A overhead is <100ms for task delegation
- [ ] Memory overhead is minimal for context passing
- [ ] Error handling prevents cascading failures
- [ ] Logging provides full A2A traceability
- [ ] Configuration is validated on startup

### Quality Requirements
- [ ] Unit test coverage >= 90%
- [ ] E2E tests pass with live LLM
- [ ] All code passes linting (ruff)
- [ ] All code passes type checking (pyright)
- [ ] Documentation is complete and accurate

---

## Testing Strategy

### Unit Tests
- **Protocol**: Message parsing, validation, serialization
- **Router**: Task routing, capability matching, fallbacks
- **Server**: Task routing, queue management, aggregation
- **Client**: Task execution, context handling, result formatting
- **Middleware**: Integration with DeepAgent lifecycle

### E2E Tests
- **Single Delegation**: Main agent delegates one task to sub-agent
- **Parallel Delegation**: Main agent delegates multiple tasks simultaneously
- **Context Passing**: Sub-agent receives and uses shared context
- **Error Handling**: Graceful fallback when sub-agent fails
- **Result Aggregation**: Multiple results merged correctly

### Verification Steps
1. Run unit tests: `pytest tests/unit/test_a2a*.py -v`
2. Run E2E tests: `pytest tests/e2e/test_a2a_workflow.py -m live -v`
3. Check coverage: `pytest --cov=src/a2a tests/unit/test_a2a*.py`
4. Verify linting: `ruff check src/a2a`
5. Verify types: `pyright src/a2a`

---

## Implementation Notes

### Key Decisions
1. **In-process Communication**: No network overhead, simpler debugging
2. **Full Context Sharing**: Sub-agents get all context by default
3. **Graceful Degradation**: A2A failures don't break main agent
4. **Async Execution**: Sub-agents run asynchronously with awaitable results

### Pitfalls to Avoid
- **Context Explosion**: Don't pass unnecessary context to sub-agents
- **Deadlocks**: Use timeouts for all A2A operations
- **Memory Leaks**: Clean up sub-agent state after task completion
- **Error Cascades**: Isolate sub-agent errors from main agent

### Integration Points
- **DeepAgent Middleware**: `src/middleware/a2a.py`
- **Tools**: `src/tools/delegate.py` for LLM-triggered delegation
- **Configuration**: `config.json` for agent capabilities

### Dependencies
- `langchain-core` - LangChain primitives
- `pydantic` - Data validation
- `asyncio` - Async execution
- `deepagents` - DeepAgent base classes

---

## Related Tickets
- **Depends on**: #4 (WebSearch Tool) - Phase 1 complete
- **Enables**: #9-12 (Phase 3) - Parallel agent work
- **Related**: #8 (Human-in-the-Loop) - A2A for approval flows

---

## Questions?
- See `AGENTS.md` for ticket workflow
- See `ROADMAP.md` for phase overview
- See `docs/a2a-architecture.md` (after completion) for details

---

Last updated: 2026-03-18
