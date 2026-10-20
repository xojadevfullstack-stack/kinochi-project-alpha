import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
import asyncio
import os
import random
import uuid
import html
import io
import logging
import httpx
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

load_dotenv(os.path.join(BASE_DIR, ".env.local"))
load_dotenv(os.path.join(BASE_DIR, "backend", ".env"))
load_dotenv(os.path.join(BASE_DIR, ".env"))

from app.core.config import settings
from app.infrastructure.db.session import async_session_factory
from app.infrastructure.db.models.series import SeriesModel, SeasonModel, EpisodeModel
from app.infrastructure.db.models.source import SourceModel
from app.infrastructure.db.models.translation import EpisodeTranslationModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logger = logging.getLogger("series_migration")

TARGET_SUPERGROUP = int(settings.AUTO_TOPIC_CHAT_ID)  # -1003847632555
TARGET_STORAGE = int(settings.STORAGE_CHANNEL_ID)    # -1003762157591
OLD_STORAGE = -1003926001543

async def create_or_get_topic(client: TelegramClient, title: str) -> int:
    from telethon.tl.functions.messages import CreateForumTopicRequest
    peer = await client.get_input_entity(TARGET_SUPERGROUP)
    r_id = random.randint(1, 2**31 - 1)
    while True:
        try:
            res = await client(CreateForumTopicRequest(
                peer=peer,
                title=title[:128],
                random_id=r_id
            ))
            break
        except FloodWaitError as fwe:
            logger.warning(f"Flood wait {fwe.seconds}s on create topic")
            await asyncio.sleep(fwe.seconds + 2)
    topic_id = None
    for u in getattr(res, 'updates', []):
        if hasattr(u, 'message') and hasattr(u.message, 'id'):
            topic_id = u.message.id
            break
        elif hasattr(u, 'id'):
            topic_id = u.id
            break
    if not topic_id:
        for u in getattr(res, 'updates', []):
            if hasattr(u, 'channel_id'):
                topic_id = getattr(u, 'id', None)
    return topic_id

async def fetch_poster_bytes(url: str) -> bytes | None:
    try:
        async with httpx.AsyncClient(timeout=15) as hclient:
            res = await hclient.get(url)
            if res.status_code == 200:
                return res.content
    except Exception as e:
        logger.warning(f"Poster yuklab olishda xatolik ({url}): {e}")
    return None

