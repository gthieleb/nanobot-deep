# Documentation TODO

## Current Policy

- GitHub Issues are the single source of truth for planning and task tracking.
- Local `docs/tickets/*` files are deprecated and being removed.

## Active Documentation Tasks

1. Keep `docs/ROADMAP.md` aligned with active GitHub issues.
2. Keep architecture policy explicit in docs:
   - DeepAgents config for LLM/provider/model
   - nanobot config for messaging/channels
   - no fallback between config systems
3. Keep issue templates and labels consistent.
4. Ensure each implementation issue includes an upstream-first check section.

## Operational Notes

- Before implementation, verify capability in:
  - upstream `nanobot`
  - upstream `deepagents-cli`
- Prefer reuse/integration over re-implementation.

Created: 2026-03-18
Last Updated: 2026-04-03
