"""Debug script to check why Polymarket game markets aren't being detected."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.fetchers.polymarket_fetcher import PolymarketFetcher
from src.sports_matcher import SportsMarketDetector

async def main():
    fetcher = PolymarketFetcher()
    detector = SportsMarketDetector()
    
    markets = await fetcher.fetch_all_markets(limit=200)
    
    print("=" * 80)
    print("POLYMARKET MARKETS ANALYSIS")
    print("=" * 80)
    
    sports_count = 0
    game_count = 0
    futures_count = 0
    no_teams_count = 0
    
    print("\n=== SPORTS MARKETS ===")
    for i, market in enumerate(markets[:50]):  # Check first 50
        title = market.get('title', '')
        if detector.is_sports_market(title):
            sports_count += 1
            teams = detector.extract_teams_from_title(title)
            
            if teams[0] and teams[1]:
                game_count += 1
                if game_count <= 10:
                    print(f"\n[{game_count}] GAME MARKET:")
                    print(f"  Title: {title}")
                    print(f"  Team 1: {teams[0]}")
                    print(f"  Team 2: {teams[1]}")
            elif teams[0] and not teams[1]:
                futures_count += 1
                if futures_count <= 5:
                    print(f"\n[{futures_count}] FUTURES MARKET:")
                    print(f"  Title: {title}")
                    print(f"  Team: {teams[0]}")
            else:
                no_teams_count += 1
                if no_teams_count <= 5:
                    print(f"\n[{no_teams_count}] NO TEAMS EXTRACTED:")
                    print(f"  Title: {title}")
    
    print("\n" + "=" * 80)
    print(f"SUMMARY (first 50 markets):")
    print(f"  Sports markets: {sports_count}")
    print(f"  Game markets (2 teams): {game_count}")
    print(f"  Futures markets (1 team): {futures_count}")
    print(f"  No teams extracted: {no_teams_count}")
    print("=" * 80)
    
    # Check all sports markets
    all_sports = [m for m in markets if detector.is_sports_market(m.get('title', ''))]
    print(f"\nTotal sports markets: {len(all_sports)}")
    
    # Detailed check of first 20 sports markets
    print("\n=== DETAILED CHECK (first 20 sports markets) ===")
    for i, market in enumerate(all_sports[:20]):
        title = market.get('title', '')
        teams = detector.extract_teams_from_title(title)
        print(f"\n{i+1}. {title}")
        print(f"   Teams: {teams}")
        if teams[0] and teams[1]:
            print(f"   [GAME] (2 teams)")
        elif teams[0]:
            print(f"   [FUTURES] (1 team)")
        else:
            print(f"   [NO TEAMS]")
    
    await fetcher.close()

if __name__ == '__main__':
    asyncio.run(main())

