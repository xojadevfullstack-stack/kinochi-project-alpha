import asyncio
import os
import sys
from sqlalchemy import text
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

load_dotenv(os.path.join(BASE_DIR, ".env.local"))
load_dotenv(os.path.join(BASE_DIR, "backend", ".env"))
load_dotenv(os.path.join(BASE_DIR, ".env"))

from app.infrastructure.db.session import async_session_factory

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# S1 1..20 -> 1583..1602
S1_MAPPING = {ep: 1582 + ep for ep in range(1, 21)}

# S2 1..21 -> 1603..1623
S2_MAPPING = {ep: 1602 + ep for ep in range(1, 22)}

async def fix_bleach():
    async with async_session_factory() as session:
        # 1. Get Bleach series
        res = await session.execute(text("SELECT id FROM series WHERE id = 1032"))
        series_row = res.fetchone()
        if not series_row:
            print("Bleach series 1032 not found!")
            return
        series_id = series_row[0]
        print(f"Fixing Bleach series ID: {series_id}")

        # 2. Update Season 1
        res_s1 = await session.execute(text("SELECT id FROM seasons WHERE series_id = :sid AND season_number = 1"), {"sid": series_id})
        s1_row = res_s1.fetchone()
        if s1_row:
            s1_id = s1_row[0]
            print(f"Season 1 ID: {s1_id}")
            for ep_num, st_id in S1_MAPPING.items():
                ep_res = await session.execute(
                    text("SELECT id FROM episodes WHERE season_id = :s1_id AND episode_number = :ep_num"),
                    {"s1_id": s1_id, "ep_num": ep_num}
                )
                ep = ep_res.fetchone()
                if ep:
                    ep_id = ep[0]
                    # Update translation
                    await session.execute(
                        text("""
                            UPDATE episode_translations 
                            SET storage_channel_message_id = :st_id, telegram_file_id = NULL
                            WHERE episode_id = :ep_id
                        """),
                        {"st_id": st_id, "ep_id": ep_id}
                    )
                    print(f"  S1E{ep_num} (ep_id={ep_id}) -> storage_msg_id={st_id}")

        # 3. Update Season 2
        res_s2 = await session.execute(text("SELECT id FROM seasons WHERE series_id = :sid AND season_number = 2"), {"sid": series_id})
        s2_row = res_s2.fetchone()
        if s2_row:
            s2_id = s2_row[0]
            print(f"Season 2 ID: {s2_id}")
            for ep_num, st_id in S2_MAPPING.items():
                ep_res = await session.execute(
                    text("SELECT id FROM episodes WHERE season_id = :s2_id AND episode_number = :ep_num"),
                    {"s2_id": s2_id, "ep_num": ep_num}
                )
                ep = ep_res.fetchone()
                if ep:
                    ep_id = ep[0]
                    await session.execute(
                        text("""
                            UPDATE episode_translations 
                            SET storage_channel_message_id = :st_id, telegram_file_id = NULL
                            WHERE episode_id = :ep_id
                        """),
                        {"st_id": st_id, "ep_id": ep_id}
                    )
                    print(f"  S2E{ep_num} (ep_id={ep_id}) -> storage_msg_id={st_id}")

        await session.commit()
        print("\nAll Bleach episodes successfully updated and committed to DB!")

if __name__ == "__main__":
    asyncio.run(fix_bleach())
