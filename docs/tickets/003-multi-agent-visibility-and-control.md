# Ticket: Multi-Agent Visibility, Discovery, and Control via Chat Channels

## Summary

Analyze how to visualize available agents in nanobot-deep and enable users to list, select, and delegate tasks to specific agents via chat channels (Telegram, Slack, WhatsApp). The challenge is that `@mentions` in these channels reference contacts, not agents. Need to design an interactive agent selection experience using inline keyboards and develop cross-chat task status tracking.

## References

### Nanobot PR
- **Telegram Inline Keyboards PR**: https://github.com/HKUDS/nanobot/pull/1273
  - Adds `buttons` field to `OutboundMessage`
  - `InlineButton` model with `label` and `callback_data`
  - Config key: `keyboard_buttons_enabled` (default: false)
  - Poll support via `poll_question` + `poll_options`

### OpenClaw Multi-Agent Implementation
- **Repository**: https://github.com/openclaw/openclaw
- **Key Implementation Files**:
  - `src/agents/tools/sessions-list-tool.ts` - Lists sessions with filters
  - `src/agents/tools/sessions-send-tool.ts` - Agent-to-agent messaging
  - `src/agents/tools/sessions-spawn-tool.ts` - Spawns subagents
  - `src/agents/tools/agents-list-tool.ts` - Lists available agent IDs
  - `src/agents/subagent-registry.ts` - Tracks active subagent runs

## The Problem

### Current Limitations
1. **No @agent mentions**: In Telegram/WhatsApp/Slack, `@` only references human contacts, not AI agents
2. **No agent discovery**: Users don't know what specialized agents are available
3. **No task tracking**: No visibility into what agents are working on across chats
4. **No interactive selection**: No way to pick an agent via UI

### Desired Experience
```
User: Analyze this codebase and write tests
Bot: I can delegate this to specialized agents:
     
     [🔍 Code Reviewer] [📝 Test Writer] [🛡️ Security Scanner]
     
     Or I can handle it myself: [✋ Main Agent]

User: [clicks Test Writer button]
Bot: ✅ Delegated to Test Writer agent. Task ID: abc123
     
     Use /status abc123 to check progress
     Use /agents to see all active tasks

User: /status abc123
Bot: Task abc123 (Test Writer):
     Status: In Progress (5/10 tests written)
     Started: 2 min ago
     ETA: ~3 min remaining
```

## OpenClaw Reference Architecture

### Session Tools
```typescript
// sessions_list - Discover active sessions
{
  kinds: ["main", "subagent", "channel"],
  activeWithinMinutes: 30,
  limit: 20
}

// sessions_send - Message another agent
{
  sessionKey: "agent:test-writer:main",
  message: "Write tests for src/auth.ts",
  timeoutSeconds: 300  // 0 = fire-and-forget
}

// sessions_spawn - Create subagent
{
  agentId: "test-writer",
  task: "Write unit tests for authentication module",
  label: "test-task-1",
  spawnMode: "session",  // or "run"
  cleanup: "delete"  // or "keep"
}

// agents_list - List available agent IDs
// Returns: { agents: [{ id, name, configured }] }
```

### Session Key Format
```
agent:<agentId>:main                    # Main session
agent:<agentId>:subagent:<uuid>         # Subagent
agent:<agentId>:<channel>:<peerKind>:<peerId>  # Channel session
```

### Visibility Scopes
- `"self"` - Only current session
- `"tree"` - Current session + spawned children (default)
- `"agent"` - All sessions in same agent
- `"all"` - Any session (requires policy)

### Agent-to-Agent Policy
```json
{
  "tools": {
    "agentToAgent": {
      "enabled": true,
      "allow": ["code-reviewer", "test-writer", "*"]
    }
  }
}
```

## Proposed Implementation for nanobot-deep

### Phase 1: Agent Registry & Discovery

#### 1.1 Agent Configuration
```python
# ~/.nanobot/deepagents.json
{
  "subagents": [
    {
      "name": "code-reviewer",
      "description": "Reviews code for bugs, style, and best practices",
      "model": "anthropic/claude-sonnet-4-5",
      "system_prompt": "You are a code reviewer...",
      "tools": ["read_file", "glob", "grep"]
    },
    {
      "name": "test-writer",
      "description": "Writes comprehensive unit and integration tests",
      "model": "openai/gpt-4o",
      "system_prompt": "You write tests...",
      "tools": ["read_file", "write_file", "execute"]
    }
  ]
}
```

