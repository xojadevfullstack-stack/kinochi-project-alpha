import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import asyncio
import os
import random
import secrets
import logging
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
from app.infrastructure.db.models.movie import MovieModel
from app.infrastructure.db.models.translation import MovieTranslationModel
from sqlalchemy import select
from telethon.tl.functions.messages import CreateForumTopicRequest

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logger = logging.getLogger("individual_topic_migration")

TARGET_SUPERGROUP = int(settings.AUTO_TOPIC_CHAT_ID)  # -1003847632555
TARGET_STORAGE = int(settings.STORAGE_CHANNEL_ID)    # -1003762157591
OLD_STORAGE = -1003926001543

ALL_MOVIES = [
    # ── 1. O'RGIMCHAK-ODAM (SPIDER-MAN UNIVERSE) — 11 TA FILM ──
    {"title": "O'rgimchak odam 1", "original_title": "Spider-Man", "tmdb_id": 557, "poster_url": "https://image.tmdb.org/t/p/w500/uxNYgyfM9zeIQevvLON8zlPLocS.jpg", "release_year": 2002, "imdb_rating": 7.4, "old_msg_id": 2765},
    {"title": "O'rgimchak odam 2", "original_title": "Spider-Man 2", "tmdb_id": 558, "poster_url": "https://image.tmdb.org/t/p/w500/VBS4TFi0R7nhrPeDAc6TmBt8XC.jpg", "release_year": 2004, "imdb_rating": 7.5, "old_msg_id": 2769},
    {"title": "O'rgimchak odam 3", "original_title": "Spider-Man 3", "tmdb_id": 559, "poster_url": "https://image.tmdb.org/t/p/w500/ngNCHBZgNdbGisLbi1hImGh2SHl.jpg", "release_year": 2007, "imdb_rating": 6.3, "old_msg_id": 2767},
    {"title": "Yangi O'rgimchak odam 1", "original_title": "The Amazing Spider-Man", "tmdb_id": 1930, "poster_url": "https://image.tmdb.org/t/p/w500/kby3x8wic9Lx4qEfstLu2vFHTVj.jpg", "release_year": 2012, "imdb_rating": 6.9, "old_msg_id": 8030},
    {"title": "Yangi O'rgimchak odam 2: Yuksak kuchlanish", "original_title": "The Amazing Spider-Man 2", "tmdb_id": 102382, "poster_url": "https://image.tmdb.org/t/p/w500/ydQMjes6xheS1kC0lJ6DZl54Yva.jpg", "release_year": 2014, "imdb_rating": 6.6, "old_msg_id": 8044},
    {"title": "O'rgimchak odam: Uyga qaytish", "original_title": "Spider-Man: Homecoming", "tmdb_id": 315635, "poster_url": "https://image.tmdb.org/t/p/w500/s0DiivKEQWKZzIaw5JWbrkDGVyv.jpg", "release_year": 2017, "imdb_rating": 7.4, "old_msg_id": 8026},
    {"title": "O'rgimchak odam: Uydan uzoqda", "original_title": "Spider-Man: Far From Home", "tmdb_id": 429617, "poster_url": "https://image.tmdb.org/t/p/w500/wL1S9750WaxxvbbuUBfkbAskDd8.jpg", "release_year": 2019, "imdb_rating": 7.4, "old_msg_id": 8024},
    {"title": "O'rgimchak odam: Uyga yo'l yo'q", "original_title": "Spider-Man: No Way Home", "tmdb_id": 634649, "poster_url": "https://image.tmdb.org/t/p/w500/qad0kyRLHG1Qccp2A0YCCUbvhiD.jpg", "release_year": 2021, "imdb_rating": 8.2, "old_msg_id": 2241},
    {"title": "O'rgimchak odam: Yondosh olam", "original_title": "Spider-Man: Into the Spider-Verse", "tmdb_id": 324857, "poster_url": "https://image.tmdb.org/t/p/w500/oCAi3NdfXNYLd8PROu5ycUhVety.jpg", "release_year": 2018, "imdb_rating": 8.4, "old_msg_id": 8028},
    {"title": "O'rgimchak odam: Olamlar to'ri", "original_title": "Spider-Man: Across the Spider-Verse", "tmdb_id": 569094, "poster_url": "https://image.tmdb.org/t/p/w500/wH0kbTvbrvtlCygso7Ye2ZfGfM1.jpg", "release_year": 2023, "imdb_rating": 8.6, "old_msg_id": 8042},
    {"title": "Venom", "original_title": "Venom", "tmdb_id": 335983, "poster_url": "https://image.tmdb.org/t/p/w500/8Gyl0fknqiZeCLm9XitxCXQmEL9.jpg", "release_year": 2018, "imdb_rating": 6.7, "old_msg_id": 8270},

    # ── 2. KARIB DENGIZI QAROQCHILARI — 5 TA FILM ──
    {"title": "Karib dengizi qaroqchilari 1: Qora marvarid tavqi la'nati", "original_title": "Pirates of the Caribbean: The Curse of the Black Pearl", "tmdb_id": 22, "poster_url": "https://image.tmdb.org/t/p/w500/70xRYK8orGWA7NfxvzhtkjpZAD6.jpg", "release_year": 2003, "imdb_rating": 8.1, "old_msg_id": 2743},
    {"title": "Karib dengizi qaroqchilari 2: Murdalar sandig'i", "original_title": "Pirates of the Caribbean: Dead Man's Chest", "tmdb_id": 58, "poster_url": "https://image.tmdb.org/t/p/w500/guSoA2bedeYB2xGTBKYLx0biENV.jpg", "release_year": 2006, "imdb_rating": 7.4, "old_msg_id": 2745},
    {"title": "Karib dengizi qaroqchilari 3: Dunyolar chegarasida", "original_title": "Pirates of the Caribbean: At World's End", "tmdb_id": 285, "poster_url": "https://image.tmdb.org/t/p/w500/e69Ov9pCwR6OYQLcrvsodrCBWlc.jpg", "release_year": 2007, "imdb_rating": 7.1, "old_msg_id": 2747},
    {"title": "Karib dengizi qaroqchilari 4: Noma'lum sohillarda", "original_title": "Pirates of the Caribbean: On Stranger Tides", "tmdb_id": 1865, "poster_url": "https://image.tmdb.org/t/p/w500/mPWUHDeVulOQfpcNzLpzm7VfIsm.jpg", "release_year": 2011, "imdb_rating": 6.6, "old_msg_id": 2749},
    {"title": "Karib dengizi qaroqchilari 5: Murdalar ertak aytmaydi", "original_title": "Pirates of the Caribbean: Dead Men Tell No Tales", "tmdb_id": 282035, "poster_url": "https://image.tmdb.org/t/p/w500/it3GF74zccZJLZQg1OfsgSJRrVH.jpg", "release_year": 2017, "imdb_rating": 6.5, "old_msg_id": 2751},

    # ── 3. JON UIK (JOHN WICK) — 5 TA FILM ──
    {"title": "Jon Uik 1", "original_title": "John Wick", "tmdb_id": 245891, "poster_url": "https://image.tmdb.org/t/p/w500/2hfeF2566IKZ30c1BAay0N2lxBr.jpg", "release_year": 2014, "imdb_rating": 7.4, "old_msg_id": 8014},
    {"title": "Jon Uik 2", "original_title": "John Wick: Chapter 2", "tmdb_id": 324552, "poster_url": "https://image.tmdb.org/t/p/w500/60dPOD22s6TS2SfQiiOGOePBg8N.jpg", "release_year": 2017, "imdb_rating": 7.5, "old_msg_id": 8012},
    {"title": "Jon Uik 3: Parabellum", "original_title": "John Wick: Chapter 3 - Parabellum", "tmdb_id": 458156, "poster_url": "https://image.tmdb.org/t/p/w500/2RDx4bMYF5TbTdTBoOwDLDgIej.jpg", "release_year": 2019, "imdb_rating": 7.4, "old_msg_id": 8016},
    {"title": "Jon Uik 4", "original_title": "John Wick: Chapter 4", "tmdb_id": 603692, "poster_url": "https://image.tmdb.org/t/p/w500/o29otcx30U3EkqNVGC2feJVz5yr.jpg", "release_year": 2023, "imdb_rating": 7.7, "old_msg_id": 2893},
    {"title": "Balerina - Jon Uik olamidan", "original_title": "From the World of John Wick: Ballerina", "tmdb_id": 541134, "poster_url": "https://image.tmdb.org/t/p/w500/oDOygUWO44K08apRKWaJUBtVyel.jpg", "release_year": 2025, "imdb_rating": 7.0, "old_msg_id": 2896},

    # ── 4. MATRITSA (THE MATRIX) — 4 TA FILM ──
    {"title": "Matritsa 1", "original_title": "The Matrix", "tmdb_id": 603, "poster_url": "https://image.tmdb.org/t/p/w500/kEDbym5htJgDQNenjUtSJxAHysB.jpg", "release_year": 1999, "imdb_rating": 8.7, "old_msg_id": 8066},
    {"title": "Matritsa 2: Qayta yuklash", "original_title": "The Matrix Reloaded", "tmdb_id": 604, "poster_url": "https://image.tmdb.org/t/p/w500/d0xVNNxIYxId2qHkqpgE39soOvD.jpg", "release_year": 2003, "imdb_rating": 7.2, "old_msg_id": 8068},
    {"title": "Matritsa 3: Revolyutsiya", "original_title": "The Matrix Revolutions", "tmdb_id": 605, "poster_url": "https://image.tmdb.org/t/p/w500/19LNhQz4nwbwS95CQ9LHLxAUAXB.jpg", "release_year": 2003, "imdb_rating": 6.8, "old_msg_id": 8070},
    {"title": "Matritsa 4: Qayta tirilish", "original_title": "The Matrix Resurrections", "tmdb_id": 624860, "poster_url": "https://image.tmdb.org/t/p/w500/wUNFs1bTM8O4ZmRNU3Pgi6c68sX.jpg", "release_year": 2021, "imdb_rating": 5.7, "old_msg_id": 8072},

    # ── 5. TERMINATOR — 4 TA FILM ──
    {"title": "Terminator 1", "original_title": "The Terminator", "tmdb_id": 218, "poster_url": "https://image.tmdb.org/t/p/w500/hcItc8IMO0WKyRWPGkI6xtKVu6X.jpg", "release_year": 1984, "imdb_rating": 8.1, "old_msg_id": 8116},
    {"title": "Terminator 2: Qiyomat kuni", "original_title": "Terminator 2: Judgment Day", "tmdb_id": 280, "poster_url": "https://image.tmdb.org/t/p/w500/67MopMcqqke4sJmcOwY5zu3kmYz.jpg", "release_year": 1991, "imdb_rating": 8.6, "old_msg_id": 8114},
    {"title": "Terminator 3: Mashinalar isyoni", "original_title": "Terminator 3: Rise of the Machines", "tmdb_id": 296, "poster_url": "https://image.tmdb.org/t/p/w500/nnZlp31UgvkRuIzSmCTHO1SkvQ.jpg", "release_year": 2003, "imdb_rating": 6.3, "old_msg_id": 8118},
    {"title": "Terminator 6: Qorong'u taqdir", "original_title": "Terminator: Dark Fate", "tmdb_id": 290859, "poster_url": "https://image.tmdb.org/t/p/w500/ffULB4SNiMuTbEl8dGPnU185hfe.jpg", "release_year": 2019, "imdb_rating": 6.2, "old_msg_id": 8112},

    # ── 6. BETMEN (BATMAN) — 6 TA FILM ──
    {"title": "Betmen (1989)", "original_title": "Batman", "tmdb_id": 268, "poster_url": "https://image.tmdb.org/t/p/w500/tLALOMEJoPiozgvEmJtwpEFfktS.jpg", "release_year": 1989, "imdb_rating": 7.5, "old_msg_id": 8051},
    {"title": "Betmenning qaytishi", "original_title": "Batman Returns", "tmdb_id": 364, "poster_url": "https://image.tmdb.org/t/p/w500/cecrP78sZpxfZI70V8Oeqx6yiON.jpg", "release_year": 1992, "imdb_rating": 7.1, "old_msg_id": 2780},
    {"title": "Betmen: Muqaddima", "original_title": "Batman Begins", "tmdb_id": 272, "poster_url": "https://image.tmdb.org/t/p/w500/wiCotiyukYXWwlL1ZcjyxxhTthi.jpg", "release_year": 2005, "imdb_rating": 8.2, "old_msg_id": 2777},
    {"title": "Qorong'i ritsar", "original_title": "The Dark Knight", "tmdb_id": 155, "poster_url": "https://image.tmdb.org/t/p/w500/aPtN76OjnNKLqCJ2FJBnQOIL031.jpg", "release_year": 2008, "imdb_rating": 9.0, "old_msg_id": 8048},
    {"title": "Qorong'i ritsar: Afsonaning qaytishi", "original_title": "The Dark Knight Rises", "tmdb_id": 49026, "poster_url": "https://image.tmdb.org/t/p/w500/cAwasqprFijx73Hz9qMBcLyEA5N.jpg", "release_year": 2012, "imdb_rating": 8.4, "old_msg_id": 2775},
    {"title": "Betmen (2022)", "original_title": "The Batman", "tmdb_id": 414906, "poster_url": "https://image.tmdb.org/t/p/w500/3EXgl14Wmr5NcbYnBy1kavGHnvh.jpg", "release_year": 2022, "imdb_rating": 7.8, "old_msg_id": 2771},

    # ── 7. LABIRINT YUGURUVCHISI (THE MAZE RUNNER) — 3 TA FILM ──
    {"title": "Labirint xavfli tuzoq 1", "original_title": "The Maze Runner", "tmdb_id": 198663, "poster_url": "https://image.tmdb.org/t/p/w500/fvy2LrxQzSCpUuGaB9jK5z1NeA6.jpg", "release_year": 2014, "imdb_rating": 6.8, "old_msg_id": 8078},
    {"title": "Labirint 2: Olov iskanjasida", "original_title": "Maze Runner: The Scorch Trials", "tmdb_id": 281518, "poster_url": "https://image.tmdb.org/t/p/w500/vhPDvT7W8A4FLPwgAMKZHGqJHtv.jpg", "release_year": 2015, "imdb_rating": 6.3, "old_msg_id": 8094},
    {"title": "Labirint 3: O'limga qarshi", "original_title": "Maze Runner: The Death Cure", "tmdb_id": 336843, "poster_url": "https://image.tmdb.org/t/p/w500/6ps20wVKQghAx0KBTQvPcLPdLlc.jpg", "release_year": 2018, "imdb_rating": 6.3, "old_msg_id": 8098},

    # ── 8. MUMIYA (THE MUMMY) — 3 TA FILM ──
    {"title": "Mumiya 1", "original_title": "The Mummy", "tmdb_id": 564, "poster_url": "https://image.tmdb.org/t/p/w500/jzwDpKRBi1gbqIcHLV2LdFqP2rb.jpg", "release_year": 1999, "imdb_rating": 7.1, "old_msg_id": 8124},
    {"title": "Mumiya 2: Qaytish", "original_title": "The Mummy Returns", "tmdb_id": 1734, "poster_url": "https://image.tmdb.org/t/p/w500/xvr0yOUvymowA6bIhSxny737Chp.jpg", "release_year": 2001, "imdb_rating": 6.4, "old_msg_id": 8122},
    {"title": "Mumiya 3: Ajdar imperatori maqbarasi", "original_title": "The Mummy: Tomb of the Dragon Emperor", "tmdb_id": 787, "poster_url": "https://image.tmdb.org/t/p/w500/i3hxOQV0F334Vb4HMFxhI1J0iyZ.jpg", "release_year": 2008, "imdb_rating": 5.2, "old_msg_id": 8126},

    # ── 9. O'YINCHOQLAR TARIXI (TOY STORY) — 4 TA FILM ──
    {"title": "O'yinchoqlar tarixi 1", "original_title": "Toy Story", "tmdb_id": 862, "poster_url": "https://image.tmdb.org/t/p/w500/gRLk7XpdRyNa697taDKtFx3l6qV.jpg", "release_year": 1995, "imdb_rating": 8.3, "old_msg_id": 8343},
    {"title": "O'yinchoqlar tarixi 2", "original_title": "Toy Story 2", "tmdb_id": 863, "poster_url": "https://image.tmdb.org/t/p/w500/descLErszABnAy79SDTzupmPD7e.jpg", "release_year": 1999, "imdb_rating": 7.9, "old_msg_id": 8341},
    {"title": "O'yinchoqlar tarixi 3", "original_title": "Toy Story 3", "tmdb_id": 10193, "poster_url": "https://image.tmdb.org/t/p/w500/2IWIk34c9fMv7xJQ5ur4Z3O1Hh9.jpg", "release_year": 2010, "imdb_rating": 8.3, "old_msg_id": 8339},
    {"title": "O'yinchoqlar tarixi 4", "original_title": "Toy Story 4", "tmdb_id": 301528, "poster_url": "https://image.tmdb.org/t/p/w500/flLgw8DJKbjSblWnZvTvvYL2pRr.jpg", "release_year": 2019, "imdb_rating": 7.7, "old_msg_id": 8337},

    # ── 10. SHREK — 5 TA QISM (Shrek 1 allaqachon ko'chirilgan, tekshirib o'tkaziladi) ──
    {"title": "Shrek 1", "original_title": "Shrek", "tmdb_id": 808, "poster_url": "https://image.tmdb.org/t/p/w500/5OPCH713UIEeWuvRZpVkkzrZ3Hd.jpg", "release_year": 2001, "imdb_rating": 7.9, "old_msg_id": 14488},
    {"title": "Shrek 2", "original_title": "Shrek 2", "tmdb_id": 809, "poster_url": "https://image.tmdb.org/t/p/w500/vALSn7rJEuX742gWKcmCVLquw5J.jpg", "release_year": 2004, "imdb_rating": 7.3, "old_msg_id": 14490},
    {"title": "Shrek 3: Uchinchi", "original_title": "Shrek the Third", "tmdb_id": 810, "poster_url": "https://image.tmdb.org/t/p/w500/o2uojIx8bgL7Bxs4PGXbKStMz2o.jpg", "release_year": 2007, "imdb_rating": 6.1, "old_msg_id": 14486},
    {"title": "Shrek va uning do'stlari: Yangi yil", "original_title": "Shrek the Halls", "tmdb_id": 13768, "poster_url": "https://image.tmdb.org/t/p/w500/bgsaRYNWlF7cp8sBAJZ4gujKKVU.jpg", "release_year": 2007, "imdb_rating": 6.5, "old_msg_id": 8238},
    {"title": "Shrek 4: Abadiy baxt", "original_title": "Shrek Forever After", "tmdb_id": 10191, "poster_url": "https://image.tmdb.org/t/p/w500/cMUmeDM2QRlSOAK9onB8PhXtdZJ.jpg", "release_year": 2010, "imdb_rating": 6.3, "old_msg_id": 14484},

    # ── 11. KUNG-FU PANDA — 4 TA FILM ──
    {"title": "Kung Fu Panda 1", "original_title": "Kung Fu Panda", "tmdb_id": 9502, "poster_url": "https://image.tmdb.org/t/p/w500/dWteA8uhU6SWyawy5f4l7BnYQCm.jpg", "release_year": 2008, "imdb_rating": 7.6, "old_msg_id": 14492},
    {"title": "Kung Fu Panda 2", "original_title": "Kung Fu Panda 2", "tmdb_id": 49444, "poster_url": "https://image.tmdb.org/t/p/w500/cJj5uI2WrSKn1u7gfPAddeESAy4.jpg", "release_year": 2011, "imdb_rating": 7.3, "old_msg_id": 14498},
    {"title": "Kung Fu Panda 3", "original_title": "Kung Fu Panda 3", "tmdb_id": 140300, "poster_url": "https://image.tmdb.org/t/p/w500/usLvCu3kF40Im3yutgqUAweXwjo.jpg", "release_year": 2016, "imdb_rating": 7.1, "old_msg_id": 14494},
    {"title": "Kung Fu Panda 4", "original_title": "Kung Fu Panda 4", "tmdb_id": 1011985, "poster_url": "https://image.tmdb.org/t/p/w500/7RK9GHFArnQusZERwYwIaMZwRll.jpg", "release_year": 2024, "imdb_rating": 6.8, "old_msg_id": 14496},

    # ── 12. MUZLIK DAVRI (ICE AGE) — 6 TA FILM ──
    {"title": "Muzlik davri 1", "original_title": "Ice Age", "tmdb_id": 425, "poster_url": "https://image.tmdb.org/t/p/w500/8aIfrY4k8TpchETMMblRZpBgPKo.jpg", "release_year": 2002, "imdb_rating": 7.5, "old_msg_id": 8311},
    {"title": "Muzlik davri 2: Jazirama issiq", "original_title": "Ice Age: The Meltdown", "tmdb_id": 950, "poster_url": "https://image.tmdb.org/t/p/w500/fWYoDDMEV107ue6QWUc10RbEF0R.jpg", "release_year": 2006, "imdb_rating": 6.8, "old_msg_id": 8331},
    {"title": "Muzlik davri 3: Dinozavrlar asri", "original_title": "Ice Age: Dawn of the Dinosaurs", "tmdb_id": 8355, "poster_url": "https://image.tmdb.org/t/p/w500/d9mrt80EbMSaWoaZ6Ytfmuq7cJv.jpg", "release_year": 2009, "imdb_rating": 6.9, "old_msg_id": 8329},
    {"title": "Muzlik davri 4: Ayro qit'alar", "original_title": "Ice Age: Continental Drift", "tmdb_id": 57800, "poster_url": "https://image.tmdb.org/t/p/w500/bZRHz4bV5WHVlpLjmYbrkOAQhyT.jpg", "release_year": 2012, "imdb_rating": 6.5, "old_msg_id": 8327},
    {"title": "Muzlik davri 5: Muqarrar to'qnashuv", "original_title": "Ice Age: Collision Course", "tmdb_id": 277834, "poster_url": "https://image.tmdb.org/t/p/w500/drbVlDdeqRLoxylGpym4dECh5ai.jpg", "release_year": 2016, "imdb_rating": 5.7, "old_msg_id": 8325},
    {"title": "Muzlik davri 6: Yovvoyi Bakining sarguzashtlari", "original_title": "The Ice Age Adventures of Buck Wild", "tmdb_id": 774825, "poster_url": "https://image.tmdb.org/t/p/w500/dS2o6kYlkM8HTKxMEP7Wt2ZVLTE.jpg", "release_year": 2022, "imdb_rating": 4.5, "old_msg_id": 8333},

    # ── 13. MADAGASKAR — 3 TA FILM ──
    {"title": "Madagaskar 1", "original_title": "Madagascar", "tmdb_id": 953, "poster_url": "https://image.tmdb.org/t/p/w500/vwPFZT7tS8b9zDSN0PdvOzeGlfW.jpg", "release_year": 2005, "imdb_rating": 6.9, "old_msg_id": 14502},
    {"title": "Madagaskar 2: Qochish", "original_title": "Madagascar: Escape 2 Africa", "tmdb_id": 10527, "poster_url": "https://image.tmdb.org/t/p/w500/rfwloSBRAZCrWwsJcXd1iveI59n.jpg", "release_year": 2008, "imdb_rating": 6.6, "old_msg_id": 14506},
    {"title": "Madagaskar 3: Yevropa bo'ylab", "original_title": "Madagascar 3: Europe's Most Wanted", "tmdb_id": 80321, "poster_url": "https://image.tmdb.org/t/p/w500/aOKn2A1Ve0rKd6u8nTS1kXYSR65.jpg", "release_year": 2012, "imdb_rating": 6.8, "old_msg_id": 14504},

    # ── 14. HORROR: ASTRAL / ANNABEL / LA'NAT / ARRA / QICHQIRIQ ──
    {"title": "Astral 1", "original_title": "Insidious", "tmdb_id": 49018, "poster_url": "https://image.tmdb.org/t/p/w500/xWQzDOslE1XrpnmflRakEEnBIBC.jpg", "release_year": 2010, "imdb_rating": 6.8, "old_msg_id": 8220},
    {"title": "Astral 2", "original_title": "Insidious: Chapter 2", "tmdb_id": 91586, "poster_url": "https://image.tmdb.org/t/p/w500/vVBPSMRxvTmiVbeQelexpbbAD3M.jpg", "release_year": 2013, "imdb_rating": 6.6, "old_msg_id": 8222},
    {"title": "Astral 3", "original_title": "Insidious: Chapter 3", "tmdb_id": 280092, "poster_url": "https://image.tmdb.org/t/p/w500/smBwrIHsSxgEsQ71rSoByaP89Au.jpg", "release_year": 2015, "imdb_rating": 6.1, "old_msg_id": 8216},
    {"title": "Annabel 1", "original_title": "Annabelle", "tmdb_id": 250574, "poster_url": "https://image.tmdb.org/t/p/w500/qn53D574tT0YRyLgirEFHQwGUXw.jpg", "release_year": 2014, "imdb_rating": 5.4, "old_msg_id": 8214},
    {"title": "La'nat 3: Shayton meni majburladi", "original_title": "The Conjuring: The Devil Made Me Do It", "tmdb_id": 423108, "poster_url": "https://image.tmdb.org/t/p/w500/XKVcCa1rh9Lk3EM1MuiGrb036x.jpg", "release_year": 2021, "imdb_rating": 6.3, "old_msg_id": 13138},
    {"title": "Arra 2", "original_title": "Saw II", "tmdb_id": 215, "poster_url": "https://image.tmdb.org/t/p/w500/u6NA8O1oDxZWDp1G8C26zmDbO5O.jpg", "release_year": 2005, "imdb_rating": 6.6, "old_msg_id": 13140},
    {"title": "Arra 3", "original_title": "Saw III", "tmdb_id": 216, "poster_url": "https://image.tmdb.org/t/p/w500/vyXRTXtL5nUvrXNIJCWg2zPNhVX.jpg", "release_year": 2006, "imdb_rating": 6.2, "old_msg_id": 13142},
    {"title": "Qichqiriq 1", "original_title": "Scream", "tmdb_id": 4232, "poster_url": "https://image.tmdb.org/t/p/w500/pV8EnIy3dZcTQBbA8uP74hcmdN6.jpg", "release_year": 1996, "imdb_rating": 7.4, "old_msg_id": 8224},
    {"title": "Qichqiriq 5", "original_title": "Scream", "tmdb_id": 646385, "poster_url": "https://image.tmdb.org/t/p/w500/8ay2awzZEQJMY6Iwm1WzhwkDqDd.jpg", "release_year": 2022, "imdb_rating": 6.3, "old_msg_id": 17628},

    # ── 15. AVATAR — 2 TA FILM ──
    {"title": "Avatar 1", "original_title": "Avatar", "tmdb_id": 19995, "poster_url": "https://image.tmdb.org/t/p/w500/lUKcrcO3wEPhNnzGq06JIX7GIEb.jpg", "release_year": 2009, "imdb_rating": 7.9, "old_msg_id": 8148},
    {"title": "Avatar 2: Suv yo'li", "original_title": "Avatar: The Way of Water", "tmdb_id": 76600, "poster_url": "https://image.tmdb.org/t/p/w500/yFNn7uWudLLWDJqfj3fwh5CcUdR.jpg", "release_year": 2022, "imdb_rating": 7.6, "old_msg_id": 23686},

    # ── 16. QASOSKORLAR (AVENGERS) — 4 TA FILM ──
    {"title": "Qasoskorlar 1", "original_title": "The Avengers", "tmdb_id": 24428, "poster_url": "https://image.tmdb.org/t/p/w500/ztkYgL0zHJLnEPY5VabK9OlmXxx.jpg", "release_year": 2012, "imdb_rating": 8.0, "old_msg_id": 2754},
    {"title": "Qasoskorlar 2: Altron davri", "original_title": "Avengers: Age of Ultron", "tmdb_id": 99861, "poster_url": "https://image.tmdb.org/t/p/w500/6rANrpZe3g2PPeF1m3lQUK1ovpW.jpg", "release_year": 2015, "imdb_rating": 7.3, "old_msg_id": 2755},
    {"title": "Qasoskorlar 3: Cheksizlik jangi", "original_title": "Avengers: Infinity War", "tmdb_id": 299536, "poster_url": "https://image.tmdb.org/t/p/w500/c6RSGB6O0RaaHG3JGLq8lnUJSBC.jpg", "release_year": 2018, "imdb_rating": 8.4, "old_msg_id": 2757},
    {"title": "Qasoskorlar 4: Intiho", "original_title": "Avengers: Endgame", "tmdb_id": 299534, "poster_url": "https://image.tmdb.org/t/p/w500/dynnf8NGGfHTNMz8Vd3CzFtYjec.jpg", "release_year": 2019, "imdb_rating": 8.4, "old_msg_id": 2759},

    # ── 17. TEMIR ODAM (IRON MAN) — 3 TA FILM ──
    {"title": "Temir odam 1", "original_title": "Iron Man", "tmdb_id": 1726, "poster_url": "https://image.tmdb.org/t/p/w500/wAKZudQn0HEXqLvaGN6BEripHbv.jpg", "release_year": 2008, "imdb_rating": 7.9, "old_msg_id": 8040},
    {"title": "Temir odam 2", "original_title": "Iron Man 2", "tmdb_id": 10138, "poster_url": "https://image.tmdb.org/t/p/w500/rT3JszXFT2C3iYJtXSSL4R0DkU7.jpg", "release_year": 2010, "imdb_rating": 7.0, "old_msg_id": 8022},
    {"title": "Temir odam 3", "original_title": "Iron Man 3", "tmdb_id": 68721, "poster_url": "https://image.tmdb.org/t/p/w500/4AZco6uSdog5NbvJ6ILqnCveV8I.jpg", "release_year": 2013, "imdb_rating": 7.1, "old_msg_id": 8018},

    # ── 18. XOBBIT (THE HOBBIT) — 3 TA FILM ──
    {"title": "Xobbit 1: Kutilmagan sayohat", "original_title": "The Hobbit: An Unexpected Journey", "tmdb_id": 49051, "poster_url": "https://image.tmdb.org/t/p/w500/zTnup9V8UJEG4jWULQQpyKB6Tq0.jpg", "release_year": 2012, "imdb_rating": 7.8, "old_msg_id": 5822},
    {"title": "Xobbit 2: Smaug xarobasi", "original_title": "The Hobbit: The Desolation of Smaug", "tmdb_id": 57158, "poster_url": "https://image.tmdb.org/t/p/w500/ccbf6gnYwB2tMaU9EAgxCi88NEe.jpg", "release_year": 2013, "imdb_rating": 7.8, "old_msg_id": 5824},
    {"title": "Xobbit 3: Besh qoʻshin jangi", "original_title": "The Hobbit: The Battle of the Five Armies", "tmdb_id": 122917, "poster_url": "https://image.tmdb.org/t/p/w500/19fnHQ9g3Sy87rHKtw3wqhkBGOh.jpg", "release_year": 2014, "imdb_rating": 7.4, "old_msg_id": 2909},

    # ── 19. YURA DAVRI (JURASSIC WORLD) — 1 TA FILM ──
    {"title": "Yura davri dunyosi 3: Hukmronlik", "original_title": "Jurassic World Dominion", "tmdb_id": 507086, "poster_url": "https://image.tmdb.org/t/p/w500/6BLMT9T4wRu5QlnqVeQUU5WApLj.jpg", "release_year": 2022, "imdb_rating": 5.6, "old_msg_id": 8060},
]

