# Sud-Texnik Ekspertizasi: 09_FRONTENDS.md
## Part 9: Veb-sayt va Admin Panel (Frontends) Tahlili

### 1. Veb-sayt (`website/`) Sahifalari va API Aloqalari
| Sahifa Yo'li (Route) | Fayl Joylashuvi | Chaqiriladigan API Endpointlari | Kesh Mantiqi (Caching) | 404 / Bo'sh / Pending Holatida Qanday Ishlaydi? |
| :--- | :--- | :--- | :--- | :--- |
| `/` (Bosh sahifa) | `website/app/page.tsx` | `GET /pages`, `GET /movies?limit=12`, `GET /series?limit=12` | `revalidate = 60` (ISR) | Pending media ro'yxatga kirmaydi; bo'sh bo'lsa skeleton/bo'sh blok |
| `/movie/[code]` | `website/app/movie/[code]/page.tsx` | `GET /movies/code/{code}` | `revalidate = 60` (ISR) | 404 bo'lsa Next.js `notFound()` (404 sahifasiga o'tadi) |
| `/series/[id]` | `website/app/series/[id]/page.tsx` | `GET /series/{id}` | `revalidate = 60` (ISR) | 404 bo'lsa Next.js `notFound()` |
| `/movies` | `website/app/movies/page.tsx` | `GET /movies?page=...&limit=24` | `fetch` kesh / dynamic | Faqat `published` filmlar ko'rinadi |
| `/series` | `website/app/series/page.tsx` | `GET /series?page=...&limit=24` | `fetch` kesh / dynamic | Faqat `published` seriallar ko'rinadi |
| `/catalog` | `website/app/catalog/page.tsx` | `GET /categories`, `GET /pages` | `revalidate = 300` | Janrlar va dinamik bo'limlar ro'yxati |
| `/category/[id]` | `website/app/category/[id]/page.tsx` | `GET /categories/{id}/movies`, `/series` | `revalidate = 60` | Janr bo'yicha saralangan media |
| `/collections/[slug]` | `website/app/collections/[slug]/page.tsx` | `GET /collections/{slug}` | `revalidate = 60` | Xronologik franshiza kartochkalari |
| `/p/[slug]` (Dinamik) | `website/app/p/[slug]/page.tsx` | `GET /pages/slug/{slug}` | `revalidate = 60` | Anime (`/p/anime`), Multfilm (`/p/multfilm`) sahifalari |

### 2. Admin Panel (`admin-panel/`) Sahifalari va Boshqaruv Qatlami
| Sahifa Yo'li | Fayl Joylashuvi | Autentifikatsiya | Chaqiriladigan API Endpointlari | Vazifasi |
| :--- | :--- | :--- | :--- | :--- |
| `/login` | `admin-panel/app/login/page.tsx` | Ochiq | `POST /auth/login` | Admin JWT token olish |
| `/movies` | `admin-panel/app/movies/page.tsx` | JWT Bearer | `GET /movies`, `POST /movies`, `PUT /movies/{id}` | Kinolar monitoringi, status o'zgartirish, tahrirlash |
| `/series` | `admin-panel/app/series/page.tsx` | JWT Bearer | `GET /series`, `POST /series` | Seriallar monitoringi |
| `/series/[id]` | `admin-panel/app/series/[seriesId]/page.tsx` | JWT Bearer | `GET /series/{id}`, `POST /seasons` | Serial fasllari va qismlari boshqaruvi |
| `/scraper` | `admin-panel/app/scraper/page.tsx` | JWT Bearer | `GET /scraper/status`, `POST /scraper/run` | Scraper navbati va holati monitoringi |
| `/reports` | `admin-panel/app/reports/page.tsx` | JWT Bearer | `GET /reports`, `PUT /reports/{id}` | Shikoyatlarni ko'rish va hal qilish |
| `/audit` | `admin-panel/app/audit/page.tsx` | JWT Bearer | `GET /audit/summary`, `POST /audit/fix` | Sifat auditi va dublikatlarni aniqlash |
| `/rejected` | `admin-panel/app/rejected/page.tsx` | JWT Bearer | `GET /rejected` | Gate tomonidan rad etilgan kontentlar |

### 3. Nima Uchun Sayt va Botda Noto'g'ri / Aralashib Ketgan Kontent Ko'rindi?
Part 5 va Part 6 da aniqlangan omillar tufayli frontendlarda quyidagi anomaliyalar yuzaga keldi:
1. **Anime va Multfilmlar Almashib Ketishi (`/p/anime`, `/p/multfilm`)**:
   - Ko'chirish skriptlari (`scripts/migrate_anime_series.py` va `scripts/categorize_and_sort_pages.py`) `page_movie` va `page_series` jadvallariga ID larni ommaviy bog'lagan.
   - Baza bo'shatilib, qayta yuklanganda ID lar o'zgargan, lekin skriptlar eski qotirilgan ID lar yoki noto'g'ri mapping bo'yicha bog'lagan. Natijada oddiy filmlar Anime sahifasida, seriallar esa multfilm sahifasida ko'rina boshlagan.
2. **Kinolar Serial Ko'rinishida, Seriallar Kino Ko'rinishida**:
   - Auto-index `/series/by-source` ni birinchi tekshirgani sababli, tartibsiz kanaldagi yuzlab kinolar serial deb qabul qilingan va saytning `/series/[id]` sahifasida 'Mavsum 1, 1-qism' bo'lib chiqqan.
   - Aksincha, ko'p qismli seriallar `movies` jadvaliga kiritilib, saytda `/movie/[code]` da faqat 1 ta qismi bilan yakka film sifatida namoyish etilgan.
3. **Kesh va CDNning Eski Ma'lumotlarni Saqlashi**:
   - Vercel Next.js `revalidate = 60` va Backend Redis `cache:movies:*` (300 soniya) tufayli, administrator bazadagi buzilgan qatorlarni o'chirganda ham, foydalanuvchilar brauzerida 1-5 daqiqa davomida eski, buzilgan ma'lumotlar keshdan ko'rinib turgan.
