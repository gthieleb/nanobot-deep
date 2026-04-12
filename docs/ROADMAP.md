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
- #65: DeepAgents slash commands via Telegram (epic)
- #134: Vault setup and integration

## Phase Overview

### Phase 0: Critical Infrastructure (Complete)

- Released: v0.2.0
- Included CI/CD, baseline DeepAgent integration fixes, containerization improvements.

### Phase 1: Core Middleware (In Progress)

Active work tracked in GitHub issues:

**Blockers (must resolve before completion):**
- #121 SanitizingCheckpointerWrapper fails langgraph isinstance check
- #128 Docker Session Checkpointer Permission Error
- #41 Zhipu provider fails via ChatLiteLLM

**Configuration:**
- #37 Configuration strategy for DeepAgent settings
- #24 Evaluate docs/tickets approach vs GitHub Issues

**Commands (Telegram-first):**
- #65 DeepAgents slash commands via Telegram (epic)
  - Subtasks: #83 /model, #84 /remember, #85 /offload, #86 /tokens, #87 /clear, #88 /threads, #89 /reload, #90 /trace, #91 /editor, #92 /changelog, #93 /docs, #94 /feedback, #95 /version, #96 /help, #97 /quit
  - Platform: #108 Slack slash commands, #109 WhatsApp command menu

**Infrastructure:**
- #131 vault-user-provisioning (safe secret provisioning)
- #36 Integrate deepagents-cli SDK into nanobot gateway
- #34 Wire memoryWindow from config.json into runtime
- #71 Stream event naming fragility and output capture strategy

**Quality:**
- #99 Tests expect ChatLiteLLM but create_model resolves from config

### Phase 2: Infrastructure Stack (Planned)

Focus: Deployable infrastructure for Vault + LiteLLM-proxy + Observability.

**Vault:**
- #134 Vault setup and integration *(new)*
- #136 Agent reads secrets from Vault via MCP *(new)*

**LiteLLM Proxy:**
- #135 LiteLLM-proxy setup integration *(new)*
- #137 LiteLLM-proxy MCP-like configuration approach *(new)*

**HITL / ACP:**
- #120 Implement ACP interrupt handling for Telegram channel
- #125 Auto-approve logic for HITL interrupts (depends on #120)
- #61 ACP support for IDE integration

**Dev Tooling:**
- #126 LangGraph Dev Server integration for custom workflows

**Observability (delivered):**
- #8 Langfuse self-hosted Docker Compose and OTEL integration ✅ CLOSED

### Phase 3: Runtime Features (Planned)

- #42 Multi-agent visibility and control
- #43 Skills middleware integration with frontmatter validation
- #44 Generic MCP integration migration
- #45 Websearch tool integration
- #46 A2A integration
- #47 Streaming support
- #48 Backends and sandboxes architecture
- #49 Human-in-the-loop integration
- #57 Heartbeat mode
- #7 Cron integration evaluation
- #116 Pydantic serialization error with LangChain message chunks
- #35 Analysis: replace custom DeepAgent runtime with upstream CLI
- #38 Analysis: DeepAgents frontend features support
- #39 Analysis: Partial support gaps for DeepAgents features

### Phase 4: Sandbox, Quality and User Features (Planned)

- #53 Docker sandbox analysis
- #54 Kubernetes/Podman research
- #55 Docker sandbox MVP implementation
- #40 Resolve deepagents-cli/daytona websockets version conflict
- #50 Media processing
- #51 README overhaul for architecture, setup, and workflows
- #52 Unit test coverage expansion
- #56 Chat vs Agent mode toggle
- #58 Speech-to-text
- #59 Text-to-speech

## Infrastructure Track (Parallel / Optional)

Research and infrastructure changes that run independently of feature phases:

- #127 Analysis: Nomad + Consul as alternative to Docker deployment
- #81 Analysis: DeepAgent workflow for OpenCode in Daytona sandbox
- #82 Analysis: Async exception triage to GitHub issues
- #80 DeepAgent gateway logs error without root cause
- #124 Dockerfile extensions for Stundenplan-Skill system libraries

## Backlog

Lower priority items deferred for future consideration:

- #68 Feedback: prevent deep CLI startup pitfalls
- #33 Epic: Memory Architecture & Runtime Integration
- #32 Analysis: Ralph Mode + Memory Hybrid
- #28 Feature: Tool-Implementation (MessageTool, TodoTool, CronTool)
- #27 Feature: Missing DeepAgent CLI/Ralph features
- #26 Migrate Pydantic model config to ConfigDict
- #25 Add user systemd + Docker deployment patterns
- #23 Integrate Z.AI Vision MCP Server
- #22 Fix ping handler in group mode (duplicate of #21)
- #21 Fix ping handler in group mode
- #19 Analysis: Tenant Support & Data Separation
- #18 Analysis: RAG for Historical Telegram Conversations
- #13 Analysis: Store Telegram reply_to ID in Memory Database
- #6 Evaluate Redis vs SQLite checkpointer
- #5 Create migration script for legacy JSONL sessions
- #4 SessionCheckpointer.setup() hangs during JSON migration

## Status Symbols

- ✅ Complete: merged and released
- 🔄 In Progress: active implementation
- 📋 Planned: scoped and ready for prioritization
- 🔒 Blocked: waiting on dependency or decision
- 🗂️ Backlog: deferred, low priority

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
- Phase 2 focuses on the infrastructure stack: Vault + LiteLLM-proxy + OTEL observability.
- All issues tracked in GitHub Project: **Nanobot-Deep Dev**

Last updated: 2026-04-12 (verified)