async def migrate_single_movie(client: TelegramClient, m_info: dict, idx: int, total: int):
    m_title = m_info["title"]
    m_orig = m_info.get("original_title", m_title)
    m_tmdb = m_info.get("tmdb_id")
    m_poster = m_info.get("poster_url")
    m_year = m_info.get("release_year")
    m_imdb = m_info.get("imdb_rating")
    old_msg_id = m_info["old_msg_id"]

    logger.info(f"[{idx}/{total}] Film tekshirilmoqda: '{m_title}' ({m_year})...")

    # 0. Check if already migrated to an individual topic (topic >= 299)
    async with async_session_factory() as session:
        movie_obj = None
        if m_tmdb:
            res_m = await session.execute(select(MovieModel).where(MovieModel.tmdb_id == m_tmdb))
            movie_obj = res_m.scalar_one_or_none()
        if not movie_obj:
            res_t = await session.execute(select(MovieModel).where(MovieModel.title == m_title))
            movie_obj = res_t.scalar_one_or_none()

        if movie_obj and movie_obj.source_chat_id == TARGET_SUPERGROUP and movie_obj.source_topic_id and movie_obj.source_topic_id >= 299:
            # Check translation
            res_trans = await session.execute(select(MovieTranslationModel).where(MovieTranslationModel.movie_id == movie_obj.id))
            trans = res_trans.scalar_one_or_none()
            if trans and trans.storage_channel_message_id:
                logger.info(f"  [ALLAQACHON MAVJUD] '{m_title}' allaqachon Topic ID: {movie_obj.source_topic_id} da bor. O'tkazib yuborildi.")
                return

    # 1. Fetch old video msg with retry
    old_msg = None
    for attempt in range(5):
        try:
            old_msg = await client.get_messages(OLD_STORAGE, ids=old_msg_id)
            break
        except FloodWaitError as e:
            logger.warning(f"  [FloodWait] {e.seconds}s kutish...")
            await asyncio.sleep(e.seconds + 2)
        except Exception as e:
            logger.error(f"  Old msg {old_msg_id} olishda xato: {e}")
            await asyncio.sleep(2.0)

    if not old_msg or not (old_msg.video or old_msg.document):
        logger.warning(f"  Msg ID {old_msg_id} da video topilmadi!")
        return

    # 2. Create Individual Forum Topic
    peer = await client.get_input_entity(TARGET_SUPERGROUP)
    topic_title = f"{m_title} ({m_year})"
    topic_id = None
    for attempt in range(5):
        try:
            res = await client(CreateForumTopicRequest(
                peer=peer,
                title=topic_title[:128],
                random_id=random.randint(1, 2**31 - 1)
            ))
            for u in getattr(res, 'updates', []):
                if hasattr(u, 'message') and hasattr(u.message, 'id'):
                    topic_id = u.message.id
                    break
                elif hasattr(u, 'id'):
                    topic_id = u.id
                    break
            if topic_id:
                break
        except FloodWaitError as e:
            logger.warning(f"  [FloodWait topic] {e.seconds}s kutish...")
            await asyncio.sleep(e.seconds + 2)
        except Exception as e:
            logger.error(f"  Topic yaratishda xato: {e}")
            await asyncio.sleep(2.0)

    if not topic_id:
        logger.error(f"  Topic yaratib bo'lmadi: '{topic_title}'!")
        return

    logger.info(f"  Alohida topic ochildi: '{topic_title}' (Topic ID: {topic_id})")

    # 3. Update/Insert in DB with topic_id FIRST (so auto_index can find it immediately)
    async with async_session_factory() as session:
        movie_obj = None
        if m_tmdb:
            res_m = await session.execute(select(MovieModel).where(MovieModel.tmdb_id == m_tmdb))
            movie_obj = res_m.scalar_one_or_none()
        if not movie_obj:
            res_t = await session.execute(select(MovieModel).where(MovieModel.title == m_title))
            movie_obj = res_t.scalar_one_or_none()

        m_code = movie_obj.code if movie_obj and movie_obj.code else secrets.token_hex(4)

        if movie_obj:
            movie_obj.source_chat_id = TARGET_SUPERGROUP
            movie_obj.source_topic_id = topic_id
            movie_obj.source_type = "superguruh"
            movie_obj.custom_source_name = "Kinochi @kinochi_mvp_bot"
            if m_poster:
                movie_obj.poster_url = m_poster
            if m_imdb:
                movie_obj.imdb_rating = m_imdb
            if m_year:
                movie_obj.release_year = m_year
            movie_obj.title = m_title
        else:
            movie_obj = MovieModel(
                title=m_title,
                original_title=m_orig,
                code=m_code,
                release_year=m_year,
                imdb_rating=m_imdb,
                tmdb_id=m_tmdb,
                poster_url=m_poster,
                publish_status="published",
                source_chat_id=TARGET_SUPERGROUP,
                source_topic_id=topic_id,
                source_type="superguruh",
                custom_source_name="Kinochi @kinochi_mvp_bot"
            )
            session.add(movie_obj)

        await session.flush()
        m_id = movie_obj.id
        await session.commit()

    # 4. Send Video to Topic
    caption = (
        f"🍿 <b>{m_title}</b> ({m_year})\n\n"
        f"🔑 <b>Film kodi:</b> <code>{m_code}</code>\n"
        f"⭐ <b>IMDb:</b> {m_imdb}\n\n"
        f"🤖 Bot orqali tomosha qiling: @kinochi_mvp_bot"
    )
    sent_topic_msg = None
    for attempt in range(5):
        try:
            sent_topic_msg = await client.send_file(
                entity=TARGET_SUPERGROUP,
                file=old_msg.media,
                caption=caption,
                reply_to=topic_id,
                parse_mode="html"
            )
            break
        except FloodWaitError as e:
            logger.warning(f"  [FloodWait video] {e.seconds}s kutish...")
            await asyncio.sleep(e.seconds + 2)
        except Exception as e:
            logger.error(f"  Video yuborishda xato: {e}")
            await asyncio.sleep(2.0)

    if not sent_topic_msg:
        logger.error(f"  Video yuborib bo'lmadi: {m_title}")
        return

    logger.info(f"  Video topicga yuborildi (Msg ID: {sent_topic_msg.id}). Bot indeksi kutilmoqda...")

    # 5. Wait for MediaPlusOfficialBot auto-indexer to process (debounce is 4.0s)
    indexed = False
    for wait_step in range(3):
        await asyncio.sleep(3.0)
        async with async_session_factory() as session:
            res_trans = await session.execute(select(MovieTranslationModel).where(MovieTranslationModel.movie_id == m_id))
            trans_obj = res_trans.scalar_one_or_none()
            if trans_obj and trans_obj.storage_channel_message_id:
                logger.info(f"  [AUTO_INDEX OK] Bot videoni indeksladi! (Storage Msg ID: {trans_obj.storage_channel_message_id})")
                indexed = True
                break

    # 6. Fallback if bot didn't index within 9s (e.g. temporary delay)
    if not indexed:
        logger.warning(f"  Bot 9 soniyada indekslamadi. Fallback sifatida to'g'ridan-to'g'ri Storage'ga saqlanmoqda...")
        try:
            storage_msg = await client.send_file(
                entity=TARGET_STORAGE,
                file=old_msg.media,
                caption=caption,
                parse_mode="html"
            )
            async with async_session_factory() as session:
                res_trans = await session.execute(select(MovieTranslationModel).where(MovieTranslationModel.movie_id == m_id))
                trans_obj = res_trans.scalar_one_or_none()
                if trans_obj:
                    trans_obj.storage_channel_message_id = storage_msg.id
                else:
                    trans_obj = MovieTranslationModel(
                        movie_id=m_id,
                        language="O'zbekcha",
                        storage_channel_message_id=storage_msg.id
                    )
                    session.add(trans_obj)
                await session.commit()
            logger.info(f"  [Fallback OK] Storage kanalga nusxalandi (Msg ID: {storage_msg.id}).")
        except Exception as e:
            logger.error(f"  Fallback nusxalashda xato: {e}")

    # Brief delay between movies to protect Telegram rate limits
    await asyncio.sleep(2.0)

async def main():
    api_id = int(os.getenv("TELEGRAM_API_ID"))
    api_hash = os.getenv("TELEGRAM_API_HASH")
    session_str = os.getenv("TELEGRAM_STRING_SESSION")

    client = TelegramClient(StringSession(session_str), api_id, api_hash)
    await client.connect()
    # Cache dialogs to ensure access hashes are populated
    await client.get_dialogs()

    total = len(ALL_MOVIES)
    logger.info(f"=== BARCHA FILMLARNI HAR BIRI UCHUN ALOHIDA TOPIC BILAN KO'CHIRISH BOSHLANDI (Jami: {total} ta film) ===")

    for idx, m_info in enumerate(ALL_MOVIES, start=1):
        try:
            await migrate_single_movie(client, m_info, idx, total)
        except Exception as e:
            logger.error(f"Xatolik '{m_info.get('title')}' ko'chirishda: {e}", exc_info=True)
            await asyncio.sleep(3.0)

    await client.disconnect()
    logger.info("=== BARCHA FILMLAR HAR BIRI ALOHIDA TOPICDA MUVAFFAQIYATLI KO'CHIRILDI VA INDEKSLANDI! ===")

if __name__ == "__main__":
    asyncio.run(main())
