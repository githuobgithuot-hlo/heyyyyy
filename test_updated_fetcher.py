"""Test the updated fetcher to see if it finds games."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.fetchers.polymarket_fetcher import PolymarketFetcher
from src.sports_matcher import SportsMarketDetector

async def main():
    fetcher = PolymarketFetcher()
    detector = SportsMarketDetector()
    
    print("=" * 80)
    print("TESTING UPDATED POLYMARKET FETCHER")
    print("=" * 80)
    
    # Fetch markets using updated method
    print("\nFetching markets (using /events + /markets)...")
    markets = await fetcher.fetch_all_markets(limit=200)
    
    print(f"\nTotal markets fetched: {len(markets)}")
    
    # Analyze markets
    sports_markets = []
    game_markets = []
    futures_markets = []
    
    for market in markets:
        title = market.get('title', '')
        
        if detector.is_sports_market(title):
            sports_markets.append(market)
            teams = detector.extract_teams_from_title(title)
            
            if teams[0] and teams[1]:
                game_markets.append((title, teams))
            elif teams[0] and not teams[1]:
                futures_markets.append((title, teams[0]))
    
    print(f"\n{'='*80}")
    print("ANALYSIS")
    print(f"{'='*80}")
    print(f"Sports markets: {len(sports_markets)}")
    print(f"  - Game markets (2 teams): {len(game_markets)}")
    print(f"  - Futures/props (1 team): {len(futures_markets)}")
    
    # Show game markets
    if game_markets:
        print(f"\n{'='*80}")
        print("GAME MARKETS FOUND (First 20):")
        print(f"{'='*80}")
        for i, (title, teams) in enumerate(game_markets[:20], 1):
            print(f"\n{i}. {title}")
            print(f"   Team 1: {teams[0]}")
            print(f"   Team 2: {teams[1]}")
    else:
        print("\nNo game markets found yet")
        print("\nShowing first 10 sports markets for debugging:")
        for i, market in enumerate(sports_markets[:10], 1):
            title = market.get('title', '')
            teams = detector.extract_teams_from_title(title)
            print(f"\n{i}. {title}")
            print(f"   Teams extracted: {teams}")
    
    await fetcher.close()

if __name__ == '__main__':
    asyncio.run(main())

