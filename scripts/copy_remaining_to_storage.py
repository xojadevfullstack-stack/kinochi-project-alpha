import asyncio
import os
import sys
from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv

BASE_DIR = r"c:\Users\Администратор\Desktop\kino bot project\kinochi project"
load_dotenv(os.path.join(BASE_DIR, ".env.local"))
load_dotenv(os.path.join(BASE_DIR, ".env"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

async def main():
    api_id = int(os.getenv("TELEGRAM_API_ID"))
    api_hash = os.getenv("TELEGRAM_API_HASH")
    session_str = os.getenv("TELEGRAM_STRING_SESSION")
    client = TelegramClient(StringSession(session_str), api_id, api_hash)
    await client.connect()

    storage_id = -1003762157591
    source_1 = -1003926001543

    # 1. Full Interstellar (msg 27519)
    print("Fetching msg 27519 (Full Interstellar)...")
    m27519 = await client.get_messages(source_1, ids=27519)
    if m27519:
        cap = (
            "🎬 Interstellar (2014)\n"
            "🔢 Kodi: R3VRY5\n"
            "🇺🇿 Tili: O'zbekcha\n"
            "⭐ IMDb: 8.7/10\n"
            "🎭 Janr: Ilmiy-fantastika, Drama, Sarguzasht"
        )
        sent1 = await client.send_file(storage_id, m27519.media, caption=cap)
        print(f"Interstellar full sent to storage! Msg ID: {sent1.id}")
        interstellar_st_id = sent1.id
    else:
        print("Error: msg 27519 not found")
        interstellar_st_id = None

    # 2. Titanik 1-qism (msg 27740)
    print("Fetching msg 27740 (Titanik 1-qism)...")
    m27740 = await client.get_messages(source_1, ids=27740)
    if m27740:
        cap = (
            "🎬 Titanik (1-qism) (1997)\n"
            "🔢 Kodi: c53231e5\n"
            "🇺🇿 Tili: O'zbek tilida\n"
            "⭐ IMDb: 7.9/10\n"
            "🎭 Janr: Drama, Romantika"
        )
        sent2 = await client.send_file(storage_id, m27740.media, caption=cap)
        print(f"Titanik 1-qism sent to storage! Msg ID: {sent2.id}")
        titanic1_st_id = sent2.id
    else:
        print("Error: msg 27740 not found")
        titanic1_st_id = None

    await client.disconnect()

    # Now update DB translations
    from app.infrastructure.db.session import async_session_factory
    from sqlalchemy import text
    async with async_session_factory() as session:
        # Update Movie 808 (Interstellar Full)
        if interstellar_st_id:
            await session.execute(text("""
                UPDATE movie_translations 
                SET storage_channel_message_id = :st_id, telegram_file_id = NULL
                WHERE movie_id = 808
            """), {"st_id": interstellar_st_id})
            print(f"Updated Movie 808 translation to storage {interstellar_st_id}")

        # Update Movie 966 (Titanik 1-qism)
        if titanic1_st_id:
            await session.execute(text("""
                UPDATE movie_translations 
                SET storage_channel_message_id = :st_id, telegram_file_id = NULL
                WHERE movie_id = 966
            """), {"st_id": titanic1_st_id})
            print(f"Updated Movie 966 translation to storage {titanic1_st_id}")

        # Update Movie 1003 (Titanik 2-qism -> 1625)
        await session.execute(text("""
            UPDATE movie_translations 
            SET storage_channel_message_id = 1625, telegram_file_id = NULL
            WHERE movie_id = 1003
        """))
        print("Updated Movie 1003 to storage 1625")

        # Update Movie 1004 (LOTR 1 part 1 -> 1626)
        await session.execute(text("""
            UPDATE movie_translations 
            SET storage_channel_message_id = 1626, telegram_file_id = NULL
            WHERE movie_id = 1004
        """))
        print("Updated Movie 1004 to storage 1626")

        # Update Movie 1005 (LOTR 1 part 2 -> 1627)
        await session.execute(text("""
            UPDATE movie_translations 
            SET storage_channel_message_id = 1627, telegram_file_id = NULL
            WHERE movie_id = 1005
        """))
        print("Updated Movie 1005 to storage 1627")

        # Update Movie 1006 (LOTR 2 part 1 -> 1629)
        await session.execute(text("""
            UPDATE movie_translations 
            SET storage_channel_message_id = 1629, telegram_file_id = NULL
            WHERE movie_id = 1006
        """))
        print("Updated Movie 1006 to storage 1629")

        # Update Movie 1007 (LOTR 2 part 2 -> 1631)
        await session.execute(text("""
            UPDATE movie_translations 
            SET storage_channel_message_id = 1631, telegram_file_id = NULL
            WHERE movie_id = 1007
        """))
        print("Updated Movie 1007 to storage 1631")

        # Update Movie 1008 (Interstellar part 1 -> 1634)
        await session.execute(text("""
            UPDATE movie_translations 
            SET storage_channel_message_id = 1634, telegram_file_id = NULL
            WHERE movie_id = 1008
        """))
        print("Updated Movie 1008 to storage 1634")

        # Update Movie 1009 (Interstellar part 2 -> 1636)
        await session.execute(text("""
            UPDATE movie_translations 
            SET storage_channel_message_id = 1636, telegram_file_id = NULL
            WHERE movie_id = 1009
        """))
        print("Updated Movie 1009 to storage 1636")

        await session.commit()
        print("All movie translations committed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
