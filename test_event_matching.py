"""
Test the new event-level matching and probability-based value detection.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.fetchers.polymarket_fetcher import PolymarketFetcher
from src.fetchers.cloudbet_fetcher import CloudbetFetcher
from src.normalizers.market_normalizer import MarketNormalizer
from src.event_matcher import EventMatcher
from src.probability_engine import ProbabilityEngine
from src.sports_arbitrage_engine import SportsArbitrageEngine
from src.config_loader import load_config


async def main():
    print("=" * 80)
    print("EVENT-LEVEL MATCHING TEST")
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
    print("STEP 1: FETCHING DATA")
    print("=" * 80)
    
    print("\nFetching from Polymarket...")
    pm_raw = await pm_fetcher.fetch_all_markets(limit=200)
    print(f"Fetched {len(pm_raw)} Polymarket markets")
    
    print("\nFetching from Cloudbet...")
    cb_raw = await cb_fetcher.fetch_all_markets()
    print(f"Fetched {len(cb_raw)} Cloudbet outcomes")
    
    # Normalize
    print("\n" + "=" * 80)
    print("STEP 2: NORMALIZING DATA")
    print("=" * 80)
    
    normalizer = MarketNormalizer()
    pm_markets = normalizer.normalize_polymarket(pm_raw)
    
    print(f"Normalized: {len(pm_markets)} Polymarket markets")
    
    # Group Cloudbet by event
    print("\n" + "=" * 80)
    print("STEP 3: GROUPING CLOUDBET BY EVENT")
    print("=" * 80)
    
    from src.sports_matcher import SportEventMatcher
    sports_matcher = SportEventMatcher()
    cb_events = sports_matcher._group_cloudbet_by_event(cb_raw)
    
    print(f"Grouped into {len(cb_events)} Cloudbet events")
    
    # Event-level matching
    print("\n" + "=" * 80)
    print("STEP 4: EVENT-LEVEL MATCHING (Teams + Sport + Time)")
    print("=" * 80)
    
    event_matcher = EventMatcher(
        team_similarity_threshold=80.0,
        time_window_hours=48
    )
    
    event_matches = event_matcher.match_events(pm_markets, cb_events)
    
    print(f"\nFound {len(event_matches)} event-level matches!")
    
    if event_matches:
        print("\n" + "-" * 80)
        print("MATCHED EVENTS:")
        print("-" * 80)
        for i, match in enumerate(event_matches[:10], 1):
            print(f"\n{i}. {match['market_name']}")
            print(f"   <-> {match['event_name']}")
            print(f"   Teams: {match['pm_teams'][0]} vs {match['pm_teams'][1]}")
            print(f"   Sport: {match.get('sport', 'unknown')}")
            if match.get('pm_time'):
                print(f"   PM Time: {match['pm_time']}")
            if match.get('cb_time'):
                print(f"   CB Time: {match['cb_time']}")
    else:
        print("\n⚠ No event-level matches found.")
        print("\nThis could mean:")
        print("  1. No overlapping events between platforms")
        print("  2. Team names don't match closely enough")
        print("  3. Events are outside the time window")
        print("  4. Different sports/leagues")
    
    # Probability-based value detection
    if event_matches:
        print("\n" + "=" * 80)
        print("STEP 5: PROBABILITY-BASED VALUE DETECTION")
        print("=" * 80)
        
        prob_engine = ProbabilityEngine(
            min_value_edge=0.05,  # 5% minimum edge
            min_arbitrage_profit=0.5  # 0.5% minimum for arbitrage
        )
        
        opportunities = prob_engine.detect_value_opportunities(event_matches)
        
        print(f"\nFound {len(opportunities)} value opportunities!")
        
        arbitrage_opps = [o for o in opportunities if o['type'] == 'arbitrage']
        value_edges = [o for o in opportunities if o['type'] == 'value_edge']
        
        print(f"  - {len(arbitrage_opps)} arbitrage opportunities")
        print(f"  - {len(value_edges)} value edge opportunities")
        
        if opportunities:
            print("\n" + "-" * 80)
            print("OPPORTUNITIES:")
            print("-" * 80)
            for i, opp in enumerate(opportunities[:10], 1):
                print(f"\n{i}. {opp['market_name']}")
                print(f"   Type: {opp['type']}")
                if opp['type'] == 'arbitrage':
                    print(f"   Team: {opp['team']}")
                    print(f"   PM Probability: {opp['pm_probability']:.2%}")
                    print(f"   CB Probability: {opp['cb_probability']:.2%}")
                    print(f"   Total Probability: {opp['total_probability']:.2%}")
                    print(f"   💰 Profit: {opp['profit_percentage']:.2f}%")
                else:
                    print(f"   Team: {opp['team']}")
                    print(f"   PM Probability: {opp['pm_probability']:.2%}")
                    print(f"   CB Probability: {opp['cb_probability']:.2%}")
                    print(f"   Edge: {opp['edge_percentage']:.2f}%")
                    print(f"   Better Platform: {opp['better_platform']}")
    
    # Cleanup
    await pm_fetcher.close()
    await cb_fetcher.close()
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)


if __name__ == '__main__':
    asyncio.run(main())

