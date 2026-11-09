import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath("backend"))
sys.path.insert(0, os.path.abspath("scraper"))

from app.infrastructure.db.session import async_session_factory
from sqlalchemy import text
import config
from telethon_moderator_pipeline import create_telethon_client

async def main():
    print("=== K6 & K7 AUDIT: KAIJU NO. 8 & S_1024 ===")
    
    # 1. Database Inspection for Series 1026
    async with async_session_factory() as session:
        print("\n--- 1. Series 1026 (Kaiju No. 8) Episodes in DB ---")
        res1026 = await session.execute(text("""
            SELECT e.id, e.episode_number, e.code, e.display_code, e.title, e.duration,
                   t.id as trans_id, t.storage_channel_message_id, t.telegram_file_id
            FROM episodes e
            LEFT JOIN episode_translations t ON e.id = t.episode_id
            WHERE e.season_id = 1307
            ORDER BY e.episode_number
        """))
        episodes_1026 = res1026.fetchall()
        for ep in episodes_1026:
            print(f"  Ep {ep.episode_number:02d} (id={ep.id}, code={ep.code}, disp={ep.display_code}, title='{ep.title}', dur={ep.duration}): msg_id={ep.storage_channel_message_id}, file_id={ep.telegram_file_id[:16] if ep.telegram_file_id else None}")

        # Check orphaned records for series 1026
        print("\n--- 2. Orphaned Records Check for Deleted Episodes (13-19, 23) ---")
        # Check if any episodes between 13 and 25 still exist in DB
        res_orph_eps = await session.execute(text("SELECT id, episode_number FROM episodes WHERE season_id = 1307 AND episode_number > 12"))
        print(f"  Episodes > 12 in season 1307: {res_orph_eps.fetchall()}")

        # Check orphaned translations
        res_orph_trans = await session.execute(text("""
            SELECT id, episode_id, storage_channel_message_id 
            FROM episode_translations 
            WHERE episode_id NOT IN (SELECT id FROM episodes)
        """))
        print(f"  Total orphaned episode_translations in entire DB: {len(res_orph_trans.fetchall())}")

        # Check watch_history
        res_orph_hist = await session.execute(text("""
            SELECT id, episode_id FROM watch_history 
            WHERE episode_id IS NOT NULL AND episode_id NOT IN (SELECT id FROM episodes)
        """))
        print(f"  Total orphaned watch_history records: {len(res_orph_hist.fetchall())}")

        # Check reports
        res_orph_rep = await session.execute(text("""
            SELECT id, episode_id FROM reports 
            WHERE episode_id IS NOT NULL AND episode_id NOT IN (SELECT id FROM episodes)
        """))
        print(f"  Total orphaned reports records: {len(res_orph_rep.fetchall())}")

        # 3. Series 1024 Check
        print("\n--- 3. Series 1024 (A Wild Last Boss Appeared) Episodes in DB ---")
        res1024 = await session.execute(text("""
            SELECT s.id as season_id, s.season_number, e.id as ep_id, e.episode_number, e.code, e.display_code, e.title,
                   t.storage_channel_message_id, t.telegram_file_id
            FROM seasons s
            LEFT JOIN episodes e ON s.id = e.season_id
            LEFT JOIN episode_translations t ON e.id = t.episode_id
            WHERE s.series_id = 1024
            ORDER BY s.season_number, e.episode_number
        """))
        for ep in res1024.fetchall():
            print(f"  S{ep.season_number} Ep {ep.episode_number} (id={ep.ep_id}, code={ep.code}, disp={ep.display_code}): msg={ep.storage_channel_message_id}")

    # 4. Telethon Storage Messages Inspection (READ-ONLY)
    print("\n--- 4. Telethon Storage Messages Inspection for Kaiju (Read-Only) ---")
    client = create_telethon_client()
    await client.connect()
    
    # Message IDs to inspect: 2733, 2699, 2700, 2701, 2702, 2734, 2703, 2713, 2714, 2715, 2704, 2705
    msg_ids = [2733, 2699, 2700, 2701, 2702, 2734, 2703, 2713, 2714, 2715, 2704, 2705]
    msgs = await client.get_messages(config.STORAGE_CHANNEL_ID, ids=msg_ids)
    
    doc_ids = {}
    for m in msgs:
        if not m:
            continue
        fname = getattr(getattr(m, "file", None), "name", None)
        size_mb = (getattr(getattr(m, "file", None), "size", 0) or 0) / (1024 * 1024)
        duration_sec = 0
        if getattr(m, "document", None) and hasattr(m.document, "attributes"):
            for attr in m.document.attributes:
                if hasattr(attr, "duration"):
                    duration_sec = attr.duration
        dur_int = int(duration_sec)
        dur_str = f"{dur_int // 60}:{dur_int % 60:02d}"
        doc_id = getattr(getattr(m, "document", None), "id", None)
        caption = (m.text or "").replace("\n", " ")[:60]
        
        if doc_id:
            doc_ids[doc_id] = doc_ids.get(doc_id, []) + [m.id]
            
        print(f"  Msg {m.id:04d}: file='{fname}' | dur={dur_str} ({dur_int}s) | size={size_mb:.1f}MB | doc_id={doc_id} | text='{caption}'")

    print("\n--- 5. Document ID Deduplication Check ---")
    for did, mids in doc_ids.items():
        if len(mids) > 1:
            print(f"  WARNING: Same document ID {did} shared by messages: {mids}")
        else:
            print(f"  Doc ID {did}: uniquely attached to msg {mids[0]}")

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
