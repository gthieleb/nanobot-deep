#!/usr/bin/env python3
import asyncio
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
SESSION_PATH = PROJECT_ROOT / "tests/e2e/test_session_user"


async def create_group():
    from telethon import TelegramClient
    from telethon.tl.functions.channels import CreateChannelRequest
    from telethon.tl.types import InputChannelEmpty

    api_id = int(os.environ["TELEGRAM_API_ID"])
    # Use raw string to avoid quote issues
    api_hash = os.environ["TELEGRAM_API_HASH"]
    phone = os.environ["TEST_USER_PHONE"]
    bot_username = os.environ.get("TELEGRAM_BOT_USERNAME", "").lstrip("@")

    print(f"Creating group 'nanobot-deep-ci'...")
    print(f"Authenticated as: {phone}")
    print(f"Bot to invite: @{bot_username}")

    client = TelegramClient(str(SESSION_PATH), api_id, api_hash)

    try:
        await client.connect()

        if not await client.is_user_authorized():
            print("User not authorized. Please run scripts/auth_telethon.py first.")
            return

        print(f"Using session: {SESSION_PATH.absolute()}")

        result = await client(
            CreateChannelRequest(
                title="nanobot-deep-ci", about="CI testing group for nanobot-deep", megagroup=True
            )
        )

        created_channel = result.chats[0]

        print(f"Group created: ID={created_channel.id}, username=@{created_channel.username}")

        bot_entity = await client.get_entity(bot_username)
        from telethon.tl.functions.channels import InviteToChannelRequest

        print(f"Adding bot @{bot_username} to group...")
        await client(InviteToChannelRequest(channel=created_channel, users=[bot_entity]))
        print(f"Bot @{bot_username} added to group!")

        group_id = created_channel.id
        if group_id > 0:
            group_id = -abs(group_id)
        print(f"\nEnvironment variable: export TELEGRAM_CI_GROUP_ID={group_id}")

        env_file = Path.home() / "env/ai/nanobot/ci"
        print(f"\nUpdating environment file: {env_file}")

        with open(env_file, "r") as f:
            env_content = f.read()

        lines = env_content.split("\n")
        new_lines = []
        for line in lines:
            if "TELEGRAM_CI_GROUP_ID=" in line:
                new_lines.append(f'export TELEGRAM_CI_GROUP_ID="{group_id}"')
            else:
                new_lines.append(line)

        with open(env_file, "w") as f:
            f.write("\n".join(new_lines))

        print(f"Environment file updated!")

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()

    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(create_group())
