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
logger = logging.getLogger("batch2_migration")

TARGET_SUPERGROUP = int(settings.AUTO_TOPIC_CHAT_ID)  # -1003847632555
TARGET_STORAGE = int(settings.STORAGE_CHANNEL_ID)    # -1003762157591
OLD_STORAGE = -1003926001543

BATCH2_MOVIES = [
    # ── 1. GARRI POTTER VA SEHRGARLAR OLAMI — 9 TA FILM ──
    {"title": "Garri Potter 1: Hikmatlar toshi", "original_title": "Harry Potter and the Sorcerer's Stone", "tmdb_id": 671, "poster_url": "https://image.tmdb.org/t/p/w500/q3LZNzwW7ZWu4kSFIPGcB5CYFE4.jpg", "release_year": 2001, "imdb_rating": 7.6, "old_msg_id": 2726},
    {"title": "Garri Potter 2: Maxfiy xujra", "original_title": "Harry Potter and the Chamber of Secrets", "tmdb_id": 672, "poster_url": "https://image.tmdb.org/t/p/w500/33Wj3LSyoAqtqkeh7YXcVMvTQzc.jpg", "release_year": 2002, "imdb_rating": 7.4, "old_msg_id": 2728},
    {"title": "Garri Potter 3: Azkaban mahbusi", "original_title": "Harry Potter and the Prisoner of Azkaban", "tmdb_id": 673, "poster_url": "https://image.tmdb.org/t/p/w500/mncDize7FLO9RBovXKZ7LefUkbu.jpg", "release_year": 2004, "imdb_rating": 7.9, "old_msg_id": 2730},
    {"title": "Garri Potter 4: Alanga kubogi", "original_title": "Harry Potter and the Goblet of Fire", "tmdb_id": 674, "poster_url": "https://image.tmdb.org/t/p/w500/wWlSRexsjrdTWBYY84s671dYde5.jpg", "release_year": 2005, "imdb_rating": 7.7, "old_msg_id": 2732},
    {"title": "Garri Potter 5: Feniks jamiyati", "original_title": "Harry Potter and the Order of the Phoenix", "tmdb_id": 675, "poster_url": "https://image.tmdb.org/t/p/w500/AvftUghR5CZT1VCYbWATs01Et1M.jpg", "release_year": 2007, "imdb_rating": 7.5, "old_msg_id": 2734},
    {"title": "Garri Potter 6: Tilsim shahzodasi", "original_title": "Harry Potter and the Half-Blood Prince", "tmdb_id": 767, "poster_url": "https://image.tmdb.org/t/p/w500/DFXFVLEHMcCjem4inUbIL2888H.jpg", "release_year": 2009, "imdb_rating": 7.6, "old_msg_id": 2736},
    {"title": "Garri Potter 7: Ajal tuhfasi 1", "original_title": "Harry Potter and the Deathly Hallows: Part 1", "tmdb_id": 12444, "poster_url": "https://image.tmdb.org/t/p/w500/2M6jaFgspjqGNLW7nrpaItRTBst.jpg", "release_year": 2010, "imdb_rating": 7.7, "old_msg_id": 2738},
    {"title": "Garri Potter 7: Ajal tuhfasi 2", "original_title": "Harry Potter and the Deathly Hallows: Part 2", "tmdb_id": 12445, "poster_url": "https://image.tmdb.org/t/p/w500/vOod9K0uygsACgtEDuwF5gqgpf7.jpg", "release_year": 2011, "imdb_rating": 8.1, "old_msg_id": 2740},
    {"title": "Jodu saltanati 1: Fantastik maxluqlar", "original_title": "Fantastic Beasts and Where to Find Them", "tmdb_id": 259316, "poster_url": "https://image.tmdb.org/t/p/w500/hqpnhHmr9L63d9Hh2Js2xLBeLer.jpg", "release_year": 2016, "imdb_rating": 7.2, "old_msg_id": 2742},

    # ── 2. FORSAJ (FAST & FURIOUS) — 11 TA FILM ──
    {"title": "Forsaj 1", "original_title": "The Fast and the Furious", "tmdb_id": 9799, "poster_url": "https://image.tmdb.org/t/p/w500/cHNzdyLZDZ25qRS6Uq3dXKhJJbv.jpg", "release_year": 2001, "imdb_rating": 6.8, "old_msg_id": 2722},
    {"title": "Forsaj 2: Ikki hissa tezroq", "original_title": "2 Fast 2 Furious", "tmdb_id": 584, "poster_url": "https://image.tmdb.org/t/p/w500/8Rr94aL7VPnkf9HGqIozpbg2sb2.jpg", "release_year": 2003, "imdb_rating": 5.9, "old_msg_id": 2720},
    {"title": "Forsaj 3: Tokio drayfti", "original_title": "The Fast and the Furious: Tokyo Drift", "tmdb_id": 9615, "poster_url": "https://image.tmdb.org/t/p/w500/qkCOHIXI2vSXsuA0psYghM9Og2U.jpg", "release_year": 2006, "imdb_rating": 6.0, "old_msg_id": 2718},
    {"title": "Forsaj 4", "original_title": "Fast & Furious", "tmdb_id": 13804, "poster_url": "https://image.tmdb.org/t/p/w500/A0HOGMFp4mphOCqwt5YNWbuSMJe.jpg", "release_year": 2009, "imdb_rating": 6.5, "old_msg_id": 2716},
    {"title": "Forsaj 5: Rio qasosi", "original_title": "Fast Five", "tmdb_id": 51497, "poster_url": "https://image.tmdb.org/t/p/w500/A9Ud0VPQKLPKvHXnfWGvs26jBsr.jpg", "release_year": 2011, "imdb_rating": 7.3, "old_msg_id": 2714},
    {"title": "Forsaj 6", "original_title": "Fast & Furious 6", "tmdb_id": 82992, "poster_url": "https://image.tmdb.org/t/p/w500/qsWinjrA5wZbFtcU87EIgpCo0Xm.jpg", "release_year": 2013, "imdb_rating": 7.0, "old_msg_id": 2712},
    {"title": "Forsaj 7", "original_title": "Furious 7", "tmdb_id": 168259, "poster_url": "https://image.tmdb.org/t/p/w500/i5A0OCxcinzkcxvesvefFu9vX3K.jpg", "release_year": 2015, "imdb_rating": 7.1, "old_msg_id": 2710},
    {"title": "Forsaj 8", "original_title": "The Fate of the Furious", "tmdb_id": 337339, "poster_url": "https://image.tmdb.org/t/p/w500/mMG9uMqEosiIMjliiPHsyycPcIA.jpg", "release_year": 2017, "imdb_rating": 6.6, "old_msg_id": 2708},
    {"title": "Forsaj: Hobbs va Shou", "original_title": "Fast & Furious Presents: Hobbs & Shaw", "tmdb_id": 384018, "poster_url": "https://image.tmdb.org/t/p/w500/uKchEnEOTCvh1iZ7AyOs7p9aoVq.jpg", "release_year": 2019, "imdb_rating": 6.5, "old_msg_id": 2724},
    {"title": "Forsaj 9", "original_title": "F9: The Fast Saga", "tmdb_id": 385128, "poster_url": "https://image.tmdb.org/t/p/w500/3Abag0sIPHTLFIP2asXcC7E0QxP.jpg", "release_year": 2021, "imdb_rating": 5.2, "old_msg_id": 2706},
    {"title": "Forsaj 10", "original_title": "Fast X", "tmdb_id": 385687, "poster_url": "https://image.tmdb.org/t/p/w500/MSc1kcaHXvvyGgoyjDa60jxdqq.jpg", "release_year": 2023, "imdb_rating": 5.8, "old_msg_id": 2704},

    # ── 3. YOVUZLIK QARORGOHI (RESIDENT EVIL) — 7 TA FILM ──
    {"title": "Yovuzlik qarorgohi 1", "original_title": "Resident Evil", "tmdb_id": 107, "poster_url": "https://image.tmdb.org/t/p/w500/zuVpG27FbWqEZQxrtDcw4f3Sl1I.jpg", "release_year": 2002, "imdb_rating": 6.6, "old_msg_id": 2904},
    {"title": "Yovuzlik qarorgohi 2: Apokalipsis", "original_title": "Resident Evil: Apocalypse", "tmdb_id": 108, "poster_url": "https://image.tmdb.org/t/p/w500/2fb0GoSbjdlE431b83f81X4kCVH.jpg", "release_year": 2004, "imdb_rating": 6.1, "old_msg_id": 2906},
    {"title": "Yovuzlik qarorgohi 3: Qirg'in", "original_title": "Resident Evil: Extinction", "tmdb_id": 77, "poster_url": "https://image.tmdb.org/t/p/w500/sP3GaLR1kRz0Fj5exKJmYKvIYzz.jpg", "release_year": 2007, "imdb_rating": 6.2, "old_msg_id": 8108},
    {"title": "Yovuzlik qarorgohi 4: O'limdan keyingi hayot", "original_title": "Resident Evil: Afterlife", "tmdb_id": 35791, "poster_url": "https://image.tmdb.org/t/p/w500/fQhJrmxRRtwKBrJ8E2V6DFLoxJI.jpg", "release_year": 2010, "imdb_rating": 5.8, "old_msg_id": 2908},
    {"title": "Yovuzlik qarorgohi 5: Qasos", "original_title": "Resident Evil: Retribution", "tmdb_id": 93837, "poster_url": "https://image.tmdb.org/t/p/w500/ui2xxngnylYkirm2P1Xc2XCcThH.jpg", "release_year": 2012, "imdb_rating": 5.3, "old_msg_id": 8106},
    {"title": "Yovuzlik qarorgohi 6: Yakuniy bob", "original_title": "Resident Evil: The Final Chapter", "tmdb_id": 173897, "poster_url": "https://image.tmdb.org/t/p/w500/2qOeinwZfRAcfGg10V7qROCjYgc.jpg", "release_year": 2016, "imdb_rating": 5.5, "old_msg_id": 8102},
    {"title": "Yovuzlik qarorgohi 7: Rakkun-Sitiga xush kelibsiz", "original_title": "Resident Evil: Welcome to Raccoon City", "tmdb_id": 460458, "poster_url": "https://image.tmdb.org/t/p/w500/nfDd3MgLQoKZr7xOK4DDIF8Snlh.jpg", "release_year": 2021, "imdb_rating": 5.2, "old_msg_id": 8104},

    # ── 4. OXIRGI MANZIL (FINAL DESTINATION) — 6 TA FILM ──
    {"title": "Oxirgi manzil 1", "original_title": "Final Destination", "tmdb_id": 9532, "poster_url": "https://image.tmdb.org/t/p/w500/rrXMDkTZYK4MeEqUAu1jqVNLzg3.jpg", "release_year": 2000, "imdb_rating": 6.7, "old_msg_id": 8236},
    {"title": "Oxirgi manzil 2", "original_title": "Final Destination 2", "tmdb_id": 9358, "poster_url": "https://image.tmdb.org/t/p/w500/r7pvTHVybZL49puwhQwwUU33ob5.jpg", "release_year": 2003, "imdb_rating": 6.2, "old_msg_id": 8234},
    {"title": "Oxirgi manzil 3", "original_title": "Final Destination 3", "tmdb_id": 9286, "poster_url": "https://image.tmdb.org/t/p/w500/hZwGf3IK42LEQ01ZCZZKRAqTpyC.jpg", "release_year": 2006, "imdb_rating": 5.8, "old_msg_id": 8232},
    {"title": "Oxirgi manzil 4", "original_title": "The Final Destination", "tmdb_id": 19912, "poster_url": "https://image.tmdb.org/t/p/w500/2hG60UUGmG8kxRRq04LJAABIL7A.jpg", "release_year": 2009, "imdb_rating": 5.1, "old_msg_id": 8230},
    {"title": "Oxirgi manzil 5", "original_title": "Final Destination 5", "tmdb_id": 55779, "poster_url": "https://image.tmdb.org/t/p/w500/554vHUVuvpQIJMfZHxaZE5x3YUJ.jpg", "release_year": 2011, "imdb_rating": 5.9, "old_msg_id": 8228},
    {"title": "Oxirgi manzil 6", "original_title": "Final Destination: Bloodlines", "tmdb_id": 578701, "poster_url": "https://image.tmdb.org/t/p/w500/yECIqoAhqOqEbSZUViTJUapRsMe.jpg", "release_year": 2025, "imdb_rating": 6.0, "old_msg_id": 8226},

    # ── 5. TRANSFORMERLAR (TRANSFORMERS) — 6 TA FILM ──
    {"title": "Transformers 1", "original_title": "Transformers", "tmdb_id": 1858, "poster_url": "https://image.tmdb.org/t/p/w500/eYFRGx7qk4JGOqUvjSWIpgToHLi.jpg", "release_year": 2007, "imdb_rating": 7.0, "old_msg_id": 2129},
    {"title": "Transformers 2: Yiqilganlar qasosi", "original_title": "Transformers: Revenge of the Fallen", "tmdb_id": 8373, "poster_url": "https://image.tmdb.org/t/p/w500/faLkNsOPqiw2ijqDOfEy2GUscw2.jpg", "release_year": 2009, "imdb_rating": 6.0, "old_msg_id": 2130},
    {"title": "Transformers 3: Oyning qorong'u tomoni", "original_title": "Transformers: Dark of the Moon", "tmdb_id": 38356, "poster_url": "https://image.tmdb.org/t/p/w500/9wamNeMspa2wLWyZW1af6PMhfCa.jpg", "release_year": 2011, "imdb_rating": 6.2, "old_msg_id": 2131},
    {"title": "Transformers 4: Yo'q bo'lish davri", "original_title": "Transformers: Age of Extinction", "tmdb_id": 91314, "poster_url": "https://image.tmdb.org/t/p/w500/egU3gts1IFjixpQGHZ9g7fmgBiR.jpg", "release_year": 2014, "imdb_rating": 5.6, "old_msg_id": 2132},
    {"title": "Transformers 5: So'nggi ritsar", "original_title": "Transformers: The Last Knight", "tmdb_id": 335988, "poster_url": "https://image.tmdb.org/t/p/w500/ne5PH0nU3tiCjEG5sogaOztr86k.jpg", "release_year": 2017, "imdb_rating": 5.2, "old_msg_id": 2133},
    {"title": "Transformers 6: Hayvonlar yuksalishi", "original_title": "Transformers: Rise of the Beasts", "tmdb_id": 667538, "poster_url": "https://image.tmdb.org/t/p/w500/e0p6MFlZedrQVbpigRZ7dFtrZDS.jpg", "release_year": 2023, "imdb_rating": 6.0, "old_msg_id": 2134},

    # ── 6. DIVERGENT — 3 TA FILM ──
    {"title": "Divergent 1", "original_title": "Divergent", "tmdb_id": 157350, "poster_url": "https://image.tmdb.org/t/p/w500/4GxZw9ADsIPAcpebbrm053DPa18.jpg", "release_year": 2014, "imdb_rating": 6.6, "old_msg_id": 8082},
    {"title": "Divergent 2: Isyonchi", "original_title": "The Divergent Series: Insurgent", "tmdb_id": 262500, "poster_url": "https://image.tmdb.org/t/p/w500/i3v2kcuvjoT35rnddLu7dl5B81o.jpg", "release_year": 2015, "imdb_rating": 6.2, "old_msg_id": 8084},
    {"title": "Divergent 3: Devor ortida", "original_title": "The Divergent Series: Allegiant", "tmdb_id": 262504, "poster_url": "https://image.tmdb.org/t/p/w500/afn26Axrs3We3bQMfH8Gyaxjd6i.jpg", "release_year": 2016, "imdb_rating": 5.7, "old_msg_id": 8080},

    # ── 7. HAYOT-MAMOT O'YINLARI (THE HUNGER GAMES) — 4 TA FILM ──
    {"title": "Hayot-Mamot o'yinlari 2: Olov iskanjasida", "original_title": "The Hunger Games: Catching Fire", "tmdb_id": 101299, "poster_url": "https://image.tmdb.org/t/p/w500/lKe3uEQKyc6uTAOlFt9KmxHs5eH.jpg", "release_year": 2013, "imdb_rating": 7.5, "old_msg_id": 8038},
    {"title": "Hayot-Mamot o'yinlari 3: Qaytuvchi qush 1", "original_title": "The Hunger Games: Mockingjay - Part 1", "tmdb_id": 131631, "poster_url": "https://image.tmdb.org/t/p/w500/kPbFeomPFnnktdwBgCBZ24NhkTj.jpg", "release_year": 2014, "imdb_rating": 6.6, "old_msg_id": 8036},
    {"title": "Hayot-Mamot o'yinlari 5: Sayroqi qushlar va ilonlar balladasi", "original_title": "The Hunger Games: The Ballad of Songbirds & Snakes", "tmdb_id": 695721, "poster_url": "https://image.tmdb.org/t/p/w500/6Lp4Aij9meeh9JBaATQuXnNyBJl.jpg", "release_year": 2023, "imdb_rating": 6.8, "old_msg_id": 8034},
    {"title": "Qaqshatqich ochlik o'yinlari", "original_title": "The Starving Games", "tmdb_id": 224141, "poster_url": "https://image.tmdb.org/t/p/w500/s4pbFVyEIlpyPjxdbG15JeIET0S.jpg", "release_year": 2013, "imdb_rating": 3.2, "old_msg_id": 8032},

    # ── 8. BETXOVEN (BEETHOVEN) — 4 TA FILM ──
    {"title": "Betxoven 1", "original_title": "Beethoven", "tmdb_id": 9494, "poster_url": "https://image.tmdb.org/t/p/w500/e78AF6bWorcCkUCR966RgAT0vRB.jpg", "release_year": 1992, "imdb_rating": 5.7, "old_msg_id": 2370},
    {"title": "Betxoven 2", "original_title": "Beethoven's 2nd", "tmdb_id": 9495, "poster_url": "https://image.tmdb.org/t/p/w500/qEMnKs6va3zHPTk2VzEZr7wn7YC.jpg", "release_year": 1993, "imdb_rating": 5.0, "old_msg_id": 2368},
    {"title": "Betxoven 3", "original_title": "Beethoven's 3rd", "tmdb_id": 10427, "poster_url": "https://image.tmdb.org/t/p/w500/x26rbS37E8begS3SrFrAMQOGtMb.jpg", "release_year": 2000, "imdb_rating": 4.2, "old_msg_id": 2608},
    {"title": "Betxoven 5", "original_title": "Beethoven's 5th", "tmdb_id": 14197, "poster_url": "https://image.tmdb.org/t/p/w500/2cJWaUNdyNpd86CzdU6jUnbfxMq.jpg", "release_year": 2003, "imdb_rating": 4.4, "old_msg_id": 2366},

    # ── 9. DC & BATMAN — 3 TA FILM ──
    {"title": "Betmen Supermenga qarshi: Adolat tongi", "original_title": "Batman v Superman: Dawn of Justice", "tmdb_id": 209112, "poster_url": "https://image.tmdb.org/t/p/w500/tAQOcxxcZbpM1jEhz7hJC5nmCDi.jpg", "release_year": 2016, "imdb_rating": 6.5, "old_msg_id": 2774},
    {"title": "Adolat ligasi", "original_title": "Justice League", "tmdb_id": 141052, "poster_url": "https://image.tmdb.org/t/p/w500/e2f1GaWLkk5Sj7cZMi38mUPXYdt.jpg", "release_year": 2017, "imdb_rating": 6.1, "old_msg_id": 2890},
    {"title": "Zak Snayderning Adolat Ligasi", "original_title": "Zack Snyder's Justice League", "tmdb_id": 791373, "poster_url": "https://image.tmdb.org/t/p/w500/tpPWUv258JrMSIdkVVV1NDp3aoT.jpg", "release_year": 2021, "imdb_rating": 8.0, "old_msg_id": 2892},

    # ── 10. VENOM DAVOMI — 2 TA FILM ──
    {"title": "Venom 2: Qirg'in boshlanishi", "original_title": "Venom: Let There Be Carnage", "tmdb_id": 580489, "poster_url": "https://image.tmdb.org/t/p/w500/pZe4xYwDkmxhf3oA8DNEihOW4pW.jpg", "release_year": 2021, "imdb_rating": 5.9, "old_msg_id": 12157, "source_chat": -1003941035700},
    {"title": "Venom 3: So'nggi raqs", "original_title": "Venom: The Last Dance", "tmdb_id": 912649, "poster_url": "https://image.tmdb.org/t/p/w500/YFcQ65dRrLpUpMiMFrrRV6rkEs.jpg", "release_year": 2024, "imdb_rating": 6.2, "old_msg_id": 8405},

    # ── 11. QIROL SHER (THE LION KING) — 5 TA FILM ──
    {"title": "Qirol Sher 1", "original_title": "The Lion King", "tmdb_id": 8587, "poster_url": "https://image.tmdb.org/t/p/w500/4pnTGyQqccNYmjmr8aAS8lvDvBy.jpg", "release_year": 1994, "imdb_rating": 8.5, "old_msg_id": 2083},
    {"title": "Qirol Sher 2: Simba g'ururi", "original_title": "The Lion King II: Simba's Pride", "tmdb_id": 9732, "poster_url": "https://image.tmdb.org/t/p/w500/1Q0juLckjyydMglTpsokxL3lafF.jpg", "release_year": 1998, "imdb_rating": 6.5, "old_msg_id": 2084},
    {"title": "Qirol Sher 3: Hakuna Matata", "original_title": "The Lion King 1½", "tmdb_id": 11430, "poster_url": "https://image.tmdb.org/t/p/w500/wIIVzCF9TPeXG79FBdr6z1Fxbbl.jpg", "release_year": 2004, "imdb_rating": 6.5, "old_msg_id": 2085},
    {"title": "Qirol Sher (2019)", "original_title": "The Lion King", "tmdb_id": 420818, "poster_url": "https://image.tmdb.org/t/p/w500/lD4Hy3ibzvA9byY2uyUNGeRNzaj.jpg", "release_year": 2019, "imdb_rating": 6.8, "old_msg_id": 2072},
    {"title": "Mufasa: Qirol Sher", "original_title": "Mufasa: The Lion King", "tmdb_id": 762509, "poster_url": "https://image.tmdb.org/t/p/w500/dOmd80QGmG7VCQCjXlY3CL82S4D.jpg", "release_year": 2024, "imdb_rating": 6.8, "old_msg_id": 2082},

    # ── 12. QASHQIRLAR MAKONI FILMLARI — 3 TA FILM ──
    {"title": "Qashqirlar makoni: Gladio", "original_title": "Kurtlar Vadisi: Gladio", "tmdb_id": 28609, "poster_url": "https://image.tmdb.org/t/p/w500/9uRHXVUBLidWIBRpZQp4Ra14qzp.jpg", "release_year": 2009, "imdb_rating": 6.3, "old_msg_id": 23712},
    {"title": "Qashqirlar makoni: Falastin", "original_title": "Kurtlar Vadisi: Filistin", "tmdb_id": 58319, "poster_url": "https://image.tmdb.org/t/p/w500/pJoHHdbcUcDYvY8pqKao0JHmtQh.jpg", "release_year": 2011, "imdb_rating": 5.9, "old_msg_id": 10825},
    {"title": "Qashqirlar makoni: Vatan", "original_title": "Kurtlar Vadisi: Vatan", "tmdb_id": 479144, "poster_url": "https://image.tmdb.org/t/p/w500/9ySkFLATDGH6ML0AA87QldiGQyB.jpg", "release_year": 2017, "imdb_rating": 5.4, "old_msg_id": 10823},

    # ── 13. YURA DAVRI QO'SHIMCHA FILMLARI — 6 TA FILM ──
    {"title": "Yura davriga sayohat 1", "original_title": "Jurassic Park", "tmdb_id": 329, "poster_url": "https://image.tmdb.org/t/p/w500/qoDjoRP7vYmPZ1lZIMTGzoHG1iR.jpg", "release_year": 1993, "imdb_rating": 8.2, "old_msg_id": 8064},
    {"title": "Yura davriga sayohat 2", "original_title": "The Lost World: Jurassic Park", "tmdb_id": 330, "poster_url": "https://image.tmdb.org/t/p/w500/cyOYIkBXPDsr2WPs0F0gNkhktG1.jpg", "release_year": 1997, "imdb_rating": 6.6, "old_msg_id": 8062},
    {"title": "Yura davri dunyosi 1", "original_title": "Jurassic World", "tmdb_id": 135397, "poster_url": "https://image.tmdb.org/t/p/w500/nSUyxiLlf9qHDiQH5LmCQQK62WX.jpg", "release_year": 2015, "imdb_rating": 7.0, "old_msg_id": 8056},
    {"title": "Yura davri dunyosi 2: Yiqilgan qirollik", "original_title": "Jurassic World: Fallen Kingdom", "tmdb_id": 351286, "poster_url": "https://image.tmdb.org/t/p/w500/4VEkflsi7zQmBN6vNpihNrmnRzj.jpg", "release_year": 2018, "imdb_rating": 6.2, "old_msg_id": 8058},
    {"title": "Yura davri dunyosi: Qayta tug'ilish", "original_title": "Jurassic World: Rebirth", "tmdb_id": 1234821, "poster_url": "https://image.tmdb.org/t/p/w500/iIk5nWcHuqTMLrz1yrwIWcmwTOM.jpg", "release_year": 2025, "imdb_rating": 6.0, "old_msg_id": 8054},
    {"title": "Yura davri bog'iga qaytish", "original_title": "Return to Jurassic Park", "tmdb_id": 1311821, "poster_url": "https://image.tmdb.org/t/p/w500/9mllhhu2HnnEZCXLXrNQP9L6eBy.jpg", "release_year": 2025, "imdb_rating": 5.8, "old_msg_id": 8052},
]

