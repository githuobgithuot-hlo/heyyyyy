"""Check Polymarket markets to see why no game markets are found."""
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
    print("POLYMARKET GAME MARKETS DIAGNOSTIC")
    print("=" * 80)
    
    markets = await fetcher.fetch_all_markets(limit=200)
    
    print(f"\nTotal markets fetched: {len(markets)}")
    
    # Categorize markets
    sports_markets = []
    game_markets = []
    futures_markets = []
    non_sports = []
    
    for market in markets:
        title = market.get('title', '')
        
        if detector.is_sports_market(title):
            sports_markets.append(market)
            teams = detector.extract_teams_from_title(title)
            
            if teams[0] and teams[1]:
                game_markets.append((title, teams))
            elif teams[0] and not teams[1]:
                futures_markets.append((title, teams[0]))
        else:
            non_sports.append(title)
    
    print(f"\nSports markets: {len(sports_markets)}")
    print(f"  - Game markets (2 teams): {len(game_markets)}")
    print(f"  - Futures/props (1 team): {len(futures_markets)}")
    print(f"Non-sports: {len(non_sports)}")
    
    # Show examples
    print("\n" + "=" * 80)
    print("GAME MARKETS (2 teams) - First 10:")
    print("=" * 80)
    for i, (title, teams) in enumerate(game_markets[:10], 1):
        print(f"\n{i}. {title}")
        print(f"   Team 1: {teams[0]}")
        print(f"   Team 2: {teams[1]}")
    
    print("\n" + "=" * 80)
    print("FUTURES/PROPS (1 team) - First 10:")
    print("=" * 80)
    for i, (title, team) in enumerate(futures_markets[:10], 1):
        print(f"\n{i}. {title}")
        print(f"   Team: {team}")
    
    # Check for "vs" patterns that might be missed
    print("\n" + "=" * 80)
    print("MARKETS WITH 'vs' OR 'v' (potential games):")
    print("=" * 80)
    vs_markets = []
    for market in markets:
        title = market.get('title', '').lower()
        if ' vs ' in title or ' v ' in title or ' versus ' in title:
            teams = detector.extract_teams_from_title(market.get('title', ''))
            vs_markets.append((market.get('title', ''), teams))
    
    print(f"\nFound {len(vs_markets)} markets with 'vs'/'v'/'versus'")
    for i, (title, teams) in enumerate(vs_markets[:10], 1):
        print(f"\n{i}. {title}")
        print(f"   Teams extracted: {teams}")
        if teams[0] and teams[1]:
            print(f"   ✓ GAME MARKET")
        elif teams[0]:
            print(f"   ✗ Only 1 team extracted")
        else:
            print(f"   ✗ No teams extracted")
    
    await fetcher.close()

if __name__ == '__main__':
    asyncio.run(main())

