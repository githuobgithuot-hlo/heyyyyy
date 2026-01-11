#!/usr/bin/env python3
"""
Helper script to get Telegram Channel ID.

Steps:
1. Add your bot to the channel as an administrator
2. Give the bot permission to post messages
3. Run this script and send a message in the channel
4. The script will print the channel ID
"""
import asyncio
from telegram import Bot
from telegram.error import TelegramError
import os
from dotenv import load_dotenv

load_dotenv()

async def get_channel_id():
    """Get channel ID by having bot forward a message from the channel."""
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN') or input("Enter your bot token: ").strip()
    
    if not bot_token:
        print("Error: Bot token is required")
        return
    
    bot = Bot(token=bot_token)
    
    print("\n" + "="*60)
    print("TELEGRAM CHANNEL ID FINDER")
    print("="*60)
    print("\nInstructions:")
    print("1. Make sure your bot is added to the channel as an ADMINISTRATOR")
    print("2. Give the bot permission to 'Post Messages'")
    print("3. Send ANY message in the channel (you can delete it later)")
    print("4. The bot will detect it and show the channel ID")
    print("\nWaiting for a message in the channel...")
    print("(Press Ctrl+C to cancel)\n")
    
    try:
        # Get updates to find channel messages
        updates = await bot.get_updates(offset=-1, timeout=60)
        
        if not updates:
            print("\nNo messages found. Make sure:")
            print("- Bot is added to channel as admin")
            print("- Bot has 'Post Messages' permission")
            print("- You sent a message in the channel")
            return
        
        for update in updates:
            if update.channel_post:
                chat = update.channel_post.chat
                print("\n" + "="*60)
                print(f"CHANNEL FOUND!")
                print("="*60)
                print(f"Channel Title: {chat.title}")
                print(f"Channel Username: @{chat.username}" if chat.username else "Channel Username: (private channel)")
                print(f"Channel ID: {chat.id}")
                print("="*60)
                print(f"\n[SUCCESS] Use this Channel ID in your .env file:")
                print(f"TELEGRAM_CHAT_ID={chat.id}")
                print("\nNote: Channel IDs are usually negative numbers (e.g., -1001234567890)")
                return
            elif update.message and update.message.chat.type == 'channel':
                chat = update.message.chat
                print("\n" + "="*60)
                print(f"CHANNEL FOUND!")
                print("="*60)
                print(f"Channel Title: {chat.title}")
                print(f"Channel Username: @{chat.username}" if chat.username else "Channel Username: (private channel)")
                print(f"Channel ID: {chat.id}")
                print("="*60)
                print(f"\n[SUCCESS] Use this Channel ID in your .env file:")
                print(f"TELEGRAM_CHAT_ID={chat.id}")
                return
        
        print("\nNo channel messages found in recent updates.")
        print("Try sending another message in the channel.")
        
    except TelegramError as e:
        print(f"\n[ERROR] Telegram Error: {e}")
        print("\nMake sure:")
        print("- Bot token is correct")
        print("- Bot is added to channel as admin")
    except KeyboardInterrupt:
        print("\n\nCancelled by user")
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")

if __name__ == "__main__":
    asyncio.run(get_channel_id())