async def migrate_series(
    client: TelegramClient,
    title: str,
    original_title: str,
    tmdb_id: int,
    poster_url: str,
    description: str,
    seasons_data: dict,
    imdb_rating: float = 8.5,
    release_year: int = 2024,
    status: str = "completed",
    genres: str = "Drama, Kriminal",
):
    safe_title = title.encode('ascii', errors='replace').decode('ascii')
    logger.info(f"==================================================")
    logger.info(f"=== Boshlanmoqda: {safe_title} ({release_year}) ===")
    logger.info(f"==================================================")

    poster_bytes = await fetch_poster_bytes(poster_url)
    
    topic_title = f"{title}"
    logger.info(f"Yangi superguruhda Topic ochilmoqda: '{safe_title}'...")
    topic_id = await create_or_get_topic(client, topic_title)
    logger.info(f"Topic ochildi! Topic ID: {topic_id}")
    await asyncio.sleep(2.0)

    caption_banner = (
        f"🎬 <b>{html.escape(title)}</b> ({release_year})\n"
        f"🎭 <b>Janr:</b> {genres}\n"
        f"⭐ <b>IMDb:</b> {imdb_rating}/10\n"
        f"🇺🇿 <b>Tili:</b> O'zbek tilida\n\n"
        f"📖 <b>Tavsif:</b>\n{html.escape(description[:700])}\n\n"
        f"🍿 @kinochi_mvp_bot orqali yuklandi."
    )

    topic_banner_msg = None
    if poster_bytes:
        f_st = io.BytesIO(poster_bytes)
        f_st.name = "poster.jpg"
        await client.send_file(TARGET_STORAGE, file=f_st, caption=caption_banner, parse_mode="html")
        await asyncio.sleep(1.5)

        f_sg = io.BytesIO(poster_bytes)
        f_sg.name = "poster.jpg"
        topic_banner_msg = await client.send_file(
            TARGET_SUPERGROUP,
            file=f_sg,
            caption=caption_banner,
            reply_to=topic_id,
            parse_mode="html"
        )
    else:
        await client.send_message(TARGET_STORAGE, message=caption_banner, parse_mode="html")
        topic_banner_msg = await client.send_message(TARGET_SUPERGROUP, message=caption_banner, reply_to=topic_id, parse_mode="html")
    
    await asyncio.sleep(1.5)

    if topic_banner_msg:
        try:
            from telethon.tl.functions.messages import UpdatePinnedMessageRequest
            await client(UpdatePinnedMessageRequest(
                peer=TARGET_SUPERGROUP,
                id=topic_banner_msg.id,
                silent=True
            ))
            logger.info(f"Banner topicga qadaldi (Msg ID: {topic_banner_msg.id})")
        except Exception as e:
            logger.warning(f"Bannerni qadashda ogohlantirish: {e}")

    await asyncio.sleep(1.5)

    async with async_session_factory() as session:
        src = SourceModel(
            name=title,
            type="superguruh",
            chat_id=TARGET_SUPERGROUP,
            topic_id=topic_id
        )
        session.add(src)
        await session.flush()

        series_obj = SeriesModel(
            title=title,
            description=description,
            status=status,
            publish_status="published",
            is_18_plus=False,
            imdb_rating=imdb_rating,
            release_year=release_year,
            tmdb_id=tmdb_id,
            poster_url=poster_url,
            source_id=src.id,
            source_type="superguruh",
            custom_source_name="Kinochi @kinochi_mvp_bot"
        )
        session.add(series_obj)
        await session.flush()

        total_migrated = 0

        for s_num in sorted(seasons_data.keys()):
            old_msg_ids = seasons_data[s_num]
            logger.info(f"{safe_title} -> {s_num}-Mavsum: {len(old_msg_ids)} ta qism ko'chirilmoqda...")

            season_obj = SeasonModel(
                series_id=series_obj.id,
                season_number=s_num,
                title=f"{s_num}-Mavsum",
                status="completed" if status == "completed" else "ongoing",
                poster_url=poster_url,
                episode_count=len(old_msg_ids)
            )
            session.add(season_obj)
            await session.flush()

            for ep_idx, old_ep_msg_id in enumerate(old_msg_ids, start=1):
                try:
                    ep_msg = await client.get_messages(OLD_STORAGE, ids=old_ep_msg_id)
                except FloodWaitError as fe:
                    logger.warning(f"FloodWait: {fe.seconds} soniya kutilmoqda...")
                    await asyncio.sleep(fe.seconds + 2)
                    ep_msg = await client.get_messages(OLD_STORAGE, ids=old_ep_msg_id)

                if not ep_msg or not (ep_msg.video or ep_msg.document):
                    logger.warning(f"  Msg ID {old_ep_msg_id} da media topilmadi!")
                    continue

                display_code = f"S{s_num}-CH{ep_idx}"
                ep_code = uuid.uuid4().hex[:8]

                caption_ep = (
                    f"🎬 <b>{html.escape(title)}</b>\n"
                    f"📺 <b>{s_num}-Mavsum, {ep_idx}-Qism</b>\n"
                    f"🔑 <b>Qism kodi:</b> <code>{display_code}</code>\n"
                    f"🇺🇿 <b>Tili:</b> O'zbek tilida\n\n"
                    f"🍿 @kinochi_mvp_bot orqali yuklandi."
                )

                try:
                    new_st_msg = await client.send_file(
                        TARGET_STORAGE,
                        file=ep_msg.media,
                        caption=caption_ep,
                        parse_mode="html"
                    )
                except FloodWaitError as fe:
                    logger.warning(f"FloodWait Storage: {fe.seconds}s...")
                    await asyncio.sleep(fe.seconds + 2)
                    new_st_msg = await client.send_file(
                        TARGET_STORAGE,
                        file=ep_msg.media,
                        caption=caption_ep,
                        parse_mode="html"
                    )

                await asyncio.sleep(1.0)

                try:
                    await client.send_file(
                        TARGET_SUPERGROUP,
                        file=ep_msg.media,
                        caption=caption_ep,
                        reply_to=topic_id,
                        parse_mode="html"
                    )
                except FloodWaitError as fe:
                    logger.warning(f"FloodWait Supergroup: {fe.seconds}s...")
                    await asyncio.sleep(fe.seconds + 2)
                    await client.send_file(
                        TARGET_SUPERGROUP,
                        file=ep_msg.media,
                        caption=caption_ep,
                        reply_to=topic_id,
                        parse_mode="html"
                    )

                await asyncio.sleep(1.2)

                ep_obj = EpisodeModel(
                    season_id=season_obj.id,
                    episode_number=ep_idx,
                    code=ep_code,
                    display_code=display_code,
                    title=f"{ep_idx}-qism",
                    source_message_id=new_st_msg.id
                )
                session.add(ep_obj)
                await session.flush()

                trans_obj = EpisodeTranslationModel(
                    episode_id=ep_obj.id,
                    language="O'zbekcha",
                    storage_channel_message_id=new_st_msg.id
                )
                session.add(trans_obj)

                total_migrated += 1
                logger.info(f"  [OK] {safe_title} {display_code} (ST Msg ID: {new_st_msg.id})")

        await session.commit()
        logger.info(f"=== MUVAFFAQIYAT: '{safe_title}' barcha {total_migrated} ta qismi ko'chirildi! ===")

