import sys
import os
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import asyncio
import re
import json
from typing import List, Dict, Any, Optional
from scraper.site_search import search_sites
from scraper.queue_manager import QueueManager, QueueItem
from scraper.duplicate_checker import DuplicateChecker

# Belgilangan franshizalar va ularning qismlarini topish qoidalari
FRANCHISES = [
    {
        "franchise": "Karib dengizi qaroqchilari",
        "search": "Karib dengizi qaroqchilari",
        "expected_parts": ["1", "2", "3", "4", "5"],
        "match": lambda t: "karib" in t.lower() and "qaroqchi" in t.lower()
    },
    {
        "franchise": "Xobbit",
        "search": "Hobbit",
        "expected_parts": ["1", "2", "3"],
        "match": lambda t: "hobbit" in t.lower() or "xobbit" in t.lower()
    },
    {
        "franchise": "Jon Uik",
        "search": "Jon Uik",
        "expected_parts": ["1", "2", "3", "4"],
        "match": lambda t: any(w in t.lower() for w in ["jon uik", "jon vik", "john wick"]) and not any(skip in t.lower() for skip in ["balerina", "kontinental"])
    },
    {
        "franchise": "Ochlik o'yinlari",
        "search": "Ochlik o'yinlari",
        "expected_parts": ["1", "2", "3", "4", "5"],
        "match": lambda t: any(w in t.lower() for w in ["ochlik", "hayot-mamot"])
    },
    {
        "franchise": "Qasoskorlar",
        "search": "Qasoskorlar",
        "expected_parts": ["1", "altron", "abadiyat", "intiho"],
        "match": lambda t: "qasoskorlar" in t.lower() and "taqdir o'yini" not in t.lower()
    },
    {
        "franchise": "Temir odam",
        "search": "Temir odam",
        "expected_parts": ["1", "2", "3"],
        "match": lambda t: "temir odam" in t.lower()
    },
    {
        "franchise": "O'rgimchak odam",
        "search": "O'rgimchak odam",
        "expected_parts": ["1", "2", "3", "qaytish", "uzoqlash", "yo'l yo'q"],
        "match": lambda t: ("o'rgimchak" in t.lower() or "orgimchak" in t.lower()) and "multfilm" not in t.lower()
    },
    {
        "franchise": "Betmen",
        "search": "Betmen",
        "expected_parts": ["boshlanish", "joker", "afsonaning", "2022"],
        "match": lambda t: any(w in t.lower() for w in ["betmen", "batman", "qora ritsar"]) and "multfilm" not in t.lower()
    },
    {
        "franchise": "Yura davri parki / olami",
        "search": "Yura davri",
        "expected_parts": ["1", "2", "3", "dunyosi"],
        "match": lambda t: "yura davri" in t.lower() and "hayvoni" not in t.lower() and "bolalari" not in t.lower()
    },
    {
        "franchise": "Matritsa",
        "search": "Matritsa",
        "expected_parts": ["1", "2", "3", "4"],
        "match": lambda t: "matritsa" in t.lower() and "kianu rivz" not in t.lower()
    },
    {
        "franchise": "Labirint yuguruvchisi",
        "search": "Labirint",
        "expected_parts": ["1", "2", "3"],
        "match": lambda t: "labirint" in t.lower() and not any(skip in t.lower() for skip in ["fransiya", "qochish"])
    },
    {
        "franchise": "Divergent",
        "search": "Divergent",
        "expected_parts": ["1", "2", "3"],
        "match": lambda t: any(w in t.lower() for w in ["divergent", "insurgent"])
    },
    {
        "franchise": "Rezident Evil (Yovuzlik qarorgohi)",
        "search": "Yovuzlik qarorgohi",
        "expected_parts": ["1", "2", "3", "4", "5", "6"],
        "match": lambda t: "yovuzlik qarorgohi" in t.lower()
    },
    {
        "franchise": "Terminator",
        "search": "Terminator",
        "expected_parts": ["1", "2", "3", "4", "5", "6"],
        "match": lambda t: "terminator" in t.lower()
    },
    {
        "franchise": "Mumiyo (Mumiya)",
        "search": "Mumiya",
        "expected_parts": ["1", "2", "3"],
        "match": lambda t: "mumiya" in t.lower() or "momiyo" in t.lower()
    },
    {
        "franchise": "Maymunlar sayyorasi",
        "search": "Maymunlar sayyorasi",
        "expected_parts": ["1", "2", "3", "4"],
        "match": lambda t: "maymunlar sayyorasi" in t.lower()
    },
    {
        "franchise": "Godzilla",
        "search": "Godzilla",
        "expected_parts": ["1", "2", "kong", "minus"],
        "match": lambda t: "godzilla" in t.lower()
    },
    {
        "franchise": "King Kong",
        "search": "King Kong",
        "expected_parts": ["1", "2"],
        "match": lambda t: "king kong" in t.lower() or "king-kong" in t.lower()
    },
    {
        "franchise": "Avatar",
        "search": "Avatar",
        "expected_parts": ["1", "2"],
        "match": lambda t: "avatar" in t.lower() and not any(s in t.lower() for s in ["gobliddin", "ang afsonasi", "olov va kul"])
    },
    {
        "franchise": "Sehrli qo'rquv / Lanat",
        "search": "Lanat",
        "expected_parts": ["1", "2", "3"],
        "match": lambda t: any(w in t.lower() for w in ["lanat", "la'nat"]) and not any(s in t.lower() for s in ["chexiya", "malika"])
    },
    {
        "franchise": "Annabel",
        "search": "Annabel",
        "expected_parts": ["1", "2", "3"],
        "match": lambda t: "annabel" in t.lower()
    },
    {
        "franchise": "Yovuzlik ichida (Astral)",
        "search": "Astral",
        "expected_parts": ["1", "2", "3", "4", "5"],
        "match": lambda t: "astral" in t.lower()
    },
    {
        "franchise": "Arra (Pila)",
        "search": "Arra",
        "expected_parts": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
        "match": lambda t: "arra" in t.lower() and any(k in t.lower() for k in ["pila", "ujas"])
    },
    {
        "franchise": "Qichqiriq (Scream)",
        "search": "Qichqiriq",
        "expected_parts": ["1", "2", "3", "4", "5", "6"],
        "match": lambda t: "qichqiriq" in t.lower() and "titragan" not in t.lower()
    },
    {
        "franchise": "So'nggi manzil (Ajal rejasi)",
        "search": "Manzil",
        "expected_parts": ["1", "2", "3", "4", "5"],
        "match": lambda t: any(w in t.lower() for w in ["oxirgi manzil", "so'nggi manzil", "ajal rejasi"])
    },
    {
        "franchise": "Sokin makon",
        "search": "Sokin",
        "expected_parts": ["1", "2", "birinchi kun"],
        "match": lambda t: "sokin hudud" in t.lower() or "sokin makon" in t.lower()
    },
    {
        "franchise": "Shrek",
        "search": "Shrek",
        "expected_parts": ["1", "2", "3", "4"],
        "match": lambda t: "shrek" in t.lower() and "etik kiygan" not in t.lower()
    },
    {
        "franchise": "Kung-fu Panda",
        "search": "Kung fu Panda",
        "expected_parts": ["1", "2", "3", "4"],
        "match": lambda t: "panda" in t.lower()
    },
    {
        "franchise": "Madagaskar",
        "search": "Madagaskar",
        "expected_parts": ["1", "2", "3"],
        "match": lambda t: "madagaskar" in t.lower() and "pingvin" not in t.lower()
    },
    {
        "franchise": "Muzlik davri",
        "search": "Muzlik davri",
        "expected_parts": ["1", "2", "3", "4", "5"],
        "match": lambda t: "muzlik davri" in t.lower()
    },
    {
        "franchise": "Jirkanch Men / Minionlar",
        "search": "Minionlar",
        "expected_parts": ["1", "2", "gryu"],
        "match": lambda t: "minion" in t.lower() or "jirkanch" in t.lower()
    },
    {
        "franchise": "O'yinchoqlar tarixi",
        "search": "O'yinchoqlar tarixi",
        "expected_parts": ["1", "2", "3", "4"],
        "match": lambda t: "o'yinchoq" in t.lower() or "oyinchoq" in t.lower()
    },
    {
        "franchise": "Jumanji",
        "search": "Jumanji",
        "expected_parts": ["1", "2", "3"],
        "match": lambda t: "jumanji" in t.lower()
    },
]

