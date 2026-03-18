# Ticket #9: Todo-List Frontend

**Status**: Pending  
**Priority**: MEDIUM  
**Phase**: Phase 3 - User Features  
**Branch**: `feature/todo-frontend`  
**Dependencies**: Ticket #8 (Human-in-the-Loop)  
**Estimated Effort**: 8-12 hours  
**Target Release**: v0.5.0

---

## Objective

Implement todo list display and management in Telegram/Slack, enabling users to view, add, complete, and remove tasks through the chat interface.

---

## Background

### Current State
- No todo list support in nanobot-deep
- No persistent task storage
- No task display in Telegram/Slack
- No task management commands
- No task state tracking

### Desired State
- Todo list display in Telegram/Slack
- Add/complete/remove task commands
- Persistent task storage (SQLite)
- Task state tracking (pending, in-progress, done)
- Task priorities and due dates
- Unit tests for todo logic
- E2E tests for todo commands
- Documentation explaining todo features

### Context from Planning Session
- **Decision**: Implement todo list with SQLite persistence
  - Rationale: Simple, reliable, no external dependencies
  - Alternative: Redis (rejected - unnecessary complexity)
- **Integration Point**: New tool for task management
- **Priority**: Phase 3 (parallel with other user features)
- **Use Case**: Manage development tasks, track progress

---

## Technical Approach

### Architecture
- **Todo Store**: SQLite-based task persistence
- **Todo Tool**: LangChain tool for task operations
- **Todo Display**: Formatted task list in Telegram/Slack
- **Todo Commands**: Natural language task management
- **State Machine**: Task state transitions

### Implementation Strategy
1. **Design Phase**: Define todo schema and API
2. **Store Phase**: Implement SQLite todo store
3. **Tool Phase**: Create LangChain todo tool
4. **Display Phase**: Format tasks for display
5. **Commands Phase**: Parse natural language commands
6. **Testing Phase**: Unit + E2E tests
7. **Documentation Phase**: Todo feature docs

### Key Decisions
- **Storage**: SQLite with async interface
- **Schema**: id, title, status, priority, due_date, created_at
- **Display**: Numbered list with status icons
- **Commands**: Natural language via LLM tool calls

---

## Tasks

### 1. Design Phase
- [ ] Task 1.1: Define todo schema
  - Fields: id, title, description, status, priority, due_date, tags, created_at, updated_at
  - File: `src/todo/schema.py`
  - Acceptance: Pydantic model for todos

- [ ] Task 1.2: Define todo store interface
  - Methods: create, read, update, delete, list, filter
  - File: `src/todo/store.py`
  - Acceptance: Abstract store interface

- [ ] Task 1.3: Define todo tool API
  - Methods: add_todo, complete_todo, remove_todo, list_todos, update_todo
  - File: `src/todo/tool.py`
  - Acceptance: Tool API design document

### 2. Todo Store Implementation
- [ ] Task 2.1: Create SQLite todo store
  - Features: CRUD operations, filtering, sorting
  - File: `src/todo/sqlite_store.py`
  - Acceptance: SQLite store implementation

- [ ] Task 2.2: Create database migrations
  - Tables: todos, todo_tags (if needed)
  - File: `src/todo/migrations.py`
  - Acceptance: Database schema migrations

- [ ] Task 2.3: Add async interface
  - Features: Async CRUD, connection pooling
  - Acceptance: Async store interface

### 3. Todo Tool Implementation
- [ ] Task 3.1: Create add todo tool
  - Input: title, description, priority, due_date, tags
  - Output: Created todo with ID
  - File: `src/todo/tools/add.py`
  - Acceptance: Add todo tool

- [ ] Task 3.2: Create list todos tool
  - Input: status, priority, tags (filters)
  - Output: Formatted todo list
  - File: `src/todo/tools/list.py`
  - Acceptance: List todos tool

- [ ] Task 3.3: Create update todo tool
  - Input: id, fields to update
  - Output: Updated todo
  - File: `src/todo/tools/update.py`
  - Acceptance: Update todo tool

- [ ] Task 3.4: Create complete todo tool
  - Input: id
  - Output: Completed todo
  - File: `src/todo/tools/complete.py`
  - Acceptance: Complete todo tool

- [ ] Task 3.5: Create remove todo tool
  - Input: id
  - Output: Confirmation
  - File: `src/todo/tools/remove.py`
  - Acceptance: Remove todo tool

