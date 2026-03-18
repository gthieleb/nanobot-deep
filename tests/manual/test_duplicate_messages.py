"""Manual test to analyze duplicate/disappearing message patterns.

This test helps investigate the "double short messages" issue where:
- Short bot responses appear briefly as duplicates
- Then disappear (likely Draft Messages being replaced by final message)

Usage:
  1. Start gateway: nanobot-deep gateway --verbose > test_gateway.log 2>&1 &
  2. Run this script: python tests/manual/test_duplicate_messages.py
  3. Manually send test messages via Telegram
  4. Observe and document the behavior

The script monitors the gateway log and correlates with sent messages.
"""

import asyncio
import time
from datetime import datetime
from pathlib import Path


class MessageLogger:
    """Monitors gateway log and tracks message patterns."""

    def __init__(self, log_path: Path = Path("gateway.log")):
        self.log_path = log_path
        self.log_position = 0
        self.events = []

    def tail_log(self) -> list[str]:
        """Read new lines from gateway log."""
        if not self.log_path.exists():
            return []

        with open(self.log_path, "r") as f:
            f.seek(self.log_position)
            new_lines = f.readlines()
            self.log_position = f.tell()
            return new_lines

    def parse_events(self, lines: list[str]) -> None:
        """Parse relevant events from log lines."""
        for line in lines:
            timestamp = datetime.now().isoformat()

            # Inbound message received
            if "Processing message from" in line:
                parts = line.split("Processing message from")[1].strip()
                channel_sender, content = parts.split(":", 1)
                self.events.append(
                    {
                        "time": timestamp,
                        "type": "inbound",
                        "channel": channel_sender,
                        "content": content.strip(),
                    }
                )

            # Draft message sent
            elif "sendMessageDraft" in line and "'text':" in line:
                # Extract text from parameters
                if "text': '" in line:
                    text_start = line.find("'text': '") + 9
                    text_end = line.find("'}", text_start)
                    if text_end == -1:
                        text_end = len(line) - 1
                    text = line[text_start:text_end]
                    self.events.append(
                        {"time": timestamp, "type": "draft", "text": text, "length": len(text)}
                    )

            # Final message sent
            elif "sendMessage" in line and "'text':" in line and "Draft" not in line:
                if "'text': '" in line or '"text": "' in line:
                    # Try both quote styles
                    if "'text': '" in line:
                        text_start = line.find("'text': '") + 9
                        text_end = line.find("'}", text_start)
                    else:
                        text_start = line.find('"text": "') + 9
                        text_end = line.find('"}', text_start)

                    if text_end == -1:
                        text_end = len(line) - 1
                    text = line[text_start:text_end]
                    self.events.append(
                        {"time": timestamp, "type": "final", "text": text, "length": len(text)}
                    )

            # Response published
            elif "Response published successfully" in line:
                self.events.append({"time": timestamp, "type": "published"})

    def summarize_last_exchange(self) -> dict:
        """Summarize the last message exchange."""
        if not self.events:
            return {}

        # Find last published event
        published_idx = None
        for i in range(len(self.events) - 1, -1, -1):
            if self.events[i]["type"] == "published":
                published_idx = i
                break

        if published_idx is None:
            return {}

        # Count drafts and finals after this published event
        drafts = [e for e in self.events[published_idx:] if e["type"] == "draft"]
        finals = [e for e in self.events[published_idx:] if e["type"] == "final"]

        inbound = None
        for i in range(published_idx, -1, -1):
            if self.events[i]["type"] == "inbound":
                inbound = self.events[i]
                break

        return {
            "inbound": inbound.get("content", "N/A") if inbound else "N/A",
            "draft_count": len(drafts),
            "final_count": len(finals),
            "final_text": finals[0]["text"] if finals else "N/A",
            "final_length": finals[0]["length"] if finals else 0,
        }


def print_instructions():
    """Print test instructions."""
    print(
        """
╔════════════════════════════════════════════════════════════════╗
║      Duplicate/Disappearing Messages Test Tool                ║
╚════════════════════════════════════════════════════════════════╝

SETUP:
  1. Gateway should be running: nanobot-deep gateway --verbose
  2. Telegram bot should be connected
  3. gateway.log should be in current directory

TEST CASES:
  Send these messages via Telegram and observe:

  A) Very short responses (likely to show duplicate):
     - "Ja"
     - "Nein" 
     - "OK"
     - "Bist du noch da?"

  B) Medium responses:
     - "Was kannst du?"
     - "Erkläre mir etwas"

  C) Long responses (unlikely to show duplicate):
     - "Schreibe mir eine lange Geschichte über..."

OBSERVATIONS TO NOTE:
  1. Do you see the message appear twice briefly?
  2. Does one copy disappear after ~1 second?
  3. What's the character length threshold?
  4. Does the draft message show "..."  or typing indicator?

Press Ctrl+C to stop monitoring.

Starting monitor...
"""
    )


async def monitor_loop():
    """Main monitoring loop."""
    logger = MessageLogger()
    print_instructions()

    exchange_count = 0

    try:
        while True:
            lines = logger.tail_log()
            if lines:
                logger.parse_events(lines)

                # Check if we have a complete exchange
                summary = logger.summarize_last_exchange()
                if summary and summary["final_count"] > 0:
                    exchange_count += 1
                    print(f"\n{'=' * 60}")
                    print(f"Exchange #{exchange_count}")
                    print(f"{'=' * 60}")
                    print(f"📨 User:          {summary['inbound']}")
                    print(f"🤖 Bot Response:  {summary['final_text'][:80]}...")
                    print(f"📏 Length:        {summary['final_length']} chars")
                    print(f"📝 Draft count:   {summary['draft_count']}")
                    print(f"✅ Final count:   {summary['final_count']}")

                    if summary["final_length"] < 50:
                        print(f"⚠️  SHORT RESPONSE - Watch for duplicate/disappearing effect!")

                    # Clear events for next exchange
                    logger.events = []

            await asyncio.sleep(0.5)

    except KeyboardInterrupt:
        print("\n\n✅ Monitoring stopped.")
        print(f"\nTotal exchanges monitored: {exchange_count}")


def main():
    """Run the monitoring tool."""
    log_path = Path("gateway.log")
    if not log_path.exists():
        print(f"❌ Error: {log_path} not found!")
        print("\nMake sure gateway is running with:")
        print("  nanobot-deep gateway --verbose > gateway.log 2>&1 &")
        return 1

    asyncio.run(monitor_loop())
    return 0


if __name__ == "__main__":
    exit(main())
