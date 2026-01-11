"""
Polymarket API client for fetching prediction market data.
"""
import asyncio
from typing import List, Dict, Optional, Any
from datetime import datetime
import httpx

from .logger import setup_logger


class PolymarketClient:
    """Client for interacting with Polymarket API."""
    
    def __init__(
        self,
        base_url: str = "https://gamma-api.polymarket.com",
        timeout: int = 10,
        retry_attempts: int = 3,
        retry_delay: int = 2,
        debug_api: bool = False
    ):
        """
        Initialize Polymarket client.
        
        Args:
            base_url: Base URL for Polymarket API (default: gamma-api.polymarket.com)
            timeout: Request timeout in seconds
            retry_attempts: Number of retry attempts
            retry_delay: Delay between retries in seconds
            debug_api: Enable diagnostic logging
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        self.debug_api = debug_api
        self.logger = setup_logger("polymarket_client")
        # Polymarket public API - no authentication required
        self.client = httpx.AsyncClient(
            timeout=timeout,
            headers={
                "Accept": "application/json",
                "User-Agent": "ArbitrageBot/1.0"
            }
        )
    
    async def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        Make HTTP request with retry logic.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
        
        Returns:
            JSON response or None if failed
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        # Log full URL for diagnostics
        if self.debug_api:
            if params:
                from urllib.parse import urlencode
                query_string = urlencode(params)
                full_url = f"{url}?{query_string}"
            else:
                full_url = url
            self.logger.debug(f"Polymarket request: {full_url}")
        
        for attempt in range(self.retry_attempts):
            try:
                response = await self.client.get(url, params=params)
                
                # Diagnostic logging
                if self.debug_api:
                    self.logger.debug(f"Response status: {response.status_code}")
                    if response.status_code != 200:
                        body_preview = response.text[:500] if response.text else "No body"
                        self.logger.debug(f"Response body: {body_preview}")
                
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                status_code = e.response.status_code
                self.logger.warning(
                    f"HTTP error on attempt {attempt + 1}/{self.retry_attempts}: {status_code}"
                )
                
                # Fail loudly on 403
                if status_code == 403:
                    self.logger.error(
                        f"Polymarket API returned 403 Forbidden. "
                        f"Check if endpoint requires authentication or if IP is blocked. "
                        f"URL: {url}"
                    )
                    return None
                
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                else:
                    self.logger.error(f"Failed to fetch {url} after {self.retry_attempts} attempts")
            except httpx.RequestError as e:
                self.logger.error(f"Request error: {e}")
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
                break
        
        return None
    
    def _convert_odds(self, price: float) -> float:
        """
        Convert Polymarket price (0-1) to decimal odds.
        
        Args:
            price: Price from Polymarket (0-1 range)
        
        Returns:
            Decimal odds
        """
        if price <= 0 or price >= 1:
            return None
        return 1.0 / price
    
    def _parse_market(self, market_data: Dict) -> Optional[Dict]:
        """
        Parse a single market from Polymarket API response.
        
        Args:
            market_data: Raw market data from API
        
        Returns:
            Normalized market dictionary or None if invalid
        """
        try:
            # Polymarket API response structure
            # Handle different possible field names
            market_id = (
                market_data.get('id') or 
                market_data.get('market_id') or 
                market_data.get('slug') or
                market_data.get('conditionId')
            )
            
            question = (
                market_data.get('question') or 
                market_data.get('title') or 
                market_data.get('name') or
                market_data.get('description')
            )
            
            if not question or not market_id:
                return None
            
            # Get outcomes and prices
            outcomes = []
            
            # Polymarket API structure: outcomePrices is a dict mapping outcome names to prices
            outcome_prices = market_data.get('outcomePrices', {})
            if outcome_prices and isinstance(outcome_prices, dict):
                for outcome_name, price in outcome_prices.items():
                    if price is not None:
                        try:
                            price_float = float(price)
                            decimal_odds = self._convert_odds(price_float)
                            if decimal_odds:
                                outcomes.append({
                                    'name': outcome_name,
                                    'odds': decimal_odds,
                                    'price': price_float
                                })
                        except (ValueError, TypeError):
                            continue
            
            # Fallback: Try different possible structures for outcomes
            tokens = market_data.get('tokens', [])
            outcomes_data = market_data.get('outcomes', [])
            markets = market_data.get('markets', [])
            
            # Handle tokens structure (common in Polymarket)
            if tokens:
                for token in tokens:
                    outcome_name = (
                        token.get('outcome') or 
                        token.get('name') or 
                        token.get('side') or
                        token.get('tokenName', '').replace('$', '')
                    )
                    price = token.get('price') or token.get('lastPrice') or token.get('currentPrice')
                    
                    if price is not None:
                        try:
                            price_float = float(price)
                            decimal_odds = self._convert_odds(price_float)
                            if decimal_odds:
                                outcomes.append({
                                    'name': outcome_name,
                                    'odds': decimal_odds,
                                    'price': price_float
                                })
                        except (ValueError, TypeError):
                            continue
            
            # Handle outcomes array structure
            elif outcomes_data:
                for outcome in outcomes_data:
                    outcome_name = outcome.get('name') or outcome.get('outcome', '')
                    price = outcome.get('price') or outcome.get('lastPrice')
                    
                    if price is not None:
                        try:
                            price_float = float(price)
                            decimal_odds = self._convert_odds(price_float)
                            if decimal_odds:
                                outcomes.append({
                                    'name': outcome_name,
                                    'odds': decimal_odds,
                                    'price': price_float
                                })
                        except (ValueError, TypeError):
                            continue
            
            # Handle markets array (nested structure)
            elif markets:
                for market in markets:
                    outcome_name = market.get('outcome') or market.get('name', '')
                    price = market.get('price') or market.get('lastPrice')
                    
                    if price is not None:
                        try:
                            price_float = float(price)
                            decimal_odds = self._convert_odds(price_float)
                            if decimal_odds:
                                outcomes.append({
                                    'name': outcome_name,
                                    'odds': decimal_odds,
                                    'price': price_float
                                })
                        except (ValueError, TypeError):
                            continue
            
            # Need at least 2 outcomes (YES/NO or multiple options)
            if len(outcomes) < 2:
                return None
            
            # Create market URL
            if isinstance(market_id, str) and market_id.startswith('0x'):
                # Condition ID format
                market_url = f"https://polymarket.com/event/{market_id}"
            else:
                # Slug or regular ID format
                market_url = f"https://polymarket.com/event/{market_id}"
            
            return {
                'id': str(market_id),
                'name': question,
                'outcomes': outcomes,
                'url': market_url,
                'platform': 'polymarket',
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error parsing market: {e}")
            return None
    
    async def get_markets(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """
        Fetch all active markets from Polymarket.
        
        Uses the official Polymarket public API endpoint:
        GET /markets?active=true
        
        Args:
            limit: Maximum number of markets to fetch
            offset: Pagination offset
        
        Returns:
            List of normalized market dictionaries
        """
        # Official Polymarket public API endpoint
        endpoint = "/markets"
        params = {
            "active": "true",
            "limit": limit,
            "offset": offset
        }
        
        try:
            response = await self._make_request(endpoint, params=params)
            
            if not response:
                self.logger.warning("No response from Polymarket API")
                return []
            
            # Polymarket returns a list of markets directly
            markets_data = response
            if isinstance(response, dict):
                markets_data = response.get('data', response.get('markets', []))
            
            if not isinstance(markets_data, list):
                self.logger.warning(f"Unexpected response format: {type(markets_data)}")
                if self.debug_api:
                    self.logger.debug(f"Response structure: {list(response.keys()) if isinstance(response, dict) else 'Not a dict'}")
                return []
            
            # Parse markets
            parsed_markets = []
            for market_data in markets_data:
                parsed = self._parse_market(market_data)
                if parsed:
                    parsed_markets.append(parsed)
            
            self.logger.info(f"Fetched {len(parsed_markets)} markets from Polymarket")
            return parsed_markets
            
        except Exception as e:
            self.logger.error(f"Error fetching Polymarket markets: {e}", exc_info=True)
            return []
    
    async def health_check(self) -> bool:
        """
        Perform a health check on the Polymarket API.
        
        Returns:
            True if API is accessible, False otherwise
        """
        try:
            endpoint = "/markets"
            params = {"active": "true", "limit": 1}
            response = await self._make_request(endpoint, params=params)
            
            if response is not None:
                self.logger.info("Polymarket API health check: PASSED")
                return True
            else:
                self.logger.error("Polymarket API health check: FAILED - No response")
                return False
        except Exception as e:
            self.logger.error(f"Polymarket API health check: FAILED - {e}")
            return False
    
    async def get_market_by_id(self, market_id: str) -> Optional[Dict]:
        """
        Fetch a specific market by ID.
        
        Args:
            market_id: Market identifier
        
        Returns:
            Market dictionary or None
        """
        try:
            response = await self._make_request(f"/markets/{market_id}")
            if response:
                return self._parse_market(response)
            return None
        except Exception as e:
            self.logger.error(f"Error fetching market {market_id}: {e}")
            return None
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

