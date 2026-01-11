#!/usr/bin/env python3
"""
Full system test with REAL API data and REAL alerts.
Tests each component end-to-end with actual live data.
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config_loader import load_config
from src.logger import setup_logger
from src.polymarket_client import PolymarketClient
from src.cloudbet_client import CloudbetClient
from src.market_matcher import MarketMatcher
from src.arbitrage_engine import ArbitrageEngine
from src.bet_sizing import BetSizing
from src.telegram_notifier import TelegramNotifier
from src.database import ArbitrageDatabase

async def test_polymarket_real():
    """Test Polymarket API with real data."""
    print("\n" + "="*60)
    print("TEST 1: Polymarket API - Real Data Fetching")
    print("="*60)
    
    config = load_config()
    client = PolymarketClient(
        base_url=config.apis.polymarket.base_url,
        timeout=config.apis.polymarket.timeout,
        retry_attempts=config.apis.polymarket.retry_attempts,
        retry_delay=config.apis.polymarket.retry_delay,
        debug_api=True
    )
    
    try:
        print(f"Fetching real markets from Polymarket...")
        markets = await client.get_markets(limit=10)
        
        print(f"\n✅ Fetched {len(markets)} real markets from Polymarket")
        
        if markets:
            print(f"\n📊 Sample Market:")
            sample = markets[0]
            print(f"  ID: {sample.get('id')}")
            print(f"  Name: {sample.get('name')}")
            print(f"  URL: {sample.get('url')}")
            print(f"  Outcomes: {len(sample.get('outcomes', []))}")
            for outcome in sample.get('outcomes', [])[:2]:
                print(f"    - {outcome.get('name')}: {outcome.get('odds', 0):.2f}")
            return markets
        else:
            print("⚠️  No markets returned - check API connection")
            return []
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        await client.close()

async def test_cloudbet_real():
    """Test Cloudbet API with real data."""
    print("\n" + "="*60)
    print("TEST 2: Cloudbet API - Real Data Fetching")
    print("="*60)
    
    config = load_config()
    client = CloudbetClient(
        api_key=config.apis.cloudbet.api_key,
        base_url=config.apis.cloudbet.base_url,
        timeout=config.apis.cloudbet.timeout,
        retry_attempts=config.apis.cloudbet.retry_attempts,
        retry_delay=config.apis.cloudbet.retry_delay,
        debug_api=True
    )
    
    try:
        print(f"Fetching real markets from Cloudbet...")
        # Try multiple sports to get data
        markets = await client.get_markets(sport='politics')
        
        if not markets or len(markets) == 0:
            print("Trying all sports...")
            markets = await client.get_markets(sport=None)
        
        print(f"\n✅ Fetched {len(markets)} real outcomes from Cloudbet")
        
        if markets:
            print(f"\n📊 Sample Outcome:")
            sample = markets[0]
            print(f"  Event: {sample.get('event_name')}")
            print(f"  Market: {sample.get('market_name')}")
            print(f"  Outcome: {sample.get('outcome')}")
            print(f"  Odds: {sample.get('odds', 0):.2f}")
            print(f"  URL: {sample.get('url')}")
            return markets
        else:
            print("⚠️  No markets returned - check API connection or try different sport")
            return []
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        await client.close()

async def test_market_matching_real(polymarket_markets, cloudbet_outcomes):
    """Test market matching with real data."""
    print("\n" + "="*60)
    print("TEST 3: Market Matching - Real Data")
    print("="*60)
    
    if not polymarket_markets or not cloudbet_outcomes:
        print("⚠️  Skipping - need both Polymarket and Cloudbet data")
        return []
    
    config = load_config()
    matcher = MarketMatcher(
        similarity_threshold=config.arbitrage.similarity_threshold
    )
    
    # Convert Cloudbet outcomes to market format for matching
    cloudbet_markets = {}
    for outcome in cloudbet_outcomes:
        key = (outcome['event_name'], outcome['market_name'])
        if key not in cloudbet_markets:
            cloudbet_markets[key] = {
                'id': f"{outcome['event_name']}_{outcome['market_name']}",
                'name': f"{outcome['event_name']} - {outcome['market_name']}",
                'outcomes': [],
                'url': outcome.get('url'),
                'platform': 'cloudbet',
                'timestamp': datetime.utcnow().isoformat()
            }
        cloudbet_markets[key]['outcomes'].append({
            'name': outcome['outcome'],
            'odds': outcome['odds']
        })
    
    print(f"Matching {len(polymarket_markets)} Polymarket markets with {len(cloudbet_markets)} Cloudbet markets...")
    
    matched = matcher.find_matches(
        polymarket_markets,
        list(cloudbet_markets.values()),
        platform_a="polymarket",
        platform_b="cloudbet"
    )
    
    print(f"\n✅ Found {len(matched)} matched market pairs")
    
    if matched:
        print(f"\n📊 Sample Match:")
        sample = matched[0]
        print(f"  Market: {sample.get('market_name')}")
        print(f"  Platform A: {sample.get('platform_a')}")
        print(f"  Platform B: {sample.get('platform_b')}")
        print(f"  Similarity: {sample.get('similarity', 0):.1f}%")
        return matched
    else:
        print("⚠️  No matches found - markets may not overlap")
        return []

async def test_arbitrage_detection_real(matched_markets):
    """Test arbitrage detection with real data."""
    print("\n" + "="*60)
    print("TEST 4: Arbitrage Detection - Real Data")
    print("="*60)
    
    if not matched_markets:
        print("⚠️  Skipping - need matched markets")
        return []
    
    config = load_config()
    engine = ArbitrageEngine(
        min_profit_threshold=config.arbitrage.min_profit_threshold
    )
    
    print(f"Analyzing {len(matched_markets)} matched markets for arbitrage...")
    
    opportunities = engine.detect_arbitrage(matched_markets)
    
    print(f"\n✅ Found {len(opportunities)} arbitrage opportunities")
    
    if opportunities:
        print(f"\n📊 Sample Opportunity:")
        sample = opportunities[0]
        print(f"  Market: {sample.get('market_name')}")
        print(f"  Profit: {sample.get('profit_percentage', 0):.2f}%")
        print(f"  Odds A: {sample.get('odds_a', 0):.2f}")
        print(f"  Odds B: {sample.get('odds_b', 0):.2f}")
        return opportunities
    else:
        print("⚠️  No arbitrage found - this is normal, arbitrage is rare")
        return []

async def test_bet_sizing_real(opportunities):
    """Test bet sizing with real data."""
    print("\n" + "="*60)
    print("TEST 5: Bet Sizing (Kelly Criterion) - Real Data")
    print("="*60)
    
    if not opportunities:
        print("⚠️  Skipping - need arbitrage opportunities")
        return []
    
    config = load_config()
    sizing = BetSizing(
        bankroll=config.bankroll.amount,
        kelly_fraction=config.bankroll.kelly_fraction
    )
    
    print(f"Calculating bet sizes for {len(opportunities)} opportunities...")
    
    sized_opportunities = []
    for opp in opportunities:
        sized = sizing.calculate_for_opportunity(opp)
        sized_opportunities.append(sized)
    
    print(f"\n✅ Calculated bet sizes for {len(sized_opportunities)} opportunities")
    
    if sized_opportunities:
        print(f"\n📊 Sample Bet Sizing:")
        sample = sized_opportunities[0]
        print(f"  Market: {sample.get('market_name')}")
        print(f"  Bet A: ${sample.get('bet_amount_a', 0):.2f} @ {sample.get('odds_a', 0):.2f}")
        print(f"  Bet B: ${sample.get('bet_amount_b', 0):.2f} @ {sample.get('odds_b', 0):.2f}")
        print(f"  Total Capital: ${sample.get('total_capital', 0):.2f}")
        print(f"  Guaranteed Profit: ${sample.get('guaranteed_profit', 0):.2f}")
        return sized_opportunities
    return []

async def test_telegram_real(opportunities):
    """Test Telegram alerts with REAL notification."""
    print("\n" + "="*60)
    print("TEST 6: Telegram Alert - REAL Notification")
    print("="*60)
    
    config = load_config()
    
    if not config.telegram.bot_token or not config.telegram.chat_id:
        print("⚠️  Skipping - Telegram not configured")
        return False
    
    notifier = TelegramNotifier(
        bot_token=config.telegram.bot_token,
        chat_id=config.telegram.chat_id
    )
    
    # Test 1: Send test message
    print("Sending test message...")
    test_sent = await notifier.send_test_message()
    
    if test_sent:
        print("✅ Test message sent successfully!")
    else:
        print("❌ Failed to send test message")
        return False
    
    # Test 2: Send real alert if we have opportunities
    if opportunities:
        print(f"\nSending real arbitrage alert for {len(opportunities)} opportunity(ies)...")
        for i, opp in enumerate(opportunities[:1], 1):  # Send first one only
            print(f"\nSending alert {i}/{min(1, len(opportunities))}...")
            sent = await notifier.send_alert(opp)
            if sent:
                print(f"✅ Real alert sent successfully!")
            else:
                print(f"❌ Failed to send alert")
            await asyncio.sleep(1)  # Rate limiting
    else:
        print("\n⚠️  No opportunities to alert - creating mock opportunity for test...")
        # Create a mock opportunity for testing
        mock_opp = {
            'market_name': 'TEST: Market Match Test',
            'profit_percentage': 1.5,
            'platform_a': 'polymarket',
            'platform_b': 'cloudbet',
            'odds_a': 2.10,
            'odds_b': 2.05,
            'outcome_a': {'name': 'YES'},
            'outcome_b': {'name': 'NO'},
            'market_a': {'url': 'https://polymarket.com/test'},
            'market_b': {'url': 'https://cloudbet.com/test'},
            'bet_amount_a': 100.0,
            'bet_amount_b': 100.0,
            'total_capital': 200.0,
            'guaranteed_profit': 3.0
        }
        sent = await notifier.send_alert(mock_opp)
        if sent:
            print("✅ Mock alert sent successfully!")
        else:
            print("❌ Failed to send mock alert")
    
    return True

async def test_database_real(opportunities):
    """Test database storage with real data."""
    print("\n" + "="*60)
    print("TEST 7: Database Storage - Real Data")
    print("="*60)
    
    config = load_config()
    db = ArbitrageDatabase(db_path=config.database.path)
    
    print("Testing database operations...")
    
    # Test insert
    if opportunities:
        opp = opportunities[0]
        db_id = db.insert_opportunity(
            market_name=opp.get('market_name', 'Test Market'),
            platform_a=opp.get('platform_a', 'polymarket'),
            platform_b=opp.get('platform_b', 'cloudbet'),
            odds_a=opp.get('odds_a', 2.0),
            odds_b=opp.get('odds_b', 2.0),
            profit_percentage=opp.get('profit_percentage', 0),
            bet_amount_a=opp.get('bet_amount_a', 0),
            bet_amount_b=opp.get('bet_amount_b', 0),
            total_capital=opp.get('total_capital', 0),
            guaranteed_profit=opp.get('guaranteed_profit', 0),
            alert_sent=False
        )
        if db_id:
            print(f"✅ Inserted opportunity with ID: {db_id}")
            
            # Test duplicate check
            is_dup = db.is_duplicate(
                opp.get('market_name', 'Test Market'),
                opp.get('platform_a', 'polymarket'),
                opp.get('platform_b', 'cloudbet'),
                opp.get('odds_a', 2.0),
                opp.get('odds_b', 2.0)
            )
            print(f"✅ Duplicate check: {is_dup}")
        else:
            print("❌ Failed to insert")
    else:
        print("⚠️  No opportunities to store")
    
    print("✅ Database test complete")

async def test_full_cycle():
    """Run full end-to-end test with real data."""
    print("\n" + "="*60)
    print("FULL SYSTEM TEST - Real Data End-to-End")
    print("="*60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Step 1: Fetch real data
    polymarket_markets = await test_polymarket_real()
    cloudbet_outcomes = await test_cloudbet_real()
    
    # Step 2: Match markets
    matched = await test_market_matching_real(polymarket_markets, cloudbet_outcomes)
    
    # Step 3: Detect arbitrage
    opportunities = await test_arbitrage_detection_real(matched)
    
    # Step 4: Calculate bet sizes
    sized_opps = await test_bet_sizing_real(opportunities)
    
    # Step 5: Send Telegram alerts (REAL)
    await test_telegram_real(sized_opps if sized_opps else opportunities)
    
    # Step 6: Store in database
    await test_database_real(opportunities)
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Polymarket Markets: {len(polymarket_markets)}")
    print(f"Cloudbet Outcomes: {len(cloudbet_outcomes)}")
    print(f"Matched Pairs: {len(matched)}")
    print(f"Arbitrage Opportunities: {len(opportunities)}")
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

if __name__ == "__main__":
    try:
        asyncio.run(test_full_cycle())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

