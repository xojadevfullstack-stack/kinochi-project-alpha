# 🚀 MASTER ROADMAP: MEDIAPLUS (v5.0 - FINAL OPERATIONAL BLUEPRINT)
## Barcha 7 Blok Bo'yicha Yakuniy Tasdiqlangan Texnik va Amaliy Spetsifikatsiya

> **Loyiha:** **MediaPlus** (Vercel: `kinochi-project-alpha.vercel.app` -> Kelajakda shaxsiy domen)  
> **Telegram Bot:** Hozirda `@kinochi_mvp_bot` -> Kelajakda `@Mediaplusofficialbot`  
> **Asosiy Konsept:** 100% Bepul, obuna va to'lovlarsiz, 1xBet reklamalarisiz, YouTube treylerli va Telegram bot orqali video yetkazuvchi premium kino portali.

---

## 📑 1. TASDIQLANGAN PARAMETRLAR JADVALI

| Blok | Parametr | Yakuniy Tanlangan Yechim |
| :--- | :--- | :--- |
| **1. Brending** | Nomi & Shior | **MediaPlus** — *"Obunasiz. Reklamasiz. Mutlaqo bepul."* |
| | Bot Username | Hozir: `@kinochi_mvp_bot` ➔ Kelajakda: `@Mediaplusofficialbot` |
| | Xosting & Domen | Hozir Vercel keshida (0$ xarajat), kelajakda shaxsiy `.uz` domen |
| **2. Bosh Sahifa** | Hero Banner | **Gibrid:** Admin belgilasa "Tanlangan kino", belgilanmasa avtomatik Trend/Premyera |
| | Hero Media | **Netflix Uslubi:** O'zi avtomatik aylanuvchi video/kadr + Treyler tugmasi |
| | Karusellar Ketma-ketligi | 1. Davom ettirish ➔ 2. Trend (Top-10) ➔ 3. Premyera ➔ 4. Dublyaj ➔ 5. Serial ➔ 6. Franshiza ➔ 7. Anime ➔ 8. Top-250 ➔ 9. Rejissyorlar |
| **3. Film Sahifasi** | Tomosha Oqimi | Tugma bosiladi ➔ Botda kino ochiladi ➔ Sifat tanlanadi (`480p`, `720p`, `1080p`) |
| | Seriallar Qismlari | Saytda hohlagan fasl (mavsum) va qismni tanlash ➔ Har bir qismning alohida bot havolasi |
| | Ulashish (Share) | **YouTube/Instagram Standarti:** Katta posterli OpenGraph Preview + Sayt havolasi + Bot havolasi |
| **4. Telegram Bot** | Obuna (OP) | Tizim kodi tayyor, lekin startda **0 ta majburiy obuna** (maksimal tez o'sish uchun) |
| | Video Formati | To'g'ridan-to'g'ri bot chatiga video/fayl sifatida sifatlar bilan yuborish |
| | Qidiruv | Ham `#CODE` orqali, ham nom bo'yicha, ham `@bot nom` inline qidiruv |
| | WebApp | Saytni Telegram ichida to'liq ochuvchi **Telegram Mini App** tugmasi |
| **5. Kontent & Baza** | Kiritish Usuli | **Gibrid:** Avtomat qoidalar (Admission Gate) + Admin paneldan tasdiqlash |
| | Janrlar Balansi | Barchasi teng huquqli: Gollivud, Turk seriallari, Koreys doramalari, O'zbek, Anime |
| | 18+ Kontent | Mavjud, lekin alohida qizil nishon va yoshni tasdiqlash modali bilan |
| **6. Foydalanuvchi** | Buyurtma & Shikoyat | "Kino topilmadi? (Buyurtma)" va "Xatolik haqida xabar berish" modallari |
| | Baholar & Izohlar | 1-10 ballik yulduzcha baholash va izohlar tizimi |
| | Eslatmalar (Push) | Serialning yangi qismi chiqqanda botdan avtomatik xabarnoma |
| **7. Monetizatsiya** | Daromad Modeli | **Gibrid:** Telegram kanallar reklamasi + Saytda toza mahalliy brendlar |

---

## 2. Sayt va Botning Birgalikda Ishlash Oqimi (Architecture Flow)

```
┌────────────────────────────────────────────────────────────────────────┐
│                        MEDIAPLUS VEB-SAYTI                             │
│                                                                        │
│  🎬 Netflix/iTV Uslubidagi Hero Banner (Avtoplay fon videosi)         │
│  🔍 Jonli Qidiruv (Nom, Janr, Rejissyor yoki #1428 kodi bilan)         │
│  📑 Allplay Jonli Filtrlar & Franshizalar Xronologiya Zanjiri          │
│  🍿 Rasmiy YouTube Treyler Modali (Sayt ichida bepul ochiladi)         │
│  📺 Seriallar: 1-Mavsum, 2-Mavsum... Har bir qism tanlash imkoniyati   │
│                                                                        │
│         [ 🔴 TELEGRAM ORQALI TOMOSHA QILISH (KOD: #1428) ]             │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ (Bitta bosish bilan)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   TELEGRAM BOT (@kinochi_mvp_bot)                      │
│                                                                        │
│  1. Start bosiladi: /start 1428                                        │
│  2. Bot film kartochkasi va sifat tugmalarini chiqaradi:               │
│     [ 📥 480p Mobil (350 MB) ]                                         │
│     [ 📥 720p HD (850 MB) ]                                            │
│     [ 📥 1080p FHD (1.8 GB) ]                                          │
│  3. Foydalanuvchi sifatni bosadi -> Video to'g'ridan-to'g'ri yuboriladi│
│  4. Yangi qismlar chiqqanda: "15-qism yuklandi!" deb xabar yuboradi   │
│  5. Mini App: Saytni Telegram ichida ochish imkoniyati                 │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Amaliy Ishga Tushirish Bosqichlari (Sprint Tasks)

### 📌 1-Sprint: Frontend Polishing & Bosh Sahifa (3-5 kun)
- [ ] Bosh sahifadagi Hero bannerni ovozsiz avtoplay kadri bilan yangilash.
- [ ] Karusellar ketma-ketligini psixologik qiziqish tartibida to'g'rilash:
  *Davom ettirish ➔ Trend ➔ Premyeralar ➔ O'zbekcha dublyaj ➔ Seriallar ➔ Franshizalar ➔ Anime ➔ Top-250*.
- [ ] Seriallar sahifasida har bir fasl (mavsum) va qismlarni tanlash tablarini sozlash.
- [ ] Har bir kartochkaga `#CODE` va sifat badgelarini qo'yish.
- [ ] Ulashish (Share) tugmasiga tayyor viral Telegram matn generatorini ulash.

### 📌 2-Sprint: Telegram Bot & WebApp Sozlamalari (3-4 kun)
- [ ] Botda `/start {code}` buyrug'i kelganda sifat tugmalarini (`480p`, `720p`, `1080p`) chiqarish.
- [ ] Inline qidiruv rejimini mukammallashtirish (`@kinochi_mvp_bot kino_nomi`).
- [ ] Telegram WebApp menyu tugmasini ulash.
- [ ] "Kino buyurtma qilish" va "Xatolik haqida xabar berish" xabarlarini admin bot/kanalga yuborish.

### 📌 3-Sprint: Avtomatik Scraper & Qoidalar (Admission Gate) (3-4 kun)
- [ ] Uzmovi, Asilmedia va Anitoob scraperlariga avtomatik filtr qoidalarini kiritish:
  *Dublikat nomlarni tozalash, minimal rasm o'lchami, o'zbekcha audio mavjudligini tekshirish*.
- [ ] TMDB enricher orqali har bir yangi filmga avtomatik treyler havolasi, aktyorlar va rejissyorlarni yozish.
- [ ] Yangi seriya chiqqanda bot bazasidagi obunachilarga avtomatik bildirishnoma yuborish.

---
*Ushbu hujjat loyihaning barcha texnik va operatsion talablarini to'liq ifodalaydi.*
