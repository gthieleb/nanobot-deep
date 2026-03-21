# Ticket: Analysis: Tenant Support & Data Separation

## Overview

Analyze tenant support and data separation for nanobot-deep to prevent data leakage between different users, organizations, or contexts when multiuser setups are deployed in the future.

**Note:** This is an analysis ticket, not an implementation ticket. Implementation should wait until multiuser setups are needed.

## Background

Currently, nanobot-deep has no tenant separation:
- All sessions are isolated by `chat_id` only
- All users in a group share the same session context
- No differentiation between personal vs business vs customer data
- RAG searches across all data (no tenant filtering)

### Current Multiuser Status

**Current Setup (2026-03-21):**
- Telegram: Single user (`allowFrom: ["Ostkind79"]`)
- Slack: Potentially multiuser (`allowFrom: ["*"]`), but no active multiuser operation
- WhatsApp/Discord/Email: Disabled or no allowlist
- **Confirmed:** No multiuser setups currently running

**Impact:**
- ✅ No urgency to implement tenant support
- ✅ Can analyze and design now without pressure
- ✅ Implementation can be done when needed
- ❌ Cannot test multiuser scenarios yet

## Problems

### 1. Data Leakage in Groups

All users in a group share the same session context.

```
Group "nanobot-deep-discussions" (chat_id=-1001234567890)
├─ User A: "My password is abc123"
├─ User B: "What's the password?"
└─ Bot: "abc123" ❌ Data leakage!
```

### 2. No Personal vs Business Separation

Personal and business conversations are not isolated.

### 3. RAG Cross-Tenant Leakage

RAG searches return results from all tenants.

```
# User A from "personal" tenant asks:
"What are my notes?"

# RAG returns (without tenant filter):
# - Notes from "business" tenant ❌ Data leakage!
# - Notes from "customer X" tenant ❌ Data leakage!
# - Notes from "personal" tenant ✅ Correct
```

### 4. Memory/Sessions Without Tenant-Awareness

```
# Session key based only on chat_id
session_key = f"telegram:{chat_id}"  # ← No tenant!

# All users in group share same session
```

## Proposed Solutions

### Option A: Per-User Tenant Isolation
- Each user gets their own tenant
- Strict data separation
- High memory overhead
- Good for: Personal assistant scenario

### Option B: Per-Group Tenant Isolation
- Each group gets a tenant
- Users in group share context (intentional)
- Lower memory overhead
- Good for: Team collaboration scenario

### Option C: Explicit Tenant Configuration
- Tenants configured manually
- Flexible (Personal/Business/Customer)
- Requires tenant management
- Good for: Organization with different contexts

### Option D: Hybrid Approach (Recommended)
- Per-user tenant for DMs
- Per-group tenant for groups
- Configurable per channel
- Most flexible
- Good for: Mixed scenarios

## Analysis Tasks

### Phase 1: Analysis (NOW - Non-Critical)

- [x] Define tenant requirements for future multiuser setups
- [ ] Analyze use cases (personal/business/customer)
- [ ] Design tenant architecture
- [ ] Evaluate impact on existing tickets (#12, #13, #18)
- [ ] Compare implementation options (A, B, C, D)
- [ ] Document recommended approach

### Phase 2: Design (When Multiuser Setups Start)
- [ ] Design tenant manager component
- [ ] Design tenant-aware session keys
- [ ] Design tenant-aware RAG filtering
- [ ] Design tenant metadata storage
- [ ] Design access control system

### Phase 3: Implementation (When Multiuser Setups Start)
- [ ] Implement Tenant Manager
- [ ] Extend SessionCheckpointer with tenant_id
- [ ] Extend RAG with tenant filtering
- [ ] Update E2E tests for tenant isolation
- [ ] Update Issue #13 for tenant-aware reply-to

## Dependencies

- ✅ Phase 0 (v0.2.0) - Infrastructure complete
- ⏸️ Phase 1 (v0.3.0) - Memory Middleware
- ⏸️ Issue #12 (E2E Tests) - Tenant testing
- ⏸️ Issue #13 (Reply-to) - Tenant-aware threads
- ⏸️ Issue #18 (RAG) - Tenant filtering

## Priority

**LOW** - Not critical for current setup (no multiuser operations running)

**Should be implemented:**
- Before multiuser setups are deployed
- Before E2E tests for groups are used in production
- Before RAG is integrated with historical data

## Benefits of Waiting

- ✅ No pressure to rush implementation
- ✅ Can design architecture properly
- ✅ Can test other features first
- ✅ Learn from actual multiuser requirements
- ✅ Avoid over-engineering for unknown use cases

## When to Implement

**Triggers:**
1. Multiuser Slack setup is deployed
2. Multiple users need bot access in same group
3. Business vs personal separation is needed
4. Customer-specific bot instances are required
5. Issue #12 group tests are used in production
6. Issue #18 RAG is integrated with real data

## Expected Outcome

### Phase 1: Analysis (This Ticket)
- ✅ Technical design document (this file)
- ✅ Tenant requirements analysis
- ✅ Comparison of implementation options
- ✅ Recommendations for future work

### Phase 2: Design (When Needed)
- [ ] Tenant architecture design
- [ ] Data model changes
- [ ] Component design
- [ ] Integration plan with existing tickets

### Phase 3: Implementation (When Needed)
- [ ] Tenant Manager component
- [ ] Tenant-aware sessions
- [ ] Tenant-aware RAG
- [ ] Updated E2E tests
- [ ] Updated Issue #13 implementation
- [ ] Updated Issue #18 implementation

## References

- nanobot-deep README: https://github.com/gthieleb/nanobot-deep#readme
- SessionCheckpointer: SQLite-based session persistence
- Telegram Bot API: https://core.telegram.org/bots/api
- Related: End-to-End Testing (#12)
- Related: Telegram reply_to ID (#13)
- Related: RAG for Historical Conversations (#18)
