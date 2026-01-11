"""Check raw Polymarket API response to see all market titles."""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.fetchers.polymarket_fetcher import PolymarketFetcher

async def main():
    fetcher = PolymarketFetcher()
    
    print("=" * 80)
    print("POLYMARKET RAW API RESPONSE CHECK")
    print("=" * 80)
    
    # Make direct API call to see raw data
    endpoint = "/markets"
    params = {
        "closed": "false",
        "limit": 200
    }
    
    response = await fetcher._make_request(endpoint, params=params)
    
    if not response:
        print("No response from API")
        await fetcher.close()
        return
    
    markets_data = response
    if isinstance(response, dict):
        markets_data = response.get('data', response.get('markets', []))
    
    print(f"\nTotal markets in API response: {len(markets_data)}")
    
    # Show all titles
    print("\n" + "=" * 80)
    print("ALL MARKET TITLES (first 50):")
    print("=" * 80)
    
    for i, market in enumerate(markets_data[:50], 1):
        title = (
            market.get('question') or
            market.get('title') or
            market.get('name') or
            market.get('description') or
            'NO TITLE'
        )
        print(f"{i}. {title}")
        
        # Check for game indicators
        title_lower = title.lower()
        if ' vs ' in title_lower or ' v ' in title_lower:
            print(f"   *** HAS 'vs' or 'v' ***")
        if 'nba' in title_lower or 'nfl' in title_lower:
            print(f"   *** NBA/NFL market ***")
    
    # Check for specific patterns
    print("\n" + "=" * 80)
    print("MARKETS WITH GAME INDICATORS:")
    print("=" * 80)
    
    game_indicators = []
    for market in markets_data:
        title = (
            market.get('question') or
            market.get('title') or
            market.get('name') or
            market.get('description') or
            ''
        )
        title_lower = title.lower()
        
        # Check various patterns
        has_vs = ' vs ' in title_lower or ' v ' in title_lower or ' versus ' in title_lower
        has_teams = any(word in title_lower for word in ['lakers', 'warriors', 'celtics', 'knicks', 'pistons', 'raptors', 'hawks', 'steelers', 'ravens', 'packers', 'vikings'])
        has_game_words = any(word in title_lower for word in ['game', 'match', 'playoff', 'finals'])
        
        if has_vs or (has_teams and has_game_words):
            game_indicators.append(title)
    
    print(f"\nFound {len(game_indicators)} markets with game indicators:")
    for i, title in enumerate(game_indicators[:20], 1):
        print(f"{i}. {title}")
    
    await fetcher.close()

if __name__ == '__main__':
    asyncio.run(main())

