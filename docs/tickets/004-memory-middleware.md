# Ticket #1: Memory Middleware Integration

**Status**: Ready to start  
**Priority**: HIGH  
**Phase**: Phase 1 - Core Middleware  
**Branch**: `feature/memory-middleware`  
**Dependencies**: Ticket #0 ✅  
**Estimated Effort**: 8-12 hours  
**Target Release**: v0.3.0

---

## Objective

Activate deepagents memory middleware to enable conversation context retention across multiple sessions, allowing the agent to remember previous interactions and maintain coherent long-term conversations.

---

## Background

### Current State
- `deepagents.json` has `"memory": []` (empty array) - memory middleware is **not activated**
- Memory files exist in `~/.nanobot/workspace/memory/`:
  - `MEMORY.md` - Intended for storing conversation context
  - `HISTORY.md` - Intended for storing conversation history
- These files are **not being used** by the agent currently
- deepagents has native `MemoryMiddleware` for conversation context
- No memory configuration in `nanobot_deep/config/schema.py`

### Desired State
- Memory middleware activated and configured in `deepagents.json`
- Agent maintains conversation context across sessions
- Memory content persisted to `MEMORY.md`
- Configuration validates memory settings
- Unit tests verify memory loading and persistence
- E2E tests verify context retention across gateway restarts
- Documentation explains memory configuration and usage

