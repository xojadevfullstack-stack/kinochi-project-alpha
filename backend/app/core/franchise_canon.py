"""
Canon Master Blueprint for Cinematic Universes & Franchises.
Enforces 100% accurate chronological story timelines vs release order.
Used by automatic pipeline enrichment and manual admin tooling.
"""
from typing import TypedDict


class CanonItemBlueprint(TypedDict, total=False):
    tmdb_id: int
    title_en: str
    title_uz: str
    chronological_order: int
    release_order: int
    timeline_event_desc: str
    year: int
    aliases: list[str]


class FranchiseBlueprint(TypedDict):
    slug: str
    name: str
    description: str
    poster_url: str
    banner_url: str
    is_franchise: bool
    sort_order: int
    items: list[CanonItemBlueprint]


CANON_FRANCHISES: dict[str, FranchiseBlueprint] = {
    "mcu": {
        "slug": "mcu",
        "name": "Marvel Kinokoinoti (MCU)",
        "description": "Marvel kinematografiya olami — 1942-yildagi Birinchi Qasoskordan boshlab, Multiverse sagasigacha bo'lgan barcha voqealar xronologiyasi.",
        "poster_url": "https://image.tmdb.org/t/p/w780/yFSIUVTCvgYrpalUktulvk3Gi5Y.jpg",
        "banner_url": "https://image.tmdb.org/t/p/original/2UNUv4NJdC36E5myDHACBJ99EwL.jpg",
        "is_franchise": True,
        "sort_order": 1,
        "items": [
            {
                "tmdb_id": 1771,
                "title_en": "Captain America: The First Avenger",
                "title_uz": "Birinchi qasoskor: Kapitan Amerika",
                "chronological_order": 1,
                "release_order": 5,
                "timeline_event_desc": "1942–1945: 2-Jahon Urushi, Qasoskorning tug'ilishi va Tesseract",
                "year": 2011,
            },
            {
                "tmdb_id": 299537,
                "title_en": "Captain Marvel",
                "title_uz": "Kapitan Marvel",
                "chronological_order": 2,
                "release_order": 21,
                "timeline_event_desc": "1995: Kree-Skrull Urushi, yosh Nik Fyuri va Tesseract",
                "year": 2019,
            },
            {
                "tmdb_id": 1726,
                "title_en": "Iron Man",
                "title_uz": "Temir odam",
                "chronological_order": 3,
                "release_order": 1,
                "timeline_event_desc": "2008: Toni Stark va zamonaviy superqahramonlar davrining boshlanishi",
                "year": 2008,
            },
            {
                "tmdb_id": 10138,
                "title_en": "Iron Man 2",
                "title_uz": "Temir odam 2",
                "chronological_order": 4,
                "release_order": 3,
                "timeline_event_desc": "2010: Ivan Vanko xuruji, Qora Beva va Qasoskorlar tashabbusi",
                "year": 2010,
            },
            {
                "tmdb_id": 1724,
                "title_en": "The Incredible Hulk",
                "title_uz": "Incredible Hulk",
                "chronological_order": 5,
                "release_order": 2,
                "timeline_event_desc": "2010: Bryus Benner qochishi va Garlem jangi",
                "year": 2008,
            },
            {
                "tmdb_id": 10195,
                "title_en": "Thor",
                "title_uz": "Tor",
                "chronological_order": 6,
                "release_order": 4,
                "timeline_event_desc": "2011: Asgard shahzodasi surguni va Mjolnir Yerga tushishi",
                "year": 2011,
            },
            {
                "tmdb_id": 24428,
                "title_en": "The Avengers",
                "title_uz": "Qasoskorlar",
                "chronological_order": 7,
                "release_order": 6,
                "timeline_event_desc": "2012: Nyu-York jangi, Loki bosqini va Qasoskorlar birlashuvi",
                "year": 2012,
            },
            {
                "tmdb_id": 68721,
                "title_en": "Iron Man 3",
                "title_uz": "Temir odam 3",
                "chronological_order": 8,
                "release_order": 7,
                "timeline_event_desc": "2012: Mandarin xuruji va Toni Stark ruhiy inqirozi",
                "year": 2013,
            },
            {
                "tmdb_id": 76338,
                "title_en": "Thor: The Dark World",
                "title_uz": "Tor 2: Zulmat dunyosi",
                "chronological_order": 9,
                "release_order": 8,
                "timeline_event_desc": "2013: Efir (Haqiqat toshi) uyg'onishi va Qorong'u elflar",
                "year": 2013,
            },
            {
                "tmdb_id": 100402,
                "title_en": "Captain America: The Winter Soldier",
                "title_uz": "Birinchi qasoskor: Qish askari",
                "chronological_order": 10,
                "release_order": 9,
                "timeline_event_desc": "2014: Qalqon ichidagi Gidra fitnasi va Bakki Barnes",
                "year": 2014,
            },
            {
                "tmdb_id": 118340,
                "title_en": "Guardians of the Galaxy",
                "title_uz": "Galaktika qo'riqchilari",
                "chronological_order": 11,
                "release_order": 10,
                "timeline_event_desc": "2014: Qudrat toshi (Orb) va kosmik qahramonlar jamoasi",
                "year": 2014,
            },
            {
                "tmdb_id": 283995,
                "title_en": "Guardians of the Galaxy Vol. 2",
                "title_uz": "Galaktika qo'riqchilari 2",
                "chronological_order": 12,
                "release_order": 15,
                "timeline_event_desc": "2014: Piter Quillning otasi Ego bilan to'qnashuvi",
                "year": 2017,
            },
            {
                "tmdb_id": 99861,
                "title_en": "Avengers: Age of Ultron",
                "title_uz": "Qasoskorlar: Altron davri",
                "chronological_order": 13,
                "release_order": 11,
                "timeline_event_desc": "2015: Altron sun'iy intellekti, Vizhn tug'ilishi va Sokoviya fojeasi",
                "year": 2015,
            },
            {
                "tmdb_id": 102899,
                "title_en": "Ant-Man",
                "title_uz": "Chumoli odam",
                "chronological_order": 14,
                "release_order": 12,
                "timeline_event_desc": "2015: Skott Leng, Pim zarrachasi va sariq ari to'qnashuvi",
                "year": 2015,
            },
            {
                "tmdb_id": 271110,
                "title_en": "Captain America: Civil War",
                "title_uz": "Birinchi qasoskor: Fuqarolar urushi",
                "chronological_order": 15,
                "release_order": 13,
                "timeline_event_desc": "2016: Sokoviya kelishuvi, Qasoskorlar bo'linishi va Zemo rejasi",
                "year": 2016,
            },
            {
                "tmdb_id": 497698,
                "title_en": "Black Widow",
                "title_uz": "Qora beva",
                "chronological_order": 16,
                "release_order": 24,
                "timeline_event_desc": "2016: Natasha Romanoff o'tmishi, Qizil Xona va Taskmaster",
                "year": 2021,
            },
            {
                "tmdb_id": 315635,
                "title_en": "Spider-Man: Homecoming",
                "title_uz": "O'rgimchak-odam: Uyga qaytish",
                "chronological_order": 17,
                "release_order": 16,
                "timeline_event_desc": "2016: Piter Parker, Toni Stark murabbiyligi va Qoraqush (Vulture)",
                "year": 2017,
            },
            {
                "tmdb_id": 284054,
                "title_en": "Black Panther",
                "title_uz": "Qora Pantera",
                "chronological_order": 18,
                "release_order": 18,
                "timeline_event_desc": "2016: T'Challaning Vakanda taxtiga o'tirishi va Killmonger",
                "year": 2018,
            },
            {
                "tmdb_id": 284052,
                "title_en": "Doctor Strange",
                "title_uz": "Doktor Strenj",
                "chronological_order": 19,
                "release_order": 14,
                "timeline_event_desc": "2016–2017: Kamar-Taj, Agamotto ko'zi (Vaqt toshi) va Dormammu",
                "year": 2016,
            },
            {
                "tmdb_id": 284053,
                "title_en": "Thor: Ragnarok",
                "title_uz": "Tor: Ragnarok",
                "chronological_order": 20,
                "release_order": 17,
                "timeline_event_desc": "2017: Sakaar sayyorasi, Hela hujumi va Asgard qulashi",
                "year": 2017,
            },
            {
                "tmdb_id": 363088,
                "title_en": "Ant-Man and the Wasp",
                "title_uz": "Chumoli odam va Ari",
                "chronological_order": 21,
                "release_order": 20,
                "timeline_event_desc": "2018: Kvant olamiga sho'ng'ish va Tanos qarsagi arafasi",
                "year": 2018,
            },
            {
                "tmdb_id": 299536,
                "title_en": "Avengers: Infinity War",
                "title_uz": "Qasoskorlar: Cheksizlik jangi",
                "chronological_order": 22,
                "release_order": 19,
                "timeline_event_desc": "2018: Tanos 6 ta toshni to'plashi va butun koinotning yarmi yo'qolishi",
                "year": 2018,
            },
            {
                "tmdb_id": 299534,
                "title_en": "Avengers: Endgame",
                "title_uz": "Qasoskorlar: Intiho",
                "chronological_order": 23,
                "release_order": 22,
                "timeline_event_desc": "2018–2023: 5 yil keyingi dunyo, Kvant vaqt sayohati va buyuk g'alaba",
                "year": 2019,
            },
            {
                "tmdb_id": 429617,
                "title_en": "Spider-Man: Far From Home",
                "title_uz": "O'rgimchak-odam: Uydan uzoqda",
                "chronological_order": 24,
                "release_order": 23,
                "timeline_event_desc": "2024: Toni Stark xotirasi, Misterio illyuziyalari va Yevropa safari",
                "year": 2019,
            },
            {
                "tmdb_id": 634649,
                "title_en": "Spider-Man: No Way Home",
                "title_uz": "O'rgimchak-odam: Uyga yo'l yo'q",
                "chronological_order": 25,
                "release_order": 27,
                "timeline_event_desc": "2024: Multiverse ochilishi, 3 ta O'rgimchak-odam birlashuvi",
                "year": 2021,
            },
            {
                "tmdb_id": 453395,
                "title_en": "Doctor Strange in the Multiverse of Madness",
                "title_uz": "Doktor Strenj: Jinilik multikoinotida",
                "chronological_order": 26,
                "release_order": 28,
                "timeline_event_desc": "2024: Vanda Maksimoff va Ko'p olamlar bo'ylab xavfli safar",
                "year": 2022,
            },
            {
                "tmdb_id": 616037,
                "title_en": "Thor: Love and Thunder",
                "title_uz": "Tor: Sevgi va Momaqaldiroq",
                "chronological_order": 27,
                "release_order": 29,
                "timeline_event_desc": "2024: Gorr Xudolar qotili va Yangi Asgard himoyasi",
                "year": 2022,
            },
            {
                "tmdb_id": 505642,
                "title_en": "Black Panther: Wakanda Forever",
                "title_uz": "Qora Pantera: Vakanda mangu",
                "chronological_order": 28,
                "release_order": 30,
                "timeline_event_desc": "2025: Namor va Talokan suv osti qirolligi bilan to'qnashuv",
                "year": 2022,
            },
            {
                "tmdb_id": 640146,
                "title_en": "Ant-Man and the Wasp: Quantumania",
                "title_uz": "Chumoli odam va Ari: Kvantomaniya",
                "chronological_order": 29,
                "release_order": 31,
                "timeline_event_desc": "2025: Kvant olamidagi Kang Fotih bilan to'qnashuv",
                "year": 2023,
            },
            {
                "tmdb_id": 447365,
                "title_en": "Guardians of the Galaxy Vol. 3",
                "title_uz": "Galaktika qo'riqchilari 3",
                "chronological_order": 30,
                "release_order": 32,
                "timeline_event_desc": "2025: Raketa o'tmishi va Oliy Evolyutsionerga qarshi so'nggi yurish",
                "year": 2023,
            },
            {
                "tmdb_id": 533535,
                "title_en": "Deadpool & Wolverine",
                "title_uz": "Dedpul va Rosomaxa",
                "chronological_order": 31,
                "release_order": 34,
                "timeline_event_desc": "2024: TVA vaqt xizmati, Bo'shliq (Void) va MCU olamiga kirish",
                "year": 2024,
            },
        ],
    },
    "harry-potter": {
        "slug": "harry-potter",
        "name": "Garri Potter va Sehrgarlar Olamı",
        "description": "J.K. Rowling sehrgarlik olami — Nyu-Yorkdagi 1926-yilgi Sehrli jonzotlardan tortib, Xogvarts uchun buyuk janggacha bo'lgan to'liq xronologiya.",
        "poster_url": "https://image.tmdb.org/t/p/w780/eVPs2Y0LyvTLZn6AP5Z6O2rtiGB.jpg",
        "banner_url": "https://image.tmdb.org/t/p/original/4gV0rKUjB1nLUdZB4zIltLvNZZr.jpg",
        "is_franchise": True,
        "sort_order": 2,
        "items": [
            {
                "tmdb_id": 259316,
                "title_en": "Fantastic Beasts and Where to Find Them",
                "title_uz": "Sehrli maxluqlar va ularning yashash joyi",
                "chronological_order": 1,
                "release_order": 9,
                "timeline_event_desc": "1926: Nyut Skamanderning Nyu-Yorkka kelishi va Obscurus",
                "year": 2016,
            },
            {
                "tmdb_id": 338952,
                "title_en": "Fantastic Beasts: The Crimes of Grindelwald",
                "title_uz": "Sehrli maxluqlar: Grindelvald jinoyatlari",
                "chronological_order": 2,
                "release_order": 10,
                "timeline_event_desc": "1927: Parij, Gellert Grindelvald qochishi va qorong'u rejalari",
                "year": 2018,
            },
            {
                "tmdb_id": 338953,
                "title_en": "Fantastic Beasts: The Secrets of Dumbledore",
                "title_uz": "Sehrli maxluqlar: Dambldor sirlari",
                "chronological_order": 3,
                "release_order": 11,
                "timeline_event_desc": "1932: Butan saylovlari, Dambldor qasamyodi va birinchi sehrgarlar urushi",
                "year": 2022,
            },
            {
                "tmdb_id": 671,
                "title_en": "Harry Potter and the Philosopher's Stone",
                "title_uz": "Garri Potter va Falsafa toshi",
                "chronological_order": 4,
                "release_order": 1,
                "timeline_event_desc": "1991–1992: Garri Potterning Xogvartsga qadami va Falsafa toshi siri",
                "year": 2001,
            },
            {
                "tmdb_id": 672,
                "title_en": "Harry Potter and the Chamber of Secrets",
                "title_uz": "Garri Potter va Maxfiy xona",
                "chronological_order": 5,
                "release_order": 2,
                "timeline_event_desc": "1992–1993: Maxfiy xona ochilishi, Slizerin merosxo'ri va Vasilisk",
                "year": 2002,
            },
            {
                "tmdb_id": 673,
                "title_en": "Harry Potter and the Prisoner of Azkaban",
                "title_uz": "Garri Potter va Azkaban mahbusi",
                "chronological_order": 6,
                "release_order": 3,
                "timeline_event_desc": "1993–1994: Dementorlar, Sirius Blek siri va Vaqt aylantirgich",
                "year": 2004,
            },
            {
                "tmdb_id": 674,
                "title_en": "Harry Potter and the Goblet of Fire",
                "title_uz": "Garri Potter va Olov kubogi",
                "chronological_order": 7,
                "release_order": 4,
                "timeline_event_desc": "1994–1995: Uch sehrgar turniri va Volan-de-Mortning jismoniy qaytishi",
                "year": 2005,
            },
            {
                "tmdb_id": 675,
                "title_en": "Harry Potter and the Order of the Phoenix",
                "title_uz": "Garri Potter va Feniks jamiyati",
                "chronological_order": 8,
                "release_order": 5,
                "timeline_event_desc": "1995–1996: Sehr vazirligi inqirozi, Feniks jamiyati va Dambldor qo'shini",
                "year": 2007,
            },
            {
                "tmdb_id": 767,
                "title_en": "Harry Potter and the Half-Blood Prince",
                "title_uz": "Garri Potter va Zotdor shahzoda",
                "chronological_order": 9,
                "release_order": 6,
                "timeline_event_desc": "1996–1997: Jonajonlar (Krestaj) siri va Dambldorning fojiali halokati",
                "year": 2009,
            },
            {
                "tmdb_id": 12444,
                "title_en": "Harry Potter and the Deathly Hallows: Part 1",
                "title_uz": "Garri Potter va Ajal tuhfalari: 1-qism",
                "chronological_order": 10,
                "release_order": 7,
                "timeline_event_desc": "1997–1998: Jonajonlarni izlash safari va Malfoylar qasridagi asirlik",
                "year": 2010,
                "aliases": ["garri potter 7: ajal tuhfasi 1", "ajal tuhfasi 1", "ajal tuhfalari: 1-qism", "deathly hallows: part 1", "deathly hallows part 1"],
            },
            {
                "tmdb_id": 12445,
                "title_en": "Harry Potter and the Deathly Hallows: Part 2",
                "title_uz": "Garri Potter va Ajal tuhfalari: 2-qism",
                "chronological_order": 11,
                "release_order": 8,
                "timeline_event_desc": "1998: Xogvarts uchun yakuniy buyuk jang va Volan-de-Mortning mag'lubiyati",
                "year": 2011,
                "aliases": ["garri potter 7: ajal tuhfasi 2", "ajal tuhfasi 2", "ajal tuhfalari: 2-qism", "deathly hallows: part 2", "deathly hallows part 2"],
            },
        ],
    },
    "middle-earth": {
        "slug": "middle-earth",
        "name": "O'rta Yer: Xobbit va Uzuklar Hukmdori",
        "description": "J.R.R. Tolkien afsonaviy olami — Bilbo Begginsning Yolg'iz tog'ga sayohatidan boshlab, Yagona Uzukning Qora Tog'da yo'q qilinishigacha bo'lgan saga.",
        "poster_url": "https://image.tmdb.org/t/p/w780/oENY593nKRVL2PnxXsMtlh8izb4.jpg",
        "banner_url": "https://image.tmdb.org/t/p/original/bccR2CGTWVVSZAG0yqmy3DIvhTX.jpg",
        "is_franchise": True,
        "sort_order": 3,
        "items": [
            {
                "tmdb_id": 49051,
                "title_en": "The Hobbit: An Unexpected Journey",
                "title_uz": "Xobbit: Kutilmagan sarguzasht",
                "chronological_order": 1,
                "release_order": 4,
                "timeline_event_desc": "Uchinchi davr, 2941: Bilbo va gnomlarning Erebor sari yo'lga chiqishi",
                "year": 2012,
            },
            {
                "tmdb_id": 57158,
                "title_en": "The Hobbit: The Desolation of Smaug",
                "title_uz": "Xobbit: Smaug xarobasi",
                "chronological_order": 2,
                "release_order": 5,
                "timeline_event_desc": "Uchinchi davr, 2941: Smaug ajdari uyg'onishi va Dol Guldur qorong'uligi",
                "year": 2013,
            },
            {
                "tmdb_id": 122917,
                "title_en": "The Hobbit: The Battle of the Five Armies",
                "title_uz": "Xobbit: Besh qo'shin jangi",
                "chronological_order": 3,
                "release_order": 6,
                "timeline_event_desc": "Uchinchi davr, 2941: Erebor ostidagi besh qo'shinning qonli jangi",
                "year": 2014,
            },
            {
                "tmdb_id": 120,
                "title_en": "The Lord of the Rings: The Fellowship of the Ring",
                "title_uz": "Uzuklar hukmdori: Uzuk ittifoqi",
                "chronological_order": 4,
                "release_order": 1,
                "timeline_event_desc": "Uchinchi davr, 3018: Yagona Uzuk xavfi va 9 birodar ittifoqi",
                "year": 2001,
            },
            {
                "tmdb_id": 121,
                "title_en": "The Lord of the Rings: The Two Towers",
                "title_uz": "Uzuklar hukmdori: Ikki qal'a",
                "chronological_order": 5,
                "release_order": 2,
                "timeline_event_desc": "Uchinchi davr, 3019: Xelm darasi mudofaasi va Izengard qulashi",
                "year": 2002,
            },
            {
                "tmdb_id": 122,
                "title_en": "The Lord of the Rings: The Return of the King",
                "title_uz": "Uzuklar hukmdori: Qirolning qaytishi",
                "chronological_order": 6,
                "release_order": 3,
                "timeline_event_desc": "Uchinchi davr, 3019: Pelennor dalalari jangi, Uzuk yo'q qilinishi va Aragorn toji",
                "year": 2003,
            },
        ],
    },
    "transformers": {
        "slug": "transformers",
        "name": "Transformerlar",
        "description": "Avtobotlar va Deseptikonlar o'rtasidagi koinot miqyosidagi urush — 1987-yildagi Bamlblining kelishidan zamonaviy davrgacha.",
        "poster_url": "https://image.tmdb.org/t/p/w780/nnFgBA6nR0pHorxdFaDvdY4nVHL.jpg",
        "banner_url": "https://image.tmdb.org/t/p/original/zvZBNNDWd5LcsIBpDhJyCB2MDT7.jpg",
        "is_franchise": True,
        "sort_order": 4,
        "items": [
            {
                "tmdb_id": 424785,
                "title_en": "Bumblebee",
                "title_uz": "Bumblebee",
                "chronological_order": 1,
                "release_order": 6,
                "timeline_event_desc": "1987: Kiberitron qulashi, B-127 (Bamlbli) Yerga kelishi va Charli",
                "year": 2018,
                "aliases": ["bumblebee", "bamlbli", "bamblebi"],
            },
            {
                "tmdb_id": 667538,
                "title_en": "Transformers: Rise of the Beasts",
                "title_uz": "Transformerlar: Maxluqlar uyg'onishi",
                "chronological_order": 2,
                "release_order": 7,
                "timeline_event_desc": "1994: Maksimallar, Yunikron tahdidi va Nyu-York / Peru jangi",
                "year": 2023,
                "aliases": ["transformers 6", "transformerlar 6", "maxluqlar uyg'onishi", "hayvonlar yuksalishi", "rise of the beasts"],
            },
            {
                "tmdb_id": 1858,
                "title_en": "Transformers",
                "title_uz": "Transformerlar",
                "chronological_order": 3,
                "release_order": 1,
                "timeline_event_desc": "2007: Sem Uitviki, Buyuk Uchqun (Allspark) va Megatron uyg'onishi",
                "year": 2007,
                "aliases": ["transformers 1", "transformerlar 1", "transformers (2007)"],
            },
            {
                "tmdb_id": 8373,
                "title_en": "Transformers: Revenge of the Fallen",
                "title_uz": "Transformerlar: Mag'lublar qasosi",
                "chronological_order": 4,
                "release_order": 2,
                "timeline_event_desc": "2009: Misr ehromlari ostidagi quyosh yo'qotuvchi mashina va Fallen",
                "year": 2009,
                "aliases": ["transformers 2", "transformerlar 2", "yiqilganlar qasosi", "mag'lublar qasosi", "revenge of the fallen"],
            },
            {
                "tmdb_id": 38356,
                "title_en": "Transformers: Dark of the Moon",
                "title_uz": "Transformerlar 3: Oyning qorong'u tomoni",
                "chronological_order": 5,
                "release_order": 3,
                "timeline_event_desc": "2011: Oyga parvoz siri, Sentinil Praym xiyonati va Chikago jangi",
                "year": 2011,
                "aliases": ["transformers 3", "transformerlar 3", "oyning qorong'u tomoni", "dark of the moon"],
            },
            {
                "tmdb_id": 91314,
                "title_en": "Transformers: Age of Extinction",
                "title_uz": "Transformerlar: Qirg'in davri",
                "chronological_order": 6,
                "release_order": 4,
                "timeline_event_desc": "2014: Transformium metali, Dinobotlar va Lokdaun ovchisi",
                "year": 2014,
                "aliases": ["transformers 4", "transformerlar 4", "yo'q bo'lish davri", "yoʻq boʻlish davri", "qirg'in davri", "age of extinction"],
            },
            {
                "tmdb_id": 335988,
                "title_en": "Transformers: The Last Knight",
                "title_uz": "Transformerlar: So'nggi ritsar",
                "chronological_order": 7,
                "release_order": 5,
                "timeline_event_desc": "2017: Qirol Artur siri, Kiberitron qaytishi va Kvintessa joduysi",
                "year": 2017,
                "aliases": ["transformers 5", "transformerlar 5", "so'nggi ritsar", "soʻnggi ritsar", "the last knight"],
            },
        ],
    },
    "fast-and-furious": {
        "slug": "fast-and-furious",
        "name": "Forsaj (Fast & Furious)",
        "description": "Dominik Toretto va uning oilasi sarguzashtlari — Los-Anjeles ko'chalaridagi poygalardan tortib butun dunyoni qutqarishgacha.",
        "poster_url": "https://image.tmdb.org/t/p/w780/zOCnMPoUxgJK1RFPfN4PcnT16gr.jpg",
        "banner_url": "https://image.tmdb.org/t/p/original/z5A5W3WYJc3UVEWljSGwdjDgQ0j.jpg",
        "is_franchise": True,
        "sort_order": 5,
        "items": [
            {
                "tmdb_id": 9799,
                "title_en": "The Fast and the Furious",
                "title_uz": "Forsaj",
                "chronological_order": 1,
                "release_order": 1,
                "timeline_event_desc": "2001: Brayan O'Konner va Dominik Toretto do'stligi boshlanishi",
                "year": 2001,
            },
            {
                "tmdb_id": 584,
                "title_en": "2 Fast 2 Furious",
                "title_uz": "Forsaj 2: Ikki hissa forsaj",
                "chronological_order": 2,
                "release_order": 2,
                "timeline_event_desc": "2003: Mayami, Brayan va Roman Pirsning Verone ustidan g'alabasi",
                "year": 2003,
            },
            {
                "tmdb_id": 13804,
                "title_en": "Fast & Furious",
                "title_uz": "Forsaj 4",
                "chronological_order": 3,
                "release_order": 4,
                "timeline_event_desc": "2009: Letti fojeasi, Braga to'dasi va Meksika tunneli poygasi",
                "year": 2009,
            },
            {
                "tmdb_id": 51497,
                "title_en": "Fast Five",
                "title_uz": "Forsaj 5: Rio drayvi",
                "chronological_order": 4,
                "release_order": 5,
                "timeline_event_desc": "2011: Rio seyfi talon-toroji va Lyuk Hobbs bilan birinchi to'qnashuv",
                "year": 2011,
            },
            {
                "tmdb_id": 87101,
                "title_en": "Fast & Furious 6",
                "title_uz": "Forsaj 6",
                "chronological_order": 5,
                "release_order": 6,
                "timeline_event_desc": "2013: Ouen Shou guruhi, Letti qaytishi va Ispaniya aeroporti jangi",
                "year": 2013,
            },
            {
                "tmdb_id": 9615,
                "title_en": "The Fast and the Furious: Tokyo Drift",
                "title_uz": "Forsaj 3: Tokio drayvi",
                "chronological_order": 6,
                "release_order": 3,
                "timeline_event_desc": "2006/2013: Shan Boshvell, Tokio drifti va Xanning sirli avtohalokati",
                "year": 2006,
            },
            {
                "tmdb_id": 168259,
                "title_en": "Furious 7",
                "title_uz": "Forsaj 7",
                "chronological_order": 7,
                "release_order": 7,
                "timeline_event_desc": "2014: Dekkard Shou qasosi, Xudoning Ko'zi va Brayanga so'nggi ehtirom",
                "year": 2015,
            },
            {
                "tmdb_id": 337339,
                "title_en": "The Fate of the Furious",
                "title_uz": "Forsaj 8",
                "chronological_order": 8,
                "release_order": 8,
                "timeline_event_desc": "2017: Kiberjinoyatchi Sayfer va Dominik Torettodan kutilmagan xiyonat",
                "year": 2017,
            },
            {
                "tmdb_id": 384018,
                "title_en": "Fast & Furious Presents: Hobbs & Shaw",
                "title_uz": "Forsaj: Hobbs va Shou",
                "chronological_order": 9,
                "release_order": 9,
                "timeline_event_desc": "2019: Brixton kiber-askari va Samoa orolidagi an'anaviy jang",
                "year": 2019,
            },
            {
                "tmdb_id": 385128,
                "title_en": "F9: The Fast Saga",
                "title_uz": "Forsaj 9",
                "chronological_order": 10,
                "release_order": 10,
                "timeline_event_desc": "2021: Jeykob Toretto siri, kosmik reys va Xanning tirik qaytishi",
                "year": 2021,
            },
            {
                "tmdb_id": 385687,
                "title_en": "Fast X",
                "title_uz": "Forsaj 10",
                "chronological_order": 11,
                "release_order": 11,
                "timeline_event_desc": "2023: Dante Reyesning qasosi va Toretto oilasining parchalanish xavfi",
                "year": 2023,
            },
        ],
    },
    "dceu": {
        "slug": "dceu",
        "name": "DC Kengaytirilgan Koinoti (DCEU)",
        "description": "DC Comics qahramonlari — Mo''jiza ayolning 1918-yildagi ilk qadamidan Zak Snayder Adolat ligasigacha.",
        "poster_url": "https://image.tmdb.org/t/p/w780/rNnIW6xSPeTiIUtsfEhFeIRiJVv.jpg",
        "banner_url": "https://image.tmdb.org/t/p/original/rPaqhsSMCky0UXVW4qmNOJq5Orp.jpg",
        "is_franchise": True,
        "sort_order": 6,
        "items": [
            {
                "tmdb_id": 297762,
                "title_en": "Wonder Woman",
                "title_uz": "Mo''jiza ayol",
                "chronological_order": 1,
                "release_order": 4,
                "timeline_event_desc": "1918: 1-Jahon Urushi, Femiskira oroli va Urush xudosi Ares",
                "year": 2017,
            },
            {
                "tmdb_id": 464052,
                "title_en": "Wonder Woman 1984",
                "title_uz": "Mo''jiza ayol 1984",
                "chronological_order": 2,
                "release_order": 9,
                "timeline_event_desc": "1984: Sovuq urush avji, Orzular toshi va Geparda",
                "year": 2020,
            },
            {
                "tmdb_id": 49521,
                "title_en": "Man of Steel",
                "title_uz": "Po'lat odam",
                "chronological_order": 3,
                "release_order": 1,
                "timeline_event_desc": "2013: Kripton halokati, Klark Kent uyg'onishi va General Zod bosqini",
                "year": 2013,
            },
            {
                "tmdb_id": 209112,
                "title_en": "Batman v Superman: Dawn of Justice",
                "title_uz": "Betmen Supermenga qarshi: Adolat tongi",
                "chronological_order": 4,
                "release_order": 2,
                "timeline_event_desc": "2015: Qahramonlar to'qnashuvi, Leks Lyutor va Doomsday fojeasi",
                "year": 2016,
            },
            {
                "tmdb_id": 297761,
                "title_en": "Suicide Squad",
                "title_uz": "O'z joniga qasd qiluvchilar otryadi",
                "chronological_order": 5,
                "release_order": 3,
                "timeline_event_desc": "2016: Amanda Uollerning Task Force X guruhi va Enchantress",
                "year": 2016,
            },
            {
                "tmdb_id": 791373,
                "title_en": "Zack Snyder's Justice League",
                "title_uz": "Zak Snayderning Adolat Ligasi",
                "chronological_order": 6,
                "release_order": 5,
                "timeline_event_desc": "2017: Ona qutilari uyg'onishi, Steppenwolf va Supermen tirilishi",
                "year": 2021,
            },
            {
                "tmdb_id": 297802,
                "title_en": "Aquaman",
                "title_uz": "Akvamen",
                "chronological_order": 7,
                "release_order": 6,
                "timeline_event_desc": "2018: Artur Karri, Atlantis taxti va Atlan nayzasi",
                "year": 2018,
            },
            {
                "tmdb_id": 287947,
                "title_en": "Shazam!",
                "title_uz": "Shazam!",
                "chronological_order": 8,
                "release_order": 7,
                "timeline_event_desc": "2019: Billi Betson va Yetti o'lim gunohi bilan to'qnashuv",
                "year": 2019,
            },
            {
                "tmdb_id": 436969,
                "title_en": "The Suicide Squad",
                "title_uz": "O'z joniga qasd qiluvchilar: Missiya",
                "chronological_order": 9,
                "release_order": 10,
                "timeline_event_desc": "2021: Korto Malteze oroli va Starro the Conqueror yirtqichi",
                "year": 2021,
            },
            {
                "tmdb_id": 436270,
                "title_en": "Black Adam",
                "title_uz": "Qora Adam",
                "chronological_order": 10,
                "release_order": 11,
                "timeline_event_desc": "2022: Qandak shahrining 5000 yillik himoyachisi uyg'onishi",
                "year": 2022,
            },
            {
                "tmdb_id": 298618,
                "title_en": "The Flash",
                "title_uz": "Flesh",
                "chronological_order": 11,
                "release_order": 13,
                "timeline_event_desc": "2023: Vaqt sayohati, Flashpoint va yangilangan multiverse",
                "year": 2023,
            },
            {
                "tmdb_id": 572802,
                "title_en": "Aquaman and the Lost Kingdom",
                "title_uz": "Akvamen va yo'qolgan qirollik",
                "chronological_order": 12,
                "release_order": 15,
                "timeline_event_desc": "2023: Qora Nayza, Qora Manta va Atlantisning yakuniy jangi",
                "year": 2023,
            },
        ],
    },
}


