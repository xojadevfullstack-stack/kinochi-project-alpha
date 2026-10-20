import json
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

with open("scripts/mapped_series_episodes.json", "r", encoding="utf-8") as f:
    data = json.load(f)

for name in ["vikings", "prison_break", "teen_wolf", "breaking_bad", "the_boys", "dark", "witcher", "sherlock", "continental"]:
    items = data.get(name, [])
    # group by season
    by_s = {}
    for it in items:
        s = it.get("season")
        ep = it.get("episode")
        if s is None:
            continue
        if s not in by_s:
            by_s[s] = []
        by_s[s].append((ep, it["id"], it["text"]))
    
    print(f"\n==================== {name.upper()} ====================")
    for s_num in sorted(by_s.keys()):
        eps = sorted(by_s[s_num], key=lambda x: (x[0] if x[0] else 0))
        print(f"Season {s_num}: {len(eps)} episodes")
        ids = [x[1] for x in eps]
        print(f"  IDs: {ids}")