### Context from Planning Session
- **Decision**: Use deepagents native memory middleware (not nanobot's)
  - Rationale: Better LangGraph integration, maintained by deepagents team
  - Alternative considered: Implementing custom memory solution (rejected - reinventing wheel)
- **Priority**: Moved to #1 (before Streaming) per user request
- **Integration**: Memory works with AsyncSqliteSaver checkpointer
- **Storage**: Uses Markdown files for human-readable memory

---

## Technical Approach

### Architecture
- **Memory Middleware**: deepagents `MemoryMiddleware` class
- **Storage Backend**: Filesystem (Markdown files in workspace)
- **Integration Point**: LangGraph state graph middleware
- **Checkpointer**: Works alongside AsyncSqliteSaver for session persistence

### Implementation Strategy
1. **Research Phase**: Read deepagents memory middleware source code
2. **Configuration Phase**: Add memory config to `deepagents.json` schema
3. **Integration Phase**: Verify middleware loads correctly in `DeepAgent`
4. **Testing Phase**: Test memory persistence and retrieval
5. **Documentation Phase**: Document memory configuration and behavior

### Key Decisions
- **Memory Type**: Use "conversation" type memory
- **Token Limit**: Start with 4000 tokens (adjust based on testing)
- **Storage Path**: Use existing `~/.nanobot/workspace/memory/MEMORY.md`
- **Checkpointer Integration**: Memory complements (not replaces) checkpointer

---

## Tasks

### 1. Analysis & Research
- [ ] Task 1.1: Read deepagents memory middleware documentation
  - URL: [deepagents docs]
  - Focus: Configuration format, API, limitations
  - Acceptance: Understanding of `MemoryMiddleware` class

- [ ] Task 1.2: Review deepagents source code
  - File: `deepagents/middleware/memory.py`
  - Focus: How memory integrates with LangGraph
  - Acceptance: Understand middleware hook points

- [ ] Task 1.3: Check AsyncSqliteSaver integration
  - Focus: Ensure memory doesn't conflict with checkpointer
  - Acceptance: Understand interaction between memory and checkpointer

### 2. Configuration
- [ ] Task 2.1: Update `deepagents.json` schema
  - File: `nanobot_deep/config/schema.py`
  - Add: Memory configuration types
  - Validation: Ensure path exists, token limit is positive

- [ ] Task 2.2: Add memory configuration to example `deepagents.json`
  - File: User's `~/.nanobot/deepagents.json`
  - Configuration:
    ```json
    {
      "memory": [
        {
          "type": "conversation",
          "path": "~/.nanobot/workspace/memory/MEMORY.md",
          "max_tokens": 4000
        }
      ]
    }
    ```

- [ ] Task 2.3: Verify memory middleware loads in DeepAgent
  - File: `nanobot_deep/agent/deep_agent.py`
  - Check: Middleware initialization doesn't fail
  - Acceptance: No errors during agent creation

### 3. Implementation
- [ ] Task 3.1: No code changes needed (deepagents handles it)
  - Focus: Configuration-driven activation
  - Edge cases: Handle missing memory files, invalid paths

- [ ] Task 3.2: Add error handling for memory initialization
  - File: `nanobot_deep/agent/deep_agent.py`
  - Handle: FileNotFoundError, PermissionError
  - Acceptance: Graceful degradation if memory fails

### 4. Testing
- [ ] Task 4.1: Write unit tests
  - File: `tests/unit/test_memory_middleware.py`
  - Test cases:
    1. `test_memory_config_loading()`: Verify config parses correctly
    2. `test_memory_middleware_initialization()`: Verify middleware creates
    3. `test_memory_file_missing()`: Handle missing MEMORY.md
    4. `test_memory_invalid_path()`: Handle invalid path in config
  - Coverage target: 80%+
  - Mock: File system, deepagents MemoryMiddleware

- [ ] Task 4.2: Write E2E tests
  - File: `tests/e2e/test_memory_integration.py`
  - Test scenarios:
    1. Send message "My name is Alice" → Verify stored in memory
    2. Send message "What's my name?" → Verify agent recalls "Alice"
    3. Restart gateway → Verify memory persists across restarts
  - Verification:
    - Check MEMORY.md content
    - Verify agent responses use context
    - Test with Telegram simulator

### 5. Documentation
- [ ] Task 5.1: Update README.md
  - Section: Add "Memory" section after "Configuration"
  - Content:
    - What memory middleware does
    - How to configure it
    - Example configuration
    - Telegram usage examples
  - Example to include:
    ```markdown
    ## Memory
    
    Memory middleware enables context retention across sessions.
    
    ### Configuration
    [Example config]
    
    ### Usage in Telegram
    [Example conversation showing memory]
    ```

- [ ] Task 5.2: Update deepagents.json template
  - File: `templates/deepagents.json`
  - Add: Commented-out memory configuration example
  - Explanation: When to enable memory, token limit guidance

---

## Deliverables

### Code Deliverables
- [ ] `nanobot_deep/config/schema.py`: Memory configuration types
- [ ] User's `~/.nanobot/deepagents.json`: Memory configuration added
- [ ] No new code files needed (configuration-driven)

### Test Deliverables
- [ ] `tests/unit/test_memory_middleware.py`: Unit tests for memory config
- [ ] `tests/e2e/test_memory_integration.py`: E2E tests for context retention

### Documentation Deliverables
- [ ] README.md: Memory section
- [ ] `templates/deepagents.json`: Example memory configuration

---

## Acceptance Criteria

### Functional Requirements
1. ✅ Multi-turn conversations maintain context across messages
   - Verification: Ask "Remember my name?" after saying "I'm Alice"
   - Test: `test_memory_context_retention()`

2. ✅ Memory persists across gateway restarts
   - Verification: Restart gateway, agent still remembers previous conversation
   - Test: `test_memory_persistence_across_restarts()`

3. ✅ Memory content appears in `MEMORY.md` file
   - Verification: Cat MEMORY.md, see conversation context
   - Test: `test_memory_file_written()`

4. ✅ Configuration validates memory settings
   - Verification: Invalid config shows clear error
   - Test: `test_invalid_memory_config()`

### Non-Functional Requirements
1. ✅ Performance: Memory lookup < 100ms
2. ✅ Security: Memory files have proper permissions (600)
3. ✅ Maintainability: Configuration is self-documenting

### Testing Requirements
- ✅ Unit test coverage ≥ 80%
- ✅ All E2E tests passing
- ✅ CI/CD pipeline passing

---

## Testing Strategy

### Unit Tests
**File**: `tests/unit/test_memory_middleware.py`

**Test Cases**:
1. `test_memory_config_loading()`:
   - Load deepagents.json with memory config
   - Verify `MemoryConfig` object created
   - Check path, max_tokens, type fields

2. `test_memory_middleware_initialization()`:
   - Mock deepagents.MemoryMiddleware
   - Call DeepAgent.__init__() with memory config
   - Verify middleware.create() called

3. `test_memory_file_missing()`:
   - Config points to non-existent file
   - Verify graceful handling (warning, not error)
   - Agent still initializes

4. `test_memory_invalid_path()`:
   - Config has invalid path format
   - Verify validation error raised
   - Error message is clear

**Mock Strategy**:
- Mock `os.path.exists()` for file checks
- Mock `deepagents.MemoryMiddleware` for initialization
- Don't mock config parsing (test real behavior)

### E2E Tests
**File**: `tests/e2e/test_memory_integration.py`

**Test Scenarios**:
1. **Happy path - Context retention**:
   - User says: "My name is Alice and I like Python"
   - Agent acknowledges
   - User asks: "What's my name and what do I like?"
   - Agent responds: "Alice" and "Python"
   - Verify: MEMORY.md contains "Alice" and "Python"

2. **Gateway restart persistence**:
   - User has conversation (3-4 messages)
   - Stop gateway
   - Check MEMORY.md has content
   - Start gateway
   - User asks: "What did we talk about?"
   - Agent recalls previous conversation

3. **Token limit handling**:
   - Have long conversation (>4000 tokens)
   - Verify: Old messages get pruned
   - Verify: Recent context still available

**Verification Steps**:
1. Use Telegram simulator to send messages
2. Capture agent responses
3. Read MEMORY.md file
4. Assert expected content in memory and responses

---

## Configuration

### Configuration Files
**File**: `~/.nanobot/deepagents.json`

```json
{
  "memory": [
    {
      "type": "conversation",
      "path": "~/.nanobot/workspace/memory/MEMORY.md",
      "max_tokens": 4000,
      "description": "Maintains conversation context across sessions"
    }
  ],
  "recursion_limit": 500,
  "skills": [],
  "subagents": []
}
```

**Configuration Options**:
- `type`: Memory type
  - Type: string
  - Valid values: "conversation", "knowledge" (future)
  - Default: "conversation"
  - Description: Type of memory to use

- `path`: Storage file path
  - Type: string (file path)
  - Valid: Absolute path or ~ expansion
  - Default: none (required)
  - Validation: Parent directory must exist

- `max_tokens`: Token limit
  - Type: integer
  - Valid: 100-16000
  - Default: 4000
  - Description: Maximum tokens to keep in memory

---

## Documentation Updates

### README.md
**Section**: Memory (after Configuration section)

**Content to add**:
```markdown
## Memory

Memory middleware enables the agent to remember conversation context across sessions.

### How It Works

- Stores conversation context in `~/.nanobot/workspace/memory/MEMORY.md`
- Maintains up to 4000 tokens of recent context
- Persists across gateway restarts
- Works alongside SQLite checkpointer for full conversation history

### Configuration

Add to `~/.nanobot/deepagents.json`:

\`\`\`json
{
  "memory": [
    {
      "type": "conversation",
      "path": "~/.nanobot/workspace/memory/MEMORY.md",
      "max_tokens": 4000
    }
  ]
}
\`\`\`

### Usage Example (Telegram)

\`\`\`
User: My name is Alice and I'm working on a Python project
Bot: Nice to meet you, Alice! Tell me about your Python project.

User: [later in conversation] What's my name again?
Bot: Your name is Alice.

[Restart gateway]

User: What was I working on?
Bot: You mentioned you're working on a Python project.
\`\`\`

### Memory vs Checkpointer

- **Memory**: Recent context (last N tokens) for intelligent responses
- **Checkpointer**: Complete conversation history (all messages) for audit/replay

Both work together to provide context-aware conversations.
```

### templates/deepagents.json
Add commented example:
```json
{
  "// memory": "Uncomment to enable conversation memory",
  "// memory": [
  "//   {",
  "//     \"type\": \"conversation\",",
  "//     \"path\": \"~/.nanobot/workspace/memory/MEMORY.md\",",
  "//     \"max_tokens\": 4000",
  "//   }",
  "// ]"
}
```

---

## Implementation Notes

### Key Decisions
1. **Decision**: Use deepagents native memory (not custom)
   - **Rationale**: Maintained by deepagents team, better integration
   - **Alternatives considered**: Custom memory implementation
   - **Tradeoffs**: Less control, but more stable and maintained

2. **Decision**: Store in Markdown files (not database)
   - **Rationale**: Human-readable, easy to debug, version controllable
   - **Alternatives considered**: SQLite, JSON files
   - **Tradeoffs**: Less efficient for large memories, but more transparent

3. **Decision**: 4000 token limit default
   - **Rationale**: Balance between context and performance
   - **Alternatives considered**: 2000 (too little), 8000 (too much)
   - **Tradeoffs**: May need tuning based on usage

### Important Considerations
- **Memory vs Checkpointer**: They serve different purposes, both needed
- **Token Counting**: Uses LLM tokenizer (varies by model)
- **Memory Pruning**: Old messages pruned when limit reached (FIFO)
- **File Permissions**: Ensure MEMORY.md is readable/writable

### Potential Pitfalls
- **Path Resolution**: `~` expansion might fail on Windows (use absolute paths)
- **Concurrent Access**: Multiple agents sharing same memory file (need locking)
- **Token Limit Too Low**: User frustrated by amnesia (monitor and adjust)
- **Token Limit Too High**: Performance degradation (monitor latency)

---

## Dependencies

### Blocked By
- Ticket #0: CI/CD pipeline must be in place ✅ (Complete)

### Blocks
- Ticket #2: Skills middleware (memory helps skills with context)

### Parallel Work
- None (sequential Phase 1)

---

## Related Documentation

### Internal Docs
- Analysis: `docs/tickets/001-deepagents-integration-analysis.md`
- Roadmap: `docs/ROADMAP.md`
- Config schema: `nanobot_deep/config/schema.py`

### External References
- [deepagents Memory Middleware](https://docs.langchain.com/oss/python/deepagents/memory)
- [LangGraph State Management](https://langchain-ai.github.io/langgraph/concepts/persistence/)
- [AsyncSqliteSaver Docs](https://langchain-ai.github.io/langgraph/reference/checkpoints/#langgraph.checkpoint.sqlite.aio.AsyncSqliteSaver)

---

## Questions & Clarifications

### Open Questions
1. **Question**: Should memory be enabled by default?
   - **Options**: 
     - A: Enable by default (better UX)
     - B: Disabled by default (opt-in for privacy)
   - **Recommendation**: Disabled by default, document how to enable

2. **Question**: Should we support multiple memory types?
   - **Context**: deepagents supports "conversation" and potentially others
   - **Options**:
     - A: Only conversation for now
     - B: Support all types deepagents offers
   - **Recommendation**: Start with conversation only, add others if needed

### Decisions Needed
1. **Token limit default**: 4000 is proposed, but might need adjustment
   - **Action**: Monitor in production, adjust if needed

---

## Success Metrics

### Measurable Outcomes
- Memory config loads successfully: 100% of time
- Context retention accuracy: >90% in E2E tests
- Memory file write latency: <50ms
- Gateway startup time increase: <10%

### Verification Methods
- Unit test pass rate
- E2E test pass rate
- Performance benchmarks
- User feedback (can agent remember?)

---

## Rollback Plan

### If Something Goes Wrong
1. Set `"memory": []` in deepagents.json (disable memory)
2. Restart gateway
3. Agent works without memory (graceful degradation)
4. Investigate logs for memory errors

### Monitoring
- Watch gateway logs for memory middleware errors
- Monitor memory file size (shouldn't grow unbounded)
- Check response latency (memory shouldn't slow down agent)
- Warning signs: FileNotFoundError, PermissionError, token limit warnings

---

## Timeline

### Estimated Breakdown
- Analysis & Research: 2 hours
- Configuration: 2 hours
- Testing: 3 hours
- Documentation: 1-2 hours
- **Total**: 8-12 hours

### Milestones
- [ ] Day 1: Analysis complete, config designed
- [ ] Day 2: Configuration implemented, manual testing done
- [ ] Day 3: Unit tests + E2E tests passing
- [ ] Day 4: Documentation complete, PR ready

---

## Post-Completion

### Follow-up Tasks
- [ ] Monitor memory usage in production (file sizes)
- [ ] Gather user feedback on context retention quality
- [ ] Tune token limit based on real usage
- [ ] Consider adding memory pruning strategies (beyond FIFO)

### Future Enhancements
- **Memory Search**: Allow agent to search old memories
- **Multiple Memory Types**: Support knowledge base memory
- **Memory Sharing**: Share memory across multiple agents
- **Memory Analytics**: Visualize what agent remembers
