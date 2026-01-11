"""Check Polymarket categories and fetch sports markets."""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.fetchers.polymarket_fetcher import PolymarketFetcher

async def main():
    fetcher = PolymarketFetcher()
    
    print("=" * 80)
    print("POLYMARKET CATEGORIES AND SPORTS MARKETS")
    print("=" * 80)
    
    # Get all categories
    categories_response = await fetcher._make_request("/categories", {})
    if categories_response:
        print(f"\nFound {len(categories_response)} categories")
        
        # Find sports category
        sports_categories = []
        for cat in categories_response:
            label = cat.get('label', '').lower()
            slug = cat.get('slug', '').lower()
            if 'sport' in label or 'sport' in slug or 'nba' in label or 'nfl' in label:
                sports_categories.append(cat)
                print(f"\nSports category found:")
                print(f"  ID: {cat.get('id')}")
                print(f"  Label: {cat.get('label')}")
                print(f"  Slug: {cat.get('slug')}")
        
        # Try to fetch markets by category
        for cat in sports_categories[:3]:  # Try first 3 sports categories
            cat_slug = cat.get('slug')
            cat_id = cat.get('id')
            
            print(f"\n{'='*80}")
            print(f"Trying to fetch markets for category: {cat.get('label')} (slug: {cat_slug}, id: {cat_id})")
            print(f"{'='*80}")
            
            # Try different parameter names
            for param_name in ['category', 'categoryId', 'categorySlug', 'cat']:
                params = {
                    "closed": "false",
                    "limit": 200,
                    param_name: cat_slug or cat_id
                }
                
                response = await fetcher._make_request("/markets", params)
                if response:
                    markets_data = response
                    if isinstance(response, dict):
                        markets_data = response.get('data', response.get('markets', []))
                    
                    if isinstance(markets_data, list) and len(markets_data) > 0:
                        print(f"  -> Found {len(markets_data)} markets with {param_name}={cat_slug or cat_id}")
                        
                        # Show first few titles
                        for i, market in enumerate(markets_data[:5], 1):
                            title = (
                                market.get('question') or
                                market.get('title') or
                                market.get('name') or
                                'NO TITLE'
                            )
                            print(f"    {i}. {title}")
                        break
    
    # Also try fetching ALL markets and check their category field
    print(f"\n{'='*80}")
    print("Checking category field in market data")
    print(f"{'='*80}")
    
    response = await fetcher._make_request("/markets", {"closed": "false", "limit": 50})
    if response:
        markets_data = response
        if isinstance(response, dict):
            markets_data = response.get('data', response.get('markets', []))
        
        if isinstance(markets_data, list):
            print(f"\nChecking first 20 markets for category info:")
            for market in markets_data[:20]:
                title = market.get('question') or market.get('title') or 'NO TITLE'
                category = market.get('category') or market.get('categoryId') or market.get('categorySlug') or 'N/A'
                tags = market.get('tags') or market.get('tag') or []
                
                print(f"  {title[:60]}")
                print(f"    Category: {category}, Tags: {tags}")
    
    await fetcher.close()

if __name__ == '__main__':
    asyncio.run(main())