#### 1.2 Agent List Command
```python
# In DeepAgent
@tool
def list_agents() -> dict:
    """List available agents for task delegation."""
    return {
        "agents": [
            {"id": "main", "name": "Main Agent", "description": "General purpose"},
            {"id": "code-reviewer", "name": "Code Reviewer", "description": "..."},
            {"id": "test-writer", "name": "Test Writer", "description": "..."},
        ]
    }
```

### Phase 2: Interactive Agent Selection via Inline Keyboards

#### 2.1 OutboundMessage Extension (from PR #1273)
```python
# nanobot/bus/events.py
class InlineButton(BaseModel):
    label: str
    callback_data: str

class OutboundMessage(BaseModel):
    channel: str
    chat_id: str
    content: str
    metadata: dict = {}
    buttons: list[list[InlineButton]] | None = None
    poll: PollData | None = None
```

#### 2.2 Agent Selection Flow
```python
# In DeepAgent or Gateway
async def _handle_delegation_request(self, msg: InboundMessage) -> OutboundMessage:
    agents = self._get_relevant_agents(msg.content)
    
    if len(agents) > 1:
        # Present inline keyboard
        buttons = [
            [InlineButton(label=f"🤖 {a.name}", callback_data=f"delegate:{a.id}")]
            for a in agents
        ]
        buttons.append([InlineButton(label="✋ Main Agent", callback_data="delegate:main")])
        
        return OutboundMessage(
            channel=msg.channel,
            chat_id=msg.chat_id,
            content=f"Which agent should handle this task?\n\n{self._summarize_agents(agents)}",
            buttons=buttons,
            metadata={"pending_delegation": True}
        )
    else:
        # Auto-delegate or handle directly
        return await self._delegate_to_agent(agents[0], msg)
```

#### 2.3 Callback Handler
```python
# In TelegramChannel or Gateway
async def _handle_callback_query(self, callback_data: str, msg: InboundMessage):
    if callback_data.startswith("delegate:"):
        agent_id = callback_data.split(":")[1]
        return await self._delegate_to_agent(agent_id, msg)
```

### Phase 3: Task Status Tracking

#### 3.1 Task Registry
```python
# nanobot_deep/tasks/registry.py
class TaskRegistry:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()
    
    async def create_task(
        self,
        task_id: str,
        agent_id: str,
        session_key: str,
        description: str,
        requester_channel: str,
        requester_chat_id: str,
    ) -> Task:
        ...
    
    async def update_status(
        self,
        task_id: str,
        status: str,  # pending, running, completed, failed
        progress: str | None = None,
        result: str | None = None,
    ):
        ...
    
    async def list_tasks(
        self,
        channel: str | None = None,
        chat_id: str | None = None,
        status: list[str] | None = None,
        limit: int = 20,
    ) -> list[Task]:
        ...
```

#### 3.2 Status Command
```python
# Command handler for /status and /tasks
@slash_command("/status")
async def status_command(task_id: str | None = None) -> OutboundMessage:
    if task_id:
        task = await registry.get_task(task_id)
        return OutboundMessage(
            content=format_task_status(task),
            buttons=get_task_buttons(task),  # [Cancel] [Details]
        )
    else:
        tasks = await registry.list_tasks(active_only=True)
        return OutboundMessage(
            content=format_tasks_list(tasks),
            buttons=[
                [InlineButton(f"#{t.id[:8]} - {t.status}", f"status:{t.id}")]
                for t in tasks[:5]
            ]
        )

@slash_command("/agents")
async def agents_command() -> OutboundMessage:
    agents = await registry.list_active_agents()
    return OutboundMessage(
        content=format_agents_status(agents),
        buttons=[
            [InlineButton(f"🤖 {a.name} ({a.active_tasks})", f"agent:{a.id}")]
            for a in agents
        ]
    )
```

#### 3.3 Progress Updates
```python
# In subagent execution
async def execute_with_progress(self, task_id: str):
    async for event in agent.astream_events(...):
        if event["event"] == "on_tool_start":
            await registry.update_progress(task_id, f"Running {event['name']}")
        elif event["event"] == "on_chat_model_stream":
            # Stream progress to requester if online
            await self._send_progress_update(task_id, event["data"]["chunk"])
```

