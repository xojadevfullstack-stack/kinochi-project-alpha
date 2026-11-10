import sys
import os
import time
import asyncio
import logging
import threading
from typing import List, Dict, Optional, Tuple, Any, Callable
from dataclasses import dataclass, fields

logger = logging.getLogger(__name__)

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

_QUEUE_FIELDS = None


@dataclass
class QueueItem:
    id: str                   # Unique identifier (e.g. uzmovi_8997, asilmedia_18509)
    source: str               # "uzmovi", "asilmedia", "kinochilar", "anitoob", "animeelar"
    title: str                # Title in Uzbek (e.g. "Odisseya")
    original_title: Optional[str] = None
    year: Optional[int] = None
    media_type: str = "movie"
    url: str = ""
    poster_url: Optional[str] = None
    status: str = "queued"
    episodes_count: Optional[int] = None
    downloaded_episodes: int = 0
    error_message: Optional[str] = None
    updated_at: Optional[float] = None
    priority: int = 0
    tmdb_id: Optional[int] = None
    payload: Optional[Dict[str, Any]] = None
    source_id: Optional[str] = None
    reason: Optional[str] = None
    db_id: Optional[int] = None
    topic_chat_id: Optional[int] = None
    topic_id: Optional[int] = None
    storage_message_id: Optional[int] = None
    media_id: Optional[int] = None

    def __post_init__(self):
        if not self.source_id and self.id:
            prefix = f"{self.source}_"
            if self.id.startswith(prefix):
                self.source_id = self.id[len(prefix):]
            else:
                self.source_id = self.id
        if self.reason and not self.error_message:
            self.error_message = self.reason
        elif self.error_message and not self.reason:
            self.reason = self.error_message


def _known_fields():
    global _QUEUE_FIELDS
    if _QUEUE_FIELDS is None:
        _QUEUE_FIELDS = {f.name for f in fields(QueueItem)}
    return _QUEUE_FIELDS


def matches_media_type(item: Any, target_type: Optional[str]) -> bool:
    if not target_type or target_type == "all":
        return True

    if isinstance(item, dict):
        m_type = str(item.get("media_type") or "movie").lower().strip()
        title_low = str(item.get("title") or "").lower()
        url_low = str(item.get("url") or "").lower()
        src = str(item.get("source") or "").lower()
    else:
        m_type = str(getattr(item, "media_type", "movie") or "movie").lower().strip()
        title_low = str(getattr(item, "title", "") or "").lower()
        url_low = str(getattr(item, "url", "") or "").lower()
        src = str(getattr(item, "source", "") or "").lower()

    target = target_type.lower().strip()
    if m_type == target:
        return True

    is_anime = (
        m_type == "anime"
        or src in ("anitoob", "animeelar")
        or "anime" in title_low
        or "/anime" in url_low
    )
    is_dorama = (
        m_type == "dorama"
        or "dorama" in title_low
        or "/drama" in url_low
        or (m_type == "series" and any(k in title_low for k in ["korey", "xitoy"]))
    )
    is_multfilm = (
        m_type == "multfilm"
        or any(w in title_low for w in ["multfilm", "multik", "multserial", "animatsiya"])
        or any(w in url_low for w in ["multfilm", "multik", "multfilmlari"])
    )

    if target == "anime":
        return is_anime
    elif target == "dorama":
        return is_dorama
    elif target == "multfilm":
        return is_multfilm
    elif target == "movie":
        return m_type == "movie" and not (is_anime or is_dorama or is_multfilm)
    elif target == "series":
        return m_type == "series" and not (is_anime or is_dorama or is_multfilm)
    return False


def _normalize_status(status: Optional[str]) -> str:
    if not status:
        return "queued"
    s = str(status).strip().lower()
    if s == "pending":
        return "queued"
    if s == "completed":
        return "published"
    return s


