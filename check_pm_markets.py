"""Quick check of Polymarket market types."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.fetchers.polymarket_fetcher import PolymarketFetcher
from src.sports_matcher import SportsMarketDetector

async def main():
    fetcher = PolymarketFetcher()
    detector = SportsMarketDetector()
    
    markets = await fetcher.fetch_all_markets(limit=100)
    
    print("=" * 80)
    print("POLYMARKET SPORTS MARKETS ANALYSIS")
    print("=" * 80)
    
    futures_count = 0
    game_count = 0
    
    for market in markets:
        title = market.get('title', '')
        if detector.is_sports_market(title):
            teams = detector.extract_teams_from_title(title)
            
            if teams[0] and teams[1]:
                game_count += 1
                if game_count <= 5:
                    print(f"\nGAME: {title}")
                    print(f"  Teams: {teams[0]} vs {teams[1]}")
            elif teams[0] and not teams[1]:
                futures_count += 1
                if futures_count <= 5:
                    print(f"\nFUTURES: {title}")
                    print(f"  Team: {teams[0]}")
    
    print(f"\n" + "=" * 80)
    print(f"SUMMARY: {game_count} game markets, {futures_count} futures markets")
    print("=" * 80)
    
    await fetcher.close()

if __name__ == '__main__':
    asyncio.run(main())

