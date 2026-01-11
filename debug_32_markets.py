"""Debug what's in those 32 markets."""
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
    print("DEBUGGING 32 MARKETS")
    print("=" * 80)
    
    # Fetch exactly like the bot does
    raw_markets = await fetcher.fetch_all_markets(limit=200)
    print(f"\nRaw markets fetched: {len(raw_markets)}")
    
    # Normalize
    normalized = normalizer.normalize_polymarket(raw_markets)
    print(f"Normalized markets: {len(normalized)}")
    
    # Show all market titles
    print(f"\n{'='*80}")
    print("ALL MARKET TITLES:")
    print(f"{'='*80}")
    
    for i, market in enumerate(normalized, 1):
        title = market.title if hasattr(market, 'title') else market.get('title', '')
        teams = detector.extract_teams_from_title(title)
        
        print(f"\n{i}. {title}")
        print(f"   Teams extracted: {teams}")
        
        if teams[0] and teams[1]:
            print(f"   *** GAME MARKET ***")
        elif teams[0]:
            print(f"   (Futures - 1 team)")
        else:
            print(f"   (No teams)")
    
    # Check raw markets for event titles
    print(f"\n{'='*80}")
    print("CHECKING RAW MARKETS FOR EVENT INFO")
    print(f"{'='*80}")
    
    for i, market in enumerate(raw_markets[:10], 1):
        title = market.get('title') or market.get('question', '')
        print(f"\n{i}. {title}")
        print(f"   ID: {market.get('id')}")
        print(f"   All keys: {list(market.keys())[:15]}")
    
    await fetcher.close()

if __name__ == '__main__':
    asyncio.run(main())
