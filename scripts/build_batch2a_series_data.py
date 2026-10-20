import json
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

with open("scripts/found_series_batch2.json", "r", encoding="utf-8") as f:
    b2_data = json.load(f)

with open("scripts/mapped_series_episodes.json", "r", encoding="utf-8") as f:
    map_data = json.load(f)

def get_episodes_from_found(items, max_seasons=None):
    seasons = {}
    for it in items:
        txt = it["text"]
        m = re.search(r'(\d+)\s*[-_]?\s*mavsum.*?(\d+)\s*[-_]?\s*qism', txt, re.IGNORECASE)
        s, ep = None, None
        if m:
            s, ep = int(m.group(1)), int(m.group(2))
        else:
            m2 = re.search(r'S(\d+)[-_]CH(\d+)', txt, re.IGNORECASE)
            if m2:
                s, ep = int(m2.group(1)), int(m2.group(2))
        if s and ep:
            if max_seasons and s > max_seasons:
                continue
            # avoid duplicates (e.g. 39 or 45 which was code)
            if ep > 50:
                continue
            seasons.setdefault(s, {})[ep] = it["id"]
    return {s: [seasons[s][e] for e in sorted(seasons[s].keys())] for s in sorted(seasons.keys())}

# 1. The Mentalist (Ruxshunos) - from map_data
# S1: 550..572 (23 eps), S2: 1255..1277 (23 eps)
mentalist_s1 = list(range(550, 573))
mentalist_s2 = list(range(1255, 1278))

# 2. Percy Jackson (8 eps) - 3556, 3558.. 3570
percy_s1 = [3556, 3558, 3560, 3562, 3564, 3566, 3568, 3570]

# 3. Reacher (6 eps) - 2190, 2192.. 2200
reacher_s1 = [2190, 2192, 2194, 2196, 2198, 2200]

# 4. The Strain (13 eps) - 3037, 3039.. 3061
strain_s1 = [3037, 3039, 3041, 3043, 3045, 3047, 3049, 3051, 3053, 3055, 3057, 3059, 3061]

# 5. Daredevil (13 eps)
# S1 eps in map_data
dd_items = map_data.get("daredevil", [])
dd_s1_dict = {}
for x in dd_items:
    if x.get("season") == 1 and x.get("episode"):
        # prefer 3882.. range
        if 3880 <= x["id"] <= 3910:
            dd_s1_dict[x["episode"]] = x["id"]
daredevil_s1 = [dd_s1_dict[e] for e in sorted(dd_s1_dict.keys())][:13]

# 6. Jessica Jones (13 eps) - from b2_data
jj_seasons = get_episodes_from_found(b2_data.get("jessica_jones", []), max_seasons=1)

# 7. Superman & Lois (15 eps S1) - from b2_data
sl_seasons = get_episodes_from_found(b2_data.get("superman_lois", []), max_seasons=1)

# 8. The Last Kingdom (5 seasons, 46 eps) - from b2_data
lk_seasons = get_episodes_from_found(b2_data.get("last_kingdom", []), max_seasons=5)

# 9. The Originals (2 seasons, 29 eps) - from b2_data
orig_seasons = get_episodes_from_found(b2_data.get("originals", []), max_seasons=2)

