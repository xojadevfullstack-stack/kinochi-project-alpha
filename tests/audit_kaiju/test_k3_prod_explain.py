import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath("backend"))

from app.infrastructure.db.session import async_session_factory
from sqlalchemy import text

async def run_k3_checks():
    print("=== K3 VERIFICATION: INDEXES & CASE SENSITIVITY ===")
    async with async_session_factory() as session:
        # 1. Indexes on episodes table
        idx_res = await session.execute(text("""
            SELECT indexname, indexdef 
            FROM pg_indexes 
            WHERE tablename = 'episodes'
        """))
        indexes = idx_res.fetchall()
        print("\n--- 1. Indexes on 'episodes' table in Prod ---")
        for idx in indexes:
            print(f"  {idx.indexname}: {idx.indexdef}")

        # 2. Case collision check
        col_res = await session.execute(text("""
            SELECT lower(code) AS lcode, count(*) AS cnt
            FROM episodes
            GROUP BY lower(code)
            HAVING count(*) > 1
        """))
        collisions = col_res.fetchall()
        print(f"\n--- 2. Case Collision Check (lower(code) count > 1) ---")
        print(f"  Total collisions found: {len(collisions)}")
        for c in collisions:
            print(f"  Collision: {c.lcode} (count={c.cnt})")

        # 3. EXPLAIN (ANALYZE, BUFFERS) on exact code
        print("\n--- 3. EXPLAIN (ANALYZE, BUFFERS) for exact match (code = 'bAcW78zJ') ---")
        exp1 = await session.execute(text("""
            EXPLAIN (ANALYZE, BUFFERS)
            SELECT id, episode_number, code, display_code, title
            FROM episodes
            WHERE code = 'bAcW78zJ'
        """))
        for row in exp1.fetchall():
            print(f"  {row[0]}")

        # 4. EXPLAIN (ANALYZE, BUFFERS) on func.lower(code)
        print("\n--- 4. EXPLAIN (ANALYZE, BUFFERS) for lower() match (lower(code) = 'bacw78zj') ---")
        exp2 = await session.execute(text("""
            EXPLAIN (ANALYZE, BUFFERS)
            SELECT id, episode_number, code, display_code, title
            FROM episodes
            WHERE lower(code) = lower('bAcW78zJ')
        """))
        for row in exp2.fetchall():
            print(f"  {row[0]}")

        # 5. Querying mixed-case code with different case
        print("\n--- 5. Querying mixed-case code with wrong case ---")
        res_exact_wrong = await session.execute(text("SELECT id, code FROM episodes WHERE code = 'bacw78zj'"))
        print(f"  WHERE code = 'bacw78zj' (exact match with lowercase): {res_exact_wrong.fetchall()}")
        
        res_lower_wrong = await session.execute(text("SELECT id, code FROM episodes WHERE lower(code) = lower('bacw78zj')"))
        print(f"  WHERE lower(code) = lower('bacw78zj') (lower match): {res_lower_wrong.fetchall()}")

if __name__ == "__main__":
    asyncio.run(run_k3_checks())
