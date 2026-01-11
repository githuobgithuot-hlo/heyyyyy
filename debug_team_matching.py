"""
Debug script to see why teams are not matching.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.fetchers.polymarket_fetcher import PolymarketFetcher
from src.fetchers.cloudbet_fetcher import CloudbetFetcher
from src.normalizers.market_normalizer import MarketNormalizer
from src.event_matcher import EventMatcher
from src.sports_matcher import SportEventMatcher
from src.config_loader import load_config


async def main():
    print("=" * 80)
    print("DEBUG: TEAM MATCHING")
    print("=" * 80)
    
    config = load_config()
    
    # Fetch data
    pm_fetcher = PolymarketFetcher(debug_api=False)
    cb_fetcher = CloudbetFetcher(api_key=config.apis.cloudbet.api_key, debug_api=False)
    
    print("\nFetching data...")
    pm_raw = await pm_fetcher.fetch_all_markets(limit=200)
    cb_raw = await cb_fetcher.fetch_all_markets()
    
    normalizer = MarketNormalizer()
    pm_markets = normalizer.normalize_polymarket(pm_raw)
    
    # Group Cloudbet
    sports_matcher = SportEventMatcher()
    cb_events = sports_matcher._group_cloudbet_by_event(cb_raw)
    
    print(f"\nPolymarket: {len(pm_markets)} markets")
    print(f"Cloudbet: {len(cb_events)} events")
    
    # Initialize event matcher
    event_matcher = EventMatcher(team_similarity_threshold=70.0, time_window_hours=168)
    
    # Show sample teams from both
    print("\n" + "=" * 80)
    print("SAMPLE POLYMARKET SPORTS MARKETS (first 10):")
    print("=" * 80)
    
    detector = event_matcher.detector
    pm_sports = []
    for market in pm_markets[:50]:
        title = market.title if hasattr(market, 'title') else market.get('title', '')
        if detector.is_sports_market(title):
            teams = detector.extract_teams_from_title(title)
            pm_sports.append((title, teams))
            if len(pm_sports) <= 10:
                print(f"\n{len(pm_sports)}. {title}")
                print(f"   Teams: {teams[0]} vs {teams[1]}")
                print(f"   Normalized: '{event_matcher._normalize_team_name(teams[0] or '')}' vs '{event_matcher._normalize_team_name(teams[1] or '')}'")
    
    print(f"\nTotal PM sports markets: {len(pm_sports)}")
    
    print("\n" + "=" * 80)
    print("SAMPLE CLOUDBET EVENTS (first 10):")
    print("=" * 80)
    
    cb_sample = list(cb_events.items())[:10]
    for i, (event_name, event_data) in enumerate(cb_sample, 1):
        teams = detector.extract_teams_from_title(event_name)
        print(f"\n{i}. {event_name}")
        print(f"   Teams: {teams[0]} vs {teams[1]}")
        if teams[0] and teams[1]:
            print(f"   Normalized: '{event_matcher._normalize_team_name(teams[0])}' vs '{event_matcher._normalize_team_name(teams[1])}'")
        print(f"   Sport: {event_data.get('sport_key', 'unknown')}")
        print(f"   Outcomes: {list(event_data.get('outcomes', {}).keys())[:5]}")
    
    # Try matching
    print("\n" + "=" * 80)
    print("ATTEMPTING MATCHES:")
    print("=" * 80)
    
    matches_found = 0
    for pm_title, pm_teams_tuple in pm_sports[:20]:  # Check first 20
        if not pm_teams_tuple[0] or not pm_teams_tuple[1]:
            continue
        
        for cb_event_name, cb_event_data in list(cb_events.items())[:50]:  # Check first 50 CB events
            cb_teams = detector.extract_teams_from_title(cb_event_name)
            if not cb_teams[0] or not cb_teams[1]:
                continue
            
            # Check teams match
            teams_match, debug_info = event_matcher._teams_match(
                pm_teams_tuple[0], pm_teams_tuple[1],
                cb_teams[0], cb_teams[1]
            )
            
            if teams_match:
                matches_found += 1
                print(f"\n✓ MATCH #{matches_found}:")
                print(f"  PM: {pm_title}")
                print(f"  CB: {cb_event_name}")
                print(f"  PM Teams: {pm_teams_tuple[0]} vs {pm_teams_tuple[1]}")
                print(f"  CB Teams: {cb_teams[0]} vs {cb_teams[1]}")
                print(f"  Similarity: {debug_info['match_score'] if 'match_score' in debug_info else 'N/A'}")
                if matches_found >= 5:
                    break
        
        if matches_found >= 5:
            break
    
    if matches_found == 0:
        print("\n⚠ No matches found. Checking why...")
        print("\nSample comparison:")
        if pm_sports and cb_sample:
            pm_title, pm_teams = pm_sports[0]
            cb_name, cb_data = cb_sample[0]
            cb_teams = detector.extract_teams_from_title(cb_name)
            
            print(f"\nPM: {pm_title}")
            print(f"  Teams: {pm_teams}")
            print(f"\nCB: {cb_name}")
            print(f"  Teams: {cb_teams}")
            
            if pm_teams[0] and pm_teams[1] and cb_teams[0] and cb_teams[1]:
                teams_match, debug_info = event_matcher._teams_match(
                    pm_teams[0], pm_teams[1],
                    cb_teams[0], cb_teams[1]
                )
                print(f"\nMatch result: {teams_match}")
                print(f"Debug info: {debug_info}")
    
    await pm_fetcher.close()
    await cb_fetcher.close()
    
    print("\n" + "=" * 80)
    print("DEBUG COMPLETE")
    print("=" * 80)


if __name__ == '__main__':
    asyncio.run(main())

