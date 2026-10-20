import urllib.request
import json
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def test_api():
    try:
        req = urllib.request.urlopen("http://127.0.0.1:8000/api/v1/movies?limit=5")
        data = json.loads(req.read().decode())
        print("=== LIVE FASTAPI /movies?limit=5 ===")
        for m in data.get("items", []):
            print(f"[{m.get('id')}] {m.get('title')} -> {m.get('poster_url')}")
    except Exception as e:
        print(f"Error checking movies API: {e}")

    try:
        req_s = urllib.request.urlopen("http://127.0.0.1:8000/api/v1/series?limit=5")
        data_s = json.loads(req_s.read().decode())
        print("\n=== LIVE FASTAPI /series?limit=5 ===")
        for s in data_s.get("items", []):
            print(f"[{s.get('id')}] {s.get('title')} -> {s.get('poster_url')}")
    except Exception as e:
        print(f"Error checking series API: {e}")

if __name__ == "__main__":
    test_api()
