#!/usr/bin/env python3
"""
ops/redis_flush_cache.py: Redis faqat cache:* kalitlarini xavfsiz tozalash skripti.

Xavfsizlik va formatlash qoidalari:
- Redis ulanish URL satri hech qachon ekranga yoki logga chiqarilmaydi.
- Faqatgina Redis xosti (host) ko'rsatiladi.
- FAQAT 'cache:*' kalitlariga tegadi; telegram sessiyalari, navbatlar, locklarga ASLO tegmaydi.
- Xabarlar faqat ASCII formatda (emojisiz) chiqariladi (Windows cp1251/cp866 mosligi).
"""

import sys
import os
import argparse
from typing import Optional
from urllib.parse import urlparse


def get_sanitized_redis_host(url_str: Optional[str]) -> str:
    """Redis URL dan faqat host nomini ajratib oladi, maxfiy ma'lumotlarni yashiradi."""
    if not url_str:
        return "NONE"
    try:
        # pydantic yoki standart urlparse
        cleaned = url_str.replace("https://", "").replace("http://", "")
        if not cleaned.startswith(("redis://", "rediss://", "unix://")):
            cleaned = f"redis://{cleaned}"
        parsed = urlparse(cleaned)
        return parsed.hostname or "localhost"
    except Exception:
        return "INVALID_URL"


def flush_cache_keys(
    redis_url: str,
    execute: bool = False,
    confirm_text: Optional[str] = None,
) -> int:
    try:
        import redis
    except ImportError:
        print("[XATO] 'redis' Python kutubxonasi o'rnatilmagan!")
        print("Iltimos, o'rnating: pip install redis")
        return 1

    host_name = get_sanitized_redis_host(redis_url)
    print("=" * 65)
    print("       KINOCHI REDIS CACHE TOZALASH SKRIPTI")
    print("=" * 65)
    print(f"Nishon Redis Xosti : {host_name}")
    print("Nishon prefiksi    : cache:* (boshqa kalitlarga tegilmaydi)")
    print("-" * 65)

    try:
        client = redis.Redis.from_url(redis_url, decode_responses=False)
        client.ping()
    except Exception as e:
        print(f"[XATO] Redis serveriga ulanib bo'lmadi: {e}")
        return 1

    # Faqat cache:* kalitlarini sanash
    try:
        matched_keys = []
        for k in client.scan_iter(match=b"cache:*", count=500):
            matched_keys.append(k)
        count = len(matched_keys)
        print(f"Topilgan 'cache:*' kalitlar soni: {count}")
    except Exception as e:
        print(f"[XATO] Kalitlarni tekshirishda xatolik yuz berdi: {e}")
        return 1

    if count == 0:
        print("[INFO] 'cache:*' kalitlari mavjud emas. Tozalash shart emas.")
        print("=" * 65)
        return 0

    if not execute:
        print("\n[DIQQAT] --execute parametri berilmagan. Kalitlar o'chirilmadi (DRY-RUN).")
        print("O'chirish uchun: python -m ops.redis_flush_cache --execute")
        print("=" * 65)
        return 0

    # Tasdiqlashni tekshirish (aniq YES bo'lishi shart)
    typed_confirm = confirm_text
    if typed_confirm is None:
        try:
            print("\nHaqiqatdan ham barcha 'cache:*' kalitlarini o'chirmoqchimisiz?")
            typed_confirm = input("Tasdiqlash uchun aniq 'YES' deb yozing: ").strip()
        except EOFError:
            typed_confirm = ""

    if typed_confirm != "YES":
        print(f"\n[RAD ETILDI] Tasdiqlash matni '{typed_confirm}' kiritildi ('YES' kutilgan edi).")
        print("Operatsiya bekor qilindi. Kalitlar o'zgarishsiz qoldi.")
        print("=" * 65)
        return 1

    # Batch (500 tadan) o'chirish
    print("\nTozalanmoqda...")
    deleted_total = 0
    batch = []
    for k in client.scan_iter(match=b"cache:*", count=500):
        batch.append(k)
        if len(batch) >= 500:
            deleted_total += client.delete(*batch)
            batch = []
    if batch:
        deleted_total += client.delete(*batch)

    print(f"[STATUS: OK] Muvaffaqiyatli o'chirildi: {deleted_total} ta 'cache:*' kaliti.")
    print("Boshqa kalitlar (navbatlar, sessiyalar) o'zgarishsiz saqlandi.")
    print("=" * 65)
    return 0


def main():
    parser = argparse.ArgumentParser(description="Kinochi Redis Cache Flush (Only cache:*)")
    parser.add_argument("--redis-env-var", type=str, default="REDIS_URL",
                        help="Redis URL o'qiladigan muhit o'zgaruvchi nomi (standart: REDIS_URL)")
    parser.add_argument("--execute", action="store_true",
                        help="Haqiqiy o'chirishni ishga tushirish")
    parser.add_argument("--confirm", type=str, default=None,
                        help="Tasdiqlash matni (aniq YES bo'lishi kerak)")

    args = parser.parse_args()

    redis_url = os.environ.get(args.redis_env_var)
    if not redis_url:
        print(f"[XATO] '{args.redis_env_var}' muhit o'zgaruvchisi topilmadi!")
        sys.exit(1)

    code = flush_cache_keys(
        redis_url=redis_url,
        execute=args.execute,
        confirm_text=args.confirm,
    )
    sys.exit(code)


if __name__ == "__main__":
    main()