### 4. Todo Display
- [ ] Task 4.1: Create todo formatter
  - Format: Numbered list with status icons, priorities
  - File: `src/todo/formatter.py`
  - Acceptance: Todo formatter for display

- [ ] Task 4.2: Add Telegram todo display
  - Features: Formatted message, inline buttons for actions
  - File: `src/todo/display/telegram.py`
  - Acceptance: Telegram todo display

- [ ] Task 4.3: Add Slack todo display
  - Features: Block Kit formatted message, action buttons
  - File: `src/todo/display/slack.py`
  - Acceptance: Slack todo display

### 5. DeepAgent Integration
- [ ] Task 5.1: Register todo tools
  - Integration: Add tools to DeepAgent
  - File: `src/agent.py` update
  - Acceptance: Todo tools available to agent

- [ ] Task 5.2: Add todo configuration
  - Config: Storage path, default priority, max items
  - File: `config.json` schema update
  - Acceptance: Todo configuration

### 6. Testing
- [ ] Task 6.1: Unit tests for todo schema
  - File: `tests/unit/test_todo_schema.py`
  - Coverage: Validation, serialization
  - Acceptance: 90%+ coverage

- [ ] Task 6.2: Unit tests for todo store
  - File: `tests/unit/test_todo_store.py`
  - Coverage: CRUD, filtering, sorting
  - Acceptance: 90%+ coverage

- [ ] Task 6.3: Unit tests for todo tools
  - File: `tests/unit/test_todo_tools.py`
  - Coverage: All tool operations
  - Acceptance: 90%+ coverage

- [ ] Task 6.4: E2E tests for todo commands
  - File: `tests/e2e/test_todo.py`
  - Mark: `@pytest.mark.live`
  - Scenario: Add, list, complete, remove via chat
  - Acceptance: Live todo management works

### 7. Documentation
- [ ] Task 7.1: Write todo feature docs
  - File: `docs/todo-features.md`
  - Content: Commands, examples, configuration
  - Acceptance: Todo feature documentation

- [ ] Task 7.2: Update README with todo section
  - Section: Todo list features, commands
  - Acceptance: README includes todo overview

---

## Deliverables

### Code
- `src/todo/` directory with:
  - `__init__.py` - Module exports
  - `schema.py` - Todo schemas
  - `store.py` - Abstract store interface
  - `sqlite_store.py` - SQLite implementation
  - `migrations.py` - Database migrations
  - `formatter.py` - Display formatting
  - `tools/` - Todo tools
    - `__init__.py`
    - `add.py`
    - `list.py`
    - `update.py`
    - `complete.py`
    - `remove.py`
  - `display/` - Platform displays
    - `__init__.py`
    - `telegram.py`
    - `slack.py`

### Tests
- `tests/unit/test_todo_schema.py`
- `tests/unit/test_todo_store.py`
- `tests/unit/test_todo_tools.py`
- `tests/e2e/test_todo.py`

### Documentation
- `docs/todo-features.md` - Feature documentation
- Updated `README.md` - Todo section

### Configuration
- Updated `config.json` schema with todo section

---

## Acceptance Criteria

### Functional Requirements
- [ ] Users can add todos via chat
- [ ] Users can list todos with filters
- [ ] Users can complete todos
- [ ] Users can remove todos
- [ ] Todos persist across sessions
- [ ] Todos display with status icons

### Non-Functional Requirements
- [ ] Todo operations complete in <100ms
- [ ] Database handles concurrent access
- [ ] Storage grows linearly with todos
- [ ] Error handling prevents data loss

### Quality Requirements
- [ ] Unit test coverage >= 90%
- [ ] E2E tests pass with live LLM
- [ ] All code passes linting (ruff)
- [ ] All code passes type checking (pyright)

---

## Implementation Notes

### Key Decisions
1. **SQLite Storage**: Simple, reliable, built-in
2. **Natural Language**: LLM interprets commands
3. **Inline Buttons**: Quick actions (complete, remove)
4. **State Machine**: Simple status transitions

### Pitfalls to Avoid
- **Data Loss**: Backup on migration
- **Race Conditions**: Async-safe operations
- **Query Injection**: Use parameterized queries
- **Schema Lock**: Support future migrations

---

## Related Tickets
- **Depends on**: #8 (Human-in-the-Loop) - Phase 2 complete
- **Parallel with**: #10, #11, #12 (Phase 3)
- **Related**: #8 (HITL) - Todo approval for sensitive operations

---

Last updated: 2026-03-18