### Phase 4: Cross-Channel Task Continuity

#### 4.1 Task Handoff
```python
# Allow checking status from any channel
User (Telegram): /status abc123
Bot: Task abc123 (Test Writer):
     Status: In Progress
     Started from: Slack #dev
     Use `/claim abc123` to receive updates here

User: /claim abc123
Bot: ✅ You'll receive updates for task abc123 here
```

#### 4.2 Broadcast Updates
```python
# Optional: broadcast task completion to all subscribed channels
async def broadcast_task_complete(self, task: Task):
    for channel, chat_id in task.subscribers:
        await self.bus.publish_outbound(OutboundMessage(
            channel=channel,
            chat_id=chat_id,
            content=f"✅ Task {task.id[:8]} completed!\n\n{task.result}",
        ))
```

## Channel-Specific Implementations

### Telegram (PR #1273 Ready)
```python
# Use inline keyboards from PR
buttons = [[InlineButton("🔍 Code Reviewer", "delegate:code-reviewer")]]
# Already supported in TelegramChannel
```

### Slack (Needs Implementation)
```python
# Use Block Kit for richer UI
blocks = [
    {
        "type": "section",
        "text": {"type": "mrkdwn", "text": "Choose an agent:"},
        "accessory": {
            "type": "static_select",
            "action_id": "agent_select",
            "options": [
                {"text": {"type": "plain_text", "text": "Code Reviewer"}, "value": "code-reviewer"},
            ]
        }
    }
]
```

### WhatsApp (Limited)
```python
# WhatsApp has limited interactive features
# Use numbered list + text reply
content = """Choose an agent:
1. Code Reviewer
2. Test Writer
3. Security Scanner

Reply with the number."""
```

### CLI
```python
# Rich terminal UI
from rich.prompt import Prompt
from rich.console import Console

agents = list_agents()
choice = Prompt.ask(
    "Choose an agent",
    choices=[a.id for a in agents],
    default="main"
)
```

## Configuration Schema Changes

```python
class DeepAgentsTaskConfig(BaseConfig):
    enabled: bool = True
    registry_path: str = "~/.nanobot/tasks.db"
    max_concurrent: int = 5
    timeout_default: int = 300  # 5 minutes
    broadcast_updates: bool = True

class DeepAgentsConfig(BaseConfig):
    # ... existing fields ...
    
    task_routing: DeepAgentsTaskRoutingConfig = Field(...)
    
    # New
    tasks: DeepAgentsTaskConfig = Field(default_factory=DeepAgentsTaskConfig)
    agent_discovery: DeepAgentsAgentDiscoveryConfig = Field(...)
```

## Implementation Priority

| Phase | Feature | Effort | Impact |
|-------|---------|--------|--------|
| 1.1 | Agent list command | Low | High |
| 1.2 | Task registry (SQLite) | Medium | High |
| 2.1 | Telegram inline keyboards | Low | High (PR exists) |
| 2.2 | Agent selection flow | Medium | High |
| 3.1 | Status tracking | Medium | High |
| 3.2 | /status, /tasks, /agents commands | Low | Medium |
| 4.1 | Cross-channel handoff | High | Medium |
| 4.2 | Progress streaming | High | Medium |

## Open Questions

1. **Persistence**: Should task history be persisted indefinitely or cleaned up?
2. **Rate limiting**: How many concurrent subagents per user/channel?
3. **Authorization**: Who can view/claim tasks? (owner-only vs shared)
4. **Agent selection UI**: Should main agent suggest relevant agents or always show all?
5. **Callback timeout**: How long should inline keyboard callbacks be valid?

## Success Criteria

- [ ] `/agents` command lists all configured agents
- [ ] Inline keyboards in Telegram for agent selection
- [ ] `/status <task_id>` shows task progress
- [ ] `/tasks` lists all active tasks for current chat
- [ ] Task progress updates are visible across channels
- [ ] Completed tasks show results with actionable buttons

## Related Files

- `nanobot_deep/agent/deep_agent.py` - Agent wrapper
- `nanobot_deep/gateway.py` - Message processing
- `nanobot_deep/config/schema.py` - Subagent configuration
- `tests/e2e/test_deepagent_live.py` - E2E tests
- External: `nanobot/bus/events.py` - InlineButton, OutboundMessage
- External: `nanobot/channels/telegram.py` - Callback query handling
