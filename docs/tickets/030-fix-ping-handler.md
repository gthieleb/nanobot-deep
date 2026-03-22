# Ticket: Fix /ping Command Handler - Response from DeepAgent instead of "pong"

## Issue

When sending `/ping` to the bot in group mode, the bot responds with:
```
I'm here and ready to help!

Workspace: /home/gun/.nanobot/workspace

What do you need?
```

Instead of the expected:
```
pong
```

## Root Cause Analysis

### What's happening
1. Gateway receives `/ping` message
2. Message is passed to DeepAgent instead of CustomTelegramChannel
3. DeepAgent processes `/ping` as a regular message and responds with AI text
4. Custom ping handler never gets triggered

### Evidence from logs
- Gateway log shows: `Processing message from telegram:915681932|Ostkind79: /ping`
- DeepAgent response: `I'm here and ready to help!` (AI text, not "pong")
- No ping handler was triggered

### Technical Details
1. `_patch_telegram_channel()` patches `sys.modules["nanobot.channels.telegram"]`
2. CustomTelegramChannel is injected into gateway
3. CustomTelegramChannel's `_on_ping()` handler should be registered
4. But it's never actually registered or executed

### Root Cause
The gateway patches the telegram module but the ping handler registration isn't working. The message is processed by DeepAgent instead of being intercepted by the custom handler.

## Solution

The ping handler should be registered BEFORE the gateway starts polling. Current code registers it inside the `start()` method, but it needs to be registered earlier.

### Files to Fix

1. **CustomTelegramChannel** in `nanobot_deep/channels/telegram.py`
   - Ensure `_on_ping()` is registered before `start_polling()`
   - Verify CommandHandler is added to Application

2. **Gateway Patching** in `nanobot_deep/gateway.py`
   - Verify CustomTelegramChannel is properly loaded
   - Check that ping handler is registered before gateway starts

3. **Test Configuration** in `tests/e2e/conftest.py`
   - Ensure test fixtures work with group mode
   - Use `get_input_entity()` for groups (already fixed)

## Status

**Current State:** 8/36 Tests Passing (22%)
- DM Tests: 8/8 passing (basic commands)
- Group Tests: 0/36 passing (ChatIdInvalidError fixed, but ping handler not working)

**Next Steps:**
1. Fix CustomTelegramChannel ping handler registration
2. Verify ping handler works in group mode
3. Run full group test suite

## Related Issues

- **#27**: Tenant Support Analysis (not critical)
- **#26**: E2E Tests for Group Mode (partially working)
- **#20**: Bot Entity Fixture (now fixed with get_input_entity)

## Files Modified

- `tests/e2e/conftest.py` - Fixed telegram_bot_entity for groups
- `scripts/create_telegram_group.py` - Create nanobot-deep-ci group
- `scripts/get_telegram_group_id.py` - Get group ID from name
- `~/env/ai/nanobot/ci` - Set TELEGRAM_CI_GROUP_ID=-1003696855572

## Labels

- `fix`
- `bug`
- `gateway`
- `ping-handler`
- `test-failure`
