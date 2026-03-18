# Ticket #2: Skills Middleware Integration & Frontmatter Analysis

**Status**: Pending  
**Priority**: HIGH  
**Phase**: Phase 1 - Core Middleware  
**Branch**: `feature/skills-middleware`  
**Dependencies**: Ticket #1  
**Estimated Effort**: 10-15 hours  
**Target Release**: v0.3.0

---

## Objective

Activate and verify deepagents skills middleware, analyze frontmatter requirements, and ensure skills load correctly from the workspace directory with proper directory access permissions.

---

## Background

### Current State
- Skills exist: `~/.nanobot/workspace/skills/slack/SKILL.md`, `skills/litellm-proxy/SKILL.md`
- **Current observation**: Skills have **NO YAML frontmatter** (plain Markdown)
- `deepagents.json` may have skills configuration (need to verify)
- Unknown: Does deepagents require frontmatter for skills?
- Unknown: Can gateway process access `~/.nanobot/workspace/skills/`?

### Desired State
- Skills middleware activated in `deepagents.json`
- Frontmatter requirements documented (if any)
- Existing skills load successfully
- Directory access verified (permissions, path resolution)
- Skills trigger correctly via Telegram/Slack messages
- Unit tests verify skills loading
- E2E tests verify skill execution
- Documentation explains skill format and creation

