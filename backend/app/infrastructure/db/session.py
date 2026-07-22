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
import socket

_original_getaddrinfo = socket.getaddrinfo

def _ipv4_only_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    """
    Ba'zi bulut muhitlarida (Render) IPv6 (AAAA) manzillarga chiquvchi
    ulanish "blackhole" bo'lib, cheksiz kutishga sabab bo'ladi. Bu yerda
    DNS javobidan faqat IPv4 (AF_INET) natijalarni qoldiramiz — hostname
    o'zi o'zgarmaydi (SNI/SSL sertifikat tekshiruviga ta'sir qilmaydi).
    """
    results = _original_getaddrinfo(host, port, family, type, proto, flags)
    ipv4_results = [r for r in results if r[0] == socket.AF_INET]
    return ipv4_results if ipv4_results else results

socket.getaddrinfo = _ipv4_only_getaddrinfo
logging.info("CHECKPOINT 5b: DB engine yaratilmoqda")
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
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
