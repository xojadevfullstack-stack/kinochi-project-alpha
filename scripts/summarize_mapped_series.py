import json
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

with open("scripts/mapped_series_episodes.json", "r", encoding="utf-8") as f:
    data = json.load(f)

for k, items in data.items():
    seasons = {}
    for it in items:
        s = it.get("season") or 1
        ep = it.get("episode")
        if s not in seasons:
            seasons[s] = []
        seasons[s].append((ep, it["id"]))
    print(f"\n=== {k.upper()} (Total videos: {len(items)}) ===")
    for s_num in sorted(seasons.keys()):
        eps = seasons[s_num]
        eps_sorted = sorted(eps, key=lambda x: (x[0] if x[0] is not None else 9999))
        print(f"  Mavsum {s_num}: {len(eps)} ta qism (Msg range: {min(x[1] for x in eps)}..{max(x[1] for x in eps)})")
