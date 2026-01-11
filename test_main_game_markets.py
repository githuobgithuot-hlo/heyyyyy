"""Test if main game markets are being extracted."""
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
    print("TESTING MAIN GAME MARKET EXTRACTION")
    print("=" * 80)
    
    # Fetch markets
    print("\nFetching markets...")
    raw_markets = await fetcher.fetch_all_markets(limit=100)
    print(f"Raw markets: {len(raw_markets)}")
    
    # Normalize
    normalized = normalizer.normalize_polymarket(raw_markets)
    print(f"Normalized markets: {len(normalized)}")
    
    # Find game markets
    print(f"\n{'='*80}")
    print("ANALYZING MARKETS")
    print(f"{'='*80}")
    
    game_markets = []
    for market in normalized:
        title = market.title if hasattr(market, 'title') else market.get('title', '')
        teams = detector.extract_teams_from_title(title)
        
        if teams[0] and teams[1]:
            game_markets.append((title, teams, market))
    
    print(f"\nGame markets found: {len(game_markets)}")
    
    if game_markets:
        print(f"\nFirst 10 game markets:")
        for i, (title, teams, market) in enumerate(game_markets[:10], 1):
            print(f"\n{i}. {title}")
            print(f"   Teams: {teams[0]} vs {teams[1]}")
            outcomes = market.outcomes if hasattr(market, 'outcomes') else market.get('outcomes', {})
            print(f"   Outcomes: {list(outcomes.keys())[:5]}")
    else:
        print("\nNo game markets found!")
        print("\nFirst 20 market titles:")
        for i, market in enumerate(normalized[:20], 1):
            title = market.title if hasattr(market, 'title') else market.get('title', '')
            print(f"{i}. {title}")
    
    await fetcher.close()

if __name__ == '__main__':
    asyncio.run(main())