SERIES_LIST = [
    # 1. Mashaqqatlar sari (Breaking Bad) — 62 eps
    {
        "title": "Mashaqqatlar sari",
        "original_title": "Breaking Bad",
        "tmdb_id": 1396,
        "poster_url": "https://image.tmdb.org/t/p/w500/anFx9aTOOYqgS3v7x3R84Kz67ly.jpg",
        "description": "Oddiy maktab kimyo o'qituvchisi Uolter Uaytga o'pka saratoni tashxisi qo'yiladi. U oilasining kelajagini ta'minlash maqsadida sobiq talabasi Jessi Pinkman bilan birga metamfetamin ishlab chiqarishni yo'lga qo'yadi va asta-sekin jinoyat olamining shafqatsiz qiroliga aylanadi.",
        "imdb_rating": 9.5,
        "release_year": 2008,
        "status": "completed",
        "genres": "Drama, Kriminal, Triller",
        "seasons_data": {
            1: [670, 671, 672, 673, 674, 675, 676],
            2: [678, 679, 680, 681, 682, 683, 684, 685, 686, 687, 688, 689, 690],
            3: [692, 693, 694, 695, 696, 697, 698, 699, 700, 701, 702, 703, 704],
            4: [706, 707, 708, 709, 710, 711, 712, 713, 714, 715, 716, 717, 718],
            5: [720, 721, 722, 723, 724, 725, 726, 727, 728, 729, 730, 731, 732, 733, 734, 735]
        }
    },
    # 2. Yigitlar (The Boys) — 31 eps
    {
        "title": "Yigitlar",
        "original_title": "The Boys",
        "tmdb_id": 76479,
        "poster_url": "https://image.tmdb.org/t/p/w500/in1R2dDc421JxsoRWaIIAqVI2KE.jpg",
        "description": "Superqahramonlar mashhurlik va hokimiyatdan o'z manfaatlari yo'lida foydalanganda, o'zini 'Yigitlar' deb ataydigan norasmiy guruh ularni fosh qilish va jilovlash uchun xavfli jangga kirishadi.",
        "imdb_rating": 8.7,
        "release_year": 2019,
        "status": "ongoing",
        "genres": "Fantastika, Jangari, Komediya",
        "seasons_data": {
            1: [2044, 2045, 2046, 2047, 2048, 2049, 2050, 2051],
            2: [2053, 2054, 2055, 2056, 2057, 2058, 2059, 2060],
            3: [2065, 2066, 2067, 2068, 2069, 2070, 2071, 2073],
            4: [2075, 2076, 2077, 2078, 2079, 2080, 2081]
        }
    },
    # 3. Sherlok (Sherlock BBC) — 12 eps
    {
        "title": "Sherlok",
        "original_title": "Sherlock",
        "tmdb_id": 19885,
        "poster_url": "https://image.tmdb.org/t/p/w500/7WTsnHkbA0FaG6R9twfFde0I9hl.jpg",
        "description": "Artur Konan Doylning mashhur asarining zamonaviy talqini. Sherlok Xolms va doktor Jon Uotson XXI asr Londonidagi eng murakkab jinoyatlarni fosh qilishadi.",
        "imdb_rating": 9.1,
        "release_year": 2010,
        "status": "completed",
        "genres": "Detektiv, Kriminal, Drama",
        "seasons_data": {
            1: [737, 738, 739],
            2: [741, 742, 743],
            3: [745, 746, 747],
            4: [749, 750, 751]
        }
    },
    # 4. Kontinental (The Continental) — 3 eps
    {
        "title": "Kontinental: Jon Uik dunyosidan",
        "original_title": "The Continental: From the World of John Wick",
        "tmdb_id": 114461,
        "poster_url": "https://image.tmdb.org/t/p/w500/eiJeWeCAEZAmRppnXHiTWDcCd3Q.jpg",
        "description": "1970-yillardagi Nyu-York. Yosh Uinston Skottning suiqasdchilar uchun xavfsiz boshpana bo'lgan afsonaviy Kontinental mehmonxonasini boshqarishga bo'lgan yo'li.",
        "imdb_rating": 7.3,
        "release_year": 2023,
        "status": "completed",
        "genres": "Jangari, Triller, Kriminal",
        "seasons_data": {
            1: [2898, 2900, 2902]
        }
    },
    # 5. Barchamiz o'likmiz (All of Us Are Dead) — 12 eps
    {
        "title": "Barchamiz oʻlikmiz",
        "original_title": "All of Us Are Dead",
        "tmdb_id": 99966,
        "poster_url": "https://image.tmdb.org/t/p/w500/pTEFqAjLd5YTsMD6NSUxV6Dq7A6.jpg",
        "description": "Maktabda zombi virusi tarqalgach, qamalib qolgan bir guruh yuqori sinf o'quvchilari omon qolish va zombilarga aylanmaslik uchun birgalikda kurashadilar.",
        "imdb_rating": 7.5,
        "release_year": 2022,
        "status": "ongoing",
        "genres": "Dahshat, Triller, Drama",
        "seasons_data": {
            1: [2116, 2117, 2118, 2119, 2120, 2121, 2122, 2123, 2124, 2125, 2126, 2127]
        }
    },
    # 6. Zulmat (Dark) — 28 eps
    {
        "title": "Zulmat",
        "original_title": "Dark",
        "tmdb_id": 70523,
        "poster_url": "https://image.tmdb.org/t/p/w500/wSXJHO9WHLb0aCwvQrtco7vOmWA.jpg",
        "description": "Nemis shaharchasida ikki bolaning g'oyib bo'lishi to'rtta oilaning o'tmishi, sirlari va vaqtlararo sayohat bilan bog'liq sirli chalkashliklarni ochib tashlaydi.",
        "imdb_rating": 8.7,
        "release_year": 2017,
        "status": "completed",
        "genres": "Ilmiy fantastika, Triller, Sirli",
        "seasons_data": {
            1: [1974, 1975, 1976, 1977, 1978, 1979, 1980, 1981, 1982, 1983],
            2: [1985, 1986, 1987, 1988, 1989, 1990, 1991, 1992, 1993, 1994],
            3: [1996, 1997, 1998, 1999, 2000, 2001, 2002, 2003]
        }
    },
    # 7. Jodugar (The Witcher) — 31 eps
    {
        "title": "Jodugar",
        "original_title": "The Witcher",
        "tmdb_id": 71912,
        "poster_url": "https://image.tmdb.org/t/p/w500/AoGsDM02UVt0npBA8OvpDcZbaMi.jpg",
        "description": "Riviya Geralti — maxluqlar ovchisi bo'lib, odamlar ko'pincha hayvonlardan ham yovuzroq bo'lgan dunyoda o'z o'rnini topishga harakat qiladi.",
        "imdb_rating": 8.0,
        "release_year": 2019,
        "status": "ongoing",
        "genres": "Fentezi, Jangari, Sarguzasht",
        "seasons_data": {
            1: [1586, 1587, 1588, 1589, 1590, 1591, 1592, 1593],
            2: [1595, 1596, 1597, 1598, 1599, 1600, 1601, 1602],
            3: [1604, 1605, 1606, 1607, 1608, 1609, 1610, 1611],
            4: [1613, 1614, 1615, 1616, 1617, 1618, 1619]
        }
    },
    # 8. Vikinglar (Vikings) — 89 eps
    {
        "title": "Vikinglar",
        "original_title": "Vikings",
        "tmdb_id": 44217,
        "poster_url": "https://image.tmdb.org/t/p/w500/bQLrHIRNEkE3PdIWQrZHynQZazu.jpg",
        "description": "Afsonaviy viking jangchisi Ragnar Lodbrok va uning birodarlarining noma'lum g'arbiy hududlarni zabt etish yo'lidagi shonli va qonli janglari.",
        "imdb_rating": 8.5,
        "release_year": 2013,
        "status": "completed",
        "genres": "Tarixiy, Jangari, Drama",
        "seasons_data": {
            1: [1380, 1381, 1382, 1383, 1384, 1385, 1386, 1387, 1388],
            2: [1390, 1391, 1392, 1394, 1395, 1396, 1397, 1398, 1399, 1400],
            3: [1402, 1403, 1404, 1405, 1406, 1407, 1408, 1409, 1410, 1411],
            4: [1413, 1414, 1415, 1416, 1417, 1418, 1419, 1420, 1421, 1422, 1423, 1424, 1425, 1426, 1427, 1428, 1429, 1430, 1431, 1432],
            5: [1434, 1435, 1436, 1437, 1438, 1439, 1440, 1441, 1442, 1443, 1444, 1445, 1446, 1447, 1448, 1449, 1450, 1451, 1452, 1453],
            6: [1455, 1456, 1457, 1458, 1459, 1460, 1461, 1462, 1463, 1464, 1465, 1466, 1467, 1468, 1469, 1470, 1471, 1472, 1473, 1474]
        }
    },
    # 9. Panjara ortida (Prison Break) — 88 eps
    {
        "title": "Panjara ortida",
        "original_title": "Prison Break",
        "tmdb_id": 2288,
        "poster_url": "https://image.tmdb.org/t/p/w500/wnmNPaLvhnMeOqnWlhNkYCZxtda.jpg",
        "description": "Maykl Skofild begunoh ekanligiga ishongan akasi Linkoln Berrouzni o'lim jazosidan qutqarish uchun o'ziga xos murakkab reja tuzadi va ataylab o'sha qamoqxonaga tushadi.",
        "imdb_rating": 8.3,
        "release_year": 2005,
        "status": "completed",
        "genres": "Jangari, Kriminal, Triller",
        "seasons_data": {
            1: [1823, 1824, 1825, 1826, 1827, 1828, 1829, 1830, 1831, 1832, 1833, 1834, 1835, 1836, 1837, 1838, 1839, 1840, 1841, 1842, 1843, 1844],
            2: [1846, 1847, 1848, 1849, 1850, 1851, 1852, 1853, 1854, 1855, 1856, 1857, 1858, 1859, 1860, 1861, 1862, 1863, 1864, 1866, 1868, 1870],
            3: [1887, 1889, 1891, 1893, 1895, 1897, 1898, 1899, 1900, 1901, 1902, 1903, 1904],
            4: [1906, 1907, 1908, 1909, 1910, 1911, 1912, 1913, 1914, 1915, 1916, 1917, 1918, 1919, 1920, 1921, 1922, 1923, 1924, 1925, 1926, 1927],
            5: [1929, 1930, 1931, 1932, 1933, 1934, 1935, 1936, 1937]
        }
    },
    # 10. Yosh bo'ri (Teen Wolf) — 99 eps
    {
        "title": "Yosh boʻri",
        "original_title": "Teen Wolf",
        "tmdb_id": 34524,
        "poster_url": "https://image.tmdb.org/t/p/w500/wjKBTcNy1xihmExqJI8kM2qvavP.jpg",
        "description": "Skott Makkoll o'rmonda sirli bo'ri tomonidan tishlangach, g'ayritabiiy qobiliyatlarga ega bo'ladi. U yangi qobiliyatlarini boshqarish bilan birga o'z shahrini yovuz kuchlardan himoya qilishga majbur.",
        "imdb_rating": 7.7,
        "release_year": 2011,
        "status": "completed",
        "genres": "Drama, Fentezi, Dahshat",
        "seasons_data": {
            1: [1665, 1666, 1667, 1668, 1669, 1670, 1671, 1672, 1673, 1674, 1675, 1676],
            2: [1678, 1679, 1680, 1681, 1682, 1683, 1684, 1685, 1686, 1687, 1688, 1689],
            3: [1691, 1692, 1693, 1694, 1695, 1696, 1697, 1698, 1699, 1700, 1701, 1702, 1703, 1704, 1705, 1706, 1707, 1708, 1709, 1710, 1711, 1712, 1713, 1714],
            4: [1730, 1731, 1732, 1733, 1734, 1735, 1736, 1737, 1738, 1739, 1740, 1741],
            5: [1743, 1744, 1745, 1746, 1747, 1748, 1749, 1750, 1751, 1752, 1753, 1754, 1755, 1756, 1757, 1758, 1759, 1760, 1761],
            6: [1763, 1764, 1765, 1766, 1767, 1768, 1769, 1770, 1771, 1772, 1773, 1774, 1775, 1776, 1777, 1778, 1779, 1780, 1781, 1782]
        }
    }
]

async def main():
    api_id = int(os.getenv("TELEGRAM_API_ID"))
    api_hash = os.getenv("TELEGRAM_API_HASH")
    session_str = os.getenv("TELEGRAM_STRING_SESSION")

    client = TelegramClient(StringSession(session_str), api_id, api_hash)
    await client.connect()
    await client.get_dialogs()

    for item in SERIES_LIST:
        try:
            await migrate_series(
                client=client,
                title=item["title"],
                original_title=item["original_title"],
                tmdb_id=item["tmdb_id"],
                poster_url=item["poster_url"],
                description=item["description"],
                seasons_data=item["seasons_data"],
                imdb_rating=item["imdb_rating"],
                release_year=item["release_year"],
                status=item["status"],
                genres=item["genres"]
            )
            await asyncio.sleep(4.0)
        except Exception as e:
            logger.error(f"Xatolik '{item['title']}' ni ko'chirishda: {e}", exc_info=True)

    await client.disconnect()
    logger.info("=== BARCHA ASOSIY SERIALLAR KO'CHIRILDI! ===")

if __name__ == "__main__":
    asyncio.run(main())
