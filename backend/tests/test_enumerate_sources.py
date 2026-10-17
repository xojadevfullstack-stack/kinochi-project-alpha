import io
import csv
import sys
from pathlib import Path
from datetime import datetime, timezone
import pytest

# docs/INCIDENT_2026-10-17 katalogini sys.path ga qo'shish
DOCS_DIR = Path(__file__).resolve().parent.parent.parent / "docs" / "INCIDENT_2026-10-17"
if str(DOCS_DIR) not in sys.path:
    sys.path.insert(0, str(DOCS_DIR))

from enumerate_sources import (
    format_topic_record,
    format_channel_record,
    build_sources_csv,
    CSV_FIELDNAMES,
)


class FakeTopic:
    """Telethon ForumTopic obyektining sodda feyk nusxasi."""
    def __init__(self, topic_id: int, title: str, messages_count: int, date: datetime):
        self.id = topic_id
        self.title = title
        self.messages_count = messages_count
        self.date = date


def test_format_topic_record_with_creation_date():
    """Forum topic yaratilgan sana (creation_date) bilan to'g'ri shakllantiriladi."""
    dt = datetime(2026, 10, 15, 12, 30, 45, tzinfo=timezone.utc)
    fake_topic = FakeTopic(topic_id=777, title="Qora Sevgi", messages_count=45, date=dt)

    record = format_topic_record(
        supergroup_id=-1003847632555,
        topic=fake_topic,
        first_date="2026-10-15T12:35:00",
        last_date="2026-10-16T18:00:00"
    )

    assert record["source_type"] == "supergroup_topic"
    assert record["chat_id"] == -1003847632555
    assert record["topic_id"] == 777
    assert record["title"] == "Qora Sevgi"
    assert record["messages_count"] == 45
    assert record["creation_date"] == dt.isoformat()
    assert record["first_date"] == "2026-10-15T12:35:00"
    assert record["last_date"] == "2026-10-16T18:00:00"


def test_format_topic_record_without_date():
    """Topic sanasi yo'q bo'lsa 'N/A' qiymati qo'yiladi."""
    class FakeTopicNoDate:
        id = 101
        title = "Nomsiz Topic"
        messages_count = 5
        date = None

    record = format_topic_record(supergroup_id=-100123, topic=FakeTopicNoDate())
    assert record["creation_date"] == "N/A"
    assert record["first_date"] == "N/A"
    assert record["last_date"] == "N/A"


def test_format_channel_record_for_old_storage():
    """Eski storage kanal uchun to'g'ri lug'at shakllantiriladi."""
    record = format_channel_record(
        chat_id=-100999888777,
        source_type="old_storage_channel",
        title="Old Storage Channel",
        messages_count=12500
    )

    assert record["source_type"] == "old_storage_channel"
    assert record["chat_id"] == -100999888777
    assert record["topic_id"] == "N/A"
    assert record["messages_count"] == 12500
    assert record["creation_date"] == "N/A"


def test_build_sources_csv_with_fakes():
    """CSV builder barcha yozuvlarni sarlavha va to'g'ri tartibda yozadi."""
    records = [
        {
            "source_type": "supergroup_topic",
            "chat_id": -100111,
            "topic_id": 1,
            "title": "Topic A",
            "messages_count": 10,
            "creation_date": "2026-10-01T00:00:00",
            "first_date": "2026-10-01T01:00:00",
            "last_date": "2026-10-02T02:00:00",
        },
        {
            "source_type": "old_storage_channel",
            "chat_id": -100222,
            "topic_id": "N/A",
            "title": "Old Storage Channel",
            "messages_count": 500,
            "creation_date": "N/A",
            "first_date": "N/A",
            "last_date": "N/A",
        }
    ]

    buffer = io.StringIO()
    build_sources_csv(records, buffer)

    buffer.seek(0)
    reader = csv.DictReader(buffer)

    assert reader.fieldnames == CSV_FIELDNAMES
    rows = list(reader)
    assert len(rows) == 2
    assert rows[0]["title"] == "Topic A"
    assert rows[0]["creation_date"] == "2026-10-01T00:00:00"
    assert rows[1]["source_type"] == "old_storage_channel"
    assert rows[1]["messages_count"] == "500"


def test_script_contains_no_hardcoded_secrets():
    """Skript matnida hech qanday maxfiy token yoki session string qattiq kodlanmagan."""
    script_path = DOCS_DIR / "enumerate_sources.py"
    content = script_path.read_text(encoding="utf-8")

    # API kalitlar yoki sessionlar faqat os.environ orqali olinishini tekshirish
    assert 'os.environ.get("TELEGRAM_API_ID"' in content
    assert 'os.environ.get("TELEGRAM_API_HASH"' in content
    assert 'os.environ.get("TELEGRAM_STRING_SESSION"' in content
    assert 'os.environ.get("OLD_STORAGE_CHANNEL_ID"' in content

    # Mutlaqo xabar yuborish yoki o'chirish metodlari chaqirilmasligi shart (Read-only)
    assert "send_message(" not in content
    assert "forward_messages(" not in content
    assert "delete_messages(" not in content
    assert "edit_message(" not in content
