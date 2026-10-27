# 🎨 KINOCHI & MEDIAPLUS: MASTER DIZAYN TIZIMI (v4.0)
## iTV, Allplay, Kinopoisk, IMDb va Netflix Dizayn Standartlari Sintezi

> **Hujjat Maqsadi:** Jahon va mahalliy 5 ta yetakchi media gigantining — **Netflix** (gorizontal karusellar, kartochka micro-animatsiyalari), **iTV** (qora/qizil kinoteatr muhiti, ulkan hero banner), **Allplay** (bir sahifali jonli filtrlar, franshizalar zanjiri), **Kinopoisk** (aktyor/rejissyor profillari, filmografiya, faktlar) va **IMDb** (chuqur metama'lumotlar, texnik xususiyatlar, global reyting) vizual standartlarini yagona mukammal dizayn tizimiga birlashtirish.

---

## 1. Vizual Stil & Ranglar Palitrasi (Design Tokens)

Interfeys ko'zni toliqtirmaydigan, kontentni (posterlar va kadrlarni) yorqin ajratib ko'rsatuvchi chuqur qorong'i palitraga asoslanadi:

```css
/* Asosiy Sirtlar (iTV & Netflix standarti) */
--bg-obsidian: #09090B;           /* Asosiy qora fon (Deep Void Black) */
--bg-surface: #121316;            /* Kartochkalar, modallar, yon menyular */
--bg-surface-elevated: #18191E;   /* Hover qilingan elementlar */
--bg-glass: rgba(18, 19, 22, 0.80);/* Glassmorphism shaffof fon */

/* Asosiy Ranglar & Aksentlar */
--primary-red: #E50914;           /* Netflix/iTV Cinematic Red — Asosiy tugmalar (CTA) */
--primary-red-hover: #F40612;     /* Tugma bosilgandagi yorqin qizil */
--primary-red-glow: rgba(229, 9, 20, 0.35); /* Neon qizil nur */

/* Reyting & Yordamchi */
--accent-gold: #F5C518;           /* IMDb & Kinopoisk sariq/oltin reyting yulduzi */
--telegram-blue: #229ED9;         /* Telegram tugmalari va nishonlari */
--text-primary: #FFFFFF;          /* Asosiy oq matn */
--text-secondary: #A1A1AA;        /* Tavsiflar, yillar, janrlar */
--border-subtle: rgba(255, 255, 255, 0.07);
```

---

## 2. Asosiy UI Komponentlari Anatomiyasi

### 2.1. Sticky Glass Header (iTV & Netflix)
* Ekranning yuqori qismida doimiy qotirilgan, skroll qilinganda xiralashuvchi shaffof navigatsiya paneli (`backdrop-blur-xl bg-[#09090B]/85 border-b border-white/5`).
* Logotip: Qizil nuqtali qalin "KINOCHI" brendi.
* Menyu: *Bosh sahifa, Filmlar, Seriallar, Multfilmlar, Anime, To'plamlar*.
* O'ng tomonda: Tezkor jonli qidiruv tugmasi (`Ctrl+K`) va Telegram Botga o'tish tugmasi.

### 2.2. Cinematic Hero Banner (iTV & Netflix)
* Balandligi: `78vh - 82vh` keng ekranli kadr.
* 3 tomonlama silliq gradient (pastdan, chapdan va vinyetka).
* Metama'lumotlar: Film nomi, original nomi, chiqarilgan yili, davomiyligi, yosh chegarasi (`16+`, `18+`), IMDb reytingi va film kodi (`#1428`).
* Asosiy Tugmalar:
  * `[ 🔴 TELEGRAM ORQALI TOMOSHA QILISH ]` (Qizil yonuvchi asosiy CTA).
  * `[ ▶️ TREYLER ]` (Sayt ichida YouTube modalini ochadi).
  * `[ 🔖 SAQLASH ]` / `[ ℹ️ BATAFSIL ]`.

### 2.3. Netflix Uslubidagi Gorizontal Kontent Karusellari (Rails)
* Bo'lim nomi: *🔥 Trenddagi xitlar*, *🇺🇿 Yangi O'zbekcha Dublyajlar*, *🍿 Hafta Premyeralari*, *👑 Kinopoisk Top-250*.
* Silliq snap-scroll gorizontal lentasi (Desktopda chap/o'ng navigatsiya strelkalari bilan).

### 2.4. 2:3 Kontent Kartochkalari (Movie Cards)
* Standart 2:3 kinoposter o'lchami (`rounded-2xl overflow-hidden`).
* **Hover Effektlari (Netflix/iTV):**
  * Kursorni borganda: `scale-[1.04] transition-all duration-300`, chuqur soya (`shadow-2xl`) va qizil hoshiya nurlanishi.
* Badgellar:
  * Yuqori chapda: `[ ⭐ 8.6 ]` (IMDb reytingi).
  * Yuqori o'ngda: `[ #CODE ]` (Film kodi).
  * Pastki burchakda: `[ FHD ]` yoki `[ 4K ]` va dublyaj tili (`[ 🇺🇿 UZ ]`).
* Pastki gradientli matn: Filmning o'zbekcha nomi, yili va asosiy janri.

### 2.5. Bir Sahifali Jonli Filtr Paneli (Allplay Uslubida)
* Katalog sahifasida barcha parametrlarni bir joyda qulay saralash:
  * *Toifa:* Barchasi / Filmlar / Seriallar / Multfilmlar / Premyeralar.
  * *Janr:* Jangari, Komediya, Drama, Triller, Fantastika, Tarixiy...
  * *Yil:* 2026, 2025, 2024, 2020-2023, Arxiv.
  * *Mamlakat:* AQSH, Turkiya, Janubiy Koreya, O'zbekiston, Buyuk Britaniya...
  * *Ovoz:* O'zbekcha dublyaj, Ruscha, Asl ovoz.
  * *Saralash:* Mashhurlik, Reyting, Yangi qo'shilganlar, Chiqqan yili.

### 2.6. Film Tafsilotlari Sahifasi (Kinopoisk & IMDb)
* Yuqori qismda keng kadrli fon va vertikal katta poster.
* To'liq metama'lumotlar: Rejissyor, aktyorlar, ssenariy muallifi, janrlar, yosh chegarasi, dublyaj studiyasi nomi.
* **Ijodkorlar Karuseli (Kinopoisk):** Rejissyor va aktyorlarning dumaloq avatarlari, filmdagi roli va ismi.
* **Franshiza Xronologiya Zanjiri (Allplay):** Bir necha qismli filmlar uchun interaktiv ketma-ketlik zanjiri (*1-qism -> 2-qism -> 3-qism*).
* **O'xshash filmlar tavsiyasi:** IMDb algoritmi asosida mos tavsiyalar.

### 2.7. Mobil Bottom Navigation Bar (Smartfonlar Uchun)
* Mobil ekranning pastki qismida ilova kabi doimiy turuvchi menyu:
  `[ 🏠 Bosh sahifa ]  [ 🎬 Filmlar ]  [ 📺 Seriallar ]  [ 📚 To'plamlar ]  [ 🔍 Qidiruv ]`

---
*Ushbu dizayn tizimi platformamizga dunyo darajasidagi estetik qiyofa va foydalanish qulayligini ta'minlaydi.*
