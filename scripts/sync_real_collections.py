import asyncio
import asyncpg
import ssl
import sys

sys.stdout.reconfigure(encoding='utf-8')

COLLECTIONS_DATA = [
    {
        "slug": "harry-potter",
        "name": "Garri Potter va Sehrgarlar Olami",
        "description": "J.K. Rowling sehrgarlik olami — Nyu-Yorkdagi 1926-yilgi Sehrli jonzotlardan tortib, Xogvarts uchun buyuk janggacha bo'lgan to'liq xronologiya.",
        "poster_url": "https://image.tmdb.org/t/p/w500/wuMc08IPKEatf9rnMNXvIDxqP4W.jpg",
        "banner_url": "https://image.tmdb.org/t/p/original/4gV0rKUjB1nLUdZB4zIltLvNZZr.jpg",
        "is_franchise": True,
        "category_type": "franchise",
        "sort_order": 1,
        "items": [
            {"movie_id": 813, "series_id": None, "chronological_order": 1, "release_order": 8, "timeline_event_desc": "1926: Nyut Skamanderning Nyu-Yorkka kelishi va Obscurus"},
            {"movie_id": 810, "series_id": None, "chronological_order": 2, "release_order": 1, "timeline_event_desc": "1991–1992: Garri Potterning Xogvartsga qadami va Falsafa toshi siri"},
            {"movie_id": 811, "series_id": None, "chronological_order": 3, "release_order": 2, "timeline_event_desc": "1992–1993: Maxfiy xona ochilishi, Slizerin merosxo'ri va Vasilisk"},
            {"movie_id": 812, "series_id": None, "chronological_order": 4, "release_order": 3, "timeline_event_desc": "1993–1994: Dementorlar, Sirius Blek siri va Vaqt aylantirgich"},
            {"movie_id": 814, "series_id": None, "chronological_order": 5, "release_order": 4, "timeline_event_desc": "1994–1995: Uch sehrgar turniri va Volan-de-Mortning jismoniy qaytishi"},
            {"movie_id": 815, "series_id": None, "chronological_order": 6, "release_order": 5, "timeline_event_desc": "1995–1996: Sehr vazirligi inqirozi, Feniks jamiyati va Dambldor qo'shini"},
            {"movie_id": 816, "series_id": None, "chronological_order": 7, "release_order": 6, "timeline_event_desc": "1996–1997: Jonajonlar (Krestaj) siri va Dambldorning fojiali halokati"},
            {"movie_id": 817, "series_id": None, "chronological_order": 8, "release_order": 7, "timeline_event_desc": "1997–1998: Jonajonlarni izlash safari va Malfoylar qasridagi asirlik"},
        ]
    },
    {
        "slug": "qashqirlar-makoni",
        "name": "Qashqirlar Makoni (Kurtlar Vadisi)",
        "description": "Polat Alemdar va uning jamoasining mafiya, davlat sirlari va xalqaro fitnalarga qarshi kurashi to'liq xronologiyasi.",
        "poster_url": "https://media.themoviedb.org/t/p/w440_and_h660_face/zPv5KaNEVqZLpbH6sEAvld9nMVr.jpg",
        "banner_url": "https://image.tmdb.org/t/p/w500/wDWkjobSJm8I5r2ctSPtneUjHxT.jpg",
        "is_franchise": True,
        "category_type": "franchise",
        "sort_order": 2,
        "items": [
            {"movie_id": None, "series_id": 1005, "chronological_order": 1, "release_order": 1, "timeline_event_desc": "2003–2005: Asl Qashqirlar makoni (Kurtlar Vadisi) 97 qism"},
            {"movie_id": 821, "series_id": None, "chronological_order": 2, "release_order": 2, "timeline_event_desc": "2006: Polat Alemdarning Iroqdagi operatsiyasi"},
            {"movie_id": None, "series_id": 1006, "chronological_order": 3, "release_order": 3, "timeline_event_desc": "2007–2016: Kurtlar Vadisi Pusu (Pistirma) davri"},
            {"movie_id": 822, "series_id": None, "chronological_order": 4, "release_order": 4, "timeline_event_desc": "2011: Falastin hududidagi maxsus missiya"},
            {"movie_id": 823, "series_id": None, "chronological_order": 5, "release_order": 5, "timeline_event_desc": "2017: Vatan himoyasi va xalqaro fitnaga qarshi kurash"},
        ]
    },
    {
        "slug": "taxtlar-oyini",
        "name": "Muz va Olov: Taxtlar va Ajdarlar Olami",
        "description": "Vesteros saltanati, Tiriklar va O'liklar urushi, Targarirlar sulolasi va Temir Taxt uchun kurash.",
        "poster_url": "https://image.tmdb.org/t/p/w500/1XS1oqL89opfnbLl8WnZY1O1uJx.jpg",
        "banner_url": "https://image.tmdb.org/t/p/original/7V0Ebks0GgpKvQ7QbLAIdX5dos4.jpg",
        "is_franchise": True,
        "category_type": "franchise",
        "sort_order": 3,
        "items": [
            {"movie_id": None, "series_id": 999, "chronological_order": 1, "release_order": 2, "timeline_event_desc": "Targarirlar parvozi, Ajdarlar raqsi va fuqarolar urushi"},
            {"movie_id": None, "series_id": 998, "chronological_order": 2, "release_order": 1, "timeline_event_desc": "7 Qirollik taxti uchun kurash va Shimoldan kelayotgan Qish"},
        ]
    },
    {
        "slug": "vampirlar-va-borilar",
        "name": "Vampirlar va Bo'rilar Olami",
        "description": "Qonxo'rlar, bo'rilar va g'ayritabiiy mavjudotlar o'rtasidagi sirli muhabbat va qonli janglar.",
        "poster_url": "https://image.tmdb.org/t/p/w500/gbp4zM0FE0n23X4UFY5EBlacrog.jpg",
        "banner_url": "https://image.tmdb.org/t/p/w500/keJOhJXGiLL54EW6QocbyvQGquA.jpg",
        "is_franchise": False,
        "category_type": "theme",
        "sort_order": 4,
        "items": [
            {"movie_id": None, "series_id": 1004, "chronological_order": 1, "release_order": 1, "timeline_event_desc": "Mistik Folls, aka-uka Salvadorlar va Elena Gilbert"},
            {"movie_id": None, "series_id": 1002, "chronological_order": 2, "release_order": 3, "timeline_event_desc": "Ilk vampirlar oilasi Mayklsonlar va Yangi Orlean taxti"},
            {"movie_id": None, "series_id": 1003, "chronological_order": 3, "release_order": 2, "timeline_event_desc": "Skott Makkol va Bikoun Xills bo'rilar to'dasi"},
        ]
    },
    {
        "slug": "christopher-nolan",
        "name": "Kristofer Nolan Durdonalari",
        "description": "Ong osti labirintlari va fazoviy vaqt egilishi — rejissyor Kristofer Nolanning aqlbovar qilmas falsafiy durdonalari.",
        "poster_url": "https://image.tmdb.org/t/p/w500/yQvGrMoipbRoddT0ZR8tPoR7NfX.jpg",
        "banner_url": "https://image.tmdb.org/t/p/w500/xlaY2zyzMfkhk0HSC5VUwzoZPU1.jpg",
        "is_franchise": False,
        "category_type": "theme",
        "sort_order": 5,
        "items": [
            {"movie_id": 825, "series_id": None, "chronological_order": 1, "release_order": 1, "timeline_event_desc": "Ong osti qatlamlari va tush ichidagi tush operatsiyasi"},
            {"movie_id": 826, "series_id": None, "chronological_order": 2, "release_order": 2, "timeline_event_desc": "Vaqt nisbiyligi va insoniyat najoti uchun galaktikalararo safar"},
        ]
    },
    {
        "slug": "superheroes",
        "name": "Superqahramonlar va Qasoskorlar",
        "description": "Marvel kinokoinotining eng ulkan kulminatsiyasi va soxta superqahramonlarni fosh etish.",
        "poster_url": "https://image.tmdb.org/t/p/w500/bR8ISy1O9XQxqiy0fQFw2BX72RQ.jpg",
        "banner_url": "https://image.tmdb.org/t/p/original/in1R2dDc421JxsoRWaIIAqVI2KE.jpg",
        "is_franchise": False,
        "category_type": "theme",
        "sort_order": 6,
        "items": [
            {"movie_id": 827, "series_id": None, "chronological_order": 1, "release_order": 1, "timeline_event_desc": "Koinot taqdiri va Tanosga qarshi so'nggi ittifoq"},
            {"movie_id": None, "series_id": 1000, "chronological_order": 2, "release_order": 2, "timeline_event_desc": "Soxta superqahramonlar va Vought korporatsiyasiga qarshi jazolovchilar"},
        ]
    },
    {
        "slug": "gladiatorlar",
        "name": "Gladiatorlar va Qadimgi Rim",
        "description": "Qadimgi Rim imperiyasi, Kolizey jangi va erkinlik uchun kurashgan sarkarda qasosi.",
        "poster_url": "https://image.tmdb.org/t/p/w500/aDb548BOkFfI4nFm0kx8A3Ezh7H.jpg",
        "banner_url": "https://image.tmdb.org/t/p/w500/aDb548BOkFfI4nFm0kx8A3Ezh7H.jpg",
        "is_franchise": False,
        "category_type": "theme",
        "sort_order": 7,
        "items": [
            {"movie_id": 828, "series_id": None, "chronological_order": 1, "release_order": 1, "timeline_event_desc": "Rim imperatori xiyonati va quldan gladiatorga aylangan sarkarda"},
        ]
    },
    {
        "slug": "kriminal-drama",
        "name": "Kriminal Drama: Mashaqqatlar Sari",
        "description": "Oddiy kimyo o'qituvchisining narkobaron Xayzenbergga aylanishi va jinoyat olami.",
        "poster_url": "https://image.tmdb.org/t/p/w500/anFx9aTOOYqgS3v7x3R84Kz67ly.jpg",
        "banner_url": "https://image.tmdb.org/t/p/w500/anFx9aTOOYqgS3v7x3R84Kz67ly.jpg",
        "is_franchise": False,
        "category_type": "theme",
        "sort_order": 8,
        "items": [
            {"movie_id": None, "series_id": 1001, "chronological_order": 1, "release_order": 1, "timeline_event_desc": "Uolter Uayt va Jessi Pinkmanning metamfetamin imperiyasi"},
        ]
    },
    {
        "slug": "fantastika-va-animatsiya",
        "name": "Epik Fantastika va Animatsiya",
        "description": "Pandora sayyorasining go'zalligi, Titanlar apokalipsisi va Shrekning mashhur ertaklar olami.",
        "poster_url": "https://image.tmdb.org/t/p/w500/wgwldDDlTDDMrluOMkpSA8lyKjv.jpg",
        "banner_url": "https://image.tmdb.org/t/p/w500/gKY6q7SjCkAU6FqvqWybDYgUKIF.jpg",
        "is_franchise": False,
        "category_type": "theme",
        "sort_order": 9,
        "items": [
            {"movie_id": 830, "series_id": None, "chronological_order": 1, "release_order": 1, "timeline_event_desc": "Shrek va Fiona uzoq-uzoq qirollikda"},
            {"movie_id": 829, "series_id": None, "chronological_order": 2, "release_order": 2, "timeline_event_desc": "Pandora sayyorasi va Na'vi qabilasi sarguzashtlari"},
            {"movie_id": 831, "series_id": None, "chronological_order": 3, "release_order": 3, "timeline_event_desc": "Eren Yeger va insoniyatning so'nggi najot jangi"},
        ]
    }
]

