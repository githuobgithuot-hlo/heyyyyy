"""Find actual game events (team vs team) in /events endpoint."""
import asyncio
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.fetchers.polymarket_fetcher import PolymarketFetcher
from src.sports_matcher import SportsMarketDetector

async def main():
    fetcher = PolymarketFetcher()
    detector = SportsMarketDetector()
    
    print("=" * 80)
    print("SEARCHING FOR ACTUAL GAME EVENTS")
    print("=" * 80)
    
    # Fetch more events
    print("\nFetching events...")
    events_response = await fetcher._make_request("/events", {
        "closed": "false",
        "limit": 500  # Fetch more
    })
    
    if not events_response or not isinstance(events_response, list):
        print("No events found")
        await fetcher.close()
        return
    
    print(f"Found {len(events_response)} total events")
    
    # Look for actual game patterns
    potential_games = []
    
    # NBA/NFL team abbreviations
    nba_abbr = ['NYK', 'DET', 'ATL', 'TOR', 'BOS', 'CHI', 'HOU', 'PHX', 'LAL', 'GSW', 'MIA', 'MIL']
    nfl_abbr = ['PIT', 'BAL', 'GB', 'MIN', 'NE', 'DAL', 'KC', 'SF']
    
    # Team names
    nba_teams = ['knicks', 'pistons', 'hawks', 'raptors', 'celtics', 'bulls', 'rockets', 'suns', 'lakers', 'warriors']
    nfl_teams = ['steelers', 'ravens', 'packers', 'vikings', 'patriots', 'cowboys', 'chiefs', '49ers']
    
    for event in events_response:
        title = event.get('title') or event.get('ticker') or ''
        title_lower = title.lower()
        
        # Check for game indicators
        has_vs = ' vs ' in title_lower or ' v ' in title_lower or ' versus ' in title_lower
        has_abbr = any(abbr in title for abbr in nba_abbr + nfl_abbr)
        has_teams = any(team in title_lower for team in nba_teams + nfl_teams)
        has_record = bool(re.search(r'\d+-\d+', title))  # Record pattern like "23-12"
        
        # Check if it's a game (not a prop/futures)
        is_prop = any(word in title_lower for word in ['winner', 'top goalscorer', 'mvp', 'champion', 'finals', 'playoff'])
        is_futures = 'will' in title_lower and ('win' in title_lower or 'championship' in title_lower)
        
        if (has_vs or (has_abbr and has_record) or (has_teams and has_record)) and not is_prop and not is_futures:
            potential_games.append((title, event))
    
    print(f"\n{'='*80}")
    print(f"POTENTIAL GAME EVENTS: {len(potential_games)}")
    print(f"{'='*80}")
    
    for i, (title, event) in enumerate(potential_games[:20], 1):
        print(f"\n{i}. {title}")
        print(f"   ID: {event.get('id')}")
        print(f"   Slug: {event.get('slug')}")
        
        # Try to get markets for this event
        event_id = event.get('id')
        event_slug = event.get('slug')
        
        # Get event details with markets
        event_details = await fetcher._make_request(f"/events/{event_id}", {})
        if event_details and isinstance(event_details, dict):
            markets = event_details.get('markets') or event_details.get('data', [])
            if isinstance(markets, list):
                print(f"   Markets: {len(markets)}")
                if len(markets) > 0:
                    # Check first market
                    first_market = markets[0]
                    market_title = first_market.get('question') or first_market.get('title') or 'NO TITLE'
                    print(f"   First market: {market_title[:60]}")
                    
                    # Check outcomes
                    outcomes = first_market.get('outcomes') or first_market.get('outcomePrices', {})
                    if outcomes:
                        if isinstance(outcomes, list):
                            print(f"   Outcomes: {outcomes[:5]}")
                        elif isinstance(outcomes, dict):
                            print(f"   Outcomes: {list(outcomes.keys())[:5]}")
    
    # Also check all event titles for patterns
    print(f"\n{'='*80}")
    print("ALL EVENT TITLES WITH 'vs' OR TEAM NAMES (First 30):")
    print(f"{'='*80}")
    
    vs_events = []
    for event in events_response:
        title = event.get('title') or event.get('ticker') or ''
        title_lower = title.lower()
        
        if ' vs ' in title_lower or ' v ' in title_lower:
            vs_events.append(title)
    
    for i, title in enumerate(vs_events[:30], 1):
        print(f"{i}. {title}")
    
    await fetcher.close()

if __name__ == '__main__':
    asyncio.run(main())

