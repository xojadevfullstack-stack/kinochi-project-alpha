"""
IngestService — PostgreSQL ingest_items navbati va holatlar mashinasi servisi.
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import select, update, delete, func, or_
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models.ingest_item import (
    IngestItemModel,
    INGEST_STATUSES,
    ALLOWED_STATUS_TRANSITIONS,
    validate_status_transition,
)


class IngestService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_batch(self, items: List[Dict[str, Any]]) -> int:
        """
        Elementlarni ingest_items jadvaliga idempotent tarzda qo'shadi:
        INSERT .. ON CONFLICT (source, source_id) DO NOTHING.
        Qaytaradi: haqiqatda qo'shilgan yangi yozuvlar soni.
        """
        if not items:
            return 0

        rows = []
        seen_keys = set()
        for raw in items:
            src = str(raw.get("source") or "").strip().lower()
            src_id = str(raw.get("source_id") or "").strip()
            if not src or not src_id:
                continue
            if (src, src_id) in seen_keys:
                continue
            seen_keys.add((src, src_id))

            status = str(raw.get("status") or "queued").strip()
            if status == "pending":
                status = "queued"
            elif status == "completed":
                status = "published"
            if status not in INGEST_STATUSES:
                status = "queued"

            rows.append({
                "source": src,
                "source_id": src_id,
                "media_type": str(raw.get("media_type") or "movie"),
                "title": str(raw.get("title") or ""),
                "original_title": raw.get("original_title"),
                "year": int(raw["year"]) if raw.get("year") is not None and str(raw.get("year")).isdigit() else None,
                "url": raw.get("url"),
                "poster_url": raw.get("poster_url"),
                "tmdb_id": int(raw["tmdb_id"]) if raw.get("tmdb_id") is not None else None,
                "payload": raw.get("payload") or {},
                "status": status,
                "reason": raw.get("reason") or raw.get("error_message"),
                "attempts": int(raw.get("attempts") or 0),
                "priority": int(raw.get("priority") or 0),
                "topic_chat_id": raw.get("topic_chat_id"),
                "topic_id": raw.get("topic_id"),
                "storage_message_id": raw.get("storage_message_id"),
                "media_id": raw.get("media_id"),
            })

        if not rows:
            return 0

        dialect_name = self.session.bind.dialect.name if self.session.bind else "postgresql"
        if dialect_name == "sqlite":
            stmt = sqlite_insert(IngestItemModel).values(rows).on_conflict_do_nothing(
                index_elements=["source", "source_id"]
            )
        else:
            stmt = pg_insert(IngestItemModel).values(rows).on_conflict_do_nothing(
                index_elements=["source", "source_id"]
            )

        res = await self.session.execute(stmt)
        await self.session.commit()
        return int(res.rowcount or 0)

    async def claim_next(
        self,
        worker_id: str = "worker",
        source: Optional[str] = None,
        media_type: Optional[str] = None,
        item_key: Optional[Tuple[str, str]] = None,
    ) -> Optional[IngestItemModel]:
        """
        Navbatdan bitta elementni atomik ravishda oladi (FOR UPDATE SKIP LOCKED)
        va statusini queued -> in_progress ga o'tkazadi.
        """
        stmt = select(IngestItemModel)
        if item_key:
            src, src_id = item_key
            stmt = stmt.where(
                IngestItemModel.source == src.lower(),
                IngestItemModel.source_id == str(src_id),
            )
        else:
            stmt = stmt.where(IngestItemModel.status == "queued")
            if source and source != "all":
                stmt = stmt.where(IngestItemModel.source == source.lower())
            if media_type and media_type != "all":
                stmt = stmt.where(IngestItemModel.media_type == media_type.lower())

        stmt = stmt.order_by(
            IngestItemModel.priority.desc(),
            IngestItemModel.id.asc(),
        ).limit(1)

        dialect_name = self.session.bind.dialect.name if self.session.bind else "postgresql"
        if dialect_name != "sqlite":
            stmt = stmt.with_for_update(skip_locked=True)

        res = await self.session.execute(stmt)
        item = res.scalar_one_or_none()
        if not item:
            return None

        validate_status_transition(item.status, "in_progress")
        item.status = "in_progress"
        item.locked_at = datetime.now(timezone.utc)
        item.locked_by = worker_id
        item.attempts = (item.attempts or 0) + 1
        item.updated_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(item)
        return item

    async def set_status(
        self,
        item_id_or_key: int | Tuple[str, str],
        new_status: str,
        reason: Optional[str] = None,
        topic_chat_id: Optional[int] = None,
        topic_id: Optional[int] = None,
        storage_message_id: Optional[int] = None,
        media_id: Optional[int] = None,
        payload_update: Optional[Dict[str, Any]] = None,
    ) -> Optional[IngestItemModel]:
        """
        Element statusini ALLOWED_STATUS_TRANSITIONS bo'yicha tekshirib yangilaydi.
        """
        if new_status == "pending":
            new_status = "queued"
        elif new_status == "completed":
            new_status = "published"

        if isinstance(item_id_or_key, tuple):
            src, src_id = item_id_or_key
            stmt = select(IngestItemModel).where(
                IngestItemModel.source == src.lower(),
                IngestItemModel.source_id == str(src_id),
            )
        else:
            stmt = select(IngestItemModel).where(IngestItemModel.id == int(item_id_or_key))

        res = await self.session.execute(stmt)
        item = res.scalar_one_or_none()
        if not item:
            return None

        validate_status_transition(item.status, new_status)
        item.status = new_status
        if reason is not None:
            item.reason = reason
        elif new_status in ("queued", "in_progress", "published"):
            item.reason = None

        if new_status != "in_progress":
            item.locked_at = None
            item.locked_by = None

        if topic_chat_id is not None:
            item.topic_chat_id = topic_chat_id
        if topic_id is not None:
            item.topic_id = topic_id
        if storage_message_id is not None:
            item.storage_message_id = storage_message_id
        if media_id is not None:
            item.media_id = media_id
        if payload_update:
            merged = dict(item.payload or {})
            merged.update(payload_update)
            item.payload = merged

        item.updated_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(item)
        return item

    async def recover_stale(self, max_age_seconds: int = 1800) -> int:
        """
        in_progress holatida locked_at > 30 daqiqa qolib ketgan elementlarni queued ga qaytaradi.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=max_age_seconds)
        stmt = (
            update(IngestItemModel)
            .where(
                IngestItemModel.status == "in_progress",
                or_(
                    IngestItemModel.locked_at.is_(None),
                    IngestItemModel.locked_at <= cutoff,
                ),
            )
            .values(
                status="queued",
                locked_at=None,
                locked_by=None,
                updated_at=datetime.now(timezone.utc),
            )
        )
        res = await self.session.execute(stmt)
        await self.session.commit()
        return int(res.rowcount or 0)

    async def get_stats(self) -> Dict[str, Any]:
        stmt = select(
            IngestItemModel.status,
            func.count(IngestItemModel.id),
        ).group_by(IngestItemModel.status)
        res = await self.session.execute(stmt)
        by_status = {row[0]: int(row[1]) for row in res.all()}

        src_stmt = select(
            IngestItemModel.source,
            IngestItemModel.status,
            func.count(IngestItemModel.id),
        ).group_by(IngestItemModel.source, IngestItemModel.status)
        src_res = await self.session.execute(src_stmt)
        by_source: Dict[str, Dict[str, int]] = {}
        for src, st, cnt in src_res.all():
            by_source.setdefault(src, {})[st] = int(cnt)

        total = sum(by_status.values())
        return {
            "total": total,
            "queued": by_status.get("queued", 0),
            "pending": by_status.get("queued", 0),
            "in_progress": by_status.get("in_progress", 0),
            "published": by_status.get("published", 0),
            "completed": by_status.get("published", 0),
            "already_exists": by_status.get("already_exists", 0),
            "failed": by_status.get("failed", 0),
            "needs_review": by_status.get("needs_review", 0),
            "rejected": by_status.get("rejected", 0),
            "blacklisted": by_status.get("blacklisted", 0),
            "discovered": by_status.get("discovered", 0),
            "by_status": by_status,
            "by_source": by_source,
        }
