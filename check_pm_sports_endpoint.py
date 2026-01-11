"""Check if Polymarket has a sports-specific endpoint or category filter."""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.fetchers.polymarket_fetcher import PolymarketFetcher

async def main():
    fetcher = PolymarketFetcher()
    
    print("=" * 80)
    print("POLYMARKET SPORTS ENDPOINT CHECK")
    print("=" * 80)
    
    # Try different endpoints/params
    endpoints_to_try = [
        ("/markets", {"closed": "false", "limit": 200}),
        ("/markets", {"closed": "false", "limit": 200, "category": "sports"}),
        ("/markets", {"closed": "false", "limit": 200, "sport": "sports"}),
        ("/markets", {"closed": "false", "limit": 200, "tags": "sports"}),
        ("/sports/markets", {"closed": "false", "limit": 200}),
        ("/categories/sports", {}),
    ]
    
    for endpoint, params in endpoints_to_try:
        print(f"\n{'='*80}")
        print(f"Trying: {endpoint} with params: {params}")
        print(f"{'='*80}")
        
        try:
            response = await fetcher._make_request(endpoint, params=params)
            
            if not response:
                print("  -> No response")
                continue
            
            markets_data = response
            if isinstance(response, dict):
                markets_data = response.get('data', response.get('markets', response.get('results', [])))
            
            if not isinstance(markets_data, list):
                print(f"  -> Unexpected format: {type(markets_data)}")
                if isinstance(response, dict):
                    print(f"  -> Keys: {list(response.keys())}")
                continue
            
            print(f"  -> Found {len(markets_data)} items")
            
            # Check for sports markets
            sports_count = 0
            game_count = 0
            for item in markets_data[:20]:
                title = (
                    item.get('question') or
                    item.get('title') or
                    item.get('name') or
                    item.get('description') or
                    ''
                )
                title_lower = title.lower()
                
                # Check if sports-related
                sports_keywords = ['nba', 'nfl', 'mlb', 'nhl', 'lakers', 'warriors', 'steelers', 'ravens', 'packers', 'game', 'match', 'vs', ' v ']
                if any(kw in title_lower for kw in sports_keywords):
                    sports_count += 1
                    if ' vs ' in title_lower or ' v ' in title_lower:
                        game_count += 1
                        print(f"    ✓ GAME: {title}")
            
            print(f"  -> Sports markets: {sports_count}, Games: {game_count}")
            
            if sports_count > 0:
                print(f"  -> SUCCESS! Found sports markets")
                break
                
        except Exception as e:
            print(f"  -> Error: {e}")
    
    # Also check if there's a categories endpoint
    print(f"\n{'='*80}")
    print("Checking for categories endpoint")
    print(f"{'='*80}")
    
    try:
        categories_response = await fetcher._make_request("/categories", {})
        if categories_response:
            print(f"Categories response: {json.dumps(categories_response, indent=2)[:500]}")
    except Exception as e:
        print(f"Categories endpoint error: {e}")
    
    await fetcher.close()

if __name__ == '__main__':
    asyncio.run(main())