async def curate_franchise_queue():
    qm = QueueManager()
    checker = DuplicateChecker()
    await checker.refresh_cache()

    curated_items: List[QueueItem] = []
    seen_keys = set()

    print("🚀 Barcha 33 ta franshiza bo'yicha eng sara qismlar tanlanmoqda...", flush=True)

    for f_cfg in FRANCHISES:
        q = f_cfg["search"]
        fname = f_cfg["franchise"]
        match_fn = f_cfg["match"]

        try:
            results = await search_sites(q, source="all")
        except Exception as e:
            print(f"Xato [{q}]: {e}", flush=True)
            continue

        franchise_picked = []
        for r in results:
            title = r["title"]
            if not match_fn(title):
                continue
            
            # Unikal kalit: title + year yoki slug
            norm_key = re.sub(r'[^a-zA-Z0-9]', '', title.lower())
            # Bir xil qismni ikki marta olmaslik (masalan, uzmovi va asilmediadan bir xil qism)
            # Uzmovini afzal ko'ramiz, agar bo'lmasa Asilmedia
            clean_part = norm_key
            if clean_part in seen_keys:
                continue

            seen_keys.add(clean_part)

            is_dup = r.get("is_duplicate", False)
            item = QueueItem(
                id=r["id"],
                source=r["source"],
                title=r["title"],
                year=r.get("year"),
                media_type="movie",
                url=r.get("url", ""),
                poster_url=r.get("poster_url"),
                status="already_exists" if is_dup else "pending",
                error_message=f"Bazada mavjud: {r.get('db_title')}" if is_dup else None,
            )
            franchise_picked.append(item)

        print(f"✅ {fname}: {len(franchise_picked)} ta qism saralandi.", flush=True)
        curated_items.extend(franchise_picked)

    print(f"\n🎉 JAMI SARALANGAN FILMLAR: {len(curated_items)} ta!", flush=True)

    # Navbat faylini to'ldirish
    # Mavjud qoralama elementlarni o'rniga aynan shu to'plamni joylashtiramiz
    items_dict = {it.id: it for it in curated_items}
    qm.items = items_dict
    qm.save()
    print(f"💾 Navbat fayliga {len(curated_items)} ta saralangan film to'liq saqlandi!", flush=True)
    stats = qm.stats()
    print(f"📊 Yangi navbat statistikasi: {stats}", flush=True)

if __name__ == "__main__":
    asyncio.run(curate_franchise_queue())
