"""
Cloudbet API client for fetching sportsbook data.

Uses the official Cloudbet public odds API:
- Base URL: https://api.cloudbet.com
- Endpoint: GET /pub/v2/odds/events
- Authentication: Authorization: Bearer <API_KEY>
"""
import asyncio
from typing import List, Dict, Optional, Any
from datetime import datetime
import httpx

from .logger import setup_logger


class CloudbetClient:
    """Client for interacting with Cloudbet API."""
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://sports-api.cloudbet.com/pub",
        timeout: int = 10,
        retry_attempts: int = 3,
        retry_delay: int = 2,
        debug_api: bool = False
    ):
        """
        Initialize Cloudbet Feed API client.
        
        Uses the official Cloudbet Feed API:
        - Base URL: https://sports-api.cloudbet.com/pub
        - Authentication: X-API-Key header
        - Endpoints: /v2/odds/sports, /v2/odds/events, etc.
        
        Args:
            api_key: Cloudbet API key
            base_url: Base URL for Cloudbet Feed API (default: https://sports-api.cloudbet.com/pub)
            timeout: Request timeout in seconds
            retry_attempts: Number of retry attempts
            retry_delay: Delay between retries in seconds
            debug_api: Enable diagnostic logging
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        self.debug_api = debug_api
        self.logger = setup_logger("cloudbet_client")
        
        # Cloudbet Feed API uses X-API-Key header
        headers = {
            "X-API-Key": api_key,
            "Accept": "application/json"
        }
        # Follow redirects (301/302)
        self.client = httpx.AsyncClient(
            timeout=timeout, 
            headers=headers,
            follow_redirects=True
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
        
        # Log full URL for diagnostics (never log secrets)
        if self.debug_api:
            if params:
                from urllib.parse import urlencode
                query_string = urlencode(params)
                full_url = f"{url}?{query_string}"
            else:
                full_url = url
            # Mask API key in logs
            safe_url = full_url.replace(self.api_key, "***MASKED***")
            self.logger.debug(f"Cloudbet request: {safe_url}")
        
        for attempt in range(self.retry_attempts):
            try:
                response = await self.client.get(url, params=params)
                
                # Diagnostic logging
                if self.debug_api:
                    self.logger.debug(f"Response status: {response.status_code}")
                    if response.status_code != 200:
                        body_preview = response.text[:500] if response.text else "No body"
                        self.logger.debug(f"Response body: {body_preview}")
                
                # Fail loudly on 403 - do not retry
                if response.status_code == 403:
                    self.logger.error(
                        "Cloudbet API returned 403 Forbidden. "
                        "Cloudbet API key lacks odds permission or environment mismatch. "
                        "Verify API key has 'trading' tier access and correct base_url."
                    )
                    return None
                
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                status_code = e.response.status_code
                self.logger.warning(
                    f"HTTP error on attempt {attempt + 1}/{self.retry_attempts}: {status_code}"
                )
                
                # Don't retry on 403
                if status_code == 403:
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
    
    def _parse_outcome(
        self,
        event_data: Dict,
        market_data: Dict,
        outcome_data: Dict
    ) -> Optional[Dict]:
        """
        Parse a single outcome from Cloudbet API response.
        
        Args:
            event_data: Event information
            market_data: Market information
            outcome_data: Outcome information
        
        Returns:
            Normalized outcome dictionary or None if invalid
        """
        try:
            # Extract event name
            event_name = (
                event_data.get('name') or 
                event_data.get('title') or 
                event_data.get('eventName') or
                'Unknown Event'
            )
            
            # Extract market name
            market_name = (
                market_data.get('name') or 
                market_data.get('marketName') or 
                market_data.get('label') or
                'Unknown Market'
            )
            
            # Extract outcome name
            outcome_name = (
                outcome_data.get('name') or 
                outcome_data.get('outcome') or 
                outcome_data.get('label') or
                'Unknown Outcome'
            )
            
            # Extract odds - Cloudbet returns decimal odds
            odds = outcome_data.get('odds')
            if odds is None:
                return None
            
            # Handle different odds formats
            if isinstance(odds, dict):
                decimal_odds = odds.get('decimal') or odds.get('dec') or odds.get('price')
            elif isinstance(odds, (int, float)):
                decimal_odds = float(odds)
            else:
                try:
                    decimal_odds = float(odds)
                except (ValueError, TypeError):
                    return None
            
            # Validate odds
            if not decimal_odds or decimal_odds <= 1.0:
                return None
            
            # Check if market/outcome is active
            if market_data.get('suspended') or market_data.get('status') == 'SUSPENDED':
                return None
            
            if outcome_data.get('suspended') or outcome_data.get('status') == 'SUSPENDED':
                return None
            
            # Create event URL
            event_id = event_data.get('id') or event_data.get('eventId')
            market_url = None
            if event_id:
                market_url = f"https://www.cloudbet.com/en/sports/event/{event_id}"
            
            # Return normalized structure
            return {
                'platform': 'cloudbet',
                'event_name': event_name,
                'market_name': market_name,
                'outcome': outcome_name,
                'odds': decimal_odds,
                'url': market_url
            }
        except Exception as e:
            self.logger.error(f"Error parsing outcome: {e}")
            return None
    
    async def get_markets(self, sport: Optional[str] = None) -> List[Dict]:
        """
        Fetch all active markets from Cloudbet Feed API.
        
        Uses the official endpoint: GET /v2/odds/events
        Does NOT send date parameters - filters by startTime in code instead.
        Only processes events with status "TRADING".
        
        Args:
            sport: Sport filter (e.g., "politics", "soccer"). 
                   If None, fetches from all available sports.
        
        Returns:
            List of normalized market dictionaries in format:
            {
                "platform": "cloudbet",
                "event_name": str,
                "market_name": str,
                "outcome": str,
                "odds": float,
                "url": str
            }
        """
        from datetime import datetime, timedelta
        
        # Official Cloudbet Feed API endpoint
        endpoint = "/v2/odds/events"
        
        # Build query parameters
        # API requires from/to, but we use wide range and filter by startTime in code
        from datetime import datetime, timedelta
        now = datetime.utcnow()
        future = now + timedelta(days=365)  # Wide range: 1 year ahead
        
        # Use epoch milliseconds format
        params = {
            'from': str(int(now.timestamp() * 1000)),
            'to': str(int(future.timestamp() * 1000))
        }
        
        # Cloudbet requires 'sport' parameter - if not provided, fetch all sports
        if sport:
            params['sport'] = sport
            return await self._fetch_events_for_sport(endpoint, params)
        else:
            # Fetch all sports and aggregate
            return await self._fetch_all_sports_events(endpoint, params)
    
    async def _fetch_all_sports_events(self, endpoint: str, base_params: Dict) -> List[Dict]:
        """Fetch events from all available sports."""
        # Get list of available sports
        sports_endpoint = "/v2/odds/sports"
        sports_response = await self._make_request(sports_endpoint)
        
        if not sports_response:
            self.logger.warning("Could not fetch sports list")
            return []
        
        # Extract sport keys
        sports = []
        if isinstance(sports_response, dict):
            sports_data = sports_response.get('sports', sports_response.get('data', []))
            if isinstance(sports_data, list):
                sports = [s.get('key') or s.get('name') for s in sports_data if isinstance(s, dict) and (s.get('key') or s.get('name'))]
        elif isinstance(sports_response, list):
            sports = [s.get('key') or s.get('name') for s in sports_response if isinstance(s, dict) and (s.get('key') or s.get('name'))]
        
        if not sports:
            self.logger.warning("No sports found")
            return []
        
        # Fetch events for each sport (no date params needed)
        all_outcomes = []
        for sport_key in sports:
            params = base_params.copy()
            params['sport'] = sport_key
            outcomes = await self._fetch_events_for_sport(endpoint, params)
            all_outcomes.extend(outcomes)
            await asyncio.sleep(0.1)  # Rate limiting
        
        self.logger.info(f"Fetched {len(all_outcomes)} total outcomes from {len(sports)} sports")
        return all_outcomes
    
    async def _fetch_events_for_sport(self, endpoint: str, params: Dict) -> List[Dict]:
        """Fetch events for a specific sport and filter by startTime."""
        from datetime import datetime, timedelta
        
        try:
            response = await self._make_request(endpoint, params=params)
            
            if not response:
                return []
            
            # Parse events response - Cloudbet returns { "competitions": [...] }
            events_data = self._extract_events_from_response(response)
            
            if not events_data:
                return []
            
            # Filter events by startTime (only events in the next 7 days)
            now = datetime.utcnow()
            future_limit = now + timedelta(days=7)
            
            filtered_events = []
            for event_data in events_data:
                if not isinstance(event_data, dict):
                    continue
                
                # Check startTime if available
                start_time = event_data.get('startTime') or event_data.get('start_time') or event_data.get('scheduledStartTime')
                if start_time:
                    try:
                        # Parse startTime (could be ISO string or timestamp)
                        if isinstance(start_time, str):
                            event_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                        elif isinstance(start_time, (int, float)):
                            # Assume milliseconds if > 1e10, seconds otherwise
                            if start_time > 1e10:
                                event_dt = datetime.utcfromtimestamp(start_time / 1000)
                            else:
                                event_dt = datetime.utcfromtimestamp(start_time)
                        else:
                            event_dt = None
                        
                        # Filter: only include events in the future (up to 7 days)
                        if event_dt and (event_dt < now or event_dt > future_limit):
                            continue
                    except (ValueError, TypeError):
                        # If we can't parse startTime, include the event anyway
                        pass
                
                filtered_events.append(event_data)
            
            # Parse filtered events into outcomes
            parsed_outcomes = self._parse_events_response({'events': filtered_events})
            
            self.logger.info(f"Fetched {len(parsed_outcomes)} outcomes from Cloudbet (from {len(filtered_events)} filtered events)")
            return parsed_outcomes
            
        except Exception as e:
            self.logger.error(f"Error fetching Cloudbet markets: {e}", exc_info=True)
            return []
    
    def _extract_events_from_response(self, response: Dict) -> List[Dict]:
        """Extract events list from API response.
        
        Cloudbet API returns: { "competitions": [...] }
        Each competition contains events.
        """
        events_list = []
        
        if isinstance(response, dict):
            # Response structure: { "competitions": [...] }
            competitions = response.get('competitions', response.get('events', response.get('data', [])))
            
            if isinstance(competitions, list):
                # Extract events from competitions
                for competition in competitions:
                    if isinstance(competition, dict):
                        # Events might be directly in competition or nested
                        comp_events = competition.get('events', [])
                        if isinstance(comp_events, list):
                            events_list.extend(comp_events)
                        # Also check if competition itself is an event (has markets)
                        if 'markets' in competition:
                            events_list.append(competition)
            elif isinstance(competitions, dict):
                # Single competition
                if 'events' in competitions:
                    events_list = competitions['events'] if isinstance(competitions['events'], list) else []
        elif isinstance(response, list):
            events_list = response
        else:
            self.logger.warning(f"Unexpected response format: {type(response)}")
            if self.debug_api:
                self.logger.debug(f"Response keys: {list(response.keys()) if isinstance(response, dict) else 'N/A'}")
        
        return events_list if isinstance(events_list, list) else []
    
    async def get_all_sports_markets(self) -> List[Dict]:
        """
        Fetch markets from all available sports.
        
        Returns:
            List of normalized market dictionaries
        """
        # Fetch all events (no sport filter)
        return await self.get_markets(sport=None)
    
    async def health_check(self) -> bool:
        """
        Perform a health check on the Cloudbet Feed API.
        
        Tests the /v2/odds/sports endpoint to verify API access.
        
        Returns:
            True if API is accessible, False otherwise
        """
        try:
            # Test the sports endpoint (lightweight check, no date params needed)
            endpoint = "/v2/odds/sports"
            response = await self._make_request(endpoint)
            
            if response is not None:
                self.logger.info("Cloudbet Feed API health check: PASSED")
                return True
            else:
                self.logger.error(
                    "Cloudbet Feed API health check: FAILED - "
                    "Check API key permissions and base_url configuration. "
                    f"Base URL: {self.base_url}, Endpoint: {endpoint}"
                )
                return False
        except Exception as e:
            self.logger.error(f"Cloudbet Feed API health check: FAILED - {e}")
            return False
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

