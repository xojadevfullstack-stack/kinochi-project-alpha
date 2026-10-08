import sys
import os
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import asyncio
import re
from typing import List, Dict, Any
from scraper.site_search import search_sites
from scraper.queue_manager import QueueManager, QueueItem

FRANCHISE_SEARCHES = [
    # 1. Karib dengizi qaroqchilari — 5 qism
    {"name": "Karib dengizi qaroqchilari", "queries": ["Karib dengizi qaroqchilari"], "keywords": ["karib", "qaroqchi"]},
    # 2. Xobbit — 3 qism
    {"name": "Xobbit", "queries": ["Hobbit", "Xobbit"], "keywords": ["hobbit", "xobbit"]},
    # 3. Jon Uik — 4 qism
    {"name": "Jon Uik", "queries": ["Jon Uik", "Jon Vik"], "keywords": ["jon uik", "jon vik", "john wick"]},
    # 4. Ochlik o‘yinlari — 5 qism
    {"name": "Ochlik o'yinlari", "queries": ["Ochlik o'yinlari", "Hayot-mamot o'yinlar"], "keywords": ["ochlik", "hayot-mamot"]},
    # 5. Qasoskorlar — 4 qism
    {"name": "Qasoskorlar", "queries": ["Qasoskorlar"], "keywords": ["qasoskorlar"]},
    # 6. Temir odam — 3 qism
    {"name": "Temir odam", "queries": ["Temir odam"], "keywords": ["temir odam"]},
    # 7. O‘rgimchak odam — asosiy filmlar
    {"name": "O'rgimchak odam", "queries": ["O'rgimchak odam", "O'rgimchak-odam", "Yangi O'rgimchak"], "keywords": ["o'rgimchak", "orgimchak"]},
    # 8. Betmen — asosiy filmlar
    {"name": "Betmen", "queries": ["Betmen", "Batman", "Qora Ritsar"], "keywords": ["betmen", "batman", "qora ritsar"]},
    # 9. Yura davri parki / olami
    {"name": "Yura davri parki / olami", "queries": ["Yura davri"], "keywords": ["yura davri", "yura davr"]},
    # 10. Matritsa — 4 qism
    {"name": "Matritsa", "queries": ["Matritsa"], "keywords": ["matritsa", "matrix"]},
    # Fantastika va jangari
    {"name": "Labirint yuguruvchisi", "queries": ["Labirint yuguruvchisi"], "keywords": ["labirint"]},
    {"name": "Divergent", "queries": ["Divergent", "Insurgent", "Elligent"], "keywords": ["divergent", "insurgent", "alligent", "elligent"]},
    {"name": "Rezident Evil", "queries": ["Yovuzlik qarorgohi", "Rezident Evil", "Resident Evil"], "keywords": ["yovuzlik qarorgohi", "rezident", "resident evil"]},
    {"name": "Terminator", "queries": ["Terminator"], "keywords": ["terminator"]},
    {"name": "Mumiyo", "queries": ["Mumiya", "Mumiyo"], "keywords": ["mumiya", "mumiyo"]},
    {"name": "Maymunlar sayyorasi", "queries": ["Maymunlar sayyorasi"], "keywords": ["maymunlar sayyorasi"]},
    {"name": "Godzilla", "queries": ["Godzilla"], "keywords": ["godzilla"]},
    {"name": "King Kong", "queries": ["King Kong", "Kong: Boshsuyak"], "keywords": ["king kong", "kong"]},
    {"name": "Avatar", "queries": ["Avatar"], "keywords": ["avatar"]},
    # Dahshatli
    {"name": "Sehrli qo'rquv", "queries": ["Sehrli qo'rquv", "Sehrli qorquv"], "keywords": ["sehrli qo'rquv", "sehrli qorquv", "conjuring"]},
    {"name": "Annabel", "queries": ["Annabel", "Annabelle"], "keywords": ["annabel"]},
    {"name": "Yovuzlik ichida (Astral)", "queries": ["Astral", "Yovuzlik ichida"], "keywords": ["astral", "yovuzlik ichida", "insidious"]},
    {"name": "Arra", "queries": ["Arra"], "keywords": ["arra"]},
    {"name": "Qichqiriq", "queries": ["Qichqiriq"], "keywords": ["qichqiriq", "scream"]},
    {"name": "So'nggi manzil", "queries": ["So'nggi manzil", "Songgi manzil"], "keywords": ["so'nggi manzil", "songgi manzil", "final destination"]},
    {"name": "Sokin makon", "queries": ["Sokin makon"], "keywords": ["sokin makon", "quiet place"]},
    # Multfilm / oilaviy
    {"name": "Shrek", "queries": ["Shrek"], "keywords": ["shrek"]},
    {"name": "Kung-fu Panda", "queries": ["Kung fu Panda", "Kung-fu Panda"], "keywords": ["kung fu panda", "kung-fu panda", "panda"]},
    {"name": "Madagaskar", "queries": ["Madagaskar"], "keywords": ["madagaskar"]},
    {"name": "Muzlik davri", "queries": ["Muzlik davri"], "keywords": ["muzlik davri", "muzlik davr"]},
    {"name": "Jirkanch Men / Minionlar", "queries": ["Jirkanch Men", "Minionlar"], "keywords": ["jirkanch men", "minion"]},
    {"name": "O'yinchoqlar tarixi", "queries": ["O'yinchoqlar tarixi"], "keywords": ["o'yinchoqlar tarixi", "oyinchoqlar tarixi"]},
    {"name": "Jumanji", "queries": ["Jumanji"], "keywords": ["jumanji"]},
]

async def collect_all():
    all_found = {}
    seen_urls = set()

    for item in FRANCHISE_SEARCHES:
        fname = item["name"]
        keywords = [k.lower() for k in item["keywords"]]
        matched_items = []

        for q in item["queries"]:
            try:
                results = await search_sites(q, source="all")
                for r in results:
                    title_l = r["title"].lower()
                    url = r.get("url", "")
                    if url in seen_urls:
                        continue
                    # Match at least one keyword
                    if any(k in title_l for k in keywords):
                        # Filter out unrelated stuff
                        if "serial" in title_l and fname not in ["Yovuzlik ichida (Astral)"]:
                            # check if it's a TV series instead of movie
                            pass
                        seen_urls.add(url)
                        matched_items.append(r)
            except Exception as e:
                print(f"Xato [{q}]: {e}", flush=True)

        all_found[fname] = matched_items
        print(f"✅ [{fname}]: {len(matched_items)} ta topildi", flush=True)
        for m in matched_items[:5]:
            print(f"   • {m['title']} ({m['id']})", flush=True)

    total_count = sum(len(v) for v in all_found.values())
    print(f"\n🎉 JAMI TOPILGAN FRANCHISE FILMLAR: {total_count} ta", flush=True)
    return all_found

if __name__ == "__main__":
    asyncio.run(collect_all())
