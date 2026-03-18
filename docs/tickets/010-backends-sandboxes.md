# Ticket #7: Backends & Sandboxes

**Status**: Pending  
**Priority**: MEDIUM  
**Phase**: Phase 2 - Features  
**Branch**: `feature/backends-sandboxes`  
**Dependencies**: Ticket #6 (Streaming Support)  
**Estimated Effort**: 10-14 hours  
**Target Release**: v0.4.0

---

## Objective

Configure and document backend support (local, Docker, Kubernetes) and implement sandbox modes for secure code execution, enabling flexible deployment options for different environments.

---

## Background

### Current State
- Single backend mode (local execution)
- No sandbox support for code execution
- No Docker backend configuration
- No Kubernetes backend configuration
- No backend switching mechanism
- No security isolation for tool execution

### Desired State
- Multiple backend support (local, Docker, Kubernetes)
- Sandbox modes for secure code execution
- Backend configuration in `config.json`
- Backend switching mechanism
- Security isolation for tool execution
- Documentation for each backend type
- Unit tests for backend switching
- E2E tests for sandbox execution
- Documentation explaining backend architecture

### Context from Planning Session
- **Decision**: Support multiple backends with sandbox modes
  - Rationale: Different security requirements per environment
  - Alternative: Single backend (rejected - limits deployment options)
- **Priority**: Second item in Phase 2 (enables secure tool execution)
- **Use Case**: Development (local), Production (Docker/K8s), High-security (sandbox)

---

## Technical Approach

### Architecture
- **Backend Interface**: Abstract backend with common API
- **Local Backend**: Direct execution (development mode)
- **Docker Backend**: Container-based execution
- **Kubernetes Backend**: Pod-based execution (future)
- **Sandbox Mode**: Isolated execution environment
- **Backend Manager**: Backend selection and switching

### Implementation Strategy
1. **Research Phase**: Study backend patterns and sandbox approaches
2. **Design Phase**: Define backend interface and configuration
3. **Local Phase**: Implement local backend with sandbox mode
4. **Docker Phase**: Implement Docker backend (analysis only for now)
5. **Integration Phase**: Connect backends to DeepAgent
6. **Testing Phase**: Unit + E2E tests for backends
7. **Documentation Phase**: Backend configuration docs

### Key Decisions
- **Interface**: Abstract base class for all backends
- **Configuration**: Backend selection in `config.json`
- **Sandbox**: Python subprocess isolation for local sandbox
- **Docker**: Docker SDK for Python (future implementation)
- **Kubernetes**: Kubernetes Python client (future implementation)

---

## Tasks

### 1. Analysis & Research
- [ ] Task 1.1: Study backend patterns
  - Focus: Abstract backends, plugin architectures, switching
  - Sources: LangChain backends, Ray backends, custom implementations
  - Acceptance: Document recommended backend patterns

- [ ] Task 1.2: Research sandbox approaches
  - Focus: Process isolation, resource limits, security boundaries
  - Sources: Python sandbox libraries, Docker sandbox, OS-level isolation
  - Acceptance: Document sandbox security considerations

- [ ] Task 1.3: Analyze Docker backend requirements
  - Focus: Docker SDK, container management, resource limits
  - Sources: Docker Python SDK docs, best practices
  - Acceptance: Document Docker backend architecture

- [ ] Task 1.4: Analyze Kubernetes backend requirements
  - Focus: Kubernetes Python client, pod management, security contexts
  - Sources: Kubernetes Python client docs, security best practices
  - Acceptance: Document Kubernetes backend architecture (future reference)

### 2. Design Phase
- [ ] Task 2.1: Define backend interface
  - Methods: execute, health_check, get_status, cleanup
  - File: `src/backends/base.py`
  - Acceptance: Abstract base class for backends

- [ ] Task 2.2: Define backend configuration schema
  - Fields: type, settings, resource_limits, security_options
  - File: `src/backends/config.py`
  - Acceptance: Pydantic model for backend configuration

- [ ] Task 2.3: Define sandbox interface
  - Methods: create_sandbox, execute_in_sandbox, destroy_sandbox
  - File: `src/backends/sandbox.py`
  - Acceptance: Abstract base class for sandbox

