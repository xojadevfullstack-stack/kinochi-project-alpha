import httpx
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

r = httpx.get("http://127.0.0.1:8000/api/v1/series/1032")
print("Status:", r.status_code)
data = r.json()
print("Title:", data.get("title"))
print("\n--- Testing episode code lookups ---")
for c in ['0c568c5d', '7fefe445']:
    try:
        ep_res = httpx.get(f"http://127.0.0.1:8000/api/v1/series/episodes/code/{c}", timeout=15)
        print(f"Code '{c}': HTTP {ep_res.status_code}")
        if ep_res.status_code == 200:
            ep_data = ep_res.json()
            print(f"  -> Title: {ep_data.get('series_title')} S{ep_data.get('season_number')}E{ep_data.get('episode_number')}")
            for t in ep_data.get('translations', []):
                print(f"     Translation: storage_id={t.get('storage_channel_message_id')} file_id={t.get('telegram_file_id')}")
    except Exception as e:
        print(f"Code '{c}': Error {e}")
