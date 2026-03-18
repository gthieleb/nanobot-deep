# nanobot-deep Development Roadmap

## Quick Reference

- **Current Phase**: Phase 1 - Core Middleware
- **Current Ticket**: Ready to start #1 (Memory Middleware)
- **Latest Release**: v0.2.0 (2026-03-18)
- **Next Release Target**: v0.3.0 (after Phase 1 completion)

## Documentation Structure

- **This file**: High-level overview of all phases and tickets
- **Ticket files**: `docs/tickets/NNN-ticket-name.md` - Comprehensive specifications
- **GitHub Issues**: Automated tracking with labels and milestones
- **AGENTS.md**: Ticket management workflow documentation

## Phase Overview

### ✅ Phase 0: Critical Infrastructure (COMPLETE)

**Status**: Complete  
**Duration**: 2026-03-18  
**Release**: v0.2.0

| Ticket | Name | Status | Branch | PR | Release |
|--------|------|--------|--------|----|---------| 
| #0 | Commit & Merge + CI/CD | ✅ Complete | `fix/deep-agent-message-flow` | [#11](https://github.com/gthieleb/nanobot-deep/pull/11) | [v0.2.0](https://github.com/gthieleb/nanobot-deep/releases/tag/v0.2.0) |

**Deliverables**:
- ChatLiteLLM + AsyncSqliteSaver fixes
- GitHub Actions CI/CD pipeline (test + coverage + lint + docker + release)
- Dockerfile with multi-stage build
- Conventional Commits documentation
- Docker image: `ghcr.io/gthieleb/nanobot-deep:0.2.0`

---

### 🔄 Phase 1: Core Middleware (IN PROGRESS)

**Status**: Ready to start  
**Approach**: Sequential (one ticket at a time)  
**Target Release**: v0.3.0  
**Estimated Duration**: 2-3 weeks

| Ticket | Name | Status | Branch | PR | Dependencies | Details |
|--------|------|--------|--------|----|--------------| --------|
| #1 | Memory Middleware | 🔜 Ready | `feature/memory-middleware` | - | #0 ✅ | [004](tickets/004-memory-middleware.md) |
| #2 | Skills Middleware | ⏸️ Pending | `feature/skills-middleware` | - | #1 | [005](tickets/005-skills-middleware.md) |
| #3 | MCP Integration | ⏸️ Pending | `feature/mcp-integration` | - | #2 | [006](tickets/006-mcp-integration.md) |
| #4 | WebSearch Tool | ⏸️ Pending | `feature/websearch-tool` | - | #3 | [007](tickets/007-websearch-tool.md) |
| #5 | A2A Integration | ⏸️ Pending | `feature/a2a-integration` | - | #4 | [008](tickets/008-a2a-integration.md) |

**Key Features**:
- Conversation context memory
- Skills from Markdown files
- Model Context Protocol tools
- Web search capability
- Agent-to-agent communication

---

### ⏸️ Phase 2: Features (PENDING)

**Status**: Blocked by Phase 1  
**Approach**: Sequential  
**Target Release**: v0.4.0  
**Estimated Duration**: 2-3 weeks

| Ticket | Name | Status | Branch | Dependencies | Details |
|--------|------|--------|--------|--------------|---------|
| #6 | Streaming Support | ⏸️ Pending | `feature/streaming-support` | #5 | [009](tickets/009-streaming-support.md) |
| #7 | Backends & Sandboxes | ⏸️ Pending | `feature/backends-sandboxes` | #6 | [010](tickets/010-backends-sandboxes.md) |
| #8 | Human-in-the-Loop | ⏸️ Pending | `feature/human-in-the-loop` | #7 | [011](tickets/011-human-in-the-loop.md) |
| #19 | Lightweight Gateway | ⏸️ Pending | `refactor/lightweight-gateway` | #8 | [019](tickets/019-lightweight-gateway.md) |

**Key Features**:
- Progressive message streaming (highest UX impact)
- Backend configuration and sandbox support
- Tool approval with Telegram/Slack buttons
- Gateway refactoring for maintainability (blocks Phase 3 gateway features)

---

### ⏸️ Phase 3: User Features (PENDING)

**Status**: Blocked by Phase 2  
**Approach**: Parallel (spawn all agents simultaneously)  
**Target Release**: v0.5.0  
**Estimated Duration**: 1-2 weeks (parallel work)

| Ticket | Name | Status | Branch | Dependencies | Details |
|--------|------|--------|--------|--------------|---------|
| #9 | Todo-List Frontend | ⏸️ Pending | `feature/todo-frontend` | #19 | [012](tickets/012-todo-frontend.md) |
| #10 | Media Processing | ⏸️ Pending | `feature/media-processing` | #19 | [013](tickets/013-media-processing.md) |
| #11 | README Documentation | ⏸️ Pending | `docs/comprehensive-readme` | #19 | [014](tickets/014-readme-documentation.md) |
| #12 | Unit Tests | ⏸️ Pending | `tests/agent-subagent-config` | #19 | [015](tickets/015-unit-tests.md) |
| #20 | Chat vs Agent Mode | ⏸️ Pending | `feature/chat-agent-mode` | #19 | [020](tickets/020-chat-agent-mode.md) |
| #21 | Heartbeat Mode | ⏸️ Pending | `feature/heartbeat-mode` | #19 | [021](tickets/021-heartbeat-mode.md) |
| #22 | Cronjob Support | ⏸️ Pending | `feature/cronjob-support` | #19 | [022](tickets/022-cronjob-support.md) |
| #23 | Speech-to-Text | ⏸️ Pending | `feature/speech-to-text` | #19 | [023](tickets/023-speech-to-text.md) |
| #24 | Text-to-Speech | ⏸️ Pending | `feature/text-to-speech` | #19 | [024](tickets/024-text-to-speech.md) |
| #25 | ACP Support | ⏸️ Pending | `feature/acp-support` | #19 | [025](tickets/025-acp-support.md) |

