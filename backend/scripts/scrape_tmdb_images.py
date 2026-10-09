import httpx
import re

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

collections = {
    "mcu": "https://www.themoviedb.org/collection/86311",
    "harry-potter": "https://www.themoviedb.org/collection/1241",
    "middle-earth": "https://www.themoviedb.org/collection/119",
    "transformers": "https://www.themoviedb.org/collection/8650",
    "fast-and-furious": "https://www.themoviedb.org/collection/9485",
    "dceu": "https://www.themoviedb.org/movie/209112",
}

with httpx.Client(headers=headers, timeout=15) as client:
    for name, url in collections.items():
        try:
            r = client.get(url, follow_redirects=True)
            text = r.text
            # Look for /t/p/
            matches = list(set(re.findall(r"/t/p/(?:w[0-9]+|original)/([a-zA-Z0-9_-]+\.jpg)", text)))
            print(f"=== {name} (status {r.status_code}) ===")
            valid_posters = []
            valid_backdrops = []
            for hash_part in matches[:10]:
                test_url = f"https://image.tmdb.org/t/p/original/{hash_part}"
                chk = client.head(test_url, follow_redirects=True)
                if chk.status_code == 200:
                    print(f"  200 OK: {test_url}")
        except Exception as e:
            print(f"Error {name}: {e}")