async def main():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    dsn = 'postgresql://neondb_owner:npg_un4HXZ9CGJiW@ep-frosty-cherry-aitqstf5-pooler.c-4.us-east-1.aws.neon.tech/neondb'
    
    conn = await asyncpg.connect(dsn, ssl=ctx, timeout=15)
    try:
        # Clean up any collections that are NOT in our curated list
        allowed_slugs = [c["slug"] for c in COLLECTIONS_DATA]
        await conn.execute("DELETE FROM collections WHERE slug != ALL($1::text[])", allowed_slugs)
        
        for c in COLLECTIONS_DATA:
            row = await conn.fetchrow("SELECT id FROM collections WHERE slug = $1", c["slug"])
            if row:
                col_id = row["id"]
                await conn.execute("""
                    UPDATE collections
                    SET name = $1, description = $2, poster_url = $3, banner_url = $4,
                        is_franchise = $5, category_type = $6, sort_order = $7, is_active = true,
                        updated_at = NOW()
                    WHERE id = $8
                """, c["name"], c["description"], c["poster_url"], c["banner_url"],
                    c["is_franchise"], c["category_type"], c["sort_order"], col_id)
                print(f"Updated collection: {c['slug']} (id={col_id})")
            else:
                col_id = await conn.fetchval("""
                    INSERT INTO collections (name, slug, description, poster_url, banner_url,
                                             is_franchise, category_type, is_active, sort_order, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, true, $8, NOW(), NOW())
                    RETURNING id
                """, c["name"], c["slug"], c["description"], c["poster_url"], c["banner_url"],
                    c["is_franchise"], c["category_type"], c["sort_order"])
                print(f"Created collection: {c['slug']} (id={col_id})")

            # Replace items for this collection
            await conn.execute("DELETE FROM collection_items WHERE collection_id = $1", col_id)
            for itm in c["items"]:
                await conn.execute("""
                    INSERT INTO collection_items (collection_id, movie_id, series_id,
                                                 chronological_order, release_order,
                                                 timeline_event_desc, is_locked, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6, false, NOW())
                """, col_id, itm["movie_id"], itm["series_id"],
                    itm["chronological_order"], itm["release_order"], itm["timeline_event_desc"])
            print(f"  Synced {len(c['items'])} items for {c['slug']}")

        print("\nAll real collections synced successfully!")
    finally:
        await conn.close()

if __name__ == '__main__':
    asyncio.run(main())
