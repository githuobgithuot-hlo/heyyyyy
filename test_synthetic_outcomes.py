"""Test if synthetic outcomes are being created."""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.fetchers.polymarket_fetcher import PolymarketFetcher

async def main():
    fetcher = PolymarketFetcher()
    
    print("=" * 80)
    print("TESTING SYNTHETIC OUTCOMES CREATION")
    print("=" * 80)
    
    # Create a test market with invalid prices but valid team names
    test_market = {
        'id': '12345',
        'question': 'Nets vs. Wizards: 1H Moneyline',
        'title': 'Nets vs. Wizards: 1H Moneyline',
        'conditionId': '12345',
        'outcomes': '["Nets", "Wizards"]',  # JSON string
        'outcomePrices': '["0", "1"]',  # Invalid prices
        'active': True,
        'closed': True
    }
    
    print(f"\nTest market:")
    print(f"  Title: {test_market['question']}")
    print(f"  Outcomes: {test_market['outcomes']}")
    print(f"  Prices: {test_market['outcomePrices']}")
    
    print(f"\nTesting _parse_market...")
    
    # Enable debug logging
    import logging
    logging.basicConfig(level=logging.DEBUG)
    fetcher.logger.setLevel(logging.DEBUG)
    
    parsed = fetcher._parse_market(test_market)
    
    if parsed:
        print(f"  -> SUCCESS! Market parsed")
        print(f"     Title: {parsed.get('title')}")
        print(f"     Outcomes: {list(parsed.get('outcomes', {}).keys())}")
        print(f"     Odds: {list(parsed.get('outcomes', {}).values())}")
    else:
        print(f"  -> FAILED - market not parsed")
        print(f"     (This is the problem!)")
        print(f"     Checking why...")
        
        # Manual check
        market_id = test_market.get('id') or test_market.get('conditionId')
        question = test_market.get('question') or test_market.get('title')
        print(f"     Market ID: {market_id}")
        print(f"     Question: {question}")
        
        if not market_id or not question:
            print(f"     -> Missing ID or question!")
        
        # Check outcomes parsing
        import json
        outcomes_list = test_market.get('outcomes', [])
        if isinstance(outcomes_list, str):
            try:
                outcomes_list = json.loads(outcomes_list)
                print(f"     Parsed outcomes: {outcomes_list}")
            except Exception as e:
                print(f"     Failed to parse outcomes: {e}")
        
        # Check if it's a game market
        question_lower = question.lower() if question else ''
        is_game_market = ' vs ' in question_lower or ' v ' in question_lower
        print(f"     Is game market: {is_game_market}")
        
        if is_game_market:
            from src.sports_matcher import SportsMarketDetector
            detector = SportsMarketDetector()
            teams = detector.extract_teams_from_title(question)
            print(f"     Extracted teams: {teams}")
    
    # Also test with event title format
    test_market2 = {
        'id': 'event_12345',
        'question': 'Nets vs. Wizards',
        'title': 'Nets vs. Wizards',
        'conditionId': '12345',
        'outcomes': '["Nets", "Wizards"]',
        'outcomePrices': '["0", "1"]',
        'active': True,
        'closed': False
    }
    
    print(f"\n{'='*80}")
    print("Testing with event title format...")
    print(f"{'='*80}")
    
    parsed2 = fetcher._parse_market(test_market2)
    
    if parsed2:
        print(f"  -> SUCCESS! Market parsed")
        print(f"     Title: {parsed2.get('title')}")
        print(f"     Outcomes: {list(parsed2.get('outcomes', {}).keys())}")
    else:
        print(f"  -> FAILED")
    
    await fetcher.close()

if __name__ == '__main__':
    asyncio.run(main())

