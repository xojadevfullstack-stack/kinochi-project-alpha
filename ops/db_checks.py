#!/usr/bin/env python3
"""
ops/db_checks.py: Ma'lumotlar bazasi holatini xavfsiz tekshirish skripti.

Xavfsizlik va formatlash qoidalari:
- Ulanish URL satri hech qachon ekranga yoki logga chiqarilmaydi.
- Faqatgina ma'lumotlar bazasi xosti (host) ko'rsatiladi.
- Xabarlar faqat ASCII formatda (emojisiz) chiqariladi (Windows cp1251/cp866 mosligi).
"""

import sys
import os
import json
import argparse
import asyncio
from typing import Dict, Any, Optional, List

# sys.path ga root va backend katalogni qo'shish
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from sqlalchemy.engine import make_url
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker


def get_sanitized_host(url_str: Optional[str]) -> str:
    """URL dan faqat host nomini ajratib oladi, maxfiy ma'lumotlarni yashiradi."""
    if not url_str:
        return "NONE"
    try:
        u = make_url(url_str)
        return str(u.host or "localhost")
    except Exception:
        return "INVALID_URL"


def normalize_async_url(url_str: str) -> str:
    """Async engine uchun URL sxemasini to'g'rilaydi."""
    if url_str.startswith("postgres://"):
        return url_str.replace("postgres://", "postgresql+asyncpg://", 1)
    if url_str.startswith("postgresql://"):
        return url_str.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url_str


import subprocess
import shutil

def to_libpq_url(url_str: str) -> str:
    """SQLAlchemy/asyncpg URL ni libpq/pg_dump/pg_restore formatiga o'tkazadi."""
    if not url_str:
        return ""
    import re
    # 1. postgresql+asyncpg:// -> postgresql://
    converted = re.sub(r"^postgres(?:ql)?\+[a-zA-Z0-9_]+://", "postgresql://", url_str)
    # 2. postgres:// -> postgresql://
    converted = re.sub(r"^postgres://", "postgresql://", converted)
    # 3. ssl=... parametrini sslmode=... ga o'tkazish
    converted = re.sub(r"([?&])ssl=([a-zA-Z0-9_-]+)", r"\1sslmode=\2", converted)
    converted = re.sub(r"([?&])sslmode=true", r"\1sslmode=require", converted)
    return converted


def create_backup(url_str: str, dump_path: str) -> bool:
    """pg_dump orqali zaxira oladi (xostda yoki Docker orqali)."""
    if not url_str:
        return False
    libpq_url = to_libpq_url(url_str)
    host = get_sanitized_host(url_str)
    os.makedirs(os.path.dirname(os.path.abspath(dump_path)), exist_ok=True)

    # 1. Xostdagi pg_dump ni tekshirish
    pg_dump_cmd = shutil.which("pg_dump")
    if pg_dump_cmd:
        cmd = [pg_dump_cmd, "-Fc", "--no-owner", "--dbname", libpq_url, "-f", dump_path]
        p = subprocess.run(cmd, capture_output=True, text=True)
        if p.returncode == 0 and os.path.exists(dump_path) and os.path.getsize(dump_path) > 0:
            return True

    # 2. Agar localhost/Docker bo'lsa va kinochi_rehearsal_pg konteyneri mavjud bo'lsa
    if host in ["localhost", "127.0.0.1"]:
        db_name = url_str.split("/")[-1].split("?")[0]
        with open(dump_path, "wb") as f:
            p = subprocess.run(
                ["docker", "exec", "kinochi_rehearsal_pg", "pg_dump", "-U", "postgres", "-Fc", db_name],
                stdout=f,
                stderr=subprocess.PIPE,
            )
            if p.returncode == 0 and os.path.exists(dump_path) and os.path.getsize(dump_path) > 0:
                return True

    return False


def verify_backup_integrity(dump_path: str) -> bool:
    """pg_restore --list orqali zaxira yaxlitligini tekshiradi."""
    if not os.path.exists(dump_path) or os.path.getsize(dump_path) == 0:
        return False

    pg_restore_cmd = shutil.which("pg_restore")
    if pg_restore_cmd:
        p = subprocess.run([pg_restore_cmd, "--list", dump_path], capture_output=True)
        return p.returncode == 0

    # Docker fallback
    with open(dump_path, "rb") as f:
        p = subprocess.run(
            ["docker", "exec", "-i", "kinochi_rehearsal_pg", "pg_restore", "--list"],
            stdin=f,
            capture_output=True,
        )
        return p.returncode == 0


PRESERVED_TABLES = [
    "users",
    "admin_users",
    "channels",
    "mandatory_channels",
    "subscriptions",
    "series_subscriptions",
    "verified_subscriptions",
    "system_settings",
    "scraper_logs",
    "pages",
    "blacklist",
]

