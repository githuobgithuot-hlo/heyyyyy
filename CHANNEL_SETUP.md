# How to Add Bot to Telegram Channel

## Step 1: Add Bot to Channel as Administrator

1. Open your Telegram channel
2. Go to **Channel Settings** → **Administrators**
3. Click **Add Administrator**
4. Search for your bot (by username, e.g., `@YourBotName`)
5. Select your bot
6. **IMPORTANT**: Enable **"Post Messages"** permission
7. Click **Done**

## Step 2: Get Channel ID

### Method 1: Using @getidsbot (Easiest)

1. Add `@getidsbot` to your channel as a member
2. Send any message in the channel
3. `@getidsbot` will reply with the channel ID (it's a negative number like `-1001234567890`)
4. Copy that number

### Method 2: Using the Helper Script

1. Make sure your bot token is in `.env` file:
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   ```

2. Run the helper script:
   ```bash
   python get_channel_id.py
   ```

3. Send a message in your channel
4. The script will display the channel ID

### Method 3: Manual Method

1. Forward any message from your channel to `@userinfobot`
2. It will show you the channel ID
3. Channel IDs are negative numbers (e.g., `-1001234567890`)

## Step 3: Update Configuration

### Option A: Update .env file (Recommended)

Edit `cloudbet/cloudbet/arbitrage-bot/.env`:

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=-1001234567890
```

Replace `-1001234567890` with your actual channel ID.

### Option B: Update config.yaml

Edit `cloudbet/cloudbet/arbitrage-bot/config/config.yaml`:

```yaml
telegram:
  bot_token: "your_bot_token_here"
  chat_id: -1001234567890  # Your channel ID (negative number)
```

## Step 4: Test the Setup

Run this command to test:

```bash
cd "E:\cloudbet (4)\cloudbet\cloudbet\arbitrage-bot"
.\venv\Scripts\python.exe -c "import asyncio; from src.config_loader import load_config; from src.telegram_notifier import TelegramNotifier; c=load_config('config/config.yaml'); n=TelegramNotifier(c.telegram.bot_token, c.telegram.chat_id); print('Sending test...'); print(asyncio.run(n.send_test_message()))"
```

If it returns `True`, the bot can send messages to your channel!

## Step 5: Restart the Bot

After updating the channel ID, restart the bot:

```bash
# Stop current bot
# Then restart:
cd "E:\cloudbet (4)\cloudbet\cloudbet\arbitrage-bot"
.\venv\Scripts\python.exe src\main.py
```

## Troubleshooting

### Bot can't send messages
- Make sure bot is **Administrator** (not just member)
- Make sure bot has **"Post Messages"** permission enabled
- Check that channel ID is correct (should be negative number)

### Channel ID not working
- Channel IDs are negative numbers (e.g., `-1001234567890`)
- Private channels: Use the method above to get the ID
- Public channels: You can also use `@channel_username` format, but numeric ID is more reliable

### Bot not receiving updates
- Make sure bot is added to channel (not just invited)
- Bot must be an administrator with post permissions