**Note**: These tickets can be worked on in parallel by spawning multiple agents.

**Key Features**:
- Todo list display in Telegram/Slack
- Full media type support
- Comprehensive documentation
- Test coverage improvements
- Chat vs Agent mode toggle
- Heartbeat and cronjob scheduling
- Voice I/O (STT/TTS) with German support
- IDE integration via ACP (Zed, JetBrains, Neovim)

---

### ⏸️ Phase 4: Advanced Features (PENDING)

**Status**: Blocked by Phase 3  
**Approach**: Analysis → Implementation (Sequential for analysis, then implementation)  
**Target Release**: v1.0.0  
**Estimated Duration**: 3-4 weeks

| Ticket | Name | Status | Branch | Dependencies | Details |
|--------|------|--------|--------|--------------|---------|
| #13 | Docker Sandbox Analysis | ⏸️ Pending | `analysis/docker-sandbox` | #12 | [016](tickets/016-docker-sandbox-analysis.md) |
| #14 | K8s/Podman Research | ⏸️ Pending | `analysis/k8s-podman` | #12 (parallel with #13) | [017](tickets/017-k8s-podman-research.md) |
| #15 | Docker Sandbox Implementation | ⏸️ Pending | `feature/docker-sandbox` | #13 ✅ | [018](tickets/018-docker-sandbox-impl.md) |

**Note**: Tickets #13 and #14 run in parallel (analysis phase). Ticket #15 waits for #13 decision.

**Key Features**:
- Container-based code execution sandboxing
- Security analysis and threat modeling
- Kubernetes/Podman compatibility research
- Production-ready sandbox implementation

---

## Status Symbols

- ✅ **Complete**: Merged to main, released
- 🔄 **In Progress**: Active development, PR open
- 🔜 **Ready**: Dependencies met, ready to start
- ⏸️ **Pending**: Blocked by dependencies
- ⚠️ **Blocked**: Issues preventing progress
- ❌ **Cancelled**: No longer needed

---

## Release Schedule

| Version | Phase | Target Date | Status | Features |
|---------|-------|-------------|--------|----------|
| v0.2.0 | Phase 0 | 2026-03-18 | ✅ Released | CI/CD + ChatLiteLLM + AsyncSqliteSaver |
| v0.3.0 | Phase 1 | TBD | 🔜 Planned | Memory + Skills + MCP + WebSearch + A2A |
| v0.4.0 | Phase 2 | TBD | ⏸️ Pending | Streaming + Backends + HITL |
| v0.5.0 | Phase 3 | TBD | ⏸️ Pending | Todos + Media + Docs + Tests |
| v1.0.0 | Phase 4 | TBD | ⏸️ Pending | Docker Sandbox |

---

## Ticket Details

All tickets have comprehensive documentation in `docs/tickets/`:

- **Background**: Current state, desired state, context
- **Technical Approach**: Architecture, implementation strategy
- **Tasks**: Detailed breakdown with acceptance criteria
- **Deliverables**: Code, tests, documentation
- **Acceptance Criteria**: Functional and non-functional requirements
- **Testing Strategy**: Unit tests, E2E tests, verification steps
- **Implementation Notes**: Key decisions, considerations, pitfalls

---

## GitHub Integration

### Issues
Each ticket has a corresponding GitHub issue:
- **Labels**: `phase-1`, `phase-2`, `priority-high`, `feat`, `fix`, etc.
- **Milestones**: Mapped to release versions (v0.3.0, v0.4.0, etc.)
- **Linked to**: Branches, PRs, commits

### Projects
Consider using GitHub Projects board:
- **Columns**: Backlog, Ready, In Progress, Review, Done
- **Automation**: Auto-move cards based on PR status

### Workflow
See `AGENTS.md` for detailed ticket management workflow.

---

## Contributing

### For AI Agents
1. Read `ROADMAP.md` to see current phase/ticket
2. Read detailed ticket file in `docs/tickets/`
3. Create GitHub issue from ticket
4. Follow implementation workflow in `AGENTS.md`

### For Human Developers
1. Check `ROADMAP.md` for available tickets
2. Read ticket specification in `docs/tickets/`
3. Create GitHub issue (or ask AI to create it)
4. Follow conventional commit format
5. Create PR linking to issue

---

## Questions?

- **Ticket workflow**: See `AGENTS.md` → "Ticket Management" section
- **Conventional commits**: See `AGENTS.md` → "Conventional Commits" section
- **CI/CD pipeline**: See `.github/workflows/ci-cd.yml`
- **Project goals**: See `README.md`

---

Last updated: 2026-03-18