def _model_to_queue_item(row: Any) -> QueueItem:
    payload = dict(row.payload or {})
    src = str(row.source or "")
    src_id = str(row.source_id or "")
    item_id = f"{src}_{src_id}" if src and src_id and not src_id.startswith(f"{src}_") else (src_id or str(row.id))
    updated_ts = row.updated_at.timestamp() if getattr(row, "updated_at", None) else time.time()
    reason = getattr(row, "reason", None)
    raw_status = row.status or "queued"
    if raw_status == "queued":
        status_val = "pending"
    elif raw_status == "published":
        status_val = "completed"
    else:
        status_val = raw_status
    return QueueItem(
        id=item_id,
        source=src,
        source_id=src_id,
        title=row.title or "",
        original_title=row.original_title,
        year=row.year,
        media_type=row.media_type or "movie",
        url=row.url or "",
        poster_url=row.poster_url,
        status=status_val,
        episodes_count=payload.get("episodes_count"),
        downloaded_episodes=int(payload.get("downloaded_episodes") or 0),
        error_message=reason,
        reason=reason,
        updated_at=updated_ts,
        priority=int(row.priority or 0),
        tmdb_id=row.tmdb_id,
        payload=payload,
        db_id=row.id,
        topic_chat_id=row.topic_chat_id,
        topic_id=row.topic_id,
        storage_message_id=row.storage_message_id,
        media_id=row.media_id,
    )


def _parse_item_key(item_id: str) -> Tuple[Optional[str], str]:
    raw = str(item_id or "").strip()
    for known_src in ("uzmovi", "asilmedia", "kinochilar", "anitoob", "animeelar"):
        prefix = f"{known_src}_"
        if raw.startswith(prefix):
            return known_src, raw[len(prefix):]
    if "_" in raw:
        parts = raw.split("_", 1)
        return parts[0].lower(), parts[1]
    return None, raw


def _build_item_select_stmt(item_id: str):
    from sqlalchemy import select
    from app.infrastructure.db.models.ingest_item import IngestItemModel

    raw = str(item_id or "").strip()
    src, src_id = _parse_item_key(raw)
    if raw.isdigit():
        return select(IngestItemModel).where(IngestItemModel.id == int(raw))
    if src:
        cands = {src_id, raw}
        if not src_id.startswith(f"{src}_"):
            cands.add(f"{src}_{src_id}")
        return select(IngestItemModel).where(
            IngestItemModel.source == src,
            IngestItemModel.source_id.in_(list(cands)),
        )
    return select(IngestItemModel).where(IngestItemModel.source_id == src_id)


def _run_coro_sync(coro):
    """Run an async coroutine safely from either sync or running event loop context."""
    async def _runner_coro():
        try:
            return await coro
        finally:
            try:
                running_loop = asyncio.get_running_loop()
                factory = getattr(running_loop, "_kinochi_loop_session_factory", None)
                if factory is not None and hasattr(factory, "kw") and "bind" in factory.kw:
                    setattr(running_loop, "_kinochi_loop_session_factory", None)
                    await factory.kw["bind"].dispose()
            except Exception:
                pass

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop is None:
        return asyncio.run(_runner_coro())

    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        def _runner():
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                return new_loop.run_until_complete(_runner_coro())
            finally:
                try:
                    factory = getattr(new_loop, "_kinochi_loop_session_factory", None)
                    if factory is not None and hasattr(factory, "kw") and "bind" in factory.kw:
                        setattr(new_loop, "_kinochi_loop_session_factory", None)
                        if not new_loop.is_closed():
                            new_loop.run_until_complete(factory.kw["bind"].dispose())
                except Exception:
                    pass
                try:
                    new_loop.close()
                except Exception:
                    pass

        fut = pool.submit(_runner)
        return fut.result()


async def _with_db_retry(coro_fn: Callable[[], Any], max_retries: int = 3, base_delay: float = 1.0) -> Any:
    for attempt in range(max_retries):
        try:
            return await coro_fn()
        except Exception as exc:
            err_msg = str(exc).lower()
            is_transient = any(
                w in err_msg for w in [
                    "timeout", "timed out", "semafora", "semaphore", "connection refused",
                    "closed", "broken pipe", "reset by peer", "protocolviolationerror",
                    "server disconnected", "connection reset",
                ]
            ) or isinstance(exc, (OSError, asyncio.TimeoutError))
            if is_transient and attempt < max_retries - 1:
                delay = base_delay * (1.5 ** attempt)
                logger.warning(
                    f"⚠️ DB transient xatolik ({attempt + 1}/{max_retries}): {exc}. "
                    f"{delay:.1f}s dan so'ng qayta urinilmoqda..."
                )
                await asyncio.sleep(delay)
                continue
            raise


