import asyncio
import sys
import os
from dotenv import load_dotenv

if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(BASE_DIR, "backend", ".env"))
sys.path.insert(0, os.path.join(BASE_DIR, "backend"))

from app.infrastructure.db.session import engine
from sqlalchemy import text

async def main():
    async with engine.begin() as conn:
        print("1. Adding is_18_plus to movies...")
        await conn.execute(text("ALTER TABLE movies ADD COLUMN IF NOT EXISTS is_18_plus BOOLEAN NOT NULL DEFAULT FALSE;"))
        
        print("2. Adding is_18_plus to series...")
        await conn.execute(text("ALTER TABLE series ADD COLUMN IF NOT EXISTS is_18_plus BOOLEAN NOT NULL DEFAULT FALSE;"))

        print("3. Creating 18+ category if not exists...")
        res = await conn.execute(text("SELECT id FROM categories WHERE slug = '18-plus' OR name = '18+'"))
        cat = res.fetchone()
        if not cat:
            await conn.execute(text("INSERT INTO categories (name, slug, is_active) VALUES ('18+', '18-plus', true);"))
            print("   Category '18+' created.")
        else:
            print(f"   Category '18+' already exists (ID: {cat[0]}).")

        print("4. Creating reports table...")
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS reports (
                id SERIAL PRIMARY KEY,
                media_type VARCHAR(20) NOT NULL,
                movie_id INTEGER REFERENCES movies(id) ON DELETE SET NULL,
                series_id INTEGER REFERENCES series(id) ON DELETE SET NULL,
                episode_id INTEGER REFERENCES episodes(id) ON DELETE SET NULL,
                issue_type VARCHAR(50) NOT NULL,
                description TEXT,
                file_url VARCHAR(1024),
                file_type VARCHAR(20),
                status VARCHAR(20) NOT NULL DEFAULT 'pending',
                ip_address VARCHAR(45),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_reports_status ON reports(status);"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_reports_created_at ON reports(created_at DESC);"))
        print("   Reports table created successfully.")

        print("5. Tagging adult content in DB (Chuhai Lips)...")
        await conn.execute(text("UPDATE series SET is_18_plus = TRUE WHERE title ILIKE '%chuhai%' OR title ILIKE '%erli ayol%';"))
        await conn.execute(text("UPDATE movies SET is_18_plus = TRUE WHERE genres ILIKE '%ecchi%' OR genres ILIKE '%hentai%' OR genres ILIKE '%erotika%';"))
        print("   Adult content tagged.")

    print("\n✅ Migration complete!")

if __name__ == "__main__":
    asyncio.run(main())
