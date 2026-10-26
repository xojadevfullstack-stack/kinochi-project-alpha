# 🎬 KINOCHI DESIGN SYSTEM SPECIFICATION (v3.0 - MASTER EDITION)
## iTV.uz (Estetika), Allplay.uz (Filtrlar) & Kinochilar.com (9 Qatlamli Taksonomiya & Rejissyorlar) Chuqur Sintezi

> **Hujjat Maqsadi:** O'zbekistondagi yetakchi media platformalarning barcha kuchli jihatlarini — **iTV.uz** ning shohona qorong'i dizayni va hero bannerini, **Allplay.uz** ning mukammal filtr tizimini hamda **Kinochilar.com** ning 9 o'lchamli media taksonomiyasi va oltin nurlanishli rejissyor/aktyor profillarini 100% o'rganib, loyihamiz ("Kinochi / MediaPlus") uchun eng yuqori darajadagi professional dizayn tizimini shakllantirish.

---

## 📑 MUNDARIJA
1. [Dizayn Falsafasi & Ranglar Tizimi (Design Tokens)](#1-dizayn-falsafasi--ranglar-tizimi-design-tokens)
2. [Tipografiya & Matn Standartlari](#2-tipografiya--matn-standartlari)
3. [9 Qatlamli Media Taksonomiya Mega-Paneli (Kinochilar Uslubi)](#3-9-qatlamli-media-taksonomiya-mega-paneli-kinochilar-uslubi)
4. [Rejissyorlar va Aktyorlar Gridi & Oltin Halo Kartochkalar](#4-rejissyorlar-va-aktyorlar-gridi--oltin-halo-kartochkalar)
5. [Cinematic Hero Banner (iTV Uslubida 75-82vh)](#5-cinematic-hero-banner-itv-uslubida-75-82vh)
6. [2:3 Nisbatdagi Kontent Kartochkalari (Movie Cards)](#6-23-nisbatdagi-kontent-kartochkalari-movie-cards)
7. [Franshizalar Xronologiya Zanjiri (Franchise Timeline)](#7-franshizalar-xronologiya-zanjiri-franchise-timeline)
8. [Studiyalar va Striming Platformalari Gridi](#8-studiyalar-va-striming-platformalari-gridi)
9. [Mavzular (Themes & Tropes) Moduli](#9-mavzular-themes--tropes-moduli)
10. [Film va Serial Tafsilotlari Sahifasi (Detail View)](#10-film-va-serial-tafsilotlari-sahifasi-detail-view)
11. [YouTube Treyler Modali & Telegram Bosh CTA](#11-youtube-treyler-modali--telegram-bosh-cta)
12. [Seriallar: Mavsumlar va Qismlar Moduli](#12-seriallar-mavsumlar-va-qismlar-moduli)
13. [Allplay Uslubidagi Jonli Filtr Paneli](#13-allplay-uslubidagi-jonli-filtr-paneli)
14. [Mobil Ekran Moslashuvi & Bottom Navigation Bar](#14-mobil-ekran-moslashuvi--bottom-navigation-bar)

---

## 1. Dizayn Falsafasi & Ranglar Tizimi (Design Tokens)

Interfeys uchta ustun rang kontrastiga asoslanadi: **Chuqur Obsidian Qora** (kinoteatr muhiti), **Kinematik Qizil** (bosh harakatlar va dinamika), hamda **Oltin/Amber** (nufuz, reytinglar va ijodkorlar avatarlari).

```css
/* ==================== SIRTLAR VA FONLAR ==================== */
--bg-obsidian: #09090B;           /* Bosh fon (Deep Void Black) */
--bg-surface: #121316;            /* Kartochkalar, yon panellar sirti */
--bg-surface-elevated: #18191E;   /* Hover holati, modal oynalar */
--bg-glass: rgba(18, 19, 22, 0.80);/* Xiralashtirilgan oyna effekti (Backdrop blur) */

/* ==================== ASOSIY AKSENTLAR ==================== */
--primary-red: #E50914;           /* iTV/Netflix qizili — asosiy harakat tugmalari */
--primary-red-hover: #F40612;     /* Tugma bosilgandagi holat */
--primary-red-glow: rgba(229, 9, 20, 0.40); /* Neon qizil nur */

/* ==================== OLTI / AMBER AKSENT ==================== */
--accent-amber: #F5C518;          /* IMDb oltini, taksonomiya sonlari */
--accent-amber-glow: rgba(245, 197, 24, 0.35); /* Rejissyorlar avatari nurlanishi */
--badge-amber-bg: rgba(42, 35, 18, 0.60);     /* Sanoq nishonlari foni */
--badge-amber-border: rgba(245, 197, 24, 0.25);

/* ==================== TELEGRAM VA YORDAMCHI ==================== */
--telegram-blue: #229ED9;         /* Telegram brend rangi */
--telegram-blue-hover: #1E88E5;
--telegram-blue-glow: rgba(34, 158, 217, 0.35);

/* ==================== MATNLAR VA CHEGARALAR ==================== */
--text-primary: #FFFFFF;          /* Asosiy oq matn */
--text-secondary: #A1A1AA;        /* Kulrang metama'lumot */
--text-muted: #71717A;            /* Nozik izohlar */
--border-subtle: rgba(255, 255, 255, 0.06); /* Nozik chegara */
--border-medium: rgba(255, 255, 255, 0.12);
--border-active: rgba(229, 9, 20, 0.50);
```

---

## 2. Tipografiya & Matn Standartlari

* **Font Stack:** `'Inter'`, `-apple-system`, `BlinkMacSystemFont`, `sans-serif` (Body va UI uchun).
* **Headings:** `'Outfit'`, `'Inter'` (`font-black`, `tracking-tight`).

### Matn Ierarxiyasi Shkalasi:
* **Hero H1:** `text-3xl sm:text-5xl lg:text-6xl font-black tracking-tight leading-none text-white drop-shadow-lg`
* **Bo'lim H2:** `text-xl sm:text-2xl font-bold tracking-tight text-white flex items-center gap-2.5`
* **Kartochka H3:** `text-sm sm:text-base font-semibold text-white line-clamp-1 group-hover:text-primary-red transition-colors`
* **Taksonomiya Nomi:** `text-sm font-semibold text-neutral-300 hover:text-white transition-colors`
* **Taksonomiya Sanoq Raqami:** `font-bold text-xs text-amber-400 ml-1.5`
* **Yillar va Statistika:** `text-xs text-neutral-400 tracking-wide`
* **Kino Kodi Badge:** `font-mono text-xs font-black tracking-widest uppercase px-2.5 py-1 rounded-md bg-white/10 text-white border border-white/15`

---

## 3. 9 Qatlamli Media Taksonomiya Mega-Paneli (Kinochilar Uslubi)

Saytning eng yuqori darajadagi saralash qatlami. Foydalanuvchi filmlarni faqat janr bo'yicha emas, balki **9 xil o'lcham** bo'yicha ko'ra oladi:

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ Franshizalar 479  Rejissyorlar 498  Aktyorlar 3085  Studiyalar 144  Janrlar uyg'unligi 24  Davlatlar 24  Mavzular 279  ...│
└────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 9 Qatlamning Har Biri Bo'yicha Spetsifikatsiya:

1. **Franshizalar (479):**
   * Dunyodagi barcha yirik kino koinotlari (*Marvel Cinematic Universe, DC Extended Universe, Garri Potter, Jon Uik, Forsaj, Yulduzlar jangi, O'rgimchak odam*).
   * Har bir franshiza ichida barcha filmlar rasmiy xronologiya bo'yicha ulanadi.
2. **Rejissyorlar (498):**
   * Dunyoning eng nufuzli rejissyorlari (*Kristofer Nolan, Kventin Tarantino, Jeyms Kemeron, Gay Richi, Nuri Bilge Jeylan, Uluch Bayraktar, Serdar Akar*).
3. **Aktyorlar (3085):**
   * Bosh rol ijrochilari (*Jeyson Steytem, Leonardo Di Kaprio, Kianu Rivz, Burak O'zchivit, Song Kang-ho*).
4. **Studiyalar va platformalar (144):**
   * Rasmiy striminglar va gigant studiyalar (*Netflix, HBO Max, Disney+, Warner Bros., Marvel Studios, A24, Apple TV+, Amazon Prime Video, Paramount*).
5. **Janrlar uyg'unligi (24):**
   * Gibrid janr kombinatsiyalari (*Jangari-Komediya, Fantastika-Triller, Tarixiy-Jangari, Qo'rqinchli-Detektiv, Melodrama-Komediya*).
6. **Davlatlar (24):**
   * Mamlakatlar bo'yicha saralash (*AQSH, Turkiya, Janubiy Koreya, Buyuk Britaniya, O'zbekiston, Fransiya, Hindiston, Yaponiya*).
7. **Mavzular (Themes & Tropes - 279):**
   * Maxsus syujet liniyalari:
     * *Vaqt sayohati (Time Travel)*
     * *Qasos (Revenge)*
     * *Zombi apokalipsis*
     * *Bank o'g'irligi (Heist)*
     * *Sun'iy intellekt va Kiborglar*
     * *Kosmos va Sayyoralararo parvoz*
     * *Mafia va Gangsterlar olami*
     * *Superqahramonlar*
     * *Omon qolish (Survival)*
8. **Kimlar uchun (Audience - 3):**
   * *Bolalar uchun (0-12 yosh — multfilmlar, sarguzashtlar)*
   * *Oila davrasida (Zo'ravonlik va ochiq sahnalarsiz umumiy filmlar)*
   * *Kattalar uchun (18+ qonli jangari, triller, psixologik dramalar)*
9. **Mukofotlar va reytinglar (16):**
   * *Oskar g'oliblari*, *Kinopoisk Top-250*, *IMDb Top-250*, *Kann festivali oltin palma shoxi*, *Oltin Globus*.

### 💻 Frontend Komponent K确:
```tsx
<div className="w-full bg-[#0A0A0D] border-b border-white/5 py-3 overflow-x-auto scrollbar-none">
  <div className="max-w-container-max mx-auto px-gutter flex items-center gap-6 whitespace-nowrap">
    {TAXONOMIES.map((item) => (
      <Link
        key={item.slug}
        href={`/collections/${item.slug}`}
        className="group flex items-center text-sm font-semibold text-neutral-300 hover:text-white transition-colors cursor-pointer"
      >
        <span>{item.name}</span>
        <span className="text-amber-400 text-xs font-bold ml-1.5 px-1.5 py-0.5 rounded-full bg-amber-950/40 border border-amber-500/20 group-hover:border-amber-500/50 transition-colors">
          {item.count}
        </span>
      </Link>
    ))}
  </div>
</div>
```

---

## 4. Rejissyorlar va Aktyorlar Gridi & Oltin Halo Kartochkalar

Kinochilar.com ning 1-rasmida ko'rsatilgan ajoyib rejissyorlar griding texnik andozasi:

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│                         [ ( 🟡 ) ]                            │
│                     Oltin Nurli Avatar                       │
│                                                              │
│                     Christopher Nolan                        │
│                   12 ta film • 2000–2026                     │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### 🧩 Kartochkaning Piksellar Standarti:
* **Konteyner:** `bg-[#121316] hover:bg-[#18191E] border border-white/5 hover:border-amber-500/40 rounded-2xl p-4 sm:p-5 flex flex-col items-center text-center transition-all duration-300 hover:-translate-y-1.5 hover:shadow-[0_12px_30px_rgba(0,0,0,0.7),0_0_20px_rgba(245,197,24,0.2)]`
* **Doiraviy Avatar (Circular Avatar):**
  * O'lchami: Desktopda `w-22 h-22 sm:w-24 sm:h-24`, mobilda `w-18 h-18`.
  * Shakli: `rounded-full overflow-hidden`.
  * **Oltin Halo / Glowing Amber Border:**
    * `ring-2 ring-amber-500/80 shadow-[0_0_16px_rgba(245,197,24,0.35)]`
* **Monogram Fallback (Surat bo'lmaganda):**
  * Surat topilmasa (masalan: *Murat Öztürk*), bo'sh yoki singan rasm o'rniga:
  * `w-full h-full bg-[#18181D] rounded-full flex items-center justify-center text-amber-400 font-black text-xl tracking-wider`
  * Matn: Ism va familiyaning bosh harflari (masalan, **"MÖ"**, **"CN"**, **"QT"**).
* **Ism:** `font-bold text-white text-sm sm:text-base mt-3 line-clamp-1 group-hover:text-amber-400 transition-colors`
* **Statistika:** `text-xs text-neutral-400 mt-1 font-medium` — `X ta film • YYYY–YYYY` (masalan: `12 ta film • 2000–2026`).
* **Grid Tuzilishi:**
  * Desktop: `grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4 sm:gap-5`
* **Pastki Tugma:**
  * `Barcha rejissyorlar — 498 ta →`
  * `w-full py-3.5 mt-6 rounded-xl border border-white/10 hover:border-amber-500/40 hover:bg-white/5 text-white/90 font-medium text-sm transition-all duration-200 flex items-center justify-center gap-2`

---

## 5. Cinematic Hero Banner (iTV Uslubida 75-82vh)

* **Balandligi:** Mobil ekranda `68vh`, Desktopda `78vh - 82vh`.
* **Fon tasviri:** Ultra yuqori tiniqlikdagi gorizontal kadr (Backdrop).
* **3-Taraflama Gradient Qatlamlari:**
  1. *Pastki qatlam:* `bg-gradient-to-t from-[#09090B] via-[#09090B]/85 to-transparent` (bosh sahifaga chiroyli qo'shilib ketadi).
  2. *Chap qatlam (Desktop):* `bg-gradient-to-r from-[#09090B] via-[#09090B]/75 to-transparent` (matn har doim o'qilishi uchun).
  3. *Radial Vignette:* Markaziy qahramonni ajratib turuvchi burchak qorayishi.
* **Metama'lumotlar bloki:**
  * **Kino Kodi Badge:** `[ #1428 ]` — oq mono shriftda.
  * **Reyting Badgelari:** `[ ⭐ IMDb 8.8 ]` (oltin matn) va `[ 🎬 Kinochi 9.3 ]`.
  * **Texnik ko'rsatkichlar:** `2024 • 2 soat 18 daqiqa • 16+ • FHD / 4K`.
  * **Janrlar:** `Jangari • Sarguzasht • Fantastika`.
* **CTA Tugmalar Klasteri:**
  1. `[ 🔴 TELEGRAM ORQALI TOMOSHA QILISH ]` (Asosiy qizil harakat tugmasi, `shadow-[0_0_25px_rgba(229,9,20,0.4)]`).
  2. `[ ▶️ TREYLER ]` (Sayt ichida YouTube modalini ochadi).
  3. `[ 🔖 SAQLASH ]` (Mahalliy xotiraga sevimli qilib qo'shadi).

---

## 6. 2:3 Nisbatdagi Kontent Kartochkalari (Movie Cards)

* **Proporsiya:** Qat'iy `aspect-[2/3]`.
* **Burchaklar:** `rounded-2xl overflow-hidden`.
* **Chegara:** `border border-white/[0.06] hover:border-[#E50914]/60`.
* **Hover Effektlari:**
  * `transform hover:scale-[1.04] transition-all duration-300 ease-out`
  * Soya: `hover:shadow-[0_12px_30px_rgba(0,0,0,0.8),0_0_20px_rgba(229,9,20,0.25)]`
  * Z-index ko'tarilishi: `hover:z-20`
* **Kartochka Ustidagi Badgellar:**
  * *Yuqori chap burchak:* `[ ⭐ 8.5 ]` — qora shisha fonli sariq yulduzcha.
  * *Yuqori o'ng burchak:* `[ #1742 ]` — film kodi (Kinochilar muxlislari uchun!).
  * *Pastki burchak:* Sifat nishoni (`FHD`, `4K`) va O'zbekcha dublyaj belgisi (`🇺🇿 UZ`).
* **Pastki Matn Gradiyenti:**
  * `bg-gradient-to-t from-black via-black/75 to-transparent p-3.5`
  * Filmning o'zbekcha nomi (`line-clamp-2 text-sm sm:text-base font-semibold text-white group-hover:text-primary-red transition-colors`).
  * Chiqarilgan yili va janri (`text-xs text-neutral-400 mt-0.5`).

---

## 7. Franshizalar Xronologiya Zanjiri (Franchise Timeline)

Allplay va Kinochilar ning eng yoqimli jihati — agar kino bir necha qismdan iborat bo'lsa (*Masalan: Garri Potter 1-8, Jon Uik 1-4, Forsaj 1-10*), sahifada quyidagi gorizontal vaqt zanjiri hosil bo'ladi:

```
[ 1-qism (2014) ] ─── [ 2-qism (2017) ] ─── [ 🟢 Hozirgi qism: 3 (2019) ] ─── [ 4-qism (2023) ]
```

* Har bir qism bosilganda darhol o'sha qismning sahifasi, treyleri va uning Telegram boti kodi ochiladi.
* Tomoshabin qismlar orasida adashib yurmaydi!

---

## 8. Studiyalar va Striming Platformalari Gridi

* **Format:** Gorizontal 16:9 nisbatdagi zamonaviy brend kartochkalari.
* **Tarkibi:**
  * Netflix, HBO, Disney+, Warner Bros, Marvel Studios, A24, Apple TV+, Amazon Prime, Sony Pictures, Paramount.
* **Kartochka Ko'rinishi:**
  * Qora yaltiroq fon (`bg-[#121316]`), markazida studiyaning rasmiy oq vektori (SVG logotipi).
  * Pastida: *"184 ta film va serial"*.
  * Bosilganda faqat o'sha studiya chiqargan kontentlar chiqadi.

---

## 9. Mavzular (Themes & Tropes) Moduli

Foydalanuvchilar kayfiyatiga ko'ra film tanlashi uchun tematik piktogrammali to'plamlar:
* ⏳ **Vaqt sayohati** (Interstellar, Tenet, Dark...)
* 🗡️ **Qasos yo'li** (Jon Uik, Qasoskor, Gladiator...)
* 🧟 **Zombi apokalipsis** (Pusanga poyezd, Men afsonaman...)
* 💰 **Bank o'g'irligi & Heist** (Qog'oz bino, Oushenning 11 do'sti...)
* 🤖 **Sun'iy intellekt** (Matritsa, Terminator, Eks Maxina...)
* 🌌 **Kosmos sirlari** (Marslik, Gravitatsiya, Yulduzlar jangi...)

---

## 10. Film va Serial Tafsilotlari Sahifasi (Detail View)

* **Hero Qismi:** Keng formatli fon kadri va chap tomonda `rounded-2xl` poster.
* **Metama'lumotlar bloki:**
  * O'zbekcha Nomi + Original Nomi (inglizcha/ruscha).
  * Chiqqan yili, davomiyligi, mamlakati, yosh chegarasi (`18+` bo'lsa qizil ogohlantirish).
  * **Ijodkorlar Bloki:** Rejissyor va Bosh rollardagi aktyorlarning oltin nurli doiraviy avatarlari karuseli!
* **Syujet Tafsifi:** O'qilishi oson, chiroyli qator oralig'i (`leading-relaxed text-neutral-300`).

---

## 11. YouTube Treyler Modali & Telegram Bosh CTA

Saytimizda ichki video pleyer bo'lmagani sababli, foydalanuvchi media tajribasini boyitish:
1. **Asosiy Qizil Tugma:** `[ 🔴 TELEGRAM ORQALI TOMOSHA QILISH ]`
   * Bosilganda: `t.me/kinochi_uz_bot?start=CODE` orqali to'g'ridan-to'g'ri Telegram ochiladi.
   * Veb sahifada esa shisha modal chiqadi: *"Film Telegram botingizda ochildi! Kod: #1428"*.
2. **Treyler Tugmasi:** `[ ▶️ TREYLER (YouTube) ]`
   * Bosilganda sahifa ustida qora shisha modal (`bg-black/90 backdrop-blur-2xl`) ochilib, 16:9 YouTube rasmiy treyeri ishga tushadi.
   * **Natija:** Serverga 0 bayt yuklama, foydalanuvchiga esa to'liq tomosha zavqi!

---

## 12. Seriallar: Mavsumlar va Qismlar Moduli

Seriallar sahifasida iTV va Allplay kabi qulay boshqaruv:
* **Mavsumlar Tablari:** `[ 1-Mavsum ]  [ 2-Mavsum ]  [ 3-Mavsum ]` (faol mavsum qizil yonadi).
* **Qismlar Gridi (Episode Cards):**
  * Har bir qism uchun gorizontal karta: 16:9 skrinshot + Qism raqami + Davomiyligi + Nomi (*"1-qism: Boshlanish"*).
  * Tugma: `[ ✈️ Telegramda ochish ]` (aynan shu qismning botdagi deep-link havolasi).

---

## 13. Allplay Uslubidagi Jonli Filtr Paneli

Katalog sahifasida barcha parametrlarni bitta sahifada boshqarish:
* **Dropdownlar:**
  * *Toifa:* Barchasi / Filmlar / Seriallar / Multfilmlar / Premyeralar
  * *Janr:* Barcha janrlar / Jangari / Komediya / Drama / Triller / Qorquv / Fantastika...
  * *Yil:* 2025-2026 / 2024 / 2023 / 2020-2022 / Arxiv
  * *Mamlakat:* AQSH / Turkiya / Janubiy Koreya / O'zbekiston / Fransiya...
  * *Ovoz:* O'zbekcha dublyaj / Ruscha / Asl ovoz
  * *Saralash:* Mashhurlik / Yangi qo'shilganlar / IMDb reytingi / Yili bo'yicha

---

## 14. Mobil Ekran Moslashuvi & Bottom Navigation Bar

Smartfon foydalanuvchilari uchun xuddi qimmatbaho mobil ilovaday ishlash:
* `fixed bottom-0 left-0 right-0 z-50 bg-[#09090B]/95 backdrop-blur-xl border-t border-white/10 md:hidden`
* **5 Asosiy Bo'lim:**
  1. `[ 🏠 Bosh sahifa ]`
  2. `[ 🎬 Filmlar ]`
  3. `[ 📺 Seriallar ]`
  4. `[ 📚 Kolleksiyalar ]` (Taksonomiya va rejissyorlar)
  5. `[ 🔍 Qidiruv ]`

---
*Ushbu hujjat loyihaning barcha frontend komponentlari (Next.js 14 + Tailwind CSS) uchun rasmiy master spetsifikatsiya hisoblanadi.*
