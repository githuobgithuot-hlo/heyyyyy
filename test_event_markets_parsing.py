"""Test if markets from events are being parsed correctly."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.fetchers.polymarket_fetcher import PolymarketFetcher
from src.normalizers.market_normalizer import MarketNormalizer

async def main():
    fetcher = PolymarketFetcher()
    normalizer = MarketNormalizer()
    
    print("=" * 80)
    print("TESTING EVENT MARKETS PARSING")
    print("=" * 80)
    
    # Fetch markets (with limit to avoid too many)
    print("\nFetching markets...")
    raw_markets = await fetcher.fetch_all_markets(limit=50)
    print(f"Raw markets fetched: {len(raw_markets)}")
    
    # Check how many are game markets
    from src.sports_matcher import SportsMarketDetector
    detector = SportsMarketDetector()
    
    game_markets = []
    for market in raw_markets:
        title = market.get('title') or market.get('question', '')
        teams = detector.extract_teams_from_title(title)
        if teams[0] and teams[1]:
            game_markets.append((title, teams))
    
    print(f"\nGame markets found: {len(game_markets)}")
    for i, (title, teams) in enumerate(game_markets[:10], 1):
        print(f"  {i}. {title}")
        print(f"     Teams: {teams[0]} vs {teams[1]}")
    
    # Normalize
    print(f"\nNormalizing markets...")
    normalized = normalizer.normalize_polymarket(raw_markets)
    print(f"Normalized markets: {len(normalized)}")
    
    # Check normalized game markets
    normalized_game = []
    for market in normalized:
        title = market.title if hasattr(market, 'title') else market.get('title', '')
        teams = detector.extract_teams_from_title(title)
        if teams[0] and teams[1]:
            normalized_game.append((title, teams))
    
    print(f"\nNormalized game markets: {len(normalized_game)}")
    for i, (title, teams) in enumerate(normalized_game[:10], 1):
        print(f"  {i}. {title}")
        print(f"     Teams: {teams[0]} vs {teams[1]}")
    
    await fetcher.close()

if __name__ == '__main__':
    asyncio.run(main())

