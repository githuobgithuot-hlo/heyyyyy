"""
Debug script to see actual similarity scores between markets.
"""
import asyncio
import sys

if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

sys.path.insert(0, 'src')

from src.fetchers.polymarket_fetcher import PolymarketFetcher
from src.fetchers.cloudbet_fetcher import CloudbetFetcher
from src.normalizers.market_normalizer import MarketNormalizer
from src.sports_matcher import SportEventMatcher, SportsMarketDetector
from src.config_loader import load_config


async def main():
    print("=" * 80)
    print("SIMILARITY SCORE DEBUGGING")
    print("=" * 80)

    config = load_config()

    # Fetch data
    print("\nFetching data...")
    pm_fetcher = PolymarketFetcher(debug_api=False)
    cb_fetcher = CloudbetFetcher(api_key=config.apis.cloudbet.api_key, debug_api=False)

    pm_raw = await pm_fetcher.fetch_all_markets(limit=200)
    cb_raw = await cb_fetcher.fetch_all_markets()

    normalizer = MarketNormalizer()
    pm_markets = normalizer.normalize_polymarket(pm_raw)

    print(f"Fetched {len(pm_markets)} Polymarket markets")
    print(f"Fetched {len(cb_raw)} Cloudbet outcomes")

    # Filter sports
    detector = SportsMarketDetector()
    matcher = SportEventMatcher(similarity_threshold=70.0)

    sports_markets = [m for m in pm_markets if detector.is_sports_market(m.title)]
    print(f"\nFiltered {len(sports_markets)} sports markets from Polymarket")

    # Group Cloudbet
    cloudbet_events = {}
    for outcome in cb_raw:
        event_name = outcome.get('event_name', '')
        if event_name not in cloudbet_events:
            cloudbet_events[event_name] = []
        cloudbet_events[event_name].append(outcome)

    print(f"Grouped Cloudbet into {len(cloudbet_events)} unique events\n")

    # Show first 5 Polymarket sports markets
    print("=" * 80)
    print("SAMPLE POLYMARKET SPORTS MARKETS:")
    print("=" * 80)
    for i, market in enumerate(sports_markets[:5], 1):
        print(f"\n{i}. {market.title}")
        teams = detector.extract_teams_from_title(market.title)
        if teams[0]:
            print(f"   Teams extracted: '{teams[0]}' vs '{teams[1]}'")
        else:
            print(f"   Teams extracted: None")
        print(f"   Outcomes: {list(market.outcomes.keys())}")

    # Show first 5 Cloudbet events
    print("\n" + "=" * 80)
    print("SAMPLE CLOUDBET EVENTS:")
    print("=" * 80)
    event_names = list(cloudbet_events.keys())[:5]
    for i, event_name in enumerate(event_names, 1):
        outcomes = cloudbet_events[event_name]
        print(f"\n{i}. {event_name}")
        teams = detector.extract_teams_from_title(event_name)
        if teams[0]:
            print(f"   Teams extracted: '{teams[0]}' vs '{teams[1]}'")
        else:
            print(f"   Teams extracted: None")
        sport = outcomes[0].get('sport_key', 'unknown')
        print(f"   Sport: {sport}")
        print(f"   Outcomes: {[o['outcome'] for o in outcomes[:3]]}")

    # Calculate similarities
    print("\n" + "=" * 80)
    print("TOP SIMILARITY SCORES (First 3 PM markets vs First 10 CB events):")
    print("=" * 80)

    test_pm = sports_markets[:3]
    test_cb = list(cloudbet_events.keys())[:10]

    all_scores = []

    for pm_market in test_pm:
        pm_title = pm_market.title
        print(f"\n{'=' * 80}")
        print(f"Polymarket: {pm_title}")
        print(f"{'=' * 80}")

        scores = []
        for cb_event_name in test_cb:
            similarity = matcher._calculate_event_similarity(pm_title, cb_event_name)
            scores.append((cb_event_name, similarity))
            all_scores.append((pm_title, cb_event_name, similarity))

        # Sort by similarity
        scores.sort(key=lambda x: x[1], reverse=True)

        # Show top 5
        for cb_name, sim in scores[:5]:
            status = "✓ MATCH" if sim >= 70.0 else "✗ Too low"
            print(f"  {sim:5.1f}% - {status} - {cb_name}")

    # Find best overall match
    print("\n" + "=" * 80)
    print("BEST OVERALL SIMILARITY SCORES:")
    print("=" * 80)

    all_scores.sort(key=lambda x: x[2], reverse=True)

    for pm_title, cb_name, sim in all_scores[:10]:
        status = "✓ MATCH" if sim >= 70.0 else "✗ Too low"
        print(f"{sim:5.1f}% - {status}")
        print(f"  PM: {pm_title}")
        print(f"  CB: {cb_name}\n")

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    matches_70 = sum(1 for _, _, s in all_scores if s >= 70.0)
    matches_60 = sum(1 for _, _, s in all_scores if s >= 60.0)
    matches_50 = sum(1 for _, _, s in all_scores if s >= 50.0)

    print(f"\nOut of {len(all_scores)} comparisons:")
    print(f"  Matches >= 70%: {matches_70}")
    print(f"  Matches >= 60%: {matches_60}")
    print(f"  Matches >= 50%: {matches_50}")

    if matches_70 == 0:
        print("\n⚠ No matches found at 70% threshold")
        print("This confirms Polymarket and Cloudbet have different event types:")
        print("  - Polymarket: Season futures (Super Bowl, MVP, etc.)")
        print("  - Cloudbet: Individual games (Team1 vs Team2)")

    await pm_fetcher.close()
    await cb_fetcher.close()


if __name__ == '__main__':
    asyncio.run(main())