import re

def find_canon_match(tmdb_id: int | None, title: str | None) -> tuple[str, CanonItemBlueprint] | None:
    """
    Look up whether a movie matches any predefined canon universe.
    Returns (franchise_slug, canon_item) or None.
    First checks by TMDb ID (rock-solid 100% precision).
    Disambiguates HP 7 Part 1 vs Part 2 if tmdb_id is 12445 and title indicates Part 1.
    Fallback checks by normalized English/Uzbek title and specific aliases.
    """
    norm_title = ""
    if title:
        norm_title = (
            title.lower()
            .replace("‘", "'")
            .replace("’", "'")
            .replace("ʻ", "'")
            .replace("`", "'")
            .strip()
        )

    # 1. TMDb ID
    if tmdb_id:
        if tmdb_id == 12445 and norm_title and (
            " 1" in norm_title or "part 1" in norm_title or "1-qism" in norm_title or "tuhfasi 1" in norm_title
        ):
            for item in CANON_FRANCHISES["harry-potter"]["items"]:
                if item["chronological_order"] == 10:
                    return "harry-potter", item

        for slug, franchise in CANON_FRANCHISES.items():
            for item in franchise["items"]:
                if item["tmdb_id"] == tmdb_id:
                    return slug, item
        # If tmdb_id was provided and didn't match any canon item, it's definitely not in canon!
        return None

    if not norm_title:
        return None

    # 2. Specific Aliases first across all franchises
    for slug, franchise in CANON_FRANCHISES.items():
        for item in franchise["items"]:
            for alias in item.get("aliases", []):
                norm_alias = (
                    alias.lower()
                    .replace("‘", "'")
                    .replace("’", "'")
                    .replace("ʻ", "'")
                    .replace("`", "'")
                    .strip()
                )
                if norm_alias and norm_alias in norm_title:
                    return slug, item

    # 3. Exact titles
    for slug, franchise in CANON_FRANCHISES.items():
        for item in franchise["items"]:
            en_lower = (
                item["title_en"]
                .lower()
                .replace("‘", "'")
                .replace("’", "'")
                .replace("ʻ", "'")
                .replace("`", "'")
                .strip()
            )
            uz_lower = (
                item["title_uz"]
                .lower()
                .replace("‘", "'")
                .replace("’", "'")
                .replace("ʻ", "'")
                .replace("`", "'")
                .strip()
            )
            if norm_title in (en_lower, uz_lower):
                return slug, item

    # 4. Fallback word boundary regex (with sequel number guard)
    has_sequel_num = bool(re.search(r"\b[2-9]\b", norm_title) or re.search(r"\b1[0-9]\b", norm_title))

    for slug, franchise in CANON_FRANCHISES.items():
        for item in franchise["items"]:
            en_lower = (
                item["title_en"]
                .lower()
                .replace("‘", "'")
                .replace("’", "'")
                .replace("ʻ", "'")
                .replace("`", "'")
                .strip()
            )
            uz_lower = (
                item["title_uz"]
                .lower()
                .replace("‘", "'")
                .replace("’", "'")
                .replace("ʻ", "'")
                .replace("`", "'")
                .strip()
            )

            item_has_num = bool(re.search(r"\b[2-9]\b", en_lower) or re.search(r"\b[2-9]\b", uz_lower))
            if has_sequel_num and not item_has_num:
                continue

            if len(en_lower) >= 6 and re.search(rf"\b{re.escape(en_lower)}\b", norm_title):
                return slug, item
            if len(uz_lower) >= 6 and re.search(rf"\b{re.escape(uz_lower)}\b", norm_title):
                return slug, item

    return None

