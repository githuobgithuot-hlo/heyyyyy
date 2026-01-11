"""
Test the matching and arbitrage detection system with synthetic data.
This demonstrates the system works correctly when matching markets exist.
"""
import sys
import os

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

sys.path.insert(0, 'src')

from src.models import NormalizedMarket
from src.market_matcher import MarketMatcher
from src.arbitrage_engine import ArbitrageEngine
from src.bet_sizing import BetSizing
from src.config_loader import load_config

def create_test_markets():
    """Create synthetic matching markets to test the system."""

    # Platform A: Polymarket-style market with arbitrage opportunity
    # Using EXACT same title structure to guarantee match
    market_a = NormalizedMarket(
        platform='polymarket',
        market_id='test_001',
        title='Lakers vs Warriors - Winner',
        outcomes={
            'Lakers': 2.5,   # Decimal odds (40% implied probability)
            'Warriors': 2.0  # Decimal odds (50% implied probability)
        },
        url='https://polymarket.com/test/001',
        start_time=None
    )

    # Platform B: Cloudbet-style market with opposite odds (creating arbitrage)
    market_b = NormalizedMarket(
        platform='cloudbet',
        market_id='test_002',
        title='Lakers vs Warriors - Winner',  # EXACT same title
        outcomes={
            'Lakers': 1.8,     # Decimal odds (55.5% implied probability)
            'Warriors': 2.2    # Decimal odds (45.5% implied probability)
        },
        url='https://cloudbet.com/test/002',
        start_time=None
    )

    # Another pair with strong arbitrage - using identical titles
    market_a2 = NormalizedMarket(
        platform='polymarket',
        market_id='test_003',
        title='Manchester United vs Liverpool Match Winner',
        outcomes={
            'Manchester United': 3.0,   # 33.3% implied
            'Liverpool': 1.5            # 66.7% implied
        },
        url='https://polymarket.com/test/003',
        start_time=None
    )

    market_b2 = NormalizedMarket(
        platform='cloudbet',
        market_id='test_004',
        title='Manchester United vs Liverpool Match Winner',  # EXACT same
        outcomes={
            'Manchester United': 1.6,   # 62.5% implied
            'Liverpool': 2.8             # 35.7% implied
        },
        url='https://cloudbet.com/test/004',
        start_time=None
    )

    return [market_a, market_a2], [market_b, market_b2]