class QueueManager:
    """
    PostgreSQL `ingest_items` backed QueueManager.
    All JSON/FileLock operations have been replaced by IngestService / IngestItemModel.
    """

    _default_session_factory: Optional[Callable] = None

    @classmethod
    def _get_nullpool_session_factory(cls):
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop is not None:
            factory = getattr(loop, "_kinochi_loop_session_factory", None)
            if factory is not None:
                return factory

        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
        from sqlalchemy.pool import NullPool
        from app.infrastructure.db.session import db_url, get_engine_kwargs
        kwargs = get_engine_kwargs(db_url)
        kwargs["poolclass"] = NullPool
        for k in ["pool_size", "max_overflow", "pool_timeout", "pool_recycle"]:
            kwargs.pop(k, None)
        cargs = kwargs.setdefault("connect_args", {})
        cargs["timeout"] = 45.0
        cargs["command_timeout"] = 60.0
        null_engine = create_async_engine(db_url, **kwargs)
        factory = async_sessionmaker(null_engine, class_=AsyncSession, expire_on_commit=False)
        if loop is not None:
            setattr(loop, "_kinochi_loop_session_factory", factory)
        return factory

    def __init__(self, session_factory: Optional[Callable] = None, **kwargs):
        self._session_factory = session_factory or self._default_session_factory

    def _get_session_factory(self):
        if self._session_factory is not None:
            return self._session_factory
        return self._get_nullpool_session_factory()

    @property
    def items(self) -> Dict[str, QueueItem]:
        rows, _ = self.get_filtered(limit=5000)
        return {item.id: item for item in rows}

    def load(self):
        """No-op for DB-backed queue; state lives in PostgreSQL ingest_items."""
        return

    def save(self):
        """No-op for DB-backed queue; mutations commit immediately."""
        return

    # ── async implementations ──────────────────────────────────────────────
    async def add_items_batch_async(self, items: List[QueueItem]) -> int:
        if not items:
            return 0
        from app.application.ingest_service import IngestService

        batch_dicts: List[Dict[str, Any]] = []
        for item in items:
            src = str(item.source or "").strip().lower()
            src_id = str(item.source_id or "").strip()
            if not src_id and item.id:
                _, src_id = _parse_item_key(item.id)
            payload = dict(item.payload or {})
            if item.episodes_count is not None:
                payload["episodes_count"] = item.episodes_count
            if item.downloaded_episodes:
                payload["downloaded_episodes"] = item.downloaded_episodes

            batch_dicts.append({
                "source": src,
                "source_id": src_id,
                "media_type": item.media_type or "movie",
                "title": item.title or "",
                "original_title": item.original_title,
                "year": item.year,
                "url": item.url,
                "poster_url": item.poster_url,
                "tmdb_id": item.tmdb_id,
                "payload": payload,
                "status": _normalize_status(item.status),
                "reason": item.reason or item.error_message,
                "priority": int(item.priority or 0),
                "topic_chat_id": item.topic_chat_id,
                "topic_id": item.topic_id,
                "storage_message_id": item.storage_message_id,
                "media_id": item.media_id,
            })

        async def _run():
            factory = self._get_session_factory()
            async with factory() as session:
                svc = IngestService(session)
                return await svc.add_batch(batch_dicts)
        return await _with_db_retry(_run)

    async def add_item_async(self, item: QueueItem) -> bool:
        added = await self.add_items_batch_async([item])
        return added > 0

    async def claim_next_async(
        self,
        worker_id: str = "worker",
        source: Optional[str] = None,
        media_type: Optional[str] = None,
        item_id: Optional[str] = None,
    ) -> Optional[QueueItem]:
        from app.application.ingest_service import IngestService

        item_key = None
        if item_id:
            src, src_id = _parse_item_key(item_id)
            if src and src_id:
                item_key = (src, src_id)

        async def _run():
            factory = self._get_session_factory()
            async with factory() as session:
                svc = IngestService(session)
                row = await svc.claim_next(
                    worker_id=worker_id,
                    source=source,
                    media_type=media_type,
                    item_key=item_key,
                )
                return _model_to_queue_item(row) if row else None
        return await _with_db_retry(_run)

    async def update_status_async(
        self,
        item_id: str,
        status: str,
        error_message: Optional[str] = None,
        episodes_count: Optional[int] = None,
        downloaded_episodes: Optional[int] = None,
        topic_chat_id: Optional[int] = None,
        topic_id: Optional[int] = None,
        storage_message_id: Optional[int] = None,
        media_id: Optional[int] = None,
    ) -> Optional[QueueItem]:
        from app.application.ingest_service import IngestService

        norm_status = _normalize_status(status)
        src, src_id = _parse_item_key(item_id)

        payload_upd: Dict[str, Any] = {}
        if episodes_count is not None:
            payload_upd["episodes_count"] = episodes_count
        if downloaded_episodes is not None:
            payload_upd["downloaded_episodes"] = downloaded_episodes

        async def _run():
            factory = self._get_session_factory()
            async with factory() as session:
                stmt = _build_item_select_stmt(item_id)
                res = await session.execute(stmt)
                row = res.scalar_one_or_none()
                if not row:
                    return None

                svc = IngestService(session)
                updated = await svc.set_status(
                    row.id,
                    norm_status,
                    reason=error_message,
                    topic_chat_id=topic_chat_id,
                    topic_id=topic_id,
                    storage_message_id=storage_message_id,
                    media_id=media_id,
                    payload_update=payload_upd or None,
                )
                return _model_to_queue_item(updated) if updated else None
        return await _with_db_retry(_run)

    async def delete_item_async(self, item_id: str) -> bool:
        from sqlalchemy import delete
        from app.infrastructure.db.models.ingest_item import IngestItemModel

        async def _run():
            factory = self._get_session_factory()
            async with factory() as session:
                stmt = _build_item_select_stmt(item_id)
                res = await session.execute(stmt)
                row = res.scalar_one_or_none()
                if not row:
                    return False
                del_stmt = delete(IngestItemModel).where(IngestItemModel.id == row.id)
                res_del = await session.execute(del_stmt)
                await session.commit()
                return (res_del.rowcount or 0) > 0
        return bool(await _with_db_retry(_run))

    async def update_item_details_async(
        self,
        item_id: str,
        title: Optional[str] = None,
        year: Optional[int] = None,
        poster_url: Optional[str] = None,
        media_type: Optional[str] = None,
        original_title: Optional[str] = None,
        status: Optional[str] = "queued",
        error_message: Optional[str] = None,
    ) -> bool:
        from datetime import datetime, timezone
        from app.infrastructure.db.models.ingest_item import validate_status_transition

        async def _run():
            factory = self._get_session_factory()
            async with factory() as session:
                stmt = _build_item_select_stmt(item_id)
                res = await session.execute(stmt)
                row = res.scalar_one_or_none()
                if not row:
                    return False

                if title:
                    row.title = title
                if year is not None:
                    row.year = year
                if poster_url is not None:
                    row.poster_url = poster_url
                if media_type is not None:
                    row.media_type = media_type
                if original_title is not None:
                    row.original_title = original_title
                if status is not None:
                    norm_st = _normalize_status(status)
                    validate_status_transition(row.status, norm_st)
                    row.status = norm_st
                row.reason = error_message
                row.updated_at = datetime.now(timezone.utc)
                await session.commit()
                return True
        return bool(await _with_db_retry(_run))

    async def retry_all_failed_async(self, source: Optional[str] = None) -> int:
        from datetime import datetime, timezone
        from sqlalchemy import update
        from app.infrastructure.db.models.ingest_item import IngestItemModel

        async def _run():
            factory = self._get_session_factory()
            async with factory() as session:
                stmt = update(IngestItemModel).where(
                    IngestItemModel.status.in_(["failed", "needs_review"])
                )
                if source == "both":
                    stmt = stmt.where(IngestItemModel.source.in_(["uzmovi", "asilmedia"]))
                elif source and source != "all":
                    stmt = stmt.where(IngestItemModel.source == source.lower())
                stmt = stmt.values(
                    status="queued",
                    reason=None,
                    locked_at=None,
                    locked_by=None,
                    updated_at=datetime.now(timezone.utc),
                )
                res = await session.execute(stmt)
                await session.commit()
                return int(res.rowcount or 0)
        return int(await _with_db_retry(_run) or 0)

    async def retry_item_async(self, item_id: str) -> bool:
        updated = await self.update_status_async(item_id, "queued", error_message=None)
        return updated is not None

    async def recover_stale_in_progress_async(self, max_age_seconds: int = 1800) -> int:
        from app.application.ingest_service import IngestService

        async def _do_recover():
            factory = self._get_session_factory()
            try:
                async with factory() as session:
                    svc = IngestService(session)
                    count = await svc.recover_stale(max_age_seconds=max_age_seconds)
                    if count > 0:
                        logger.info(f"♻️ {count} ta eskirgan (stale) 'in_progress' element 'queued' holatiga qaytarildi.")
                    return count
            except Exception as exc:
                if "different loop" in str(exc) or "Future" in str(exc):
                    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
                    from sqlalchemy.pool import NullPool
                    from app.infrastructure.db.session import db_url, get_engine_kwargs
                    kwargs = get_engine_kwargs(db_url)
                    kwargs["poolclass"] = NullPool
                    for k in ["pool_size", "max_overflow", "pool_timeout", "pool_recycle"]:
                        kwargs.pop(k, None)
                    cargs = kwargs.setdefault("connect_args", {})
                    cargs["timeout"] = 45.0
                    cargs["command_timeout"] = 60.0
                    temp_engine = create_async_engine(db_url, **kwargs)
                    temp_factory = async_sessionmaker(temp_engine, class_=AsyncSession, expire_on_commit=False)
                    try:
                        async with temp_factory() as session:
                            svc = IngestService(session)
                            count = await svc.recover_stale(max_age_seconds=max_age_seconds)
                            if count > 0:
                                logger.info(f"♻️ {count} ta eskirgan (stale) 'in_progress' element 'queued' holatiga qaytarildi.")
                            return count
                    except Exception as inner_exc:
                        logger.warning(f"Fallback recover_stale muvaffaqiyatsiz: {inner_exc}")
                        return 0
                    finally:
                        await temp_engine.dispose()
                raise

        try:
            return await _with_db_retry(_do_recover, max_retries=3, base_delay=1.0)
        except Exception as exc:
            logger.warning(f"⚠️ recover_stale_in_progress_async xatosi: {exc}")
            return 0

    async def clear_by_status_async(self, status: str) -> int:
        from sqlalchemy import delete
        from app.infrastructure.db.models.ingest_item import IngestItemModel

        norm_st = _normalize_status(status)

        async def _run():
            factory = self._get_session_factory()
            async with factory() as session:
                stmt = delete(IngestItemModel).where(IngestItemModel.status == norm_st)
                res = await session.execute(stmt)
                await session.commit()
                return int(res.rowcount or 0)
        return int(await _with_db_retry(_run) or 0)

    async def clear_all_async(self) -> int:
        from sqlalchemy import delete
        from app.infrastructure.db.models.ingest_item import IngestItemModel

        async def _run():
            factory = self._get_session_factory()
            async with factory() as session:
                stmt = delete(IngestItemModel)
                res = await session.execute(stmt)
                await session.commit()
                return int(res.rowcount or 0)
        return int(await _with_db_retry(_run) or 0)

    async def clear_finished_and_existing_async(self) -> int:
        from sqlalchemy import delete
        from app.infrastructure.db.models.ingest_item import IngestItemModel

        async def _run():
            factory = self._get_session_factory()
            async with factory() as session:
                stmt = delete(IngestItemModel).where(
                    IngestItemModel.status.in_(["published", "already_exists"])
                )
                res = await session.execute(stmt)
                await session.commit()
                return int(res.rowcount or 0)
        return int(await _with_db_retry(_run) or 0)

    async def get_item_async(self, item_id: str) -> Optional[QueueItem]:
        async def _run():
            factory = self._get_session_factory()
            async with factory() as session:
                stmt = _build_item_select_stmt(item_id)
                res = await session.execute(stmt)
                row = res.scalar_one_or_none()
                return _model_to_queue_item(row) if row else None
        return await _with_db_retry(_run)

    async def get_item_by_code_async(self, code: str) -> Optional[QueueItem]:
        from sqlalchemy import select
        from app.infrastructure.db.models.ingest_item import IngestItemModel

        clean_code = str(code).strip()
        src, src_id = _parse_item_key(clean_code)

        async def _run():
            factory = self._get_session_factory()
            async with factory() as session:
                if src:
                    stmt = select(IngestItemModel).where(
                        IngestItemModel.source == src,
                        IngestItemModel.source_id == src_id,
                    ).limit(1)
                else:
                    stmt = select(IngestItemModel).where(
                        IngestItemModel.source_id == clean_code
                    ).limit(1)
                res = await session.execute(stmt)
                row = res.scalar_one_or_none()
                return _model_to_queue_item(row) if row else None
        return await _with_db_retry(_run)

    async def get_pending_async(
        self,
        limit: int = 50,
        source: Optional[str] = None,
        media_type: Optional[str] = None,
    ) -> List[QueueItem]:
        from sqlalchemy import select
        from app.infrastructure.db.models.ingest_item import IngestItemModel

        async def _run():
            factory = self._get_session_factory()
            async with factory() as session:
                stmt = select(IngestItemModel).where(IngestItemModel.status == "queued")
                if source == "both":
                    stmt = stmt.where(IngestItemModel.source.in_(["uzmovi", "asilmedia"]))
                elif source and source != "all":
                    stmt = stmt.where(IngestItemModel.source == source.lower())
                stmt = stmt.order_by(
                    IngestItemModel.priority.desc(),
                    IngestItemModel.id.asc(),
                )
                res = await session.execute(stmt)
                rows = [_model_to_queue_item(r) for r in res.scalars().all()]
                if media_type and media_type != "all":
                    rows = [it for it in rows if matches_media_type(it, media_type)]
                return rows[:limit]
        return await _with_db_retry(_run)

    async def get_filtered_async(
        self,
        status: Optional[str] = None,
        source: Optional[str] = None,
        search: Optional[str] = None,
        media_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[QueueItem], int]:
        from sqlalchemy import select, or_
        from app.infrastructure.db.models.ingest_item import IngestItemModel

        async def _run():
            factory = self._get_session_factory()
            async with factory() as session:
                stmt = select(IngestItemModel)
                if status and status != "all":
                    norm_st = _normalize_status(status)
                    stmt = stmt.where(IngestItemModel.status == norm_st)
                if source == "both":
                    stmt = stmt.where(IngestItemModel.source.in_(["uzmovi", "asilmedia"]))
                elif source and source != "all":
                    stmt = stmt.where(IngestItemModel.source == source.lower())
                if search:
                    q = f"%{search.strip()}%"
                    stmt = stmt.where(
                        or_(
                            IngestItemModel.title.ilike(q),
                            IngestItemModel.original_title.ilike(q),
                            IngestItemModel.source_id.ilike(q),
                        )
                    )
                stmt = stmt.order_by(IngestItemModel.id.desc())
                res = await session.execute(stmt)
                all_items = [_model_to_queue_item(r) for r in res.scalars().all()]

                if media_type and media_type != "all":
                    all_items = [it for it in all_items if matches_media_type(it, media_type)]

                status_priority = {
                    "in_progress": 0,
                    "queued": 1,
                    "needs_review": 2,
                    "failed": 3,
                    "rejected": 4,
                    "blacklisted": 5,
                    "published": 6,
                    "already_exists": 7,
                    "discovered": 8,
                }
                all_items.sort(key=lambda i: status_priority.get(i.status, 99))
                total_count = len(all_items)
                return all_items[skip: skip + limit], total_count
        return await _with_db_retry(_run)

    async def stats_async(self) -> Dict[str, Any]:
        from app.application.ingest_service import IngestService

        async def _run():
            factory = self._get_session_factory()
            async with factory() as session:
                svc = IngestService(session)
                return await svc.get_stats()
        return await _with_db_retry(_run)

    # ── synchronous compatibility wrappers ─────────────────────────────────
    def add_item(self, item: QueueItem) -> bool:
        return bool(_run_coro_sync(self.add_item_async(item)))

    add = add_item

    def add_items_batch(self, items: List[QueueItem]) -> int:
        return int(_run_coro_sync(self.add_items_batch_async(items)) or 0)

    def claim_next(
        self,
        worker_id: str = "worker",
        source: Optional[str] = None,
        media_type: Optional[str] = None,
        item_id: Optional[str] = None,
    ) -> Optional[QueueItem]:
        return _run_coro_sync(
            self.claim_next_async(
                worker_id=worker_id,
                source=source,
                media_type=media_type,
                item_id=item_id,
            )
        )

    def update_status(
        self,
        item_id: str,
        status: str,
        error_message: Optional[str] = None,
        episodes_count: Optional[int] = None,
        downloaded_episodes: Optional[int] = None,
        topic_chat_id: Optional[int] = None,
        topic_id: Optional[int] = None,
        storage_message_id: Optional[int] = None,
        media_id: Optional[int] = None,
    ):
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop is not None and loop.is_running():
            return loop.create_task(
                self.update_status_async(
                    item_id=item_id,
                    status=status,
                    error_message=error_message,
                    episodes_count=episodes_count,
                    downloaded_episodes=downloaded_episodes,
                    topic_chat_id=topic_chat_id,
                    topic_id=topic_id,
                    storage_message_id=storage_message_id,
                    media_id=media_id,
                )
            )

        return _run_coro_sync(
            self.update_status_async(
                item_id=item_id,
                status=status,
                error_message=error_message,
                episodes_count=episodes_count,
                downloaded_episodes=downloaded_episodes,
                topic_chat_id=topic_chat_id,
                topic_id=topic_id,
                storage_message_id=storage_message_id,
                media_id=media_id,
            )
        )

    def delete_item(self, item_id: str) -> bool:
        return bool(_run_coro_sync(self.delete_item_async(item_id)))

    def update_item_details(
        self,
        item_id: str,
        title: Optional[str] = None,
        year: Optional[int] = None,
        poster_url: Optional[str] = None,
        media_type: Optional[str] = None,
        original_title: Optional[str] = None,
        status: Optional[str] = "queued",
        error_message: Optional[str] = None,
    ) -> bool:
        return bool(
            _run_coro_sync(
                self.update_item_details_async(
                    item_id=item_id,
                    title=title,
                    year=year,
                    poster_url=poster_url,
                    media_type=media_type,
                    original_title=original_title,
                    status=status,
                    error_message=error_message,
                )
            )
        )

    def retry_all_failed(self, source: Optional[str] = None) -> int:
        return int(_run_coro_sync(self.retry_all_failed_async(source=source)) or 0)

    def retry_item(self, item_id: str) -> bool:
        return bool(_run_coro_sync(self.retry_item_async(item_id)))

    def reset_stuck_in_progress(self) -> int:
        return int(_run_coro_sync(self.recover_stale_in_progress_async(max_age_seconds=0)) or 0)

    def recover_stale_in_progress(self, max_age_seconds: int = 1800) -> int:
        return int(_run_coro_sync(self.recover_stale_in_progress_async(max_age_seconds=max_age_seconds)) or 0)

    def clear_by_status(self, status: str) -> int:
        return int(_run_coro_sync(self.clear_by_status_async(status)) or 0)

    def clear_all(self) -> int:
        return int(_run_coro_sync(self.clear_all_async()) or 0)

    def clear_finished_and_existing(self) -> int:
        return int(_run_coro_sync(self.clear_finished_and_existing_async()) or 0)

    def get_item(self, item_id: str) -> Optional[QueueItem]:
        return _run_coro_sync(self.get_item_async(item_id))

    def get_item_by_code(self, code: str) -> Optional[QueueItem]:
        return _run_coro_sync(self.get_item_by_code_async(code))

    def get_pending(
        self,
        limit: int = 50,
        source: Optional[str] = None,
        media_type: Optional[str] = None,
    ) -> List[QueueItem]:
        return _run_coro_sync(self.get_pending_async(limit=limit, source=source, media_type=media_type)) or []

    def get_filtered(
        self,
        status: Optional[str] = None,
        source: Optional[str] = None,
        search: Optional[str] = None,
        media_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[QueueItem], int]:
        return _run_coro_sync(
            self.get_filtered_async(
                status=status,
                source=source,
                search=search,
                media_type=media_type,
                skip=skip,
                limit=limit,
            )
        )

    def stats(self) -> Dict[str, Any]:
        return _run_coro_sync(self.stats_async()) or {}
