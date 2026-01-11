"""Check if Polymarket API returns games in a different format."""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.fetchers.polymarket_fetcher import PolymarketFetcher
from src.sports_matcher import SportsMarketDetector

async def main():
    fetcher = PolymarketFetcher()
    detector = SportsMarketDetector()
    
    print("=" * 80)
    print("CHECKING POLYMARKET FOR GAME FORMATS")
    print("=" * 80)
    
    # Fetch markets
    markets = await fetcher.fetch_all_markets(limit=500)  # Fetch more
    
    print(f"\nTotal markets: {len(markets)}")
    
    # Look for NBA/NFL team patterns
    nba_teams = ['knicks', 'pistons', 'hawks', 'raptors', 'celtics', 'bulls', 'rockets', 'suns', 'lakers', 'warriors']
    nfl_teams = ['steelers', 'ravens', 'packers', 'vikings', 'patriots', 'cowboys']
    
    potential_games = []
    
    for market in markets:
        title = market.get('title', '')
        title_lower = title.lower()
        
        # Check for team names
        found_teams = []
        all_teams = nba_teams + nfl_teams
        for team in all_teams:
            if team in title_lower:
                found_teams.append(team)
        
        # If multiple teams or specific patterns
        if len(found_teams) >= 2:
            potential_games.append((title, found_teams, 'multiple_teams'))
        elif len(found_teams) == 1:
            # Check if it's a game format (not futures)
            # Games might have: team abbreviations, records, "vs" implied
            if any(abbr in title_lower for abbr in ['nyk', 'det', 'atl', 'tor', 'bos', 'chi', 'hou', 'phx']):
                potential_games.append((title, found_teams, 'abbreviation'))
            # Check for record pattern (e.g., "23-12")
            import re
            if re.search(r'\d+-\d+', title):
                potential_games.append((title, found_teams, 'record_pattern'))
    
    print(f"\nFound {len(potential_games)} potential games:")
    for i, (title, teams, pattern) in enumerate(potential_games[:20], 1):
        print(f"\n{i}. {title}")
        print(f"   Teams: {teams}")
        print(f"   Pattern: {pattern}")
        
        # Try extracting teams
        extracted = detector.extract_teams_from_title(title)
        print(f"   Extracted: {extracted}")
    
    # Also check raw API for any fields we might be missing
    print(f"\n{'='*80}")
    print("CHECKING RAW API FOR GAME-SPECIFIC FIELDS")
    print(f"{'='*80}")
    
    response = await fetcher._make_request("/markets", {"closed": "false", "limit": 100})
    if response:
        markets_data = response
        if isinstance(response, dict):
            markets_data = response.get('data', response.get('markets', []))
        
        # Check first market structure
        if markets_data and len(markets_data) > 0:
            print("\nSample market structure:")
            sample = markets_data[0]
            print(json.dumps(sample, indent=2)[:1000])
            
            # Look for games specifically
            print(f"\n{'='*80}")
            print("SEARCHING FOR MARKETS WITH GAME INDICATORS")
            print(f"{'='*80}")
            
            for market in markets_data:
                title = market.get('question') or market.get('title') or ''
                # Check all fields
                market_type = market.get('type') or market.get('marketType') or market.get('category')
                tags = market.get('tags') or market.get('tag') or []
                outcomes = market.get('outcomes') or market.get('outcomePrices') or {}
                
                title_lower = title.lower()
                
                # Check if it looks like a game
                has_teams = any(team in title_lower for team in nba_teams + nfl_teams)
                has_abbr = any(abbr in title_lower for abbr in ['nyk', 'det', 'atl', 'tor'])
                has_record = bool(re.search(r'\d+-\d+', title))
                
                if (has_teams or has_abbr) and (has_record or 'game' in title_lower):
                    print(f"\nPotential game market:")
                    print(f"  Title: {title}")
                    print(f"  Type: {market_type}")
                    print(f"  Tags: {tags}")
                    print(f"  Outcomes: {list(outcomes.keys()) if isinstance(outcomes, dict) else outcomes}")
                    print(f"  All keys: {list(market.keys())}")
    
    await fetcher.close()

if __name__ == '__main__':
    import re
    asyncio.run(main())

