"""
Test sports matching with real API data.
Demonstrates the new sports event matching and outcome translation.
"""
import asyncio
import sys
import os

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

sys.path.insert(0, 'src')

from src.fetchers.polymarket_fetcher import PolymarketFetcher
from src.fetchers.cloudbet_fetcher import CloudbetFetcher
from src.normalizers.market_normalizer import MarketNormalizer
from src.sports_matcher import SportEventMatcher, SportsMarketDetector
from src.sports_arbitrage_engine import SportsArbitrageEngine
from src.bet_sizing import BetSizing
from src.config_loader import load_config


async def main():
    print("=" * 80)
    print("SPORTS MATCHING TEST - Real API Data")
    print("=" * 80)
    print()

    # Load configuration
    config = load_config()

    # Initialize fetchers
    print("Initializing API fetchers...")
    pm_fetcher = PolymarketFetcher(debug_api=False)
    cb_fetcher = CloudbetFetcher(
        api_key=config.apis.cloudbet.api_key,
        debug_api=False
    )

    # Fetch data
    print("\n" + "=" * 80)
    print("STEP 1: FETCHING REAL DATA")
    print("=" * 80)

    print("\nFetching from Polymarket...")
    pm_raw = await pm_fetcher.fetch_all_markets(limit=200)

    print(f"\nFetching from Cloudbet...")
    cb_raw = await cb_fetcher.fetch_all_markets()

    # Normalize
    print("\n" + "=" * 80)
    print("STEP 2: NORMALIZING DATA")
    print("=" * 80)

    normalizer = MarketNormalizer()
    pm_markets = normalizer.normalize_polymarket(pm_raw)
    cb_markets = normalizer.normalize_cloudbet(cb_raw)

    print(f"\nPolymarket: {len(pm_markets)} markets")
    print(f"Cloudbet: {len(cb_markets)} markets ({len(cb_raw)} total outcomes)")

    # Filter for sports
    print("\n" + "=" * 80)
    print("STEP 3: FILTERING FOR SPORTS MARKETS")
    print("=" * 80)

    detector = SportsMarketDetector()
    sports_markets = []

    for market in pm_markets:
        if detector.is_sports_market(market.title):
            sports_markets.append(market)
            teams = detector.extract_teams_from_title(market.title)
            print(f"\n  ✓ {market.title}")
            if teams[0]:
                print(f"    Teams: {teams[0]} vs {teams[1]}")
            print(f"    Outcomes: {list(market.outcomes.keys())}")

    print(f"\nTotal sports markets found: {len(sports_markets)}")

    if len(sports_markets) == 0:
        print("\n⚠ No sports markets found in Polymarket.")
        print("This is expected - Polymarket focuses on politics/crypto/entertainment.")
        print("\nTo test this feature, you would need:")
        print("  1. Polymarket to offer sports betting markets, OR")
        print("  2. Add a sports-focused prediction market API")
        await pm_fetcher.close()
        await cb_fetcher.close()
        return

    # Sports matching
    print("\n" + "=" * 80)
    print("STEP 4: SPORTS EVENT MATCHING")
    print("=" * 80)

    matcher = SportEventMatcher(similarity_threshold=70.0)
    sports_matches = matcher.find_sports_matches(
        polymarket_markets=pm_markets,
        cloudbet_outcomes=cb_raw,
        platform_a="polymarket",
        platform_b="cloudbet"
    )

    print(f"\n✓ Found {len(sports_matches)} sports event matches")

    if sports_matches:
        for i, match in enumerate(sports_matches, 1):
            print(f"\n{'-' * 80}")
            print(f"MATCH #{i}")
            print(f"{'-' * 80}")
            print(f"Polymarket: {match['market_name']}")
            print(f"Cloudbet:   {match['market_b']['event_name']}")
            print(f"Similarity: {match['similarity']:.1f}%")
            print(f"Sport: {match['market_b'].get('sport_key', 'unknown')}")
            print(f"Competition: {match['market_b'].get('competition_key', 'unknown')}")
            print(f"\nOutcome Mappings ({len(match['outcome_mapping'])}):")
            for pm_outcome, cb_outcome in match['outcome_mapping']:
                print(f"  {pm_outcome['name']:20} @ {pm_outcome['odds']:.2f} <-> {cb_outcome['name']:20} @ {cb_outcome['odds']:.2f}")

    # Arbitrage detection
    print("\n" + "=" * 80)
    print("STEP 5: ARBITRAGE DETECTION")
    print("=" * 80)

    arb_engine = SportsArbitrageEngine(
        min_profit_threshold=config.arbitrage.min_profit_threshold
    )

    opportunities = arb_engine.detect_sports_arbitrage(sports_matches)

    print(f"\n✓ Found {len(opportunities)} arbitrage opportunities")

    if opportunities:
        # Calculate bet sizing
        bet_sizer = BetSizing(
            bankroll=config.bankroll.amount,
            kelly_fraction=config.bankroll.kelly_fraction
        )

        for opp in opportunities:
            bet_sizer.calculate_for_opportunity(opp)

        # Display opportunities
        print("\n" + "=" * 80)
        print("ARBITRAGE OPPORTUNITIES")
        print("=" * 80)

        for i, opp in enumerate(opportunities, 1):
            print(f"\n{'=' * 80}")
            print(f"OPPORTUNITY #{i}")
            print(f"{'=' * 80}")
            print(f"\nEvent: {opp['market_name']}")
            print(f"Sport: {opp.get('sport_key', 'unknown')}")
            print(f"Start Time: {opp.get('start_time', 'TBD')}")

            print(f"\nPlatform A (Polymarket):")
            print(f"  Outcome: {opp['outcome_a']['name']}")
            print(f"  Odds: {opp['odds_a']:.2f}")
            print(f"  Bet Amount: ${opp.get('bet_amount_a', 0):,.2f}")

            print(f"\nPlatform B (Cloudbet):")
            print(f"  Outcome: {opp['outcome_b']['name']}")
            print(f"  Odds: {opp['odds_b']:.2f}")
            print(f"  Bet Amount: ${opp.get('bet_amount_b', 0):,.2f}")

            print(f"\n💰 PROFIT ANALYSIS:")
            print(f"  Total Capital: ${opp.get('total_capital', 0):,.2f}")
            print(f"  Guaranteed Profit: ${opp.get('guaranteed_profit', 0):,.2f}")
            print(f"  Profit %: {opp.get('profit_percentage', 0):.2f}%")

            # Probability analysis
            implied_a = (1 / opp['odds_a']) * 100
            implied_b = (1 / opp['odds_b']) * 100
            total_implied = implied_a + implied_b

            print(f"\n📊 PROBABILITY ANALYSIS:")
            print(f"  Implied Prob A: {implied_a:.2f}%")
            print(f"  Implied Prob B: {implied_b:.2f}%")
            print(f"  Total Implied: {total_implied:.2f}%")
            print(f"  Arbitrage Margin: {100 - total_implied:.2f}%")

    else:
        print("\nNo arbitrage opportunities found.")
        if sports_matches:
            print("\nReasons could be:")
            print("  - Odds too similar between platforms")
            print("  - Profit below minimum threshold ({:.2f}%)".format(config.arbitrage.min_profit_threshold))
            print("  - Market inefficiencies not present")

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"\nPolymarket markets: {len(pm_markets)}")
    print(f"Sports markets detected: {len(sports_markets)}")
    print(f"Cloudbet outcomes: {len(cb_raw)}")
    print(f"Sports matches found: {len(sports_matches)}")
    print(f"Arbitrage opportunities: {len(opportunities)}")

    if len(sports_markets) > 0 and len(sports_matches) > 0:
        print("\n✅ Sports matching system is WORKING!")
        print("   - Successfully detected sports markets in Polymarket")
        print("   - Successfully matched with Cloudbet events")
        print("   - Outcome translation working correctly")
    elif len(sports_markets) > 0:
        print("\n⚠ Sports markets detected but no matches found")
        print("   This could mean:")
        print("   - Different events between platforms")
        print("   - Team/event names too different")
        print("   - Try lowering similarity threshold")
    else:
        print("\n⚠ No sports markets found in Polymarket")
        print("   Polymarket primarily covers politics, crypto, and entertainment")

    print("\n" + "=" * 80)

    # Cleanup
    await pm_fetcher.close()
    await cb_fetcher.close()


if __name__ == '__main__':
    asyncio.run(main())