### Context from Planning Session
- **Decision**: Use deepagents skills (not nanobot's skills)
  - Rationale: Native LangGraph integration, better maintained
- **Open Question**: Do skills require YAML frontmatter?
  - Current skills are plain Markdown (no `---` delimiters)
  - Need to analyze deepagents source code
- **Priority**: Sequential ticket after Memory (#1)

---

## Technical Approach

### Architecture
- **Skills Middleware**: deepagents `SkillsMiddleware` class
- **Storage Backend**: Filesystem (Markdown files in workspace/skills/)
- **Trigger Mechanism**: Pattern matching in skill content or metadata
- **Integration Point**: LangGraph tool calling

### Implementation Strategy
1. **Analysis Phase**: Review deepagents skills source code
2. **Frontmatter Investigation**: Determine if YAML frontmatter required
3. **Configuration Phase**: Update skills config in `deepagents.json`
4. **Access Verification**: Test directory permissions and path resolution
5. **Skill Update**: Add frontmatter if required
6. **Testing Phase**: Unit + E2E tests
7. **Documentation Phase**: Document skill format requirements

### Key Decisions
- **Frontmatter Format**: TBD (depends on deepagents requirements)
- **Skill Discovery**: Recursive search in skills directory
- **Path Resolution**: Support both absolute and `~` paths
- **Trigger Strategy**: TBD (depends on skill definition format)

---

## Tasks

### 1. Analysis & Research
- [ ] Task 1.1: Read deepagents skills middleware documentation
  - Focus: Skill file format, frontmatter requirements, trigger mechanisms
  - Acceptance: Understand `SkillsMiddleware` API

- [ ] Task 1.2: Review deepagents skills source code
  - File: `deepagents/middleware/skills.py`
  - Focus: How skills are parsed, loaded, and triggered
  - Question: Is YAML frontmatter required or optional?
  - Acceptance: Clear understanding of skill format requirements

- [ ] Task 1.3: Analyze existing skill files
  - Files: `~/.nanobot/workspace/skills/slack/SKILL.md`, `skills/litellm-proxy/SKILL.md`
  - Current format: Plain Markdown (no frontmatter)
  - Action: Document current structure

### 2. Frontmatter Analysis
- [ ] Task 2.1: Determine frontmatter requirements
  - Test: Load skill without frontmatter
  - Test: Load skill with minimal frontmatter
  - Document: Required vs optional frontmatter fields
  - Decision: Do we need to add frontmatter to existing skills?

- [ ] Task 2.2: Define standard frontmatter format (if required)
  - Fields: name, description, trigger, version, etc.
  - Example:
    ```yaml
    ---
    name: slack
    description: Slack integration skills
    trigger: "slack|channel|message"
    version: 1.0
    ---
    ```
  - Acceptance: Standard template for new skills

### 3. Configuration
- [ ] Task 3.1: Verify/update skills configuration in `deepagents.json`
  - Configuration:
    ```json
    {
      "skills": [
        {
          "path": "~/.nanobot/workspace/skills",
          "recursive": true,
          "pattern": "**/*.md"
        }
      ]
    }
    ```
  - Validation: Path exists, is readable

- [ ] Task 3.2: Test path resolution
  - Test `~` expansion
  - Test absolute paths
  - Test relative paths
  - Acceptance: All path formats work correctly

### 4. Directory Access Verification
- [ ] Task 4.1: Check file permissions
  - Command: `ls -la ~/.nanobot/workspace/skills/`
  - Verify: Gateway process can read skill files
  - Fix: Adjust permissions if needed (`chmod 644 *.md`)

- [ ] Task 4.2: Test with gateway running
  - Start gateway with skills config
  - Check logs for skill loading messages
  - Verify: No permission errors
  - Acceptance: Skills load without errors

### 5. Skill Updates (if frontmatter required)
- [ ] Task 5.1: Add frontmatter to existing skills
  - File: `slack/SKILL.md`
  - File: `litellm-proxy/SKILL.md`
  - Format: As defined in Task 2.2
  - Preserve: Existing Markdown content

- [ ] Task 5.2: Create skill template
  - File: `templates/SKILL_TEMPLATE.md`
  - Include: Frontmatter example + Markdown structure
  - Purpose: Guide for creating new skills

### 6. Testing
- [ ] Task 6.1: Write unit tests
  - File: `tests/unit/test_skills_middleware.py`
  - Test cases:
    1. `test_skills_config_loading()`: Verify config parses
    2. `test_skills_directory_exists()`: Check directory access
    3. `test_skill_file_loading()`: Load skill with/without frontmatter
    4. `test_invalid_skill_format()`: Handle malformed skills
    5. `test_skill_pattern_matching()`: Verify trigger patterns
  - Mock: File system, skill parsing

- [ ] Task 6.2: Write E2E tests
  - File: `tests/e2e/test_skills_integration.py`
  - Test scenarios:
    1. Trigger skill via Telegram message
    2. Verify skill execution (check logs/outputs)
    3. Test skill with context from memory
  - Use: Telegram simulator

### 7. Documentation
- [ ] Task 7.1: Update README.md
  - Section: Add "Skills" section
  - Content:
    - What skills are
    - Skill file format (with/without frontmatter)
    - How to create skills
    - How skills are triggered
    - Telegram examples
  
- [ ] Task 7.2: Document skill format requirements
  - Create: `docs/SKILLS_FORMAT.md`
  - Include: Frontmatter specification (if required)
  - Include: Example skills
  - Include: Best practices

---

## Deliverables

### Code Deliverables
- [ ] `nanobot_deep/config/schema.py`: Skills configuration types (if needed)
- [ ] Updated skill files (if frontmatter required):
  - [ ] `~/.nanobot/workspace/skills/slack/SKILL.md`
  - [ ] `~/.nanobot/workspace/skills/litellm-proxy/SKILL.md`
- [ ] `templates/SKILL_TEMPLATE.md`: Skill creation template

### Test Deliverables
- [ ] `tests/unit/test_skills_middleware.py`: Unit tests
- [ ] `tests/e2e/test_skills_integration.py`: E2E tests

### Documentation Deliverables
- [ ] README.md: Skills section
- [ ] `docs/SKILLS_FORMAT.md`: Skill format specification
- [ ] Frontmatter analysis report (in this ticket)

---

## Acceptance Criteria

### Functional Requirements
1. ✅ Skills load successfully from `~/.nanobot/workspace/skills/`
   - Verification: Check gateway logs for skill loading messages
   - Test: `test_skills_directory_loaded()`

2. ✅ Skills trigger correctly via Telegram/Slack messages
   - Verification: Send message matching skill trigger pattern
   - Test: `test_skill_triggered_by_message()`

3. ✅ Frontmatter requirements documented
   - Verification: `docs/SKILLS_FORMAT.md` exists with clear specification
   - Decision: Required vs optional documented

4. ✅ Gateway can access skills directory
   - Verification: No permission errors in logs
   - Test: `test_skills_directory_accessible()`

### Non-Functional Requirements
1. ✅ Performance: Skill loading < 1 second at startup
2. ✅ Security: Skills execute in controlled environment
3. ✅ Maintainability: Clear skill format documentation

### Testing Requirements
- ✅ Unit test coverage ≥ 80%
- ✅ All E2E tests passing
- ✅ CI/CD pipeline passing

---

## Testing Strategy

### Unit Tests
**File**: `tests/unit/test_skills_middleware.py`

**Test Cases**:
1. `test_skills_config_loading()`:
   - Load deepagents.json with skills config
   - Verify SkillsConfig object created
   - Check path, recursive, pattern fields

2. `test_skill_file_parsing()`:
   - Mock skill file with/without frontmatter
   - Parse skill content
   - Verify metadata extracted correctly

3. `test_skills_directory_scanning()`:
   - Mock filesystem with multiple skills
   - Scan directory recursively
   - Verify all skills discovered

4. `test_invalid_skill_handling()`:
   - Malformed YAML frontmatter
   - Missing required fields
   - Invalid Markdown syntax
   - Verify graceful error handling

**Mock Strategy**:
- Mock filesystem with `pathlib.Path`
- Mock skill file contents
- Don't mock YAML parsing (test real behavior)

### E2E Tests
**File**: `tests/e2e/test_skills_integration.py`

**Test Scenarios**:
1. **Skill triggering**:
   - Configure gateway with skills
   - Send Telegram message: "Show slack channels"
   - Verify: Slack skill triggered
   - Verify: Appropriate response received

2. **Skill with memory context**:
   - Previous conversation about Slack
   - Trigger skill: "Update that channel"
   - Verify: Skill uses memory context
   - Verify: Correct channel updated

3. **Multiple skills**:
   - Send message matching multiple skills
   - Verify: Correct skill selected
   - Verify: Skill priority/selection logic

**Verification Steps**:
1. Check gateway logs for skill execution
2. Verify Telegram response content
3. Check skill side effects (if any)

---

## Configuration

### Configuration Files
**File**: `~/.nanobot/deepagents.json`

```json
{
  "skills": [
    {
      "path": "~/.nanobot/workspace/skills",
      "recursive": true,
      "pattern": "**/*.md",
      "enabled": true
    }
  ],
  "memory": [...],
  "recursion_limit": 500
}
```

**Configuration Options**:
- `path`: Skills directory path
  - Type: string
  - Required: yes
  - Validation: Directory must exist

- `recursive`: Recursive search
  - Type: boolean
  - Default: true
  - Description: Search subdirectories

- `pattern`: File pattern
  - Type: string
  - Default: "**/*.md"
  - Description: Glob pattern for skill files

- `enabled`: Enable skills
  - Type: boolean
  - Default: true
  - Description: Toggle skills on/off

---

## Documentation Updates

### README.md
**Section**: Skills (after Memory section)

**Content**:
```markdown
## Skills

Skills are reusable capabilities loaded from Markdown files.

### Skill Format

Skills are defined in Markdown files with optional YAML frontmatter:

\`\`\`markdown
---
name: slack
description: Slack integration skills
trigger: "slack|channel|message"
---

# Slack Skills

[Skill documentation in Markdown]

## Commands

- List channels
- Send message
- Update channel
\`\`\`

### Configuration

\`\`\`json
{
  "skills": [
    {
      "path": "~/.nanobot/workspace/skills",
      "recursive": true
    }
  ]
}
\`\`\`

### Creating Skills

1. Create Markdown file in skills directory
2. Add frontmatter (if required)
3. Document skill capabilities
4. Restart gateway to load skill

### Usage Example

\`\`\`
User: Show me the Slack channels
Bot: [Uses slack skill to list channels]
\`\`\`

See `docs/SKILLS_FORMAT.md` for detailed format specification.
```

---

## Implementation Notes

### Key Decisions
1. **Decision**: TBD - Frontmatter required or optional?
   - **Analysis needed**: Review deepagents source code
   - **Impact**: May need to update existing skills
   - **Fallback**: Support both formats (with/without frontmatter)

2. **Decision**: Use deepagents skills (confirmed)
   - **Rationale**: Native LangGraph integration
   - **Alternative**: nanobot skills (rejected)

3. **Decision**: Recursive directory scanning
   - **Rationale**: Support organizing skills in subdirectories
   - **Example**: `skills/slack/`, `skills/github/`, etc.

### Important Considerations
- **Frontmatter Format**: YAML vs TOML vs JSON (deepagents decides)
- **Skill Isolation**: Are skills sandboxed? Security implications
- **Skill Priority**: If multiple skills match, which executes?
- **Skill Dependencies**: Can skills depend on each other?

### Potential Pitfalls
- **Permission Issues**: Gateway can't read skills directory
- **Path Resolution**: `~` expansion may fail in some environments
- **Frontmatter Parsing**: YAML syntax errors break skill loading
- **Pattern Matching**: Trigger patterns may be too broad/narrow

---

## Dependencies

### Blocked By
- Ticket #1: Memory middleware (provides context for skills) ✅

### Blocks
- Ticket #3: MCP Integration (skills and MCP tools work together)

### Parallel Work
- None (sequential Phase 1)

---

## Related Documentation

### Internal Docs
- Analysis: `docs/tickets/001-deepagents-integration-analysis.md`
- Roadmap: `docs/ROADMAP.md`
- Memory ticket: `docs/tickets/004-memory-middleware.md`

### External References
- [deepagents Skills Middleware](https://docs.langchain.com/oss/python/deepagents/skills)
- [LangGraph Tools](https://langchain-ai.github.io/langgraph/concepts/tools/)
- [YAML Frontmatter Spec](https://jekyllrb.com/docs/front-matter/)

---

## Questions & Clarifications

### Open Questions
1. **Question**: Does deepagents require YAML frontmatter for skills?
   - **Action**: Analyze source code in Task 1.2
   - **Impact**: May need to update existing skills

2. **Question**: How are skills triggered?
   - **Options**:
     - A: Pattern matching in frontmatter
     - B: LLM decides which skill to use
     - C: Explicit commands
   - **Action**: Determine from deepagents docs/source

3. **Question**: Can skills have dependencies?
   - **Context**: Can slack skill depend on auth skill?
   - **Action**: Research in deepagents docs

### Decisions Needed
1. **Frontmatter format**: TBD after analysis
2. **Skill template structure**: TBD after format decision

---

## Success Metrics

### Measurable Outcomes
- Skills load successfully: 100% of time
- Skill trigger accuracy: >90%
- Skill execution latency: <500ms
- Directory access: No permission errors

### Verification Methods
- Unit test pass rate
- E2E test pass rate
- Gateway log analysis
- User feedback on skill availability

---

## Rollback Plan

### If Something Goes Wrong
1. Set `"skills": []` in deepagents.json (disable skills)
2. Restart gateway
3. Agent works without skills (graceful degradation)
4. Investigate skill loading errors

### Monitoring
- Watch for skill loading errors at startup
- Monitor skill execution frequency
- Check for permission errors
- Warning signs: FileNotFoundError, YAMLError, PermissionError

---

## Timeline

### Estimated Breakdown
- Analysis & Research: 3 hours
- Frontmatter Investigation: 2 hours
- Configuration & Access Verification: 2 hours
- Skill Updates: 2 hours
- Testing: 4 hours
- Documentation: 2 hours
- **Total**: 10-15 hours

### Milestones
- [ ] Day 1-2: Analysis complete, frontmatter requirements documented
- [ ] Day 3: Configuration and access verified
- [ ] Day 4: Skills updated (if needed), tests written
- [ ] Day 5: Documentation complete, PR ready

---

## Post-Completion

### Follow-up Tasks
- [ ] Monitor skill usage in production
- [ ] Create additional example skills
- [ ] Gather user feedback on skill effectiveness
- [ ] Optimize skill loading performance

### Future Enhancements
- **Skill Marketplace**: Share skills across users
- **Skill Versioning**: Track skill updates
- **Skill Analytics**: Monitor skill usage patterns
- **Skill Testing Framework**: Test skills in isolation
