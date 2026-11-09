# FILTER_CONTRACT.md — Filtr Zanjiri Kontrakti va Uzilishlar Audit Jadvali

Ushbu hujjat foydalanuvchi interfeysida (UI) ko'rinadigan har bir filtr parametrining to'liq zanjirini (UI → URL Query → Frontend API chaqiruvi → Backend Endpoint Query parametri → SQL/Repository sharti → DB ustuni) hamda zanjirdagi barcha uzilish va nuqsonlarni belgilaydi.

---

## 1. "Bo'lim", "Kategoriya", "Sahifa" va "Tur" terminlari tahlili

Loyiha arxitekturasida uchraydigan terminlar chalkashligi:

1. **"Bo'lim" (UI da `UnifiedFilterBar` dagi 2-dropdown):**
   - **Haqiqiy holati:** `UnifiedFilterBar` dagi "Bo'lim" dropdowniga `/categories` API orqali keladigan `categories` jadvali ma'lumotlari (`id`, `name`) uzatiladi.
   - **URL parametri:** `?category={id}`.
   - **Backend parametri:** `category_id: int`.
   - **DB bog'lanishi:** `movie_categories` ko'pdan-ko'pga (M2M) jadvali orqali `categories.id`.
   - **Muammo:** Baza arxitekturasida alohida `pages` jadvali ham bor bo'lib, ayrim joylarda "Sahifalar", ayrim joylarda "Bo'limlar" deb ataladi (`page_id`). Foydalanuvchi "Bo'lim" deganda ba'zan `page_id` ni, ba'zan `category_id` ni nazarda tutadi.

2. **"Tur" / "Turi" (UI da `UnifiedFilterBar` dagi 3-dropdown):**
   - **Haqiqiy holati:** Kontent formati va media turi: `movie` (kino), `series` (serial), `dorama` (dorama), `anime` (anime), `animation` (multfilm).
   - **URL parametri:** `?type={id}`.
   - **DB bog'lanishi:** Alohida `media_type` ustuni yo'q. Kinolar va Seriallar alohida jadvallarda (`movies` vs `series`). Anime, dorama va multfilmlar esa qisman `categories` yoki `pages` orqali ajratiladi.
   - **Farqi:** "Bo'lim/Kategoriya" — kontentning mavzusi/yo'nalishi (masalan, Komediya, Triller, Sarguzasht); "Tur" — kontentning format va kelib chiqish tabiati (To'liq metrajli film, Ko'p qismli serial, Anime, Dorama).

---

## 2. To'liq Filtr Zanjiri va Uzilishlar Jadvali (Contract Mapping)