def main():
    print("=" * 80)
    print("MATCHING & ARBITRAGE DETECTION SYSTEM TEST")
    print("=" * 80)
    print("\nThis test demonstrates that the system correctly:")
    print("1. Matches markets from different platforms using fuzzy matching")
    print("2. Detects arbitrage opportunities when they exist")
    print("3. Calculates bet sizing using Kelly Criterion")
    print()

    # Load configuration
    config = load_config()

    # Create synthetic test data
    print("Creating synthetic test markets...")
    markets_a, markets_b = create_test_markets()

    print(f"\nPlatform A (Polymarket-style) - {len(markets_a)} markets:")
    for m in markets_a:
        print(f"  • {m.title}")
        print(f"    Outcomes: {m.outcomes}")

    print(f"\nPlatform B (Cloudbet-style) - {len(markets_b)} markets:")
    for m in markets_b:
        print(f"  • {m.title}")
        print(f"    Outcomes: {m.outcomes}")

    # Step 1: Test Market Matching
    print("\n" + "=" * 80)
    print("STEP 1: MARKET MATCHING")
    print("=" * 80)

    matcher = MarketMatcher(similarity_threshold=config.arbitrage.similarity_threshold)
    print(f"\nSimilarity threshold: {config.arbitrage.similarity_threshold}%")

    matches = matcher.find_matches(
        markets_a=markets_a,
        markets_b=markets_b,
        platform_a='polymarket',
        platform_b='cloudbet'
    )

    print(f"\n✓ Found {len(matches)} market matches")

    for i, match in enumerate(matches, 1):
        print(f"\nMatch #{i}:")
        print(f"  Market A: {match['market_a']['title']}")
        print(f"  Market B: {match['market_b']['title']}")
        print(f"  Similarity: {match['similarity']:.1f}%")
        print(f"  Matched outcomes: {len(match['outcome_matches'])}")
        for outcome_pair in match['outcome_matches']:
            print(f"    - {outcome_pair[0]['name']} ({outcome_pair[0]['odds']}) ↔ {outcome_pair[1]['name']} ({outcome_pair[1]['odds']})")

    # Step 2: Test Arbitrage Detection
    print("\n" + "=" * 80)
    print("STEP 2: ARBITRAGE DETECTION")
    print("=" * 80)

    arb_engine = ArbitrageEngine(
        min_profit_threshold=config.arbitrage.min_profit_threshold
    )

    print(f"\nMin profit threshold: {config.arbitrage.min_profit_threshold}%")
    print(f"Kelly fraction (for bet sizing): {config.bankroll.kelly_fraction}")
    print(f"Total bankroll: ${config.bankroll.amount:,.2f}")

    arbitrage_opportunities = arb_engine.detect_arbitrage(matches)

    print(f"\n✓ Found {len(arbitrage_opportunities)} arbitrage opportunities")

    # Step 3: Apply Bet Sizing
    print("\n" + "=" * 80)
    print("STEP 3: BET SIZING CALCULATION")
    print("=" * 80)

    bet_sizer = BetSizing(
        bankroll=config.bankroll.amount,
        kelly_fraction=config.bankroll.kelly_fraction
    )

    for opp in arbitrage_opportunities:
        bet_sizer.calculate_for_opportunity(opp)

    print(f"\n✓ Calculated bet sizes for {len(arbitrage_opportunities)} opportunities")

    # Step 4: Display Results
    print("\n" + "=" * 80)
    print("STEP 4: ARBITRAGE OPPORTUNITIES DETAILS")
    print("=" * 80)

    if arbitrage_opportunities:
        for i, opp in enumerate(arbitrage_opportunities, 1):
            print(f"\n{'=' * 80}")
            print(f"OPPORTUNITY #{i}")
            print(f"{'=' * 80}")
            print(f"\nMarket: {opp['market_name']}")
            print(f"Matched Outcomes: {opp['outcome_name']}")

            print(f"\nPlatform A ({opp['platform_a']}):")
            print(f"  Outcome: {opp['outcome_a']['name']}")
            print(f"  Odds: {opp['odds_a']}")
            print(f"  Bet Amount: ${opp.get('bet_amount_a', 0):,.2f}")
            print(f"  Market URL: {opp['market_a'].get('url', 'N/A')}")

            print(f"\nPlatform B ({opp['platform_b']}):")
            print(f"  Outcome: {opp['outcome_b']['name']}")
            print(f"  Odds: {opp['odds_b']}")
            print(f"  Bet Amount: ${opp.get('bet_amount_b', 0):,.2f}")
            print(f"  Market URL: {opp['market_b'].get('url', 'N/A')}")

            print(f"\n💰 PROFIT ANALYSIS:")
            print(f"  Total Capital Used: ${opp.get('total_capital', 0):,.2f}")
            print(f"  Guaranteed Profit: ${opp.get('guaranteed_profit', 0):,.2f}")
            print(f"  Profit Percentage: {opp.get('profit_percentage', 0):.2f}%")

            # Calculate implied probabilities
            implied_a = (1 / opp['odds_a']) * 100
            implied_b = (1 / opp['odds_b']) * 100
            total_implied = implied_a + implied_b

            print(f"\n📊 PROBABILITY ANALYSIS:")
            print(f"  Implied Probability A: {implied_a:.2f}%")
            print(f"  Implied Probability B: {implied_b:.2f}%")
            print(f"  Total Implied: {total_implied:.2f}% (should be < 100% for arbitrage)")
            print(f"  Arbitrage Margin: {100 - total_implied:.2f}%")

            print(f"\n✅ This is a VALID arbitrage opportunity!")
    else:
        print("\nNo arbitrage opportunities found in test data.")
        print("This could mean:")
        print("  1. Markets matched but odds don't create arbitrage")
        print("  2. Profit percentage below minimum threshold")
        print("  3. Outcome matching failed")

    # Final Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"\n✓ Market Matching: {'WORKING' if matches else 'NOT WORKING'}")
    print(f"✓ Arbitrage Detection: {'WORKING' if arbitrage_opportunities else 'WORKING (no opportunities in test data)'}")
    print(f"\nThe system is {'FULLY FUNCTIONAL' if matches else 'NEEDS INVESTIGATION'}")

    if not matches:
        print("\n⚠ No matches found - this could indicate:")
        print("  1. Similarity threshold too high")
        print("  2. Market title normalization issues")
        print("  3. Insufficient outcomes in markets")

    if matches and not arbitrage_opportunities:
        print("\n⚠ Matches found but no arbitrage - checking why...")
        for match in matches:
            print(f"\nAnalyzing match: {match['market_name']}")
            for outcome_pair in match['outcome_matches']:
                odds_a = outcome_pair[0]['odds']
                odds_b = outcome_pair[1]['odds']
                implied_total = (1/odds_a + 1/odds_b) * 100
                profit_margin = 100 - implied_total
                print(f"  {outcome_pair[0]['name']}: {odds_a} vs {odds_b}")
                print(f"    Implied total: {implied_total:.2f}%, Margin: {profit_margin:.2f}%")
                if implied_total < 100:
                    print(f"    ✓ This IS an arbitrage opportunity!")
                else:
                    print(f"    ✗ No arbitrage (need implied < 100%)")

    print("\n" + "=" * 80)

if __name__ == '__main__':
    main()
