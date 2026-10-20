import json

with open("scripts/series_search_summary.json", "r", encoding="utf-8") as f:
    data = json.load(f)

with open("scripts/series_search_results.txt", "w", encoding="utf-8") as out:
    for name, chs in data.items():
        out.write(f"\n====================\n{name}\n")
        for ch_id, msgs in chs.items():
            out.write(f"  Channel {ch_id}: {len(msgs)} messages\n")
            for m in msgs[:6]:
                mid = m["id"]
                media = m["media"]
                txt = m["text"][:100]
                out.write(f"    Msg {mid} ({media}): {txt}\n")

print("Written to scripts/series_search_results.txt")