batch2a_config = {
    "mentalist": {
        "title": "Ruxshunos",
        "original_title": "The Mentalist",
        "tmdb_id": 5920,
        "poster_url": "https://image.tmdb.org/t/p/w500/acUuh7jY3t6a0i4d1m6A0P0g0k.jpg",
        "description": "Patrik Jeyn — Kaliforniya Tergov Byurosining mustaqil maslahatchisi. Uning aqlbovar qilmas kuzatuvchanlik va psixologik tahlil qobiliyatlari eng chigal jinoyatlarni fosh etishga yordam beradi.",
        "imdb_rating": 8.2,
        "release_year": 2008,
        "status": "completed",
        "genres": "Kriminal, Drama, Sirli",
        "seasons_data": {1: mentalist_s1, 2: mentalist_s2}
    },
    "percy_jackson": {
        "title": "Persi Jekson va olimpiyachilar",
        "original_title": "Percy Jackson and the Olympians",
        "tmdb_id": 114472,
        "poster_url": "https://image.tmdb.org/t/p/w500/bvUfA6014QxM5fB1o5Fk3V6g0k.jpg",
        "description": "12 yoshli Persi Jekson o'zining dengiz xudosi Poseydonning o'g'li ekanligini bilib qoladi va Zevsning o'g'irlangan chaqmog'ini topish uchun xavfli sarguzashtga otlanadi.",
        "imdb_rating": 7.1,
        "release_year": 2023,
        "status": "ongoing",
        "genres": "Fentezi, Sarguzasht, Jangari",
        "seasons_data": {1: percy_s1}
    },
    "reacher": {
        "title": "Jek Richer",
        "original_title": "Reacher",
        "tmdb_id": 108978,
        "poster_url": "https://image.tmdb.org/t/p/w500/j7vA8z2XQy6m1F9k5G0k0L0P0k.jpg",
        "description": "Harbiy politsiyaning sobiq mayori Jek Richer adolatsizlikka duch kelganda o'zining jismoniy kuchi va o'tkir aqli bilan haqiqatni tiklaydi.",
        "imdb_rating": 8.1,
        "release_year": 2022,
        "status": "ongoing",
        "genres": "Jangari, Kriminal, Drama",
        "seasons_data": {1: reacher_s1}
    },
    "the_strain": {
        "title": "Shtamm",
        "original_title": "The Strain",
        "tmdb_id": 46028,
        "poster_url": "https://image.tmdb.org/t/p/w500/e9Q3h4f5k6m7N8o9P0q1r2s3t4.jpg",
        "description": "Nyu-Yorkka qo'ngan samolyotda barcha yo'lovchilar sirli virus sababli halok bo'ladi. Tez orada shaharni qadimiy vampir epidemiyasi qamrab oladi.",
        "imdb_rating": 7.3,
        "release_year": 2014,
        "status": "completed",
        "genres": "Dahshat, Triller, Drama",
        "seasons_data": {1: strain_s1}
    },
    "daredevil": {
        "title": "Qoʻrqmas (Daredevil)",
        "original_title": "Daredevil",
        "tmdb_id": 61889,
        "poster_url": "https://image.tmdb.org/t/p/w500/QWbPaRFaZhgv2qmxA6iq4vum.jpg",
        "description": "Bolaligida ko'rish qobiliyatini yo'qotgan Mett Merdok boshqa sezgilarini favqulodda rivojlantirib, kechalari Do'zax oshxonasi ko'chalarida yovuzlikka qarshi kurashadi.",
        "imdb_rating": 8.6,
        "release_year": 2015,
        "status": "completed",
        "genres": "Jangari, Kriminal, Drama",
        "seasons_data": {1: daredevil_s1}
    },
    "jessica_jones": {
        "title": "Jessika Jons",
        "original_title": "Jessica Jones",
        "tmdb_id": 38472,
        "poster_url": "https://image.tmdb.org/t/p/w500/c1i4j7k1x5k5o1l1l1l1l1.jpg",
        "description": "Superqahramonlik faoliyatidagi fojiali yakundan so'ng, Jessika Jons Nyu-Yorkda o'zining shaxsiy detektivlik agentligini ochadi.",
        "imdb_rating": 7.9,
        "release_year": 2015,
        "status": "completed",
        "genres": "Jangari, Kriminal, Drama",
        "seasons_data": jj_seasons
    },
    "superman_lois": {
        "title": "Supermen va Lois",
        "original_title": "Superman & Lois",
        "tmdb_id": 95057,
        "poster_url": "https://image.tmdb.org/t/p/w500/6Sn0Q7W1UuA9q6rK2Z1m1l1l1l.jpg",
        "description": "Klark Kent va Lois Leyn dunyoni qutqarish bilan birga, zamonaviy jamiyatda o'smir farzandlarni tarbiyalashdek mashaqqatli vazifani ham uddalashga harakat qilishadi.",
        "imdb_rating": 7.8,
        "release_year": 2021,
        "status": "completed",
        "genres": "Ilmiy fantastika, Jangari, Drama",
        "seasons_data": sl_seasons
    },
    "last_kingdom": {
        "title": "So‘nggi qirollik",
        "original_title": "The Last Kingdom",
        "tmdb_id": 63333,
        "poster_url": "https://image.tmdb.org/t/p/w500/8d8H0H1K1h7k1x5k5o1l1l1l1l1.jpg",
        "description": "Sakson aslzodasi Uxtred bolaligida vikinglar tomonidan asir olinib, ularning tarbiyasida o'sadi. Voyaga yetgach, u o'z tug'ilgan yurti va uni voyaga yetkazgan qabilasi o'rtasida tanlov qilishi kerak bo'ladi.",
        "imdb_rating": 8.5,
        "release_year": 2015,
        "status": "completed",
        "genres": "Tarixiy, Jangari, Drama",
        "seasons_data": lk_seasons
    },
    "originals": {
        "title": "The Originals (Haqiqiylar)",
        "original_title": "The Originals",
        "tmdb_id": 48865,
        "poster_url": "https://image.tmdb.org/t/p/w500/bL2iYVp6jW0m0M0K0L0K0P0G0K.jpg",
        "description": "Ming yillik Mikelsonlar oilasi Yangi Orleanga qaytadi va shahar ustidan nazoratni qaytarib olish uchun g'ayritabiiy mavjudotlar bilan shafqatsiz kurashga kirishadi.",
        "imdb_rating": 8.3,
        "release_year": 2013,
        "status": "completed",
        "genres": "Drama, Fentezi, Dahshat",
        "seasons_data": orig_seasons
    }
}

for k, v in batch2a_config.items():
    s_lens = {s: len(eps) for s, eps in v["seasons_data"].items()}
    total = sum(s_lens.values())
    print(f"{v['title']} ({v['release_year']}): {total} eps -> {s_lens}")

with open("scripts/batch2a_config.json", "w", encoding="utf-8") as f:
    json.dump(batch2a_config, f, ensure_ascii=False, indent=2)

print("\nSaved to scripts/batch2a_config.json")