### 3. Local Backend Implementation
- [ ] Task 3.1: Create local backend
  - Features: Direct execution, no isolation
  - File: `src/backends/local.py`
  - Acceptance: Local backend implementation

- [ ] Task 3.2: Create local sandbox mode
  - Features: Subprocess isolation, resource limits, timeout
  - File: `src/backends/local_sandbox.py`
  - Acceptance: Local sandbox implementation

- [ ] Task 3.3: Add resource limiting
  - Features: CPU, memory, time limits
  - File: `src/backends/resource_limiter.py`
  - Acceptance: Resource limiting for local sandbox

### 4. Docker Backend (Analysis Only)
- [ ] Task 4.1: Design Docker backend architecture
  - Focus: Container lifecycle, image management, resource limits
  - File: `docs/docker-backend-design.md`
  - Acceptance: Docker backend design document

- [ ] Task 4.2: Identify Docker backend dependencies
  - Dependencies: `docker` Python package, Docker daemon
  - File: `pyproject.toml` (optional extras)
  - Acceptance: Document Docker backend requirements

- [ ] Task 4.3: Create Docker backend stub
  - File: `src/backends/docker.py`
  - Content: Placeholder with NotImplementedError
  - Acceptance: Docker backend stub for future implementation

### 5. Backend Manager
- [ ] Task 5.1: Create backend manager
  - Features: Backend selection, initialization, switching
  - File: `src/backends/manager.py`
  - Acceptance: Backend manager implementation

- [ ] Task 5.2: Add backend configuration
  - File: `config.json` schema update
  - Config: Backend type, settings, resource limits
  - Acceptance: Backend configuration in config.json

- [ ] Task 5.3: Add backend health checks
  - Features: Periodic health checks, automatic failover
  - File: `src/backends/health.py`
  - Acceptance: Backend health check system

### 6. DeepAgent Integration
- [ ] Task 6.1: Add backend selection to DeepAgent
  - Integration: DeepAgent uses configured backend
  - File: `src/agent.py`
  - Acceptance: DeepAgent backend integration

- [ ] Task 6.2: Add sandbox mode for tool execution
  - Integration: Tools can request sandbox execution
  - File: `src/tools/` updates
  - Acceptance: Tool sandbox execution support

- [ ] Task 6.3: Add backend middleware
  - Integration: Middleware for backend lifecycle
  - File: `src/middleware/backend.py`
  - Acceptance: Backend middleware implementation

### 7. Testing
- [ ] Task 7.1: Unit tests for backend interface
  - File: `tests/unit/test_backends_base.py`
  - Coverage: Interface methods, validation
  - Acceptance: 90%+ coverage for base module

- [ ] Task 7.2: Unit tests for local backend
  - File: `tests/unit/test_backends_local.py`
  - Coverage: Execution, error handling, cleanup
  - Acceptance: 90%+ coverage for local backend

- [ ] Task 7.3: Unit tests for local sandbox
  - File: `tests/unit/test_backends_local_sandbox.py`
  - Coverage: Isolation, resource limits, timeout
  - Acceptance: 90%+ coverage for local sandbox

- [ ] Task 7.4: Unit tests for backend manager
  - File: `tests/unit/test_backends_manager.py`
  - Coverage: Selection, initialization, switching
  - Acceptance: 90%+ coverage for manager

- [ ] Task 7.5: E2E tests for backend execution
  - File: `tests/e2e/test_backends.py`
  - Mark: `@pytest.mark.live`
  - Scenario: Execute code in local backend and sandbox
  - Acceptance: Live backend execution works

### 8. Documentation
- [ ] Task 8.1: Write backend architecture docs
  - File: `docs/backends-architecture.md`
  - Content: Interface, backends, sandbox, integration
  - Acceptance: Complete backend architecture documentation

- [ ] Task 8.2: Write backend configuration guide
  - File: `docs/backends-configuration.md`
  - Content: Local, Docker, Kubernetes configuration
  - Acceptance: Backend configuration guide

- [ ] Task 8.3: Write sandbox security guide
  - File: `docs/sandbox-security.md`
  - Content: Security considerations, best practices
  - Acceptance: Sandbox security documentation

- [ ] Task 8.4: Update README with backends section
  - Section: Backend support, configuration, security
  - Acceptance: README includes backends overview

