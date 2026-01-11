"""
Mock data loader for testing when APIs return empty.
"""
import json
from pathlib import Path
from typing import List, Dict
from datetime import datetime

from ..logger import setup_logger


class MockDataLoader:
    """Loads mock market data for testing."""
    
    def __init__(self):
        self.logger = setup_logger("mock_data_loader")
        self.mock_dir = Path(__file__).parent
    
    def load_polymarket_mock(self) -> List[Dict]:
        """Load mock Polymarket data."""
        mock_file = self.mock_dir / "polymarket_mock.json"
        
        if not mock_file.exists():
            # Generate default mock data
            return self._generate_polymarket_mock()
        
        try:
            with open(mock_file, 'r') as f:
                data = json.load(f)
                self.logger.info(f"Loaded {len(data)} mock Polymarket markets")
                return data
        except Exception as e:
            self.logger.warning(f"Error loading mock Polymarket data: {e}")
            return self._generate_polymarket_mock()
    
    def load_cloudbet_mock(self) -> List[Dict]:
        """Load mock Cloudbet data."""
        mock_file = self.mock_dir / "cloudbet_mock.json"
        
        if not mock_file.exists():
            # Generate default mock data
            return self._generate_cloudbet_mock()
        
        try:
            with open(mock_file, 'r') as f:
                data = json.load(f)
                self.logger.info(f"Loaded {len(data)} mock Cloudbet outcomes")
                return data
        except Exception as e:
            self.logger.warning(f"Error loading mock Cloudbet data: {e}")
            return self._generate_cloudbet_mock()
    
    def _generate_polymarket_mock(self) -> List[Dict]:
        """Generate default Polymarket mock data."""
        return [
            {
                'platform': 'polymarket',
                'market_id': 'mock_poly_1',
                'title': 'Will Trump win the 2024 US Presidential Election?',
                'outcomes': {'YES': 1.85, 'NO': 2.15},
                'url': 'https://polymarket.com/event/mock-1',
                'start_time': None
            },
            {
                'platform': 'polymarket',
                'market_id': 'mock_poly_2',
                'title': 'Will Biden be re-elected in 2024?',
                'outcomes': {'YES': 2.10, 'NO': 1.90},
                'url': 'https://polymarket.com/event/mock-2',
                'start_time': None
            },
            {
                'platform': 'polymarket',
                'market_id': 'mock_poly_3',
                'title': 'Will there be a recession in 2024?',
                'outcomes': {'YES': 1.75, 'NO': 2.25},
                'url': 'https://polymarket.com/event/mock-3',
                'start_time': None
            }
        ]
    
    def _generate_cloudbet_mock(self) -> List[Dict]:
        """Generate default Cloudbet mock data."""
        return [
            {
                'platform': 'cloudbet',
                'event_name': '2024 US Presidential Election',
                'market_name': 'Winner',
                'outcome': 'Trump',
                'odds': 2.20,
                'url': 'https://www.cloudbet.com/en/sports/politics/mock-1',
                'start_time': None
            },
            {
                'platform': 'cloudbet',
                'event_name': '2024 US Presidential Election',
                'market_name': 'Winner',
                'outcome': 'Biden',
                'odds': 1.80,
                'url': 'https://www.cloudbet.com/en/sports/politics/mock-1',
                'start_time': None
            },
            {
                'platform': 'cloudbet',
                'event_name': '2024 US Presidential Election',
                'market_name': 'Will Trump Win?',
                'outcome': 'YES',
                'odds': 2.10,
                'url': 'https://www.cloudbet.com/en/sports/politics/mock-2',
                'start_time': None
            },
            {
                'platform': 'cloudbet',
                'event_name': '2024 US Presidential Election',
                'market_name': 'Will Trump Win?',
                'outcome': 'NO',
                'odds': 1.95,
                'url': 'https://www.cloudbet.com/en/sports/politics/mock-2',
                'start_time': None
            }
        ]

