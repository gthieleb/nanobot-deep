# Analysis: Voice-Triggered Model Escalation

## Overview

Implement voice-triggered model escalation allowing users to dynamically switch between model tiers via spoken commands during voice/audio sessions. This enables starting with fast/cheap local models and escalating to more capable cloud models on demand.

## Reference Implementation

**Source**: [OpenClaw PR #46362](https://github.com/openclaw/openclaw/pull/46362)

### Key Mechanisms

1. **Trigger Phrase Detection**: Regex patterns in voice transcription pipeline
2. **Session Model Override**: Persisted model selection via session store
3. **Tier Mapping**:
   - `"go deep"` / `"think harder"` → Claude Sonnet (high tier)
   - `"switch to haiku"` / `"medium mode"` → Claude Haiku (medium tier)
   - `"go fast"` / `"quick mode"` → Default local model

### Identified Issues (from PR review)

1. **False-positive triggers**: Overly broad patterns (e.g., "think about that") fire on normal speech
2. **Trigger forwarding**: Commands like "go deep" sent to agent as queries after escalation
3. **Early session handling**: Escalation fails on first utterance before session persisted

## Nanobot Ecosystem Check

**Repository**: https://github.com/HKUDS/nanobot/issues

- No existing tickets for voice-triggered escalation
- No PRs related to dynamic model switching
- Related open issues:
  - #2072: Feature Request: Native Multi-Agent Routing
  - #2098: Agent loop performance issues

## LiteLLM Proxy Evaluation

**Documentation**: https://docs.litellm.ai/docs/simple_proxy

### Readiness Assessment: ✅ READY

| Feature | Status | Notes |
|---------|--------|-------|
| Multi-model support | ✅ | 100+ LLMs supported |
| Dynamic model routing | ✅ | Load balancing, fallbacks |
| Custom hooks/plugins | ✅ | Request/response modification |
| Session management | ✅ | Virtual keys, budgets per user |
| Caching | ✅ | OpenAI/Anthropic prompt caching |
| Guardrails | ✅ | Policy-based controls |
| Rate limiting | ✅ | Per-key/user budgets |

### Integration Path

LiteLLM proxy can serve as the model routing layer:

```
Voice Input → Transcription → Trigger Detection → LiteLLM Proxy → Model Selection
                                    ↓
                            Session Override
```

**Advantages**:
- Unified API for all providers (local Ollama, Anthropic, OpenAI)
- Built-in fallback chains (local → cloud on failure)
- Cost tracking and budgets
- Custom hooks for trigger detection injection

## Implementation Proposal

### Phase 1: Core Escalation Mechanism

1. **Trigger Detection Middleware**
   - Pattern matching on transcribed text
   - Explicit command syntax (avoid false positives)
   - Return boolean to stop/continue pipeline

2. **Session Model Override**
   - Extend session config with `model_override` field
   - Persist across turns until explicitly changed
   - Fallback to default on session reset

3. **Recommended Trigger Phrases**
   ```
   High tier:  "escalate" / "use sonnet" / "go deep"
   Medium:     "use haiku" / "medium mode"
   Default:    "go local" / "use default" / "quick mode"
   ```

### Phase 2: LiteLLM Integration

1. Deploy LiteLLM proxy as model gateway
2. Configure model tier groups
3. Add escalation hook to modify `model` parameter
4. Enable fallback chains for resilience

### Phase 3: Voice Interface (Optional)

1. Add audio transcription pipeline
2. Real-time trigger detection
3. Voice feedback on mode switch

## Technical Considerations

### OpenClaw PR Lessons

1. **Return early on trigger match** - Don't forward command text to agent
2. **Handle new sessions** - Create session entry before applying override
3. **Explicit phrases only** - Avoid conversational false positives
4. **User feedback** - Confirm mode switch (audio/text)

### LiteLLM Configuration Example

```yaml
model_list:
  - model_name: "fast"
    litellm_params:
      model: "ollama/llama3.1:8b"
  - model_name: "medium"
    litellm_params:
      model: "anthropic/claude-haiku-4-5"
  - model_name: "deep"
    litellm_params:
      model: "anthropic/claude-sonnet-4-6"

router_settings:
  routing_strategy: "simple-shuffle"
  num_retries: 2
  fallbacks: [{"fast": ["medium", "deep"]}]
```

## Next Steps

1. [ ] Design session schema extension for model override
2. [ ] Implement trigger detection with explicit phrases
3. [ ] Add LiteLLM proxy configuration
4. [ ] Create escalation middleware
5. [ ] Add unit tests for trigger detection
6. [ ] Add E2E tests for escalation flow

## References

- OpenClaw PR: https://github.com/openclaw/openclaw/pull/46362
- LiteLLM Proxy: https://docs.litellm.ai/docs/simple_proxy
- LiteLLM Routing: https://docs.litellm.ai/docs/routing-load-balancing
