"""
Async SQLAlchemy session factory.

Infrastructure Layer — this module creates the async engine and
session-maker used by all repositories.  It reads the DATABASE_URL
from core.config.
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings
import logging
import re
import socket
import uuid

_original_getaddrinfo = socket.getaddrinfo
_dns_cache: dict = {}

def _ipv4_only_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    """
    Ba'zi bulut muhitlarida (Render) IPv6 (AAAA) manzillarga chiquvchi
    ulanish "blackhole" bo'lib, cheksiz kutishga sabab bo'ladi. Bu yerda
    DNS javobidan faqat IPv4 (AF_INET) natijalarni qoldiramiz.
    DNS natijalarini keshlaymiz, shunda har safar 1.5s kutish bo'lmaydi.
    """
    cache_key = (host, port, family, type, proto, flags)
    if cache_key in _dns_cache:
        return _dns_cache[cache_key]
    results = _original_getaddrinfo(host, port, family, type, proto, flags)
    ipv4_results = [r for r in results if r[0] == socket.AF_INET]
    res = ipv4_results if ipv4_results else results
    _dns_cache[cache_key] = res
    return res

socket.getaddrinfo = _ipv4_only_getaddrinfo
logging.info("CHECKPOINT 5b: DB engine yaratilmoqda")

db_url = re.sub(r"\s+", "", str(settings.DATABASE_URL))
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
elif db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
db_url = re.sub(r"([?&])sslmode=([a-zA-Z0-9_-]+)", r"\1ssl=\2", db_url)
db_url = re.sub(r"[?&]channel_binding=[^&]+", "", db_url)
db_url = re.sub(r"[?&]gssencmode=[^&]+", "", db_url)
if "?" not in db_url and "&" in db_url:
    db_url = db_url.replace("&", "?", 1)
db_url = re.sub(r"\?&", "?", db_url).rstrip("?&")


def get_engine_kwargs(
    url: str,
    pool_size: int | None = None,
    max_overflow: int | None = None,
) -> dict:
    """SQLAlchemy async engine parametrlarini shakllantiradi."""
    effective_pool_size = pool_size if pool_size is not None else getattr(settings, "DB_POOL_SIZE", 10)
    effective_max_overflow = max_overflow if max_overflow is not None else getattr(settings, "DB_MAX_OVERFLOW", 20)

    kwargs: dict = {
        "echo": False,
        "pool_pre_ping": True,
    }
    if "sqlite" not in url.lower():
        kwargs.update({
            "pool_size": effective_pool_size,
            "max_overflow": effective_max_overflow,
            "pool_recycle": 300,
            "pool_timeout": 15,
            "connect_args": {
                "statement_cache_size": 0,
                "prepared_statement_cache_size": 0,
                "prepared_statement_name_func": lambda: f"__asyncpg_{uuid.uuid4()}__",
            },
        })
    return kwargs


engine_kwargs = get_engine_kwargs(db_url)

engine = create_async_engine(
    db_url,
    **engine_kwargs
)
logging.info("CHECKPOINT 5c: DB engine yaratildi")

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""
    pass
