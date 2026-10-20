import json
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

with open("scripts/found_series_batch2.json", "r", encoding="utf-8") as f:
    data = json.load(f)

for name in ["vampire_diaries", "originals", "last_kingdom", "superman_lois", "jessica_jones", "kurtlar_pusu"]:
    items = data.get(name, [])
    print(f"\n==================== {name.upper()} (Total: {len(items)}) ====================")
    by_s = {}
    for it in items:
        txt = it["text"]
        # extract S and Ep
        m = re.search(r'(\d+)\s*[-_]?\s*mavsum.*?(\d+)\s*[-_]?\s*qism', txt, re.IGNORECASE)
        s, ep = None, None
        if m:
            s, ep = int(m.group(1)), int(m.group(2))
        else:
            m2 = re.search(r'S(\d+)[-_]CH(\d+)', txt, re.IGNORECASE)
            if m2:
                s, ep = int(m2.group(1)), int(m2.group(2))
            else:
                m3 = re.search(r'(\d+)\s*[-_]?\s*qism', txt, re.IGNORECASE)
                if m3:
                    s, ep = 1, int(m3.group(1))

        if s is not None and ep is not None:
            by_s.setdefault(s, {})[ep] = it["id"]
        else:
            # show unparsed
            pass

    for s in sorted(by_s.keys()):
        eps = by_s[s]
        print(f"  Mavsum {s}: {len(eps)} ta qism -> {sorted(eps.keys())[:5]}..{sorted(eps.keys())[-3:]} (msg range: {min(eps.values())}..{max(eps.values())})")
