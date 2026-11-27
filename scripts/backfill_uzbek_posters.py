"""CLI helper to safely backfill existing unlocalized media posters through the v10 quality-gated pipeline."""
import argparse
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.api.v1.posters import backfill_one_unlocalized_poster  # noqa: E402
from app.infrastructure.db.session import async_session_factory  # noqa: E402


async def _run_batch(limit: int, delay_sec: float) -> None:
    localized, skipped = 0, 0
    for idx in range(limit):
        async with async_session_factory() as db:
            res = await backfill_one_unlocalized_poster(db, allow_in_testing=True, daily_limit=max(100, limit))
            await db.commit()
        if res.get("localized"):
            localized += 1
            print(f"[{idx + 1}/{limit}] OK -> {res['media_type']}#{res['media_id']} ({res.get('title')})")
        elif res.get("skipped"):
            skipped += 1
            print(f"[{idx + 1}/{limit}] SKIP (gate/cooldown) -> {res['media_type']}#{res['media_id']} ({res.get('title')})")
        else:
            print(f"[{idx + 1}/{limit}] DONE: no remaining unlocalized candidates.")
            break
        if delay_sec > 0:
            await asyncio.sleep(delay_sec)
    print(f"Summary: localized={localized}, skipped={skipped}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill unlocalized movie/series posters via v10 localizer.")
    parser.add_argument("--limit", type=int, default=15, help="Max media items to process in this batch")
    parser.add_argument("--delay", type=float, default=1.5, help="Delay seconds between items")
    args = parser.parse_args()
    asyncio.run(_run_batch(max(1, args.limit), max(0.0, args.delay)))


if __name__ == "__main__":
    main()
