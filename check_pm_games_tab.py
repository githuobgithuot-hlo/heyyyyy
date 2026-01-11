"""Check if Polymarket has a separate endpoint for Games tab."""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.fetchers.polymarket_fetcher import PolymarketFetcher

async def main():
    fetcher = PolymarketFetcher()
    
    print("=" * 80)
    print("CHECKING POLYMARKET GAMES TAB ENDPOINTS")
    print("=" * 80)
    
    # Try different endpoints that might return games
    endpoints_to_try = [
        ("/markets", {"closed": "false", "limit": 200, "type": "game"}),
        ("/markets", {"closed": "false", "limit": 200, "marketType": "game"}),
        ("/markets", {"closed": "false", "limit": 200, "tab": "games"}),
        ("/markets", {"closed": "false", "limit": 200, "category": "sports", "type": "game"}),
        ("/sports/games", {"closed": "false", "limit": 200}),
        ("/sports/nba/games", {}),
        ("/games", {"closed": "false", "limit": 200}),
        ("/events", {"closed": "false", "limit": 200}),
    ]
    
    for endpoint, params in endpoints_to_try:
        print(f"\n{'='*80}")
        print(f"Trying: {endpoint} with {params}")
        print(f"{'='*80}")
        
        try:
            response = await fetcher._make_request(endpoint, params=params)
            
            if not response:
                print("  -> No response or error")
                continue
            
            markets_data = response
            if isinstance(response, dict):
                markets_data = response.get('data', response.get('markets', response.get('games', response.get('events', []))))
            
            if not isinstance(markets_data, list):
                print(f"  -> Not a list: {type(markets_data)}")
                if isinstance(response, dict):
                    print(f"  -> Keys: {list(response.keys())[:10]}")
                continue
            
            print(f"  -> Found {len(markets_data)} items")
            
            # Check for game-like markets
            game_like = []
            for item in markets_data[:20]:
                title = (
                    item.get('question') or
                    item.get('title') or
                    item.get('name') or
                    item.get('eventName') or
                    ''
                )
                title_lower = title.lower()
                
                # Check for game indicators
                has_vs = ' vs ' in title_lower or ' v ' in title_lower
                has_teams = any(team in title_lower for team in ['knicks', 'pistons', 'hawks', 'raptors', 'celtics', 'bulls'])
                has_abbr = any(abbr in title_lower for abbr in ['nyk', 'det', 'atl', 'tor', 'bos', 'chi'])
                has_record = bool(any(char.isdigit() for char in title) and '-' in title)
                
                if has_vs or (has_teams and has_record) or (has_abbr and has_record):
                    game_like.append(title)
                    print(f"    GAME-LIKE: {title}")
            
            if len(game_like) > 0:
                print(f"  -> SUCCESS! Found {len(game_like)} game-like markets")
                break
                
        except Exception as e:
            print(f"  -> Error: {e}")
    
    # Also check if there's a way to get "Games" vs "Props" 
    print(f"\n{'='*80}")
    print("CHECKING FOR GAMES VS PROPS DISTINCTION")
    print(f"{'='*80}")
    
    # Try to see if markets have a type field
    response = await fetcher._make_request("/markets", {"closed": "false", "limit": 50})
    if response:
        markets_data = response
        if isinstance(response, dict):
            markets_data = response.get('data', response.get('markets', []))
        
        if isinstance(markets_data, list):
            print("\nChecking market fields for type/category distinction:")
            for market in markets_data[:10]:
                title = market.get('question') or market.get('title') or 'NO TITLE'
                market_type = market.get('type') or market.get('marketType') or market.get('tab') or 'N/A'
                category = market.get('category') or market.get('categoryId') or 'N/A'
                
                print(f"  {title[:50]}")
                print(f"    Type: {market_type}, Category: {category}")
                print(f"    All keys: {list(market.keys())[:15]}")
    
    await fetcher.close()

if __name__ == '__main__':
    import re
    asyncio.run(main())