MEDIA_TABLES = [
    "movies",
    "series",
    "seasons",
    "episodes",
    "sources",
    "movie_sources",
    "series_sources",
    "movie_translations",
    "episode_translations",
    "reports",
    "reviews",
    "watch_history",
    "rejected_items",
    "page_movie",
]


async def run_db_checks(
    env_var_name: str = "DATABASE_URL",
    expected_alembic: Optional[str] = "e8f9a0b1c2d3",
    expected_default: str = "pending",
    check_zero_media: bool = False,
    baseline_file: Optional[str] = None,
    output_json: bool = False,
    allow_empty: bool = False,
) -> Dict[str, Any]:
    url_str = os.environ.get(env_var_name)
    host_name = get_sanitized_host(url_str)

    if not url_str:
        err_msg = f"[XATO] '{env_var_name}' muhit o'zgaruvchisi topilmadi!"
        if not output_json:
            print(err_msg)
        return {"ok": False, "error": err_msg, "host": host_name, "issues": [err_msg]}

    if not output_json:
        print("=" * 65)
        print("       KINOCHI DB CHECKS (XAVFSIZ TEKSHIRUV)")
        print("=" * 65)
        print(f"Nishon DB Xosti : {host_name}")
        print(f"Muhit o'zgaruvchi: {env_var_name}")
        print("-" * 65)

    async_url = normalize_async_url(url_str)
    engine = create_async_engine(async_url, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    results: Dict[str, Any] = {
        "ok": True,
        "host": host_name,
        "alembic_version": None,
        "publish_status_defaults": {},
        "table_counts": {},
        "issues": [],
    }

    try:
        async with session_factory() as session:
            # 1. alembic_version ni tekshirish
            try:
                av_res = await session.execute(text("SELECT version_num FROM alembic_version"))
                versions = av_res.scalars().all()
                results["alembic_version"] = versions[0] if versions else None
                if expected_alembic and results["alembic_version"] != expected_alembic:
                    results["issues"].append(
                        f"alembic_version kutilgan '{expected_alembic}' emas, hozirgi: '{results['alembic_version']}'"
                    )
            except Exception as e:
                if allow_empty:
                    results["is_empty_db"] = True
                    results["alembic_version"] = None
                else:
                    results["issues"].append(f"alembic_version jadvali tekshirilmadi: {e}")

            # Agar bo'sh baza bo'lsa va allow_empty faol bo'lsa, qolgan tekshiruvlarni o'tkazib yuboramiz
            if results.get("is_empty_db"):
                results["ok"] = len(results["issues"]) == 0
                return results

            # 2. publish_status ustunining default qiymatini tekshirish
            for tbl in ["movies", "series"]:
                try:
                    col_q = await session.execute(text(
                        "SELECT column_default FROM information_schema.columns "
                        f"WHERE table_name = '{tbl}' AND column_name = 'publish_status'"
                    ))
                    val = col_q.scalar()
                    results["publish_status_defaults"][tbl] = val
                    if not val or expected_default not in str(val).lower():
                        results["issues"].append(
                            f"[{tbl}] publish_status default qiymati '{expected_default}' emas: {val}"
                        )
                except Exception as e:
                    results["issues"].append(f"[{tbl}] ustun defaulti tekshirilmadi: {e}")

            # 3. Jadvallar qatorlar sonini tekshirish
            all_tables = set(PRESERVED_TABLES + MEDIA_TABLES + ["alembic_version", "seed_candidates"])
            for t in sorted(all_tables):
                try:
                    cnt_q = await session.execute(text(f"SELECT count(*) FROM {t}"))
                    results["table_counts"][t] = cnt_q.scalar() or 0
                except Exception:
                    # Jadval bazada bo'lmasligi mumkin
                    results["table_counts"][t] = None

            # 4. Agar --check-zero-media so'ralgan bo'lsa
            if check_zero_media:
                for mt in MEDIA_TABLES:
                    cnt = results["table_counts"].get(mt)
                    if cnt is not None and cnt > 0:
                        results["issues"].append(
                            f"[RESET TEKSHIRUVI] {mt} jadvalida {cnt} ta qator bor (0 kutilgan)!"
                        )

            # 5. Agar --check-preserved-counts / --baseline-file so'ralgan bo'lsa
            if baseline_file and os.path.exists(baseline_file):
                with open(baseline_file, "r", encoding="utf-8") as f:
                    saved_counts = json.load(f)
                for pt in PRESERVED_TABLES:
                    old_c = saved_counts.get(pt)
                    new_c = results["table_counts"].get(pt)
                    if old_c is not None and new_c is not None:
                        if new_c < old_c:
                            results["issues"].append(
                                f"[SAQLANUVCHI JADVAL] {pt} soni kamaygan! Oldin: {old_c}, hozir: {new_c}"
                            )

    except Exception as e:
        results["ok"] = False
        results["error"] = str(e)
        results["issues"].append(f"DB ulanish xatoligi: {e}")
    finally:
        await engine.dispose()

    if results["issues"]:
        results["ok"] = False

    if output_json:
        print(json.dumps(results, indent=2, ensure_ascii=True))
    else:
        print(f"Alembic Version         : {results['alembic_version']}")
        print(f"publish_status (movies) : {results['publish_status_defaults'].get('movies')}")
        print(f"publish_status (series) : {results['publish_status_defaults'].get('series')}")
        print("-" * 65)
        print("Jadvallar bo'yicha qatorlar soni:")
        for t, cnt in sorted(results["table_counts"].items()):
            cnt_str = str(cnt) if cnt is not None else "[mavjud emas]"
            print(f"  {t:25}: {cnt_str}")
        print("-" * 65)
        if results["ok"]:
            print("[STATUS: OK] Barcha DB tekshiruvlari muvaffaqiyatli o'tdi.")
        else:
            print("[STATUS: MUAMMO]")
            for iss in results["issues"]:
                print(f"  - {iss}")
        print("=" * 65 + "\n")

    return results


def main():
    parser = argparse.ArgumentParser(description="Kinochi Database Checks Utility (No secrets printed)")
    parser.add_argument("--url-env-var", "--env-var", dest="url_env_var", type=str, default="DATABASE_URL",
                        help="DB URL o'qiladigan muhit o'zgaruvchi nomi (standart: DATABASE_URL)")
    parser.add_argument("--expected-alembic", type=str, default="e8f9a0b1c2d3",
                        help="Kutilayotgan alembic_version (standart: e8f9a0b1c2d3)")
    parser.add_argument("--expected-default", type=str, default="pending",
                        help="Kutilayotgan publish_status default qiymati (standart: pending)")
    parser.add_argument("--check-zero-media", action="store_true",
                        help="Media jadvallar (movies, series, episodes, etc.) 0 ekanligini tasdiqlash")
    parser.add_argument("--save-baseline", "--save-counts", dest="save_baseline", type=str, default=None,
                        help="Hozirgi qatorlar sonini json faylga saqlash")
    parser.add_argument("--check-preserved-counts", "--baseline-file", dest="baseline_file", type=str, default=None,
                        help="Saqlangan qatorlar soni bilan solishtirish (kamaymaganligini tasdiqlash)")
    parser.add_argument("--allow-empty", action="store_true",
                        help="Bo'sh bazada alembic_version yo'qligiga ruxsat berish")
    parser.add_argument("--create-backup", type=str, default=None,
                        help="pg_dump orqali zaxira olish va ko'rsatilgan faylga yozish")
    parser.add_argument("--verify-backup", type=str, default=None,
                        help="pg_restore --list orqali zaxira fayli yaxlitligini tekshirish")
    parser.add_argument("--json", action="store_true", help="JSON formatida chiqarish")

    args = parser.parse_args()

    # Agar --create-backup so'ralgan bo'lsa
    if args.create_backup:
        url_str = os.environ.get(args.url_env_var)
        if not url_str:
            print(f"[XATO] '{args.url_env_var}' muhit o'zgaruvchisi topilmadi!")
            sys.exit(1)
        ok = create_backup(url_str, args.create_backup)
        if not ok:
            print(f"[XATO] Zaxira nusxa olish muvaffaqiyatsiz bo'ldi: {args.create_backup}")
            sys.exit(1)
        print(f"[OK] Zaxira muvaffaqiyatli olindi: {args.create_backup}")
        sys.exit(0)

    # Agar --verify-backup so'ralgan bo'lsa
    if args.verify_backup:
        ok = verify_backup_integrity(args.verify_backup)
        if not ok:
            print(f"[XATO] Zaxira fayli yaxlitligi tekshiruvdan o'tmadi: {args.verify_backup}")
            sys.exit(1)
        print(f"[OK] Zaxira fayli yaxlitligi tasdiqlandi: {args.verify_backup}")
        sys.exit(0)

    results = asyncio.run(
        run_db_checks(
            env_var_name=args.url_env_var,
            expected_alembic=args.expected_alembic,
            expected_default=args.expected_default,
            check_zero_media=args.check_zero_media,
            baseline_file=args.baseline_file,
            output_json=args.json,
            allow_empty=args.allow_empty,
        )
    )

    if args.save_baseline and results.get("table_counts"):
        os.makedirs(os.path.dirname(os.path.abspath(args.save_baseline)), exist_ok=True)
        with open(args.save_baseline, "w", encoding="utf-8") as f:
            json.dump(results["table_counts"], f, indent=2)
        if not args.json:
            print(f"[INFO] Qatorlar soni '{args.save_baseline}' fayliga saqlandi.")

    if not results.get("ok"):
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