| # | UI Parametri (Komponent) | URL Query Nomi | Frontend API Chaqiruvi | Backend Endpoint Query | SQL / Repository Sharti | DB Ustuni / Tipi | Uzilish / Xatolik (Gap) |
|---|---|---|---|---|---|---|---|
| **1** | **Janr** (`UnifiedFilterBar`) | `genre` (masalan: `action`, `comedy`, `scifi`) | `&genre=${genre}` | `genre: str | None` (`/movies`, `/series`) | `MovieModel.genres.ilike(f"%{clean_g}%")` | `movies.genres` (VARCHAR) | 🔴 **UZILISH:** UI dan inglizcha slug (`action`, `scifi`, `crime`) boradi, lekin DB da `genres` o'zbekcha yozilgan (`"Jangari"`, `"Fantastika"`). Natija: `action` tanlanganda DB dan film topilmaydi (0 ta natija)! |
| **2** | **Bo'lim** (`UnifiedFilterBar`) | `category` (masalan: `3`) | `&category_id=${category}` | `category_id: int | None` | `MovieModel.categories.any(id=category_id)` | `movie_categories.category_id` (INT) | 🟢 **MOS:** `category_id` to'g'ri bog'langan. Biroq `/category/[id]` sahifasida bu parametr URL da emas, route paramda (`params.id`). |
| **3** | **Turi** (`UnifiedFilterBar`) | `type` (masalan: `movie`, `series`, `dorama`, `anime`) | `/movies/page.tsx` da faqat `anime` va `cartoon` qisman ushlangan; `catalog/page.tsx` da endpoint o'zgaradi | Backendda yagona `type` parametri yo'q | `/movies` va `/series` alohida jadvallar | `movies` vs `series` | 🔴 **UZILISH:** `/movies` sahifasida foydalanuvchi "Seriallar" yoki "Doramalar" tanlasa, frontend baribir `/movies` ga so'rov yuboradi. Natija o'zgarmaydi. Magic ID lar (`category_id=40`, `category_id=2`) ishlatilgan. |
| **4** | **Yil** (`UnifiedFilterBar`) | `year` (masalan: `2024`) | `&year=${year}` | `year: int | None` | `MovieModel.release_year == year` | `movies.release_year` (INT) | 🟢 **MOS (Kinolar uchun):** Kinolarda to'g'ri ishlaydi. Biroq `/series` da `year` parametri SeriesRepository ga uzatiladi, lekin `CatalogGrid` paginationda `year` yo'qolib ketadi! |
| **5** | **Reyting / Saralash** (`UnifiedFilterBar`) | `sort` (`rating`, `latest`, `all`) | `/movies/page.tsx` va `series/page.tsx` da API ga **UMUMAN UZATILMAYDI** | `sort` parametri `/movies` va `/series` endpointlarida **MAVJUD EMAS** | Repository da `order_by(MovieModel.id.asc())` qotirilgan | `movies.imdb_rating`, `movies.id` | 🔴 **UZILISH (Kritik):** Foydalanuvchi "Reyting bo'yicha saralash" ni tanlasa ham, API ga `sort` bormaydi, backendda `sort` qabul qilinmaydi va DB har doim `id.asc()` (eng eski birinchi) tartibida qaytaradi! |
| **6** | **Pagination (Yana yuklash)** (`CatalogGrid`) | `skip`, `limit` | `/movies?skip=36&limit=36` | `skip: int`, `limit: int` | `offset(skip).limit(limit)` | - | 🔴 **UZILISH:** `CatalogGrid.tsx` da `type === "series"` bo'lganda `genre`, `year`, `search` parametrlari `loadMore` ga qo'shilmagan! 2-sahifadan boshlab filtrlar o'chib ketadi! |
| **7** | **Qidiruv filtri** (`/search`) | `q` (qidiruv so'zi) | `/movies/search?q=...` | `q: str` | `title.ilike(...)` | `movies.title` | 🔴 **UZILISH:** `/search` backend marshrutida `year`, `genre`, `category_id`, `sort` parametrlari umuman yo'q. Foydalanuvchi qidiruv natijalarini filtrlay olmaydi. |
| **8** | **To'plamlar soni** (`/collections`) | - | `GET /collections` | - | `select(func.count(CollectionItemModel.id))` | `collection_items` | 🔴 **UZILISH:** Kartadagi `items_count` pending/draft kinolarni ham hisoblaydi, lekin ichkariga kirganda faqat published kinolar chiqadi. Sonlar mos kelmaydi! |
| **9** | **Aktyor filmlari mavjudligi** (`/actors/[id]/movies`) | - | `GET /actors/{id}/movies` | - | `MovieModel.tmdb_id.in_(tmdb_ids)` | `movies.publish_status` | 🔴 **UZILISH:** Pending/draft holatdagi kinolar ham `is_available: True` deb belgilanadi, foydalanuvchi bossa 404 chiqadi. |
| **10** | **Rejissyorlar** (`/actors`) | - | `GET /actors` | `search: str | None` | - | - | ⚠️ **MAVJUD EMAS:** Alohida `/directors` yo'q, 4 ta rejissyor aktyorlar ichiga aralashtirib qo'yilgan. |

---

## 3. Komponentlar Inventarizatsiyasi

### 1. `UnifiedFilterBar`
- **Joylashuvi:** `website/components/catalog/UnifiedFilterBar.tsx`
- **Props:**
  - `categories?: CategoryItem[]`
  - `genres?: GenreItem[]`
  - `years?: number[]`
  - `types?: MediaTypeItem[]`
  - `selectedCategory?: string`
  - `selectedGenre?: string`
  - `selectedYear?: string`
  - `selectedType?: string`
  - `selectedSort?: string`
  - `baseUrl?: string`
  - `totalItems?: number`
- **Ichki holat:** `openDropdown` ("genre" | "category" | "type" | "year" | "sort" | null).
- **Harakat xulqi:** Har bir tanlovda `router.push(queryString)` chaqiradi.
- **Kamchiliklar:**
  - Janr sluglari (`action`) bilan DB qiymatlari (`Jangari`) translatsiya qilinmagan.
  - Turi tanlanganda sahifa marshruti o'zgarmaydi (masalan, `/movies` dan `/series` ga).
  - Saralash qiymati backendga bormaydi.

### 2. `CategoryFilter` (Eski komponent)
- **Joylashuvi:** `website/components/CategoryFilter.tsx`
- **Ishlatilgan joyi:** `website/app/p/[slug]/page.tsx`
- **Props:** `categories: Category[]`, `currentCategory?: string`, `baseUrl: string`.
- **Kamchiliklar:** Yil, reyting, kontent turi yo'q, modal faqat janr/kategoriya qidiradi.

### 3. `CollectionsClientView` (To'plamlar Tablari)
- **Joylashuvi:** `website/components/CollectionsClientView.tsx`
- **Ichki holat:** `selectedCategory` ("all" | "theme" | "franchise" | "chronology"), `searchQuery`.
- **Kamchiliklar:** Faqat mijoz tomonida (client-side) filtrlaydi, backendga so'rov yubormaydi.

### 4. `CollectionTimelineView` (Xronologiya)
- **Joylashuvi:** `website/components/CollectionTimelineView.tsx`
- **Ichki holat:** `viewMode` ("list" | "map"), `sortMode` ("chronological" | "release").
- **Harakat xulqi:** Mijoz tomonida `sortedItems` orqali tartiblaydi.

### 5. `SearchClientView` (Qidiruv)
- **Joylashuvi:** `website/components/SearchClientView.tsx`
- **Ichki holat:** `query`, `results`, `externalResults`, `isLoading`.
- **Kamchiliklar:** Qidiruv natijalarini saralash yoki filtrlash paneli mavjud emas.
