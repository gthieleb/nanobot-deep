#!/usr/bin/env python3
"""
Helper script to get Telegram group ID by name.

Usage:
    python scripts/get_telegram_group_id.py

Example:
    python scripts/get_telegram_group_id.py nanobot-deep-ci
    → Outputs: Found group: nanobot-deep-ci
              Group ID: -1001234567890
              Environment export: export TELEGRAM_CI_GROUP_ID="-1001234567890"
"""

import asyncio
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
SESSION_PATH = PROJECT_ROOT / "tests/e2e/test_session_user"


async def get_group_by_name(group_name: str):
    """Get Telegram group ID by searching through dialogs.

    Args:
        group_name: Name of the group to find

    Returns:
        Group ID or None if not found
    """
    from telethon import TelegramClient

    api_id = int(os.environ["TELEGRAM_API_ID"])
    # Use raw string to avoid quote issues
    api_hash = os.environ["TELEGRAM_API_HASH"]
    phone = os.environ["TEST_USER_PHONE"]

    client = TelegramClient(str(SESSION_PATH), api_id, api_hash)

    try:
        await client.connect()

        if not await client.is_user_authorized():
            print(f"User not authorized. Please run scripts/auth_telethon.py first.")
            return None

        print(f"Searching for group: '{group_name}'...")

        # Search through all dialogs
        async for dialog in client.iter_dialogs():
            if dialog.is_group or dialog.is_channel:
                if dialog.name and dialog.name.lower() == group_name.lower():
                    # Format the ID correctly
                    group_id = dialog.id

                    # For private channels/supergroups, ID should be negative
                    if group_id > 0:
                        group_id = -abs(group_id)

                    print(f"Found group: {dialog.name}")
                    print(f"  Group ID: {group_id}")
                    print(f"  Group type: {'Supergroup' if dialog.is_channel else 'Group'}")
                    print(
                        f"  Member count: {dialog.entity.members_count if dialog.entity else 'N/A'}"
                    )

                    # Also output environment format
                    print(f"\nEnvironment export:")
                    print(f"  export TELEGRAM_CI_GROUP_ID={group_id}")

                    return group_id

        print(f"Group '{group_name}' not found!")
        print(f"\nSearching all groups for matching patterns...")
        print(f"Look for:")
        print(f"  - Similar group names")
        print(f"  - Case-insensitive search")

        return None

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()

    finally:
        await client.disconnect()


async def main():
    """Main function."""
    group_name = sys.argv[1] if len(sys.argv) > 1 else "nanobot-deep-ci"

    print(f"Getting group ID for: {group_name}\n")

    group_id = await get_group_by_name(group_name)

    if group_id:
        print(f"\nSUCCESS! Use this ID in environment:")
        print(f"export TELEGRAM_CI_GROUP_ID={group_id}")
        sys.exit(0)
    else:
        print(f"\nGroup not found. Manual steps:")
        print(f"1. Check in Telegram app for group '{group_name}'")
        print(f"2. Note the exact group name (case-sensitive)")
        print(f"3. Run this script again")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
