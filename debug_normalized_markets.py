"""Debug what markets are being normalized and passed to event matcher."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.fetchers.polymarket_fetcher import PolymarketFetcher
from src.normalizers.market_normalizer import MarketNormalizer
from src.sports_matcher import SportsMarketDetector

async def main():
    fetcher = PolymarketFetcher()
    normalizer = MarketNormalizer()
    detector = SportsMarketDetector()
    
    print("=" * 80)
    print("DEBUGGING NORMALIZED MARKETS")
    print("=" * 80)
    
    # Fetch exactly like the bot does
    print("\n1. Fetching raw markets...")
    raw_markets = await fetcher.fetch_all_markets(limit=200)
    print(f"   Raw markets: {len(raw_markets)}")
    
    # Show first few raw markets
    print(f"\n   First 10 raw market titles:")
    for i, market in enumerate(raw_markets[:10], 1):
        title = market.get('title', 'NO TITLE')
        print(f"     {i}. {title}")
    
    # Normalize
    print(f"\n2. Normalizing markets...")
    normalized = normalizer.normalize_polymarket(raw_markets)
    print(f"   Normalized markets: {len(normalized)}")
    
    # Show first few normalized
    print(f"\n   First 10 normalized market titles:")
    for i, market in enumerate(normalized[:10], 1):
        title = market.title if hasattr(market, 'title') else market.get('title', 'NO TITLE')
        print(f"     {i}. {title}")
    
    # Check for game markets
    print(f"\n3. Checking for game markets...")
    game_count = 0
    for market in normalized:
        title = market.title if hasattr(market, 'title') else market.get('title', '')
        teams = detector.extract_teams_from_title(title)
        
        if teams[0] and teams[1]:
            game_count += 1
            if game_count <= 5:
                print(f"     Game {game_count}: {title}")
                print(f"       Teams: {teams[0]} vs {teams[1]}")
    
    print(f"\n   Total game markets: {game_count}")
    
    # Check what's in raw markets that might be games
    print(f"\n4. Checking raw markets for game-like titles...")
    game_like_raw = []
    for market in raw_markets:
        title = market.get('title', '') or market.get('question', '')
        if ' vs ' in title.lower() or ' v ' in title.lower():
            game_like_raw.append(title)
    
    if game_like_raw:
        print(f"   Found {len(game_like_raw)} raw markets with 'vs':")
        for i, title in enumerate(game_like_raw[:10], 1):
            print(f"     {i}. {title}")
    else:
        print(f"   No raw markets with 'vs' found")
    
    await fetcher.close()

if __name__ == '__main__':
    asyncio.run(main())

