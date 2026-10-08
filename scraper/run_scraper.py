import sys
import os
import asyncio
import argparse

import logging

if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Set root directory in sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from scraper.queue_manager import QueueManager
from scraper.site_parser import (
    parse_uzmovi_page,
    parse_asilmedia_page,
    parse_uzmovi_page_async,
    parse_asilmedia_page_async,
)
from scraper.duplicate_checker import DuplicateChecker
from scraper.telethon_moderator_pipeline import TelethonModeratorPipeline, create_telethon_client
from scraper.config import TARGET_BOTS, TELEGRAM_API_ID, TELEGRAM_API_HASH

async def cmd_parse(source: str, max_pages: int, media_type: str = "all"):
    qm = QueueManager()
    checker = DuplicateChecker()
    await checker.refresh_cache(force=True)

    print(f"\n🔍 [{source.upper()}] saytidan katalog yig'ish boshlanmoqda (Maksimal sahifalar: {max_pages}, Turi: {media_type})...")

    urls = []
    for page in range(1, max_pages + 1):
        if source == "uzmovi":
            if media_type in ("all", "movie"):
                urls.append(f"https://uzmovi.net/tarjima-kinolarri/page/{page}/" if page > 1 else "https://uzmovi.net/tarjima-kinolarri")
            if media_type in ("all", "series"):
                urls.append(f"https://uzmovi.net/serialar/page/{page}/" if page > 1 else "https://uzmovi.net/serialar")
        elif source == "asilmedia":
            if media_type in ("all", "movie"):
                urls.append(f"https://asilmedia.org/films/tarjima_kinolar/page/{page}/" if page > 1 else "https://asilmedia.org/films/tarjima_kinolar/")
            if media_type in ("all", "series"):
                urls.append(f"https://asilmedia.org/films/serial/page/{page}/" if page > 1 else "https://asilmedia.org/films/serial/")
        else:
            print("❌ Noma'lum manba. 'uzmovi' yoki 'asilmedia' tanlang.")
            return

    # Parallel aiohttp orqali barcha sahifalarni bir vaqtda tortamiz
    import aiohttp
    conn = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(connector=conn) as session:
        if source == "uzmovi":
            tasks = [parse_uzmovi_page_async(session, u) for u in urls]
        else:
            tasks = [parse_asilmedia_page_async(session, u) for u in urls]
        pages_results = await asyncio.gather(*tasks, return_exceptions=True)

    all_items = []
    for p_idx, res in enumerate(pages_results, 1):
        if isinstance(res, Exception):
            print(f"⚠️ Sahifa {p_idx} yuklanmadi: {res}")
            continue
        all_items.extend(res)
        print(f"📄 Sahifa {p_idx}: {len(res)} ta element yuklandi.")

    # Dublikatlarni parallel tekshirish (1 soniyada yuzlab kinolar tekshiriladi)
    print(f"🔄 {len(all_items)} ta kino/serial bazadagi dublikatlarga parallel tekshirilmoqda...")
    dup_tasks = [
        checker.check(item.title, year=item.year, original_title=item.original_title, media_type=item.media_type)
        for item in all_items
    ]
    dup_results = await asyncio.gather(*dup_tasks, return_exceptions=True)

    duplicates_detected = 0
    for item, dup_res in zip(all_items, dup_results):
        if isinstance(dup_res, Exception):
            continue
        if dup_res.is_duplicate:
            item.status = "already_exists"
            item.error_message = f"Bazada mavjud: {dup_res.reason} (ID: {dup_res.matched_id})"
            duplicates_detected += 1

    total_added = qm.add_items_batch(all_items)
    print(f"\n✅ Yig'ish yakunlandi! Jami topilgan: {len(all_items)}, Yangi qo'shilgan: {total_added}, Bazadagi dublikatlar: {duplicates_detected}")
    print(f"📊 Navbat holati: {qm.stats()}\n")

def parse_codes_arg(codes_str: str) -> list:
    res = []
    parts = [p.strip() for p in codes_str.split(",") if p.strip()]
    for p in parts:
        if "-" in p:
            sub = p.split("-")
            if len(sub) == 2 and sub[0].isdigit() and sub[1].isdigit():
                for n in range(int(sub[0]), int(sub[1]) + 1):
                    res.append(str(n))
            else:
                res.append(p)
        else:
            res.append(p)
    return res

async def cmd_download(limit: int, target: str, codes: str = None, media_type: str = "all", item_id: str = None):
    checker = DuplicateChecker()
    await checker.refresh_cache(force=True)

    bot_username = TARGET_BOTS.get(target, target)
    code_list = parse_codes_arg(codes) if (codes and not item_id) else []
    
    if item_id:
        qm = QueueManager()
        target_item = qm.items.get(item_id)
        if not target_item:
            print(f"❌ Element #{item_id} navbatda topilmadi!")
            return
        pending = [target_item]
        bot_username = TARGET_BOTS.get(target_item.source, bot_username)
        print(f"\n🚀 Aniq element yuklanmoqda: [{target_item.media_type.upper()}] '{target_item.title}' (Bot: @{bot_username})...")
    elif code_list:
        print(f"\n🚀 {len(code_list)} ta film kodi bo'yicha yuklash boshlanmoqda (Maqsadli bot: @{bot_username}, Kodlar: {', '.join(code_list)})...")
    else:
        qm = QueueManager()
        target_source = "asilmedia" if "asil" in target.lower() else "uzmovi"
        m_type = None if media_type == "all" else media_type
        pending = qm.get_pending(limit=limit, source=target_source, media_type=m_type)
        if not pending:
            pending = qm.get_pending(limit=limit, media_type=m_type)

        if not pending:
            print("ℹ️ Navbatda yuklanadigan yangi kinolar yo'q. Avval --parse orqali ro'yxat yig'ing yoki --codes orqali film kodini kiriting.")
            return

        print(f"\n🚀 {len(pending)} ta kino/serialni yuklash boshlanmoqda (Maqsadli bot: @{bot_username})...")

    client = create_telethon_client()
    try:
        await client.connect()
        if not await client.is_user_authorized():
            print("\n❌ Telegram client avtorizatsiyadan o'tmagan! kinochi_userbot.session faylini tekshiring.")
            return
    except Exception as e:
        print(f"\n❌ Telegram clientni ishga tushirishda xatolik: {e}")
        return

    pipeline = TelethonModeratorPipeline(client=client, duplicate_checker=checker)

    try:
        if code_list:
            qm = QueueManager()
            for idx, c in enumerate(code_list, 1):
                print(f"\n[{idx}/{len(code_list)}] 🎬 Kod #{c} bo'yicha moderator sikli boshlanmoqda...")
                try:
                    success = await pipeline.run_by_code(code=c, target_bot=bot_username)
                except Exception as ex:
                    print(f"❌ Kod #{c} da kutilmagan xatolik: {ex}")
                    success = False

                if success:
                    print(f"✅ Kod #{c} muvaffaqiyatli saqlandi, Topic ochildi va Websaytga ulandi.")
                    for qid in [f"asilmedia_{c}", f"uzmovi_{c}"]:
                        if qid in qm.items:
                            qm.update_status(qid, "completed")
                else:
                    print(f"⚠️ Kod #{c} yuklab bo'lmadi yoki o'tkazib yuborildi.")
                
                if idx < len(code_list):
                    print("⏳ 2 soniya tanaffus...")
                    await asyncio.sleep(2.0)
        else:
            qm = QueueManager()
            downloaded_count = 0
            for idx, item in enumerate(pending, 1):
                media_label = "SERIAL" if item.media_type == "series" else "KINO"

                # Pre-check duplicate in DB
                dup = await checker.check(
                    title=item.title,
                    year=item.year,
                    original_title=item.original_title,
                    media_type=item.media_type
                )
                if dup.is_duplicate:
                    qm.update_status(item.id, "already_exists", error_message=f"Bazada mavjud: {dup.reason} (ID: {dup.matched_id})")
                    print(f"⏭️ [{media_label}] '{item.title}' bazada mavjud: [{dup.matched_type}] '{dup.matched_title}' (ID: {dup.matched_id}). O'tkazib yuborildi.")
                    continue

                print(f"\n[{downloaded_count + 1}/{limit}] 🚀 [{media_label}] '{item.title}' ({item.year or 'Noma\'lum'}) bo'yicha sikl boshlanmoqda...")
                qm.update_status(item.id, "in_progress")
                
                try:
                    success = await pipeline.run_item(item, target_bot=bot_username)
                except Exception as ex:
                    print(f"❌ '{item.title}' yuklashda kutilmagan xatolik: {ex}")
                    qm.update_status(item.id, "failed", error_message=f"Kutilmagan xatolik: {ex}")
                    success = False

                if success:
                    qm.update_status(item.id, "completed")
                    downloaded_count += 1
                    print(f"✅ Muvaffaqiyatli saqlandi, Topic ochildi va Websaytga ulandi: {item.title}")
                else:
                    fresh = qm.items.get(item.id)
                    if not (fresh and fresh.status in ("already_exists", "needs_review", "failed")):
                        err_msg = fresh.error_message if (fresh and fresh.error_message) else "Video olinmadi yoki xatolik"
                        qm.update_status(item.id, "failed", error_message=err_msg)
                        print(f"⚠️ Yuklab bo'lmadi: {item.title} ({err_msg})")
                    elif fresh and fresh.status == "failed" and fresh.error_message:
                        print(f"⚠️ Yuklab bo'lmadi: {item.title} ({fresh.error_message})")
                    else:
                        print(f"⚠️ Yuklab bo'lmadi: {item.title}")

                if downloaded_count >= limit:
                    break

                # Telegram flood limitiga tushmaslik uchun xavfsiz qisqa kutish
                if idx < len(pending):
                    print("⏳ 2.5 soniya tanaffus...")
                    await asyncio.sleep(2.5)

    finally:
        await client.disconnect()
        print("\n🏁 Yuklash jarayoni to'xtatildi.")
        if not code_list:
            qm = QueueManager()
            print(f"📊 Navbat statistikasi: {qm.stats()}\n")

async def cmd_clean_duplicates():
    qm = QueueManager()
    checker = DuplicateChecker()
    await checker.refresh_cache(force=True)
    print("\n🔍 Navbatdagi barcha kinolar bazadagi dublikatlarga tekshirilmoqda...")
    
    checked = 0
    duplicates_found = 0
    for item_id, item in list(qm.items.items()):
        if item.status in ("pending", "failed"):
            checked += 1
            dup = await checker.check(item.title, year=item.year, original_title=item.original_title, media_type=item.media_type)
            if dup.is_duplicate:
                duplicates_found += 1
                qm.update_status(item.id, "already_exists", error_message=f"Bazada mavjud: {dup.reason} (ID: {dup.matched_id})")
                print(f"  ❌ [{dup.matched_type.upper()}] '{item.title}' -> Bazada mavjud: '{dup.matched_title}' (ID: {dup.matched_id}, Kod: {dup.matched_code or 'yoq'})")

    print(f"\n✅ Tekshiruv yakunlandi! Jami tekshirildi: {checked}, Dublikat deb topildi: {duplicates_found}")
    print(f"📊 Yangilangan navbat statistikasi: {qm.stats()}\n")

def cmd_stats():
    qm = QueueManager()
    print("\n📊 Navbat statistikasi:")
    for k, v in qm.stats().items():
        print(f"  • {k}: {v}")
    print()

def main():
    parser = argparse.ArgumentParser(description="Kinochi Avtomatlashtirilgan Parser & Grabber")
    parser.add_argument("--parse", action="store_true", help="Saytdan kinolar ro'yxatini yig'ish")
    parser.add_argument("--source", type=str, default="uzmovi", choices=["uzmovi", "asilmedia"], help="Sayt manbasi (uzmovi yoki asilmedia)")
    parser.add_argument("--pages", type=int, default=3, help="Yig'iladigan sahifalar soni (default: 3)")
    parser.add_argument("--download", action="store_true", help="Navbatdagi kinolarni Telegram botdan yuklab olish")
    parser.add_argument("--target", type=str, default="uzmovi", choices=["uzmovi", "asilmedia"], help="Maqsadli bot (uzmovi yoki asilmedia)")
    parser.add_argument("--limit", type=int, default=5, help="Yuklanadigan kinolar soni (default: 5)")
    parser.add_argument("--codes", type=str, default=None, help="Muayyan film kodlari (masalan: 15 yoki 1-5 yoki 10,15,20)")
    parser.add_argument("--clean-duplicates", action="store_true", help="Navbatdagi mavjud bazadagi dublikatlarni tozalash")
    parser.add_argument("--media-type", type=str, default="all", choices=["all", "movie", "series"], help="Media turi (all, movie yoki series)")
    parser.add_argument("--item-id", type=str, default=None, help="Navbatdagi aniq bitta element ID si (masalan: asilmedia_18509)")
    parser.add_argument("--stats", action="store_true", help="Navbat holatini ko'rish")

    args = parser.parse_args()

    if args.stats:
        cmd_stats()
    elif args.clean_duplicates:
        asyncio.run(cmd_clean_duplicates())
    elif args.parse:
        asyncio.run(cmd_parse(args.source, args.pages, args.media_type))
    elif args.download:
        asyncio.run(cmd_download(args.limit, args.target, args.codes, args.media_type, args.item_id))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