---

## Deliverables

### Code
- `src/backends/` directory with:
  - `__init__.py` - Module exports
  - `base.py` - Abstract backend interface
  - `config.py` - Configuration schemas
  - `sandbox.py` - Abstract sandbox interface
  - `local.py` - Local backend
  - `local_sandbox.py` - Local sandbox
  - `resource_limiter.py` - Resource limiting
  - `manager.py` - Backend manager
  - `health.py` - Health checks
  - `docker.py` - Docker backend stub
- `src/middleware/backend.py` - Backend middleware

### Tests
- `tests/unit/test_backends_base.py`
- `tests/unit/test_backends_local.py`
- `tests/unit/test_backends_local_sandbox.py`
- `tests/unit/test_backends_manager.py`
- `tests/e2e/test_backends.py`

### Documentation
- `docs/backends-architecture.md` - Architecture documentation
- `docs/backends-configuration.md` - Configuration guide
- `docs/sandbox-security.md` - Security guide
- `docs/docker-backend-design.md` - Docker design document
- Updated `README.md` - Backends section

### Configuration
- Updated `config.json` schema with backends section

---

## Acceptance Criteria

### Functional Requirements
- [ ] Local backend executes code directly
- [ ] Local sandbox isolates code execution
- [ ] Backend manager selects correct backend
- [ ] Backend configuration is validated
- [ ] Resource limits are enforced in sandbox
- [ ] Health checks work correctly
- [ ] Backend switching works without restart

### Non-Functional Requirements
- [ ] Sandbox adds <50ms overhead per execution
- [ ] Resource limits prevent runaway processes
- [ ] Error handling prevents cascading failures
- [ ] Logging captures backend events
- [ ] Configuration is validated on startup

### Quality Requirements
- [ ] Unit test coverage >= 90%
- [ ] E2E tests pass with live execution
- [ ] All code passes linting (ruff)
- [ ] All code passes type checking (pyright)
- [ ] Documentation is complete and accurate

---

## Testing Strategy

### Unit Tests
- **Base**: Interface methods, validation
- **Local Backend**: Execution, error handling, cleanup
- **Local Sandbox**: Isolation, resource limits, timeout
- **Manager**: Selection, initialization, switching
- **Health Checks**: Health status, failover

### E2E Tests
- **Local Execution**: Execute code in local backend
- **Sandbox Execution**: Execute code in sandbox
- **Resource Limits**: Verify limits are enforced
- **Backend Switching**: Switch backends at runtime
- **Error Recovery**: Handle backend failures

### Verification Steps
1. Run unit tests: `pytest tests/unit/test_backends*.py -v`
2. Run E2E tests: `pytest tests/e2e/test_backends.py -m live -v`
3. Check coverage: `pytest --cov=src/backends tests/unit/test_backends*.py`
4. Verify linting: `ruff check src/backends`
5. Verify types: `pyright src/backends`

---

## Implementation Notes

### Key Decisions
1. **Interface**: Abstract base class for all backends
2. **Local Sandbox**: Python subprocess with resource limits
3. **Docker**: Design only, implementation in Phase 4
4. **Kubernetes**: Design only, implementation in Phase 4

### Pitfalls to Avoid
- **Security Gaps**: Sandbox must properly isolate execution
- **Resource Leaks**: Clean up processes and resources
- **Deadlocks**: Use timeouts for all operations
- **Configuration Drift**: Validate configuration strictly

### Integration Points
- **DeepAgent**: `src/agent.py` backend selection
- **Tools**: `src/tools/` sandbox execution
- **Configuration**: `config.json` backends section

### Dependencies
- `asyncio` - Async execution
- `resource` - Unix resource limits (Linux only)
- `subprocess` - Process isolation
- `pydantic` - Configuration validation

---

## Related Tickets
- **Depends on**: #6 (Streaming Support) - Phase 2 started
- **Enables**: #13-15 (Phase 4) - Docker/K8s backend implementation
- **Related**: #8 (Human-in-the-Loop) - Secure tool execution

---

## Questions?
- See `AGENTS.md` for ticket workflow
- See `ROADMAP.md` for phase overview
- See `docs/backends-architecture.md` (after completion) for details

---

Last updated: 2026-03-18
