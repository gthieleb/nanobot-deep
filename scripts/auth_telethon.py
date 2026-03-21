#!/usr/bin/env python3
"""
Telethon authentication script for E2E tests.

Run this once to create a session file for Telegram E2E tests.
After successful authentication, tests will use the existing session.
"""

import asyncio
import os
from pathlib import Path


async def authenticate():
    """Authenticate Telethon client and create session file."""
    from telethon import TelegramClient

    api_id = int(os.environ["TELEGRAM_API_ID"])
    api_hash = os.environ["TELEGRAM_API_HASH"]
    phone = os.environ["TEST_USER_PHONE"]

    print(f"Authenticating for phone: {phone}")
    print("Waiting for verification code...")
    print("Check your Telegram app for code.")

    session_path = Path("tests") / "e2e" / "test_session_user"
    print(f"Session path: {session_path}")

    client = TelegramClient(str(session_path), api_id, api_hash)

    try:
        await client.connect()

        if not await client.is_user_authorized():
            await client.send_code_request(phone)
            # Try to get code from environment variable first
            code = os.environ.get("TELEGRAM_AUTH_CODE", "")
            if not code:
                code = input(f"Enter code for {phone}: ")
            await client.sign_in(phone, code)

        print("✓ Authentication successful!")
        print(f"Session file created: {session_path.absolute()}")

    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(authenticate())
