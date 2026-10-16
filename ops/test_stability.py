import asyncio
import httpx

async def test_all():
    base = 'https://kinochi-project-alpha-9g6j.onrender.com'
    print('=== 1. CLOUD BACKEND (RENDER) TESTS ===')
    async with httpx.AsyncClient(timeout=15.0) as client:
        # Health
        try:
            r = await client.get(f'{base}/health')
            print(f'[OK] /health -> {r.status_code}: {r.json()}')
        except Exception as e:
            print(f'[FAIL] /health -> {e}')

        # Diag
        try:
            r = await client.get(f'{base}/api/v1/diag')
            print(f'[OK] /api/v1/diag -> {r.status_code}: {r.json()}')
        except Exception as e:
            print(f'[FAIL] /api/v1/diag -> {e}')

        # Movies
        try:
            r = await client.get(f'{base}/api/v1/movies')
            data = r.json()
            total = data.get('total')
            print(f'[OK] /api/v1/movies -> {r.status_code}: Total = {total}')
            for m in data.get('items', []):
                t = m.get('title')
                c = m.get('code')
                src = m.get('source_type')
                st = m.get('publish_status')
                print(f'     - {t}, Code: {c}, Source: {src}, Status: {st}')
        except Exception as e:
            print(f'[FAIL] /api/v1/movies -> {e}')

        # Categories
        try:
            r = await client.get(f'{base}/api/v1/categories')
            print(f'[OK] /api/v1/categories -> {r.status_code}: {len(r.json())} categories')
        except Exception as e:
            print(f'[FAIL] /api/v1/categories -> {e}')

        # Scraper status without auth
        try:
            r = await client.get(f'{base}/api/v1/scraper/status')
            detail = r.json().get('detail', '') if r.status_code != 200 else '200 OK'
            print(f'[INFO] /api/v1/scraper/status without auth -> {r.status_code} ({detail})')
        except Exception as e:
            print(f'[FAIL] /api/v1/scraper/status -> {e}')

    print('\n=== 2. VERCEL FRONTEND TESTS ===')
    async with httpx.AsyncClient(timeout=15.0) as client:
        for page in ['https://kinochi-project-alpha.vercel.app', 'https://kinochi-project-alpha.vercel.app/movies']:
            try:
                r = await client.get(page)
                print(f'[OK] {page} -> {r.status_code}')
            except Exception as e:
                print(f'[FAIL] {page} -> {e}')

if __name__ == '__main__':
    asyncio.run(test_all())
