"""Explore Polymarket API to find games endpoint."""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.fetchers.polymarket_fetcher import PolymarketFetcher

async def main():
    fetcher = PolymarketFetcher(debug_api=True)
    
    print("=" * 80)
    print("EXPLORING POLYMARKET API ENDPOINTS")
    print("=" * 80)
    
    base_url = "https://gamma-api.polymarket.com"
    
    # List of endpoints to try
    endpoints_to_explore = [
        # Standard endpoints
        ("/markets", {"closed": "false", "limit": 10}),
        ("/events", {"closed": "false", "limit": 10}),
        ("/categories", {}),
        
        # Sports-specific
        ("/sports", {}),
        ("/sports/markets", {"closed": "false", "limit": 10}),
        ("/sports/events", {"closed": "false", "limit": 10}),
        ("/sports/nba", {}),
        ("/sports/nba/markets", {"closed": "false", "limit": 10}),
        ("/sports/nba/games", {}),
        ("/sports/nfl", {}),
        ("/sports/nfl/markets", {"closed": "false", "limit": 10}),
        
        # Games-specific
        ("/games", {"closed": "false", "limit": 10}),
        ("/games/nba", {}),
        ("/games/nfl", {}),
        
        # With filters
        ("/markets", {"closed": "false", "limit": 10, "category": "sports"}),
        ("/markets", {"closed": "false", "limit": 10, "sport": "nba"}),
        ("/markets", {"closed": "false", "limit": 10, "type": "game"}),
        ("/markets", {"closed": "false", "limit": 10, "marketType": "game"}),
        ("/markets", {"closed": "false", "limit": 10, "tab": "games"}),
        
        # Alternative base URLs
    ]
    
    print(f"\nBase URL: {base_url}")
    print(f"Testing {len(endpoints_to_explore)} endpoints...\n")
    
    successful_endpoints = []
    
    for endpoint, params in endpoints_to_explore:
        print(f"{'='*80}")
        print(f"Testing: {endpoint}")
        if params:
            print(f"Params: {params}")
        print(f"{'='*80}")
        
        try:
            response = await fetcher._make_request(endpoint, params=params)
            
            if not response:
                print("  -> No response or error\n")
                continue
            
            # Check response structure
            if isinstance(response, dict):
                keys = list(response.keys())
                print(f"  -> Response is dict with keys: {keys[:10]}")
                
                # Check for data/markets/events
                data = response.get('data') or response.get('markets') or response.get('events') or response.get('games')
                if data:
                    if isinstance(data, list):
                        print(f"  -> Found list with {len(data)} items")
                        if len(data) > 0:
                            print(f"  -> First item keys: {list(data[0].keys())[:10]}")
                            title = data[0].get('question') or data[0].get('title') or data[0].get('name') or 'NO TITLE'
                            print(f"  -> First item: {title[:60]}")
                    else:
                        print(f"  -> Data is {type(data)}")
                
                # Check if it's a list of markets directly
                if 'question' in keys or 'title' in keys:
                    print(f"  -> Response appears to be a market object")
                    
            elif isinstance(response, list):
                print(f"  -> Response is list with {len(response)} items")
                if len(response) > 0:
                    print(f"  -> First item keys: {list(response[0].keys())[:10]}")
                    title = response[0].get('question') or response[0].get('title') or response[0].get('name') or 'NO TITLE'
                    print(f"  -> First item: {title[:60]}")
                    
                    # Check if it's a game
                    title_lower = title.lower()
                    has_teams = any(team in title_lower for team in ['knicks', 'pistons', 'hawks', 'raptors', 'vs', ' v '])
                    if has_teams:
                        print(f"  -> *** POTENTIAL GAME MARKET FOUND! ***")
                        successful_endpoints.append((endpoint, params))
            else:
                print(f"  -> Unexpected response type: {type(response)}")
            
            print()
            
        except Exception as e:
            print(f"  -> Error: {e}\n")
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    if successful_endpoints:
        print(f"\nFound {len(successful_endpoints)} endpoints that might return games:")
        for endpoint, params in successful_endpoints:
            print(f"  - {endpoint} with {params}")
    else:
        print("\nNo endpoints found that return game markets.")
        print("Games might not be available via API, or require different parameters.")
    
    await fetcher.close()

if __name__ == '__main__':
    asyncio.run(main())

