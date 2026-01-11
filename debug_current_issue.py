"""Debug why no game markets are being matched."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.fetchers.polymarket_fetcher import PolymarketFetcher
from src.sports_matcher import SportsMarketDetector
from src.normalizer import MarketNormalizer

async def main():
    fetcher = PolymarketFetcher()
    detector = SportsMarketDetector()
    normalizer = MarketNormalizer()
    
    print("=" * 80)
    print("DEBUGGING CURRENT ISSUE")
    print("=" * 80)
    
    # Fetch markets the same way the bot does
    print("\n1. Fetching markets...")
    raw_markets = await fetcher.fetch_all_markets(limit=200)
    print(f"   Raw markets fetched: {len(raw_markets)}")
    
    # Normalize them
    print("\n2. Normalizing markets...")
    normalized = normalizer.normalize_polymarket(raw_markets)
    print(f"   Normalized markets: {len(normalized)}")
    
    # Check what we have
    print("\n3. Analyzing markets...")
    game_markets = []
    futures_markets = []
    no_teams = []
    
    for market in normalized[:50]:  # Check first 50
        title = market.title if hasattr(market, 'title') else market.get('title', '')
        teams = detector.extract_teams_from_title(title)
        
        if teams[0] and teams[1]:
            game_markets.append((title, teams))
        elif teams[0] and not teams[1]:
            futures_markets.append((title, teams[0]))
        else:
            no_teams.append(title)
    
    print(f"\n   Game markets (2 teams): {len(game_markets)}")
    print(f"   Futures/props (1 team): {len(futures_markets)}")
    print(f"   No teams extracted: {len(no_teams)}")
    
    # Show examples
    if game_markets:
        print(f"\n   Game markets found:")
        for i, (title, teams) in enumerate(game_markets[:5], 1):
            print(f"     {i}. {title}")
            print(f"        Teams: {teams[0]} vs {teams[1]}")
    else:
        print(f"\n   No game markets found!")
        print(f"\n   First 10 markets with no teams:")
        for i, title in enumerate(no_teams[:10], 1):
            print(f"     {i}. {title}")
    
    # Check raw markets structure
    print(f"\n4. Checking raw market structure...")
    if raw_markets:
        first = raw_markets[0]
        print(f"   First market keys: {list(first.keys())[:15]}")
        print(f"   Title: {first.get('title', 'NO TITLE')}")
        print(f"   Question: {first.get('question', 'NO QUESTION')}")
    
    await fetcher.close()

if __name__ == '__main__':
    asyncio.run(main())

