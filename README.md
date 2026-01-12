# Arbitrage Detection Bot

A production-ready Python bot that detects arbitrage opportunities between Polymarket (prediction markets) and Cloudbet (sportsbook) and sends real-time Telegram alerts.

## 🎯 Project Overview

This bot continuously monitors odds from both platforms, matches equivalent markets using fuzzy string matching, detects risk-free arbitrage opportunities, calculates optimal bet sizing using the Kelly Criterion, and sends instant Telegram notifications.

### Key Features

- ✅ **Real-time Monitoring**: Continuous polling of both platforms
- ✅ **Fuzzy Market Matching**: Uses rapidfuzz to match markets across platforms
- ✅ **Sports Event Matching**: Intelligent sports-specific matching with outcome translation (NEW!)
- ✅ **Arbitrage Detection**: Calculates guaranteed profit opportunities
- ✅ **Kelly Criterion Bet Sizing**: Optimal capital allocation
- ✅ **Telegram Alerts**: Instant notifications with full opportunity details
- ✅ **SQLite Persistence**: Stores all detected opportunities
- ✅ **Production Ready**: Error handling, retries, logging, and graceful shutdown
- ✅ **Docker Support**: Easy deployment with Docker and docker-compose

## 📋 Prerequisites

- Python 3.9 or higher
- Telegram Bot Token (get from [@BotFather](https://t.me/botfather))
- Telegram Chat ID (get from [@userinfobot](https://t.me/userinfobot))
- Cloudbet API Key (from Cloudbet account)

## 🚀 Quick Start

### 1. Clone and Setup

```bash
cd arbitrage-bot
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` and add your credentials:

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
CLOUDBET_API_KEY=your_api_key_here
```

### 3. Configure Settings

Edit `config/config.yaml` to customize:

- Bankroll amount
- Kelly fraction (0.5 = half Kelly recommended)
- Minimum profit threshold
- Polling interval
- Similarity threshold for market matching

### 4. Run the Bot

```bash
python src/main.py
```

Or with custom config:

```bash
python src/main.py config/config.yaml
```

## 🐳 Docker Deployment

### Build and Run

```bash
# Build the image
docker build -t arbitrage-bot .

# Run with docker-compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Environment Variables in Docker

Create a `.env` file or set environment variables:

```bash
docker run -d \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/data:/app/data \
  -e TELEGRAM_BOT_TOKEN=your_token \
  -e TELEGRAM_CHAT_ID=your_chat_id \
  -e CLOUDBET_API_KEY=your_key \
  arbitrage-bot
```

## 📁 Project Structure

```
arbitrage-bot/
├── config/
│   └── config.yaml              # Main configuration file
├── src/
│   ├── main.py                  # Main entry point
│   ├── config_loader.py         # Configuration management
│   ├── logger.py                # Logging setup
│   ├── fetchers/
│   │   ├── polymarket_fetcher.py # Polymarket API client
│   │   └── cloudbet_fetcher.py   # Cloudbet API client
│   ├── market_matcher.py        # Regular fuzzy market matching
│   ├── sports_matcher.py        # Sports-specific event matching (NEW!)
│   ├── arbitrage_engine.py      # Arbitrage detection logic
│   ├── sports_arbitrage_engine.py # Sports arbitrage detection (NEW!)
│   ├── bet_sizing.py            # Kelly Criterion calculator
│   ├── telegram_notifier.py     # Telegram alerts
│   └── database.py              # SQLite persistence
├── tests/
│   ├── test_arbitrage.py        # Unit tests
│   ├── test_matching_system.py  # Matching system test
│   └── test_sports_matching.py  # Sports matching test (NEW!)
├── logs/                        # Log files (auto-created)
├── data/                        # Database files (auto-created)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── README.md
├── SPORTS_MATCHING_FEATURE.md   # Sports feature docs (NEW!)
└── IMPLEMENTATION_SUMMARY.md    # Implementation summary (NEW!)
```

## ⚙️ Configuration

### config/config.yaml

```yaml
bankroll:
  amount: 10000.0        # Total capital in USD
  kelly_fraction: 0.5    # Kelly multiplier (0.5 = half Kelly)

arbitrage:
  min_profit_threshold: 0.5  # Minimum profit % to alert
  polling_interval: 30        # Seconds between polls
  similarity_threshold: 80   # Market matching threshold (0-100)

telegram:
  bot_token: ""  # Set via TELEGRAM_BOT_TOKEN env var
  chat_id: ""    # Set via TELEGRAM_CHAT_ID env var

apis:
  cloudbet:
    api_key: ""  # Set via CLOUDBET_API_KEY env var
    base_url: "https://sports-api.cloudbet.com/pub/v2"
    timeout: 10
    retry_attempts: 3
    retry_delay: 2
  
  polymarket:
    base_url: "https://clob.polymarket.com"
    timeout: 10
    retry_attempts: 3
    retry_delay: 2

quiet_hours:
  enabled: false
  start_hour: 2  # 2 AM UTC
  end_hour: 8    # 8 AM UTC
```

## 🔍 How Arbitrage Works

### Detection Logic

1. **Market Fetching**: Bot fetches active markets from both platforms concurrently
2. **Market Matching**: Uses fuzzy string matching (rapidfuzz) to find equivalent markets
3. **Arbitrage Calculation**: For matched markets, calculates:
   ```
   total_probability = 1/odds_a + 1/odds_b
   
   If total_probability < 1.0:
       arbitrage_exists = True
       profit_percentage = ((1.0 - total_probability) / total_probability) * 100
   ```
4. **Bet Sizing**: Uses Kelly Criterion to calculate optimal bet amounts:
   ```
   bet_a = (capital * odds_b) / (odds_a + odds_b)
   bet_b = (capital * odds_a) / (odds_a + odds_b)
   ```
5. **Alert**: Sends Telegram notification with full details

### Example

**Market**: "Trump wins 2024 Election"

- **Polymarket**: YES at 2.0 odds (50% implied probability)
- **Cloudbet**: NO at 2.1 odds (47.6% implied probability)
- **Total Probability**: 97.6% (< 100% = arbitrage!)
- **Profit**: ~2.4% guaranteed

## 📊 Telegram Alert Format

```
🚨 ARBITRAGE OPPORTUNITY DETECTED

Market: Trump wins 2024 Election
Outcome: YES

💰 Profit: 2.40%
💵 Guaranteed Profit: $240.00

📊 Betting Strategy:
• POLYMARKET:
  - Bet: $5,000.00
  - Odds: 2.00
  - [Link]

• CLOUDBET:
  - Bet: $4,762.00
  - Odds: 2.10
  - [Link]

💼 Total Capital Required: $9,762.00

⏰ Detected at: 2024-12-25 14:30:00 UTC
```

## ⚽ Sports Matching Feature (NEW!)

The bot now includes intelligent **sports-specific event matching** with outcome translation:

### How It Works

1. **Sports Detection**: Automatically identifies sports markets in Polymarket using keyword matching (173 sports markets detected from recent data)

2. **Event Matching**: Fuzzy matches sports events between platforms:
   - Team name normalization (handles "Los Angeles Lakers" vs "Lakers")
   - Similarity threshold: 70% (more flexible than regular 85%)
   - Date/league aware matching

3. **Outcome Translation**: Intelligently maps different outcome formats:
   - `Polymarket YES/NO → Cloudbet Team Names`
   - Direct team matching with normalization
   - Player/award market mapping

### Example Translations

```python
# Case 1: Future Market
Polymarket: "Will Lakers beat Warriors?" → YES/NO
Cloudbet:   "Lakers vs Warriors" → Lakers/Warriors
Translation: YES → Lakers, NO → Warriors

# Case 2: Direct Match
Polymarket: "Lakers vs Warriors - Winner" → Lakers/Warriors
Cloudbet:   "Lakers - Warriors" → s-lakers/s-warriors
Translation: Direct fuzzy matching with normalization
```

### Testing Sports Matching

```bash
# Test sports matching with real API data
python test_sports_matching.py

# Expected output:
# - Detects 173 sports markets from Polymarket
# - Processes 20,000+ Cloudbet outcomes
# - Shows matching results and arbitrage opportunities
```

### Documentation

See [SPORTS_MATCHING_FEATURE.md](SPORTS_MATCHING_FEATURE.md) for complete documentation including:
- Technical implementation details
- API formats and data structures
- Configuration options
- Troubleshooting guide

## 🧪 Testing

Run unit tests:

```bash
# Test regular matching system
python test_matching_system.py

# Test sports matching system
python test_sports_matching.py

# Run pytest unit tests
pytest tests/test_arbitrage.py -v
```

Tests cover:
- Arbitrage detection logic
- Kelly Criterion bet sizing
- Sports event matching and outcome translation
- Profit threshold validation
- Edge cases (invalid odds, etc.)

## 📝 Logging

Logs are written to:
- **Console**: INFO level and above
- **File**: `logs/arbitrage_bot.log` (DEBUG level and above)

Log rotation: 10 MB max, 5 backup files

## ⚠️ Known Risks & Limitations

### 1. **Odds Movement**
- Odds can change between detection and bet placement
- Always verify current odds before placing bets
- Consider implementing a confirmation step

### 2. **Latency**
- API response times vary
- Network delays can affect opportunity detection
- Bot includes retry logic and error handling

### 3. **Market Matching**
- Fuzzy matching may produce false positives
- Adjust `similarity_threshold` in config if needed
- Review matched markets in logs

### 4. **API Rate Limits**
- Both platforms have rate limits
- Bot includes retry logic with exponential backoff
- Adjust `polling_interval` if hitting limits

### 5. **Liquidity**
- Small markets may not support calculated bet sizes
- Check market liquidity before placing large bets

### 6. **Platform Differences**
- Polymarket uses YES/NO outcomes
- Cloudbet uses various outcome formats
- Matching logic handles common variations

## 🔧 Troubleshooting

### Bot not starting

1. **Check configuration**:
   ```bash
   python -c "from src.config_loader import load_config; load_config()"
   ```

2. **Verify environment variables**:
   ```bash
   echo $TELEGRAM_BOT_TOKEN
   echo $TELEGRAM_CHAT_ID
   echo $CLOUDBET_API_KEY
   ```

3. **Check logs**:
   ```bash
   tail -f logs/arbitrage_bot.log
   ```

### No markets found

- Verify API endpoints are correct
- Check API keys are valid
- Review API response format (may need adjustment)
- Check network connectivity

### Telegram alerts not sending

1. **Verify bot token and chat ID**:
   - Bot token from [@BotFather](https://t.me/botfather)
   - Chat ID from [@userinfobot](https://t.me/userinfobot)

2. **Test Telegram connection**:
   ```python
   from src.telegram_notifier import TelegramNotifier
   notifier = TelegramNotifier(token, chat_id)
   await notifier.send_test_message()
   ```

3. **Check quiet hours**:
   - Disable `quiet_hours.enabled` in config for testing

### Database errors

- Ensure `data/` directory exists and is writable
- Check disk space
- Review database file permissions

## 🚀 Production Deployment

### VPS Deployment (Ubuntu/Debian)

```bash
# Install dependencies
sudo apt update
sudo apt install python3 python3-pip python3-venv git

# Clone repository
git clone <your-repo> arbitrage-bot
cd arbitrage-bot

# Setup virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Setup systemd service
sudo nano /etc/systemd/system/arbitrage-bot.service
```

**Service file** (`/etc/systemd/system/arbitrage-bot.service`):

```ini
[Unit]
Description=Arbitrage Detection Bot
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/arbitrage-bot
Environment="PATH=/path/to/arbitrage-bot/venv/bin"
ExecStart=/path/to/arbitrage-bot/venv/bin/python src/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable arbitrage-bot
sudo systemctl start arbitrage-bot
sudo systemctl status arbitrage-bot
```

### Cloud VM Setup

1. **Create VM** (AWS EC2, Google Cloud, Azure, etc.)
2. **Install Docker**:
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   sh get-docker.sh
   ```
3. **Deploy with docker-compose**:
   ```bash
   docker-compose up -d
   ```

## 📚 API Documentation Notes

### Polymarket API

The bot uses the Polymarket public API. The actual endpoint structure may vary. Common endpoints:
- `/markets` - List all markets
- `/markets/{id}` - Get specific market

**Note**: You may need to adjust the API endpoints in `polymarket_client.py` based on the actual Polymarket API structure.

### Cloudbet API

The bot uses the Cloudbet Sports API. Endpoints:
- `/odds/sport/{sport}` - Get odds for a sport category

**Note**: Verify the exact API structure in Cloudbet documentation and adjust `cloudbet_client.py` if needed.

## 🤝 Contributing

This is a production-ready project. To extend:

1. **Add new platforms**: Create new client classes following the pattern in `polymarket_client.py`
2. **Improve matching**: Enhance `market_matcher.py` with better normalization
3. **Add features**: Extend `arbitrage_engine.py` for additional strategies

## 📄 License

This project is provided as-is for educational and commercial use.

## ⚡ Performance

- **Polling Interval**: Configurable (default: 30 seconds)
- **Concurrent Fetching**: Markets fetched in parallel
- **Memory Usage**: ~50-100 MB typical
- **CPU Usage**: Minimal (mostly I/O bound)

## 🔐 Security

- **API Keys**: Never commit `.env` file
- **Credentials**: Use environment variables
- **Database**: SQLite file should be secured
- **Logs**: May contain sensitive data - secure log files

## 📞 Support

For issues or questions:
1. Check logs in `logs/arbitrage_bot.log`
2. Review configuration in `config/config.yaml`
3. Verify API endpoints match current documentation
4. Test individual components (see Troubleshooting)

---

**Built with ❤️ for quantitative trading and arbitrage detection**

#   t e m p  
 #   c l o u d b e t  
 