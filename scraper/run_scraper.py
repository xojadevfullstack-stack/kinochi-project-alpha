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
    parse_kawaii_page_async,
)
from scraper.state_manager import StateManager
from scraper.duplicate_checker import DuplicateChecker
from scraper.telethon_moderator_pipeline import TelethonModeratorPipeline, create_telethon_client
from telethon.errors import FloodWaitError
from scraper.config import TARGET_BOTS, TELEGRAM_API_ID, TELEGRAM_API_HASH

async def cmd_parse(
    source: str,
    max_pages: int,
    media_type: str = "all",
    start_page: int = None,
    min_rating: float = None
):
    qm = QueueManager()
    sm = StateManager()
    state = sm.get_state()

    if start_page is None:
        start_page = int(state.get(f"{source.lower()}_current_page", 1))
    if min_rating is None:
        min_rating = float(state.get("min_rating", 6.0))

    end_page = start_page + max_pages - 1
    checker = DuplicateChecker()
    await checker.refresh_cache(force=True)

    print(f"\n🔍 [{source.upper()}] saytidan katalog yig'ish boshlanmoqda (Sahifalar: {start_page}..{end_page}, Min reyting: {min_rating}, Turi: {media_type})...")

    urls = []
    if source in ("uzmovi", "asilmedia"):
        for page in range(start_page, end_page + 1):
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
    elif source == "kawaii":
        pass
    else:
        print("❌ Noma'lum manba. 'uzmovi', 'asilmedia' yoki 'kawaii' tanlang.")
        return

    # Parallel aiohttp orqali barcha sahifalarni bir vaqtda tortamiz
    import aiohttp
    conn = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(connector=conn) as session:
        if source == "uzmovi":
            tasks = [parse_uzmovi_page_async(session, u, min_rating=min_rating) for u in urls]
        elif source == "kawaii":
            tasks = [parse_kawaii_page_async(session, page=p, min_rating=min_rating, media_type=media_type) for p in range(start_page, end_page + 1)]
        else:
            tasks = [parse_asilmedia_page_async(session, u, min_rating=min_rating) for u in urls]
        pages_results = await asyncio.gather(*tasks, return_exceptions=True)

    all_items = []
    for p_offset, res in enumerate(pages_results):
        actual_page = start_page + p_offset
        if isinstance(res, Exception):
            print(f"⚠️ Sahifa {actual_page} yuklanmadi: {res}")
            continue
        all_items.extend(res)
        print(f"📄 Sahifa {actual_page}: {len(res)} ta mos element yuklandi.")

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
    next_page = sm.advance_page(source, max_pages, from_page=start_page)
    print(f"\n✅ Yig'ish yakunlandi! Jami topilgan: {len(all_items)}, Yangi qo'shilgan: {total_added}, Bazadagi dublikatlar: {duplicates_detected}")
    print(f"📑 [STATE] {source.upper()} keyingi sahifa: {next_page}")
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
        if target == "kawaii":
            target_source = "kawaii"
        elif "asil" in target.lower():
            target_source = "asilmedia"
        else:
            target_source = "uzmovi"
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
                except FloodWaitError as fe:
                    wait_m = round(fe.seconds / 60, 1)
                    print(f"\n🛑 Telegram FloodWait: {fe.seconds} soniya ({wait_m} daqiqa) kutish talab qilinadi. Akkaunt xavfsizligi uchun navbat to'xtatildi!", flush=True)
                    try:
                        StateManager().set_bot_status("flood_wait")
                    except Exception:
                        pass
                    break
                except Exception as ex:
                    print(f"❌ Kod #{c} da kutilmagan xatolik: {ex}")
                    success = False

                if success:
                    print(f"✅ Kod #{c} muvaffaqiyatli saqlandi, Topic ochildi va Websaytga ulandi.")
                    for qid in [f"asilmedia_{c}", f"uzmovi_{c}", f"kawaii_{c}"]:
                        if qid in qm.items:
                            qm.update_status(qid, "completed")
                else:
                    print(f"⚠️ Kod #{c} yuklab bo'lmadi yoki o'tkazib yuborildi.")
                
                if idx < len(code_list):
                    print("⏳ 4 soniya tanaffus...")
                    await asyncio.sleep(4.0)
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
                    media_type=item.media_type,
                    episodes_count=item.episodes_count
                )
                if dup.is_duplicate:
                    qm.update_status(item.id, "already_exists", error_message=f"Bazada mavjud: {dup.reason} (ID: {dup.matched_id})")
                    print(f"⏭️ [{media_label}] '{item.title}' bazada mavjud: [{dup.matched_type}] '{dup.matched_title}' (ID: {dup.matched_id}). O'tkazib yuborildi.")
                    continue
                elif getattr(dup, "is_incomplete", False):
                    print(f"🔄 [{media_label}] '{item.title}' bazada mavjud ammo qismlari to'liq emas (ID: {dup.matched_id}). Mavjud mavzuga ulanib qismlar yuklanmoqda...")

                print(f"\n[{downloaded_count + 1}/{limit}] 🚀 [{media_label}] '{item.title}' ({item.year or 'Noma\'lum'}) bo'yicha sikl boshlanmoqda...")
                qm.update_status(item.id, "in_progress")
                
                try:
                    success = await pipeline.run_item(item, target_bot=bot_username)
                except FloodWaitError as fe:
                    wait_m = round(fe.seconds / 60, 1)
                    print(f"\n🛑 Telegram FloodWait: {fe.seconds} soniya ({wait_m} daqiqa) kutish talab qilinadi. Akkaunt xavfsizligi uchun navbat to'xtatildi!", flush=True)
                    qm.update_status(item.id, "failed", error_message=f"Telegram FloodWait ({fe.seconds}s)")
                    try:
                        StateManager().set_bot_status("flood_wait")
                    except Exception:
                        pass
                    break
                except Exception as ex:
                    print(f"❌ '{item.title}' yuklashda kutilmagan xatolik: {ex}")
                    qm.update_status(item.id, "failed", error_message=f"Kutilmagan xatolik: {ex}")
                    success = False

                if success:
                    qm.update_status(item.id, "completed")
                    downloaded_count += 1
                    print(f"✅ Muvaffaqiyatli saqlandi, Topic ochildi va Websaytga ulandi: {item.title}")
                else:
                    qm.load()
                    fresh = qm.items.get(item.id)
                    if fresh and fresh.status in ("already_exists", "needs_review"):
                        print(f"⏭️ {item.title}: {fresh.error_message or fresh.status}")
                    elif not (fresh and fresh.status == "failed"):
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
                    print("⏳ 4 soniya tanaffus...")
                    await asyncio.sleep(4.0)

    finally:
        await client.disconnect()
        try:
            StateManager().set_bot_status("idle")
            StateManager().update(autopilot_active=False)
        except Exception:
            pass
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
    sm = StateManager()
    print("\n📊 Navbat statistikasi:")
    for k, v in qm.stats().items():
        print(f"  • {k}: {v}")
    st = sm.get_state()
    print("\n📑 Checkpoint holati:")
    print(f"  • Uzmovi joriy sahifa: {st.get('uzmovi_current_page', 1)} / {st.get('uzmovi_total_pages', 350)}")
    print(f"  • Asilmedia joriy sahifa: {st.get('asilmedia_current_page', 1)} / {st.get('asilmedia_total_pages', 400)}")
    print(f"  • Minimal reyting: {st.get('min_rating', 6.0)}+")
    print()

def cmd_retry_failed():
    qm = QueueManager()
    count = 0
    for item_id, item in list(qm.items.items()):
        if item.status == "failed":
            item.status = "pending"
            item.error_message = None
            count += 1
    qm.save()
    print(f"\n♻️ {count} ta muvaffaqiyatsiz (failed) element 'kutilmoqda' holatiga qaytarildi.")
    print(f"📊 Yangilangan navbat statistikasi: {qm.stats()}\n")

async def cmd_autopilot(source: str = "all", pages: int = None, limit: int = None, media_type: str = "all", min_rating: float = None):
    qm = QueueManager()
    sm = StateManager()
    checker = DuplicateChecker()
    await checker.refresh_cache(force=True)

    if min_rating is None:
        min_rating = float(sm.get_state().get("min_rating", 6.0))

    sources_to_run = ["uzmovi", "asilmedia", "kawaii"] if source in ("all", "both") else [source]
    src_title = "BARCHASI (UZMOVI, ASILMEDIA & KAWAII)" if len(sources_to_run) > 1 else source.upper()

    print(f"\n" + "="*60, flush=True)
    print(f"🚀 TO'LIQ AVTONOM AVTOPILOT ISHGA TUSHIRILMOQDA", flush=True)
    print(f"   Manba: {src_title}", flush=True)
    print(f"   Minimal reyting: {min_rating}+", flush=True)
    print(f"   Media turi: {media_type.upper()}", flush=True)
    if pages and limit:
        print(f"   Rejim: Cheklangan ({pages} ta sahifa, {limit} ta yuklash)", flush=True)
    else:
        print(f"   Rejim: Cheksiz Avtonom (Xotiradan to'xtovsiz davom etish)", flush=True)
    print("="*60 + "\n", flush=True)

    # 1. Agar foydalanuvchi qat'iy cheklangan pages/limit bergan bo'lsa (parametrli rejim):
    if pages and limit:
        for s in sources_to_run:
            target_bot = "kawaii" if s == "kawaii" else ("asilmedia" if "asil" in s.lower() else "uzmovi")
            await cmd_parse(source=s, max_pages=pages, media_type=media_type, min_rating=min_rating)
            await cmd_download(limit=limit, target=target_bot, media_type=media_type)
        print("\n🏁 Avtopilot sikli yakunlandi!", flush=True)
        return

    # 2. Cheksiz rejimda: agar oldingi sessiyadan qolib ketgan kutilayotgan filmlar bo'lsa, avval ularni yuklaymiz
    for s in sources_to_run:
        target_bot = "kawaii" if s == "kawaii" else ("asilmedia" if "asil" in s.lower() else "uzmovi")
        old_pending = qm.get_pending(limit=25, source=s, media_type=None if media_type == "all" else media_type)
        if old_pending:
            print(f"📋 [{s.upper()}] Oldingi navbatda kutilayotgan {len(old_pending)} ta film yuklanmoqda...", flush=True)
            await cmd_download(limit=len(old_pending), target=target_bot, media_type=media_type)

    # 3. CHEKSIZ AVTONOM REJIM (Foydalanuvchi xohlagan yangi uzluksiz avtopilot)
    cycle_count = 0
    while True:
        cycle_count += 1
        any_pages_left = False

        for s in sources_to_run:
            st = sm.get_state()
            cur_page = int(st.get(f"{s.lower()}_current_page", 1))
            total_pages = int(st.get(f"{s.lower()}_total_pages", 400))

            if cur_page > total_pages:
                print(f"ℹ️ [{s.upper()}] Saytdagi barcha sahifalar ({total_pages}) to'liq ko'rib chiqilgan.", flush=True)
                continue

            any_pages_left = True
            print(f"\n------------------------------------------------------------", flush=True)
            print(f"📄 AVTOPILOT SIKLI #{cycle_count}: [{s.upper()}] {cur_page}-sahifa skanerlanmoqda...", flush=True)
            print(f"------------------------------------------------------------", flush=True)

            # Aynan bitta sahifani tahlil qilamiz va checkpointni 1 ga oshiramiz
            await cmd_parse(
                source=s,
                max_pages=1,
                start_page=cur_page,
                min_rating=min_rating,
                media_type=media_type
            )

            # Yangi saralangan pending filmlarni yuklaymiz
            target_bot = "kawaii" if s == "kawaii" else ("asilmedia" if "asil" in s.lower() else "uzmovi")
            pending = qm.get_pending(limit=25, source=s, media_type=None if media_type == "all" else media_type)
            if pending:
                print(f"🚀 [{s.upper()}] {len(pending)} ta yangi saralangan film Telegram orqali yuklanmoqda...", flush=True)
                await cmd_download(limit=len(pending), target=target_bot, media_type=media_type)
            else:
                print(f"ℹ️ [{s.upper()}] {cur_page}-sahifada yangi film yo'q (bazada mavjud yoki reyting past).", flush=True)

            print("⏳ 3 soniya tanaffus (navbatdagi qadam oldidan)...", flush=True)
            await asyncio.sleep(3.0)

        if not any_pages_left:
            print("\n🎉 Barcha manbalardagi barcha sahifalar to'liq yakunlandi!", flush=True)
            break

def main():
    parser = argparse.ArgumentParser(description="Kinochi Avtomatlashtirilgan Parser & Grabber")
    parser.add_argument("--parse", action="store_true", help="Saytdan kinolar ro'yxatini yig'ish")
    parser.add_argument("--source", type=str, default="all", choices=["uzmovi", "asilmedia", "kawaii", "all"], help="Sayt manbasi (uzmovi, asilmedia, kawaii yoki all)")
    parser.add_argument("--pages", type=int, default=None, help="Yig'iladigan sahifalar soni")
    parser.add_argument("--start-page", type=int, default=None, help="Boshlang'ich sahifa (agar berilmasa, state.json dan olinadi)")
    parser.add_argument("--min-rating", type=float, default=None, help="Minimal reyting (default: 6.0)")
    parser.add_argument("--download", action="store_true", help="Navbatdagi kinolarni Telegram botdan yuklab olish")
    parser.add_argument("--target", type=str, default="uzmovi", choices=["uzmovi", "asilmedia", "kawaii"], help="Maqsadli bot (uzmovi, asilmedia yoki kawaii)")
    parser.add_argument("--limit", type=int, default=5, help="Yuklanadigan kinolar soni (default: 5)")
    parser.add_argument("--codes", type=str, default=None, help="Muayyan film kodlari (masalan: 15 yoki 1-5 yoki 10,15,20)")
    parser.add_argument("--clean-duplicates", action="store_true", help="Navbatdagi mavjud bazadagi dublikatlarni tozalash")
    parser.add_argument("--retry-failed", action="store_true", help="Xatolik bergan barcha filmlarni qayta navbatga qo'yish")
    parser.add_argument("--autopilot", action="store_true", help="Bir martalik yoki uzluksiz to'liq avtopilot: Parse + Download")
    parser.add_argument("--media-type", type=str, default="all", choices=["all", "movie", "series"], help="Media turi (all, movie yoki series)")
    parser.add_argument("--item-id", type=str, default=None, help="Navbatdagi aniq bitta element ID si (masalan: asilmedia_18509)")
    parser.add_argument("--stats", action="store_true", help="Navbat holatini ko'rish")

    args = parser.parse_args()

    if args.stats:
        cmd_stats()
    elif args.clean_duplicates:
        asyncio.run(cmd_clean_duplicates())
    elif args.retry_failed:
        cmd_retry_failed()
    elif args.autopilot:
        asyncio.run(cmd_autopilot(args.source, args.pages, args.limit, args.media_type, args.min_rating))
    elif args.parse:
        asyncio.run(cmd_parse(args.source, args.pages or 3, args.media_type, args.start_page, args.min_rating))
    elif args.download:
        asyncio.run(cmd_download(args.limit, args.target, args.codes, args.media_type, args.item_id))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

