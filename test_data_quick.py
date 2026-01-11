"""Quick test to see what data we're getting."""
import asyncio
import sys
sys.path.insert(0, 'src')

from src.fetchers.polymarket_fetcher import PolymarketFetcher
from src.fetchers.cloudbet_fetcher import CloudbetFetcher
from src.normalizers.market_normalizer import MarketNormalizer
from src.config_loader import load_config

async def main():
    config = load_config()

    print('=== Fetching Polymarket ===')
    pm_fetcher = PolymarketFetcher(debug_api=False)
    pm_raw = await pm_fetcher.fetch_all_markets(limit=5)
    print(f'Raw markets: {len(pm_raw)}')

    print('\n=== Normalizing Polymarket ===')
    normalizer = MarketNormalizer()
    pm_markets = normalizer.normalize_polymarket(pm_raw)
    print(f'Normalized: {len(pm_markets)}')

    for i, m in enumerate(pm_markets[:3]):
        print(f'{i+1}. {m.title}')
        print(f'   Outcomes: {list(m.outcomes.keys())}')

    print('\n=== Fetching Cloudbet (limited) ===')
    cb_fetcher = CloudbetFetcher(
        api_key=config.apis.cloudbet.api_key,
        debug_api=False
    )
    cb_raw = await cb_fetcher.fetch_all_markets()
    print(f'Raw outcomes: {len(cb_raw)}')

    print('\n=== Normalizing Cloudbet ===')
    cb_markets = normalizer.normalize_cloudbet(cb_raw)
    print(f'Normalized markets: {len(cb_markets)}')

    for i, m in enumerate(cb_markets[:3]):
        print(f'{i+1}. {m.title}')
        print(f'   Outcomes: {list(m.outcomes.keys())[:5]}')

    await pm_fetcher.close()
    await cb_fetcher.close()

if __name__ == '__main__':
    asyncio.run(main())
