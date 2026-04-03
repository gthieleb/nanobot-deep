# nanobot-deep Development Roadmap

## Source of Truth

- Roadmap summary: this file
- Task tracking and planning: GitHub Issues only
- No local `docs/tickets/*` workflow

## Architecture Direction (Active)

- LLM/provider/model configuration comes from DeepAgents CLI configuration.
- nanobot configuration is used for messaging/channels only (Telegram and message routing).
- No cross-config fallback for LLM settings; fail fast with clear errors.

Primary tracking issues:
- #37: configuration strategy and migration execution
- #41: provider-specific bug (Zhipu/LiteLLM mismatch)
- #24: documentation/process migration to GitHub Issues as source of truth

## Phase Overview

### Phase 0: Critical Infrastructure (Complete)

- Released: v0.2.0
- Included CI/CD, baseline DeepAgent integration fixes, containerization improvements.

### Phase 1: Core Middleware (In Progress)

- Active work is tracked in GitHub issues, including:
  - #42 Multi-agent visibility and control
  - #43 Skills middleware integration
  - #44 Generic MCP integration migration
  - #45 Websearch tool integration
  - #46 A2A integration

### Phase 2: Runtime Features (Planned)

- #47 Streaming support
- #48 Backends and sandboxes architecture
- #49 Human-in-the-loop integration
- #57 Heartbeat mode
- #7 Cron integration evaluation

### Phase 3: User and Quality Features (Planned)

- #50 Media processing
- #51 README overhaul
- #52 Unit test coverage expansion
- #56 Chat vs Agent mode toggle
- #58 Speech-to-text
- #59 Text-to-speech

### Phase 4: Sandbox Research and Delivery (Planned)

- #53 Docker sandbox analysis
- #54 Kubernetes/Podman research
- #55 Docker sandbox MVP implementation
- #40 dependency unblocker for future sandbox support

## Status Symbols

- Complete: merged and released
- In Progress: active implementation
- Planned: scoped and ready for prioritization
- Blocked: waiting on dependency or decision

## Workflow

1. Create or pick a GitHub issue.
2. Verify upstream-first before implementation:
   - Check upstream `nanobot`
   - Check upstream `deepagents-cli`
   - Reuse/integrate where possible
3. Implement on feature branch linked to issue.
4. Validate with tests and open PR.

## Notes

- This repository no longer relies on local ticket markdown files for planning.
- Keep issue bodies current with scope, acceptance criteria, and implementation notes.

Last updated: 2026-04-03
