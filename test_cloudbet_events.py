#!/usr/bin/env python3
"""Test Cloudbet Feed API events endpoint - use wide date range and filter by startTime."""
import asyncio
import httpx
from datetime import datetime, timedelta

async def test_events():
    """Test Cloudbet events endpoint."""
    api_key = "eyJhbGciOiJSUzI1NiIsImtpZCI6IkhKcDkyNnF3ZXBjNnF3LU9rMk4zV05pXzBrRFd6cEdwTzAxNlRJUjdRWDAiLCJ0eXAiOiJKV1QifQ.eyJhY2Nlc3NfdGllciI6InRyYWRpbmciLCJleHAiOjIwODI3MjIyMzAsImlhdCI6MTc2NzM2MjIzMCwianRpIjoiNTM1MzRlZDAtM2VkYS00MmYwLTgzMGMtZDZhNzE3MWMzM2JmIiwic3ViIjoiNjAxODNmNmEtZDA1ZS00NjZkLWE2MDctNjFlOGZjOTBiYTM4IiwidGVuYW50IjoiY2xvdWRiZXQiLCJ1dWlkIjoiNjAxODNmNmEtZDA1ZS00NjZkLWE2MDctNjFlOGZjOTBiYTM4In0.AYRbz2H6msv8_2XK0MM3pg-RWxhirjaBPo0jq-smk9IqA_PDROdAVh39GQNdNkczyvuC1afeyiV3TOQmI9GZQbSIm6rm5tpw7s1Uo8A7gflTYdMF9Sgck2zU-ML5lL-Mn3hpGYrsXd0EDgcBzbGnYY8-dOwktgvMwUCFOVpQxrCczEfLY6y5siMXVRaGh-ZHidKvrzOcVTzp-8nN63aLWExLK2IjaAdjvMcxqMYK_ER7RJjJi4tGjJE9efEA7SyaH526kh1ZS_rJj4sPDi_LXajs2i1UZbOAwb5S7r0_MQcbQCRheaqFXwmqTi4QAK5L_Fu6ynyAzhQjFC9lsEa-Ug"
    base_url = "https://sports-api.cloudbet.com/pub"
    
    headers = {
        "X-API-Key": api_key,
        "Accept": "application/json"
    }
    
    client = httpx.AsyncClient(timeout=10, headers=headers, follow_redirects=True)
    
    try:
        # Get available sports
        print("Fetching available sports...")
        sports_response = await client.get(f"{base_url}/v2/odds/sports")
        if sports_response.status_code == 200:
            sports_data = sports_response.json()
            print(f"Sports response type: {type(sports_data)}")
            if isinstance(sports_data, dict) and 'sports' in sports_data:
                sports_list = sports_data['sports']
                print(f"Available sports: {len(sports_list) if isinstance(sports_list, list) else 'N/A'}")
        
        # API requires from/to, but we'll use wide range and filter by startTime in code
        # Use epoch milliseconds (wide range: now to 1 year ahead)
        now = datetime.utcnow()
        future = now + timedelta(days=365)
        
        from_ms = int(now.timestamp() * 1000)
        to_ms = int(future.timestamp() * 1000)
        
        params = {
            'sport': 'politics',
            'from': str(from_ms),
            'to': str(to_ms)
        }
        
        url = f"{base_url}/v2/odds/events"
        print(f"\nTesting events with epoch milliseconds (wide range)...")
        print(f"Params: sport=politics, from={from_ms}, to={to_ms}")
        
        response = await client.get(url, params=params)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"SUCCESS! Response type: {type(data)}")
            if isinstance(data, dict):
                print(f"Response keys: {list(data.keys())}")
                if 'events' in data:
                    events = data['events']
                    print(f"Total events returned: {len(events) if isinstance(events, list) else 'N/A'}")
                    if isinstance(events, list) and len(events) > 0:
                        print(f"First event keys: {list(events[0].keys())[:10]}")
                        if 'startTime' in events[0]:
                            print(f"First event startTime: {events[0]['startTime']}")
                        # Filter by startTime (next 7 days only)
                        now_ts = now.timestamp()
                        future_limit_ts = (now + timedelta(days=7)).timestamp()
                        filtered = [e for e in events if isinstance(e, dict) and e.get('startTime')]
                        print(f"Events with startTime: {len(filtered)}")
        else:
            print(f"Error: {response.text[:300]}")
    finally:
        await client.aclose()

if __name__ == "__main__":
    asyncio.run(test_events())
