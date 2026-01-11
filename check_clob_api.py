"""Check if clob.polymarket.com API has games."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.fetchers.polymarket_fetcher import PolymarketFetcher

async def main():
    print("=" * 80)
    print("CHECKING CLOB.POLYMARKET.COM API")
    print("=" * 80)
    
    # Try clob API
    clob_fetcher = PolymarketFetcher(base_url="https://clob.polymarket.com")
    
    endpoints_to_try = [
        ("/markets", {"closed": "false", "limit": 20}),
        ("/events", {"closed": "false", "limit": 20}),
        ("/sports", {}),
    ]
    
    for endpoint, params in endpoints_to_try:
        print(f"\n{'='*80}")
        print(f"Testing CLOB API: {endpoint} with {params}")
        print(f"{'='*80}")
        
        try:
            response = await clob_fetcher._make_request(endpoint, params=params)
            
            if not response:
                print("  -> No response")
                continue
            
            if isinstance(response, list):
                print(f"  -> Found {len(response)} items")
                if len(response) > 0:
                    first = response[0]
                    title = first.get('question') or first.get('title') or first.get('name') or 'NO TITLE'
                    print(f"  -> First: {title[:60]}")
                    print(f"  -> Keys: {list(first.keys())[:10]}")
            elif isinstance(response, dict):
                print(f"  -> Dict with keys: {list(response.keys())[:10]}")
                
        except Exception as e:
            print(f"  -> Error: {e}")
    
    await clob_fetcher.close()
    
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print("\nPolymarket API Findings:")
    print("  - gamma-api.polymarket.com: Has /markets, /events, /sports")
    print("  - But /markets returns mostly futures/props, not games")
    print("  - Games might not be exposed via public API")
    print("  - OR games require different endpoint/parameters")
    print("\nNext Steps:")
    print("  1. Check Polymarket official API docs")
    print("  2. Check if games require authentication")
    print("  3. Check if games are only in website UI (not API)")

if __name__ == '__main__':
    asyncio.run(main())

