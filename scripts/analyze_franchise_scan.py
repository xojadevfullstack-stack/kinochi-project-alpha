import json
import os

with open("scripts/franchise_scan_full.json", "r", encoding="utf-8") as f:
    data = json.load(f)

with open("scripts/franchise_details.txt", "w", encoding="utf-8") as out:
    for name, items in data.items():
        out.write(f"\n========================================\n{name} ({len(items)} ta element)\n========================================\n")
        # filter only items that have video or document
        unique_entries = {}
        for it in items:
            txt = it["text"].replace("\n", " ")
            out.write(f"  ID {it['id']} | Date: {it['date']} | Video: {it['has_video']} | Doc: {it['doc_name']} | Text: {txt}\n")

print("Tahlil scripts/franchise_details.txt ga yozildi!")
