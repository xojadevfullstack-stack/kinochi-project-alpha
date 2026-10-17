"""
enumerate_sources.py — Read-only Telegram Manbalarini Ro'yxatga Olish Skripti (Forensic Tool).

DIQQAT: Ushbu skript FAQAT O'QISH (READ-ONLY) rejimida ishlaydi.
Hech qanday xabar yubormaydi, o'chirmaydi, tahrirlamaydi yoki forward qilmaydi.
Telegram FloodWait holatida avtomatik kutadi.

Qo'llash bo'yicha yo'riqnoma:
1. Muhit o'zgaruvchilarini o'rnating:
   $env:TELEGRAM_API_ID = "123456"
   $env:TELEGRAM_API_HASH = "abcdef..."
   $env:TELEGRAM_STRING_SESSION = "1ApWap..."
   $env:AUTO_TOPIC_CHAT_ID = "-1003847632555"
   $env:STORAGE_CHANNEL_ID = "-1003762157591"
   $env:OLD_STORAGE_CHANNEL_ID = "-1001234567890"

2. Ishga tushirish (faqat operator ruxsati bilan):
   python docs/INCIDENT_2026-10-17/enumerate_sources.py --output sources_audit.csv
"""

import os
import sys
import csv
import asyncio
import logging
from typing import Any, List, Dict
from datetime import datetime

try:
    from telethon import TelegramClient
    from telethon.sessions import StringSession
    from telethon.errors import FloodWaitError
    from telethon.tl.functions.channels import GetForumTopicsRequest
    from telethon.tl.functions.messages import GetHistoryRequest
except ImportError:
    TelegramClient = None

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("enumerate_sources")

CSV_FIELDNAMES = [
    "source_type",
    "chat_id",
    "topic_id",
    "title",
    "messages_count",
    "creation_date",
    "first_date",
    "last_date",
]


def format_topic_record(
    supergroup_id: int,
    topic: Any,
    first_date: str = "N/A",
    last_date: str = "N/A",
) -> Dict[str, Any]:
    """Telethon forum topic obyektidan xavfsiz lug'at hosil qiladi."""
    t_id = getattr(topic, "id", "N/A")
    t_title = getattr(topic, "title", "Nomsiz")
    t_count = getattr(topic, "messages_count", 0)

    # Forum topic yaratilgan sanasi
    creation_date = "N/A"
    raw_date = getattr(topic, "date", None)
    if raw_date:
        creation_date = raw_date.isoformat() if hasattr(raw_date, "isoformat") else str(raw_date)

    return {
        "source_type": "supergroup_topic",
        "chat_id": supergroup_id,
        "topic_id": t_id,
        "title": t_title,
        "messages_count": t_count,
        "creation_date": creation_date,
        "first_date": first_date or "N/A",
        "last_date": last_date or "N/A",
    }


def format_channel_record(
    chat_id: int,
    source_type: str,
    title: str,
    messages_count: int,
) -> Dict[str, Any]:
    """Storage yoki boshqa kanal uchun xavfsiz lug'at hosil qiladi."""
    return {
        "source_type": source_type,
        "chat_id": chat_id,
        "topic_id": "N/A",
        "title": title,
        "messages_count": messages_count,
        "creation_date": "N/A",
        "first_date": "N/A",
        "last_date": "N/A",
    }


def build_sources_csv(records: List[Dict[str, Any]], output_target: Any) -> None:
    """Yozuvlarni CSV formatida faylga yoki StringIO bufferiga yozadi."""
    if isinstance(output_target, str):
        with open(output_target, "w", newline="", encoding="utf-8") as fp:
            writer = csv.DictWriter(fp, fieldnames=CSV_FIELDNAMES)
            writer.writeheader()
            writer.writerows(records)
    else:
        writer = csv.DictWriter(output_target, fieldnames=CSV_FIELDNAMES)
        writer.writeheader()
        writer.writerows(records)