async def migrate_single_movie(client: TelegramClient, m_info: dict, idx: int, total: int):
    m_title = m_info["title"]
    m_orig = m_info.get("original_title", m_title)
    m_tmdb = m_info.get("tmdb_id")
    m_poster = m_info.get("poster_url")
    m_year = m_info.get("release_year")
    m_imdb = m_info.get("imdb_rating")
    old_msg_id = m_info["old_msg_id"]
    from_chat = m_info.get("source_chat", OLD_STORAGE)

    logger.info(f"[{idx}/{total}] Film ko'rib chiqilmoqda: '{m_title}' ({m_year})...")

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
            res_trans = await session.execute(select(MovieTranslationModel).where(MovieTranslationModel.movie_id == movie_obj.id))
            translations = res_trans.scalars().all()
            if any(bool(t.storage_channel_message_id) for t in translations):
                logger.info(f"  [ALLAQACHON MAVJUD] '{m_title}' Topic ID: {movie_obj.source_topic_id} da bor. O'tkazildi.")
                return

    # 1. Fetch old video msg
    old_msg = None
    for attempt in range(5):
        try:
            old_msg = await client.get_messages(from_chat, ids=old_msg_id)
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

    # 3. Update/Insert in DB with topic_id FIRST
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
            translations = res_trans.scalars().all()
            if any(bool(t.storage_channel_message_id) for t in translations):
                logger.info(f"  [AUTO_INDEX OK] Bot videoni indeksladi!")
                indexed = True
                break

    # 6. Fallback if bot delayed
    if not indexed:
        logger.warning(f"  Fallback sifatida to'g'ridan-to'g'ri Storage'ga saqlanmoqda...")
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

    await asyncio.sleep(2.0)

async def main():
    api_id = int(os.getenv("TELEGRAM_API_ID"))
    api_hash = os.getenv("TELEGRAM_API_HASH")
    session_str = os.getenv("TELEGRAM_STRING_SESSION")

    client = TelegramClient(StringSession(session_str), api_id, api_hash)
    await client.connect()
    await client.get_dialogs()

    total = len(BATCH2_MOVIES)
    logger.info(f"=== 2-BOSQICH: BARCHA QOLGAN FILMLARNI HAR BIRI UCHUN ALOHIDA TOPIC BILAN KO'CHIRISH (Jami: {total} ta film) ===")

    for idx, m_info in enumerate(BATCH2_MOVIES, start=1):
        try:
            await migrate_single_movie(client, m_info, idx, total)
        except Exception as e:
            logger.error(f"Xatolik '{m_info.get('title')}' ko'chirishda: {e}", exc_info=True)
            await asyncio.sleep(3.0)

    await client.disconnect()
    logger.info("=== 2-BOSQICH BARCHA FILMLAR ALOHIDA TOPICLARDA MUVAFFAQIYATLI YAKUNLANDI! ===")

if __name__ == "__main__":
    asyncio.run(main())
