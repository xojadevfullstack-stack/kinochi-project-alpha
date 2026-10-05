import asyncio
import sys
import os

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from dotenv import load_dotenv
load_dotenv("backend/.env")
sys.path.insert(0, "backend")
sys.path.insert(0, ".")

from app.infrastructure.db.session import async_session_factory
from sqlalchemy import text
from scraper.smart_enricher import clean_synopsis_text

UPDATES_SERIES = {
    60: {
        "poster_url": "https://image.tmdb.org/t/p/w500/dJbG3paFR4TeCENN7ognYyZ2Xhy.jpg",
        "description": "Oddiy maktab o‘quvchisi Yoshioka Futaba yigitlarni umuman yoqtirmaydi. Ammo ular orasida u boshqacha munosabatda bo‘ladigan bir yigit bor — Tanaka. Vaqt o‘tishi bilan ularning munosabatlari rivojlana boshlaydi, biroq Futaba yozgi ta’til paytida Tanaka hech narsa demay boshqa maktabga o‘tib ketganini bilib, qattiq hayratga tushadi."
    },
    61: {
        "poster_url": "https://image.tmdb.org/t/p/w500/4tblBrslcKSifMVZ3TmtT2ukMor.jpg",
        "description": "Oddiy yuqori sinf o‘quvchisi Mark Greyson darsdan keyin ishlab, odatiy hayot kechiradi. Faqat bir farqi bor: uning otasi Norman — sayyoradagi eng qudratli superqahramon, ya’ni Omni-men. 17 yoshga kirgach, Mark otasining kuchlari unga ham meros bo‘lib o‘tganini bilib qoladi. Chunki Norman galaktikani kashf etgan va ezgu maqsad bilan Yerga kelgan Viltrumitlar irqiga mansub edi."
    },
    62: {
        "poster_url": "https://image.tmdb.org/t/p/w500/gHUCCMy1vvj58tzE3dZqeC9SXus.jpg",
        "description": "Agent Fil Kolson o‘limdan so‘ng sirli tarzda qayta tiklanadi va maxfiy huquq-tartibot tashkiloti \"QALQON\" tarkibiga qaytadi. Unga insoniyatni yashirin va tahlikali tahdidlardan himoya qilish vazifasi yuklatiladi. Bu missiyani amalga oshirish uchun u eng ishonchli va qobiliyatli agentlardan iborat jamoani tuzadi."
    },
    63: {
        "poster_url": "https://image.tmdb.org/t/p/w500/f1VCQIG2iCyOookdgOzwtUpwWC0.jpg",
        "description": "Sobiq harbiy politsiya mayori Jek Richer korruptsiyaga qarshi kurashchini o'ldirishda gumonlanib hibsga olingan kichik shaharchaga tashrif buyuradi. Mahalliy politsiya xavfli ko'rinishga ega bu katta yigit ular qidirayotgan odam emasligini anglab etgach, unga haqiqiy qotillarni topishda hamkorlik qilish taklif etiladi."
    }
}

UPDATES_MOVIES = {
    111: {
        "description": "Ota-ona sevgisining muqaddasligi va umidsizlikka uchragan umidlar haqida ta'sirchan hikoya: yosh Dunyasha otasining xohishiga qarshi uydan yosh rake bilan chiqib ketadi. Cholning hayoti barbod bo‘ldi, ota-onasining so‘zini olmagan qizi esa baxtsiz."
    }
}

async def run_cleanup():
    async with async_session_factory() as session:
        for sid, data in UPDATES_SERIES.items():
            await session.execute(
                text("""
                    UPDATE series
                    SET poster_url = :poster_url,
                        description = :description
                    WHERE id = :id
                """),
                {
                    "id": sid,
                    "poster_url": data["poster_url"],
                    "description": data["description"]
                }
            )
            print(f"✅ Series [{sid}] muvaffaqiyatli yangilandi: Poster={data['poster_url'][:35]}...")

        for mid, data in UPDATES_MOVIES.items():
            await session.execute(
                text("""
                    UPDATE movies
                    SET description = :description
                    WHERE id = :id
                """),
                {
                    "id": mid,
                    "description": data["description"]
                }
            )
            print(f"✅ Movie [{mid}] tavsifi muvaffaqiyatli yangilandi.")

        await session.commit()
        print("\n🎉 Barcha o'zgarishlar PostgreSQL bazasiga to'liq saqlandi!")

if __name__ == "__main__":
    asyncio.run(run_cleanup())