async def enumerate_telegram_sources(output_csv: str = "telegram_sources_truth.csv"):
    if TelegramClient is None:
        logger.error("Telethon kutubxonasi o'rnatilmagan!")
        sys.exit(1)

    api_id = int(os.environ.get("TELEGRAM_API_ID", 0))
    api_hash = os.environ.get("TELEGRAM_API_HASH", "").strip()
    session_str = os.environ.get("TELEGRAM_STRING_SESSION", "").strip()
    supergroup_id = int(os.environ.get("AUTO_TOPIC_CHAT_ID", 0))
    storage_id = int(os.environ.get("STORAGE_CHANNEL_ID", 0))
    old_storage_id = int(os.environ.get("OLD_STORAGE_CHANNEL_ID", 0))

    if not api_id or not api_hash or not session_str:
        logger.error("TELEGRAM_API_ID, TELEGRAM_API_HASH yoki TELEGRAM_STRING_SESSION o'rnatilmagan!")
        sys.exit(1)

    client = TelegramClient(StringSession(session_str), api_id, api_hash)
    await client.connect()

    if not await client.is_user_authorized():
        logger.error("Telegram sessiyasi avtorizatsiyadan o'tmagan!")
        await client.disconnect()
        sys.exit(1)

    logger.info("Telegram mijoziga muvaffaqiyatli ulandi (READ-ONLY).")

    records = []

    # 1. Superguruh forum mavzularini (topics) ro'yxatga olish
    if supergroup_id:
        try:
            logger.info(f"Superguruh ({supergroup_id}) topiclarini olish boshlandi...")
            peer = await client.get_input_entity(supergroup_id)
            offset_date = 0
            offset_id = 0
            offset_topic = 0
            limit = 100

            while True:
                try:
                    result = await client(GetForumTopicsRequest(
                        channel=peer,
                        offset_date=offset_date,
                        offset_id=offset_id,
                        offset_topic=offset_topic,
                        limit=limit
                    ))
                except FloodWaitError as e:
                    logger.warning(f"FloodWait hit: {e.seconds}s kutish...")
                    await asyncio.sleep(e.seconds + 2)
                    continue

                topics = getattr(result, "topics", [])
                if not topics:
                    break

                for t in topics:
                    t_id = t.id

                    # Birinchi va oxirgi xabarlar sanasini olish (Read-only)
                    first_date = None
                    last_date = None
                    try:
                        msgs = await client.get_messages(peer, reply_to=t_id, limit=1)
                        if msgs:
                            last_date = msgs[0].date.isoformat()
                    except Exception:
                        pass

                    records.append(format_topic_record(
                        supergroup_id=supergroup_id,
                        topic=t,
                        first_date=first_date or "N/A",
                        last_date=last_date or "N/A"
                    ))

                logger.info(f"Yig'ildi: {len(records)} ta topic...")
                if len(topics) < limit:
                    break

                offset_topic = topics[-1].id
                offset_id = topics[-1].top_message

        except Exception as e:
            logger.error(f"Superguruh topiclarini olishda xatolik: {e}")

    # 2. Yangi storage kanal xabarlar sonini olish (STORAGE_CHANNEL_ID)
    if storage_id:
        try:
            logger.info(f"Storage kanal ({storage_id}) xabarlar sonini hisoblash...")
            storage_peer = await client.get_input_entity(storage_id)
            hist = await client(GetHistoryRequest(
                peer=storage_peer,
                offset_id=0,
                offset_date=None,
                add_offset=0,
                limit=1,
                max_id=0,
                min_id=0,
                hash=0
            ))
            total_storage_msgs = getattr(hist, "count", 0)
            records.append(format_channel_record(
                chat_id=storage_id,
                source_type="storage_channel",
                title="Storage Channel",
                messages_count=total_storage_msgs
            ))
            logger.info(f"Storage kanaldagi jami xabarlar: {total_storage_msgs}")
        except Exception as e:
            logger.error(f"Storage kanalni hisoblashda xatolik: {e}")

    # 3. Eski storage kanal xabarlar sonini olish (OLD_STORAGE_CHANNEL_ID)
    if old_storage_id:
        try:
            logger.info(f"Eski storage kanal ({old_storage_id}) xabarlar sonini hisoblash...")
            old_storage_peer = await client.get_input_entity(old_storage_id)
            old_hist = await client(GetHistoryRequest(
                peer=old_storage_peer,
                offset_id=0,
                offset_date=None,
                add_offset=0,
                limit=1,
                max_id=0,
                min_id=0,
                hash=0
            ))
            total_old_storage_msgs = getattr(old_hist, "count", 0)
            records.append(format_channel_record(
                chat_id=old_storage_id,
                source_type="old_storage_channel",
                title="Old Storage Channel",
                messages_count=total_old_storage_msgs
            ))
            logger.info(f"Eski storage kanaldagi jami xabarlar: {total_old_storage_msgs}")
        except Exception as e:
            logger.error(f"Eski storage kanalni hisoblashda xatolik: {e}")

    # CSV ga yozish
    build_sources_csv(records, output_csv)
    logger.info(f"Barcha manbalar haqiqati '{output_csv}' fayliga muvaffaqiyatli saqlandi ({len(records)} qator).")
    await client.disconnect()


if __name__ == "__main__":
    out_file = sys.argv[2] if len(sys.argv) > 2 and sys.argv[1] == "--output" else "sources_truth.csv"
    asyncio.run(enumerate_telegram_sources(out_file))
