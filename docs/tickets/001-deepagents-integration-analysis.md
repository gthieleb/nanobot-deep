# Ticket: Analyze DeepAgents SDK/CLI Integration

## Summary

Analyze the deepagents SDK and CLI codebase to determine if a more robust integration is possible, addressing current limitations around LLM provider support and LiteLLM usage.

## Links

- **DeepAgents CLI Docs**: https://docs.langchain.com/oss/python/deepagents/cli/overview
- **GitHub Repository**: https://github.com/langchain-ai/deepagents
- **SDK Docs**: https://docs.langchain.com/oss/python/deepagents/overview
- **Providers Reference**: https://docs.langchain.com/oss/python/deepagents/cli/providers

## Current Implementation

### nanobot-deep (`nanobot_deep/agent/deep_agent.py`)
- Uses `ChatLiteLLM` from `langchain-litellm` for model initialization
- Custom bridge layer (`LangGraphBridge`) for message translation
- Custom `DeepAgentsConfig` schema for configuration
- Manual MCP connection via `langchain-mcp-adapters`
- Calls `create_deep_agent()` from deepagents but wraps it with custom logic

### Current Limitations
1. **LiteLLM dependency** - Uses `ChatLiteLLM` which may not support all providers that LangChain natively supports
2. **Duplicate configuration** - Custom `DeepAgentsConfig` duplicates some deepagents config options
3. **Bridge overhead** - Custom message translation layer adds complexity
4. **Missing CLI features** - Skills, memory, sandboxes not fully integrated

## DeepAgents SDK Capabilities

### Model Support
DeepAgents uses `langchain.chat_models.init_chat_model()` which supports:
- **Built-in**: OpenAI, Anthropic, Google (Gemini)
- **Optional extras**: Ollama, Groq, xAI, Azure, AWS Bedrock, Cohere, Fireworks, Together, Mistral, etc.

```python
from langchain_litellm import ChatLiteLLM

model = ChatLiteLLM(model="openai/gpt-4o")
model = ChatLiteLLM(model="anthropic/claude-sonnet-4-5")
model = ChatLiteLLM(model="ollama/llama3.2")
```

### Core Features
- **Tools**: `read_file`, `write_file`, `edit_file`, `ls`, `glob`, `grep`, `execute`, `http_request`, `web_search`, `task`, `ask_user`, `compact_conversation`, `write_todos`
- **MCP Support**: Via `langchain-mcp-adapters` with auto-discovery
- **Skills**: Project and user-level skill directories with `SKILL.md` files
- **Memory**: Persistent memory storage in `~/.deepagents/<agent>/memories/`
- **Sandboxes**: Modal, Daytona, Runloop for remote execution
- **Human-in-the-loop**: Interrupt/approval system for sensitive operations
- **Tracing**: LangSmith integration

### CLI Features (potential reuse)
- Non-interactive mode (`-n`, piped stdin)
- Model switching mid-session (`/model`)
- Thread management (`/threads`, `/clear`)
- Configuration via `~/.deepagents/config.toml`
- Shell allow-lists for security

## Proposed Analysis Tasks

### 1. Provider Integration Analysis
- [ ] Compare `init_chat_model()` vs `ChatLiteLLM` provider coverage
- [ ] Determine if nanobot's config can map to `init_chat_model()` format
- [ ] Assess impact on existing LiteLLM-based configurations

### 2. SDK Integration Assessment
- [ ] Evaluate direct use of `create_deep_agent()` without custom wrapper
- [ ] Identify which bridge functions can be removed
- [ ] Determine if `DeepAgentsConfig` can be simplified or replaced

### 3. Feature Gap Analysis
- [ ] Compare nanobot's `DeepGateway` vs deepagents CLI architecture
- [ ] Identify missing features in current implementation
- [ ] Assess feasibility of using deepagents CLI as subprocess vs library integration

### 4. Configuration Harmonization
- [ ] Map `~/.nanobot/config.json` to `~/.deepagents/config.toml`
- [ ] Determine config precedence and merging strategy
- [ ] Plan migration path for existing users

### 5. Channel Integration
- [ ] How would deepagents work with nanobot's channel system (Telegram, WhatsApp, etc.)?
- [ ] Can deepagents CLI run as a daemon with message bus integration?
- [ ] Assess `MessageBus` + `InboundMessage`/`OutboundMessage` compatibility

## Potential Integration Approaches

### Option A: SDK-First (Recommended)
Use deepagents SDK directly, minimal custom code:
```python
from deepagents import create_deep_agent
from langchain.chat_models import init_chat_model

model = init_chat_model("anthropic:claude-sonnet-4-5")
agent = create_deep_agent(
    model=model,
    system_prompt=custom_prompt,
    checkpointer=checkpointer,
)

# Direct invoke without bridge
result = agent.invoke({"messages": [HumanMessage(content=msg.content)]})
```

**Pros**: 
- Full provider support via `init_chat_model()`
- Less maintenance burden
- Automatic updates from deepagents releases

**Cons**: 
- Less control over agent behavior
- May need to adapt nanobot's message format

### Option B: CLI Wrapper
Run deepagents CLI as subprocess:
```python
import subprocess

result = subprocess.run(
    ["deepagents", "-n", message, "--model", model],
    capture_output=True,
    text=True,
)
```

**Pros**:
- Zero integration complexity
- All CLI features available

**Cons**:
- No real-time streaming
- Process overhead
- Harder to integrate with message bus

### Option C: Hybrid (Current + Enhancements)
Keep current architecture but:
- Replace `ChatLiteLLM` with `init_chat_model()`
- Import tools directly from deepagents
- Use deepagents' skill/memory system

## Questions to Resolve

1. Does `init_chat_model()` support all providers that LiteLLM supports?
2. Can we pass a custom checkpointer to `create_deep_agent()` and maintain session persistence?
3. How does deepagents handle multi-turn conversations with checkpointing?
4. What is the minimal set of deepagents tools we need vs custom nanobot tools?
5. Can deepagents' skills system replace nanobot's skills paths?

## Success Criteria

- [ ] All nanobot-supported providers work without LiteLLM dependency
- [ ] E2E tests pass with new integration
- [ ] Token usage and costs are comparable or better
- [ ] Configuration is simpler for end users
- [ ] All channel integrations continue to work

## References

- Current DeepAgent implementation: `nanobot_deep/agent/deep_agent.py`
- Message bridge: `nanobot_deep/langgraph/bridge.py`
- Config schema: `nanobot_deep/config/schema.py`
- DeepAgents source: `libs/cli/` and `libs/sdk/` in deepagents repo
