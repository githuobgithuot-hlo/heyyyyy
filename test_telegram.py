#!/usr/bin/env python3
"""
Standalone test script for Telegram integration.

Usage:
    python test_telegram.py
"""
import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.telegram_notifier import test_telegram
from src.config_loader import load_config


async def main():
    """Test Telegram integration."""
    try:
        # Load config
        config = load_config("config/config.yaml")
        
        bot_token = config.telegram.bot_token
        chat_id = config.telegram.chat_id
        
        if not bot_token or not chat_id:
            print("ERROR: Telegram bot_token or chat_id not configured!")
            print("   Set them in config/config.yaml or environment variables:")
            print("   - TELEGRAM_BOT_TOKEN")
            print("   - TELEGRAM_CHAT_ID")
            return False
        
        print(f"Testing Telegram integration...")
        print(f"Bot Token: {bot_token[:10]}...")
        print(f"Chat ID: {chat_id}")
        print()
        
        success = await test_telegram(bot_token, chat_id)
        return success
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

