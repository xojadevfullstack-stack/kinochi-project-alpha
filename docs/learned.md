## Layered Toggleable Minimalism (Non-Destructive CSS Class Override)
- Dizayndagi vizual shovqinni kamaytirishda HTML elementlarini o'chirib tashlash o'rniga `body.<variant>` klassi orqali ustma-ust CSS qatlamini (`#apple-pure-minimal`) ulash orqaga qaytishni (rollback) va A/B taqqoslashni 1 klikda xavfsiz bajarish imkonini beradi.
- Analogy: Xonadagi ortiqcha buyumlarni sindirib tashlamasdan alohida parda ortiga yashirish kabi — yoqmasa bir soniyada pardani ochib avvalgi holatga qaytarish mumkin.

## Seamless Layer Hierarchy & Scrim-Protected Light Mode Imagery
- Hero va sahnadagi fon rasmlari yorug' rejimda mutlaqo o'chirilmasdan (`display: none` o'rniga), yengil oq/kulrang scrim (`linear-gradient`) bilan himoyalangan holda 38% shaffoflikda ko'rsatilishi kerak; subheader va breadcrumbs kabi oraliq qatlamlar esa sahifa foni bilan bir xil (`bg-transparent border-none`) bo'lib, gorizontal chiziqli chalg'itishlarni yo'qotishi shart.
- Analogy: Vitrina oynasi ortidagi eksponat ustiga tushayotgan quyosh nurini yengil pardoz bilan yumshatish kabi; eksponatni yashirib qo'yish shart emas, yorug'likni to'g'ri sindirish kifoya.

## DOMContentLoaded Immediate Init vs Blocking Window Onload
- Veb-ilovalarda ma'lumotlar ro'yxatini chizish (render) va mavzuni boshlashni `window.onload` ga bog'lab qo'yish tashqi rasm yoki shriftlar kechikkanida butun sahifani bo'sh (blank) qoldiradi; bu amallar `DOMContentLoaded` va xavfsiz darhol chaqiruv bilan amalga oshirilishi shart.
- Analogy: Restoranga kirgan mehmon stoliga taomlar menyusini darhol taqdim etish kabi; restoranning tashqi devoridagi barcha lampochkalar to'liq yonib bo'lishini kutib mehmonni och qoldirmaslik kerak.

## Footer Action Pill Contrast & Cinematic Red Hover Consistency
- Sayt footeridagi ijtimoiy va tashqi havola tugmalari (Telegram Bot, Kanal) yorug' rejimda oq fon ustida erib ketmasligi uchun standart slate fon (`#F1F5F9`) va chegara (`#CBD5E1`) berilishi, hover paytida esa yagona Primary Red (`#E50914`) rangiga o'tishi shart.
- Analogy: Oq dasturxon ustiga qo'yilgan kumushrang qoshiq va sanchqilarning chetlari va shakli yaqqol ajralib turishi kabi; oq qog'ozga oq plastmassa qo'yilsa ko'z ilg'amaydi.

## HTML5 Head Integrity & Mobile Touch Hover Immunity
- HTML5 da `<head>` ichiga `<div>` tegi tushib qolsa brauzer avtomatik `<head>` ni yopib <body> ochadi va barcha uslublarni buzadi; shuningdek, mobilda `:hover` stillari bosilgach qotib qolmasligi uchun `@media (hover: hover)` bilan o'rash shart.
- Analogy: Uyning fundamenti ustiga xato qilib xona mebelini joylashtirib qo'yilsa uyning barcha devorlari egri qurilishi kabi; xona mebellari faqat fundament to'liq tugab xona (body) ochilgandagina joylashtirilishi shart.

## Universal Icon System Parity & Contrast Immunity
- Standart header va navigatsiya elementlari (orqaga, bildirishnoma, rejim, qidiruv) bir xil oyna effekti va border parametrlariga ega bo'lishi hamda to'q fonli bannerlar ichidagi tugmalarning rejim almashganda qorayib ketmasligi uchun "contrast immunity" qoidasi zarur.
- Analogy: Mashinaning barcha asboblari va tugmalari bitta estetikada tayyorlangani kabi; bitta tugma boshqacha rangli qora plastmassadan bo'lsa darhol ko'zga xunuk tashlanadi.


## Per-Platform Publisher Isolation (Adapter Pattern)
- Barcha ijtimoiy tarmoqlar (`Telegram`, `Instagram`, `Facebook`, `YouTube`, `TikTok`) bitta `BaseSocialPublisher` shartnomasini (`PublishResult`) bajaradi; bir tarmoq tokeni tugasa yoki xato bersa, qolgan tarmoqlarga post yuborish to'xtamaydi.
- Analogy: 5 ta turli pochta xizmatiga bitta standart konvert shaklida jo'natma berish — agar bitta pochta bo'limi yopiq bo'lsa ham, qolgan 4 tasi xatlarni manzilga yetkazaveradi.

## Concurrent Dispatch with Per-Platform Error Containment
- `asyncio.gather(..., return_exceptions=True)` yordamida bir videoni 5 ta tashqi API ga parallel yuborish umumiy kutish vaqtini qisqartiradi va bitta tarmoqning exception/timeout xatosini boshqalarga tarqatmaydi.
- Analogy: 5 ta turli aviakompaniyaga bir vaqtda chipta so'rovi yuborish — bitta aviakompaniya sayti ishlamay tursa ham qolgan 4 tasi javob qaytaradi.

## Portable JSON Column & Singleton Settings Pattern
- ORM modellarida Postgres-specific `JSONB` o'rniga SQLAlchemy `JSON` turidan foydalanish va Alembic migratsiyasida `JSONB` saqlab qolish bir vaqtda ham `SQLite` tezkor testlarida, ham `PostgreSQL` production'da xatosiz ishlashni ta'minlaydi.
- Analogy: Uy ichidagi rozetkalarni universal standartda yasash — elektr stansiyasi generator bo'ladimi yoki quyosh batareyasi bo'ladimi, barcha jihozlar ulanaveradi.

## Dual-Mode Control Surface (Autonomous vs Human-in-the-Loop)
- Bitta UI boshqaruv panelida `SEMI_AUTO` (tasdiqlash va qayta kesish) va `FULL_AUTO` (jadval bo'yicha avtonom chiqarish) rejimlarini yagona state-machine ustida almashtirish operatori xatosiz nazoratni saqlagan holda avtomatlashtirish darajasini bosqichma-bosqich oshirish imkonini beradi.
- Analogy: Samolyotda uchishda "qo'lda boshqaruv" va "avtopilot" tugmasi bo'lishi — ob-havo murakkab bo'lganda uchuvchi ruxsat beradi, yo'l ochiq bo'lganda avtopilot o'zi uchiraveradi.

## Slot-Based Idempotent Scheduling (Daily Quota + Hour Deduplication)
- `FULL_AUTO` jadvalida kunlik limitni sanash va har bir soat slotida (`HH:00`) oxirgi post vaqtini solishtirish bitta soat ichida tasodifan ikki marta dublikat post chiqib ketishini (duplicate dispatch) oldini oladi.
- Analogy: Dori ichish jadvalida "soat 12:00 dozasi ichilgan" belgisini qo'yib qo'yish — soat 12:05 da hamshira kelib qayta dori berib yubormaydi.


## Savepoint Isolation & API Capability Fallback
- Asosiy Cycle 1 kino tranzaksiyasini buzmaslik uchun Cycle 2 navbatga qo'shish `db.begin_nested()` (savepoint) va feature-flag (`SMM_AUTOPILOT_ENABLED`) bilan izolyatsiyalanadi; TikTok Direct Post audit (`App Review`) o'tmagan holatda esa `inbox/video/init/` fallback orqali akkauntni Public qoldirib yuklash saqlanadi.
- Analogy: Asosiy poezd vagoniga qo'shimcha pochta vagonini xavfsiz qulf bilan ulash — agar pochta vagonida muammo chiqsa, asosiy yo'lovchi poezdi to'xtab qolmaydi; asosiy darvoza yopiq bo'lsa, pochta xizmat eshigidan qabul qilinadi.


## FFmpeg Downscaled Blur & Single-Thread Event-Loop Isolation
- 1080x1920 fonda to'liq o'lchamli `boxblur` (`732.4 MB` RAM) o'rniga fonni `270x480` da xiralashtirib `720x1280` ga cho'zish, `-threads 1` berish va `asyncio.to_thread` da yurgizish RAM sarfini 5 barobar kamaytiradi (`142.6 MB`) va FastAPI/Bot event loop'ini bloklamaydi.
- Analogy: Katta devoriy rasmning orqa fonini alohida kichik varaqda bo'yab kattalashtirib osish — ko'zga bir xil chiroyli ko'rinadi, lekin ustaxonaning butun joyini band qilib qo'ymaydi.

## Dual-Code Aliasing (Backward-Compatible Short Numeric Code)
- Eski harf-raqamli kodlarni (`PT3BQB`) o'zgartirmasdan alohida `short_code` (`1001+`) alias ustuni qo'shish va qidiruvda `code`/`short_code` ni raqamli `id` fallback'idan ustun qo'yish eski havolalarni sindirmasdan ijtimoiy tarmoq konversiyasini oshiradi.
- Analogy: Ko'chaga yangi qisqa pochta indeksi berilganda eski manzil xatlarini ham bir vaqtda qabul qilishni davom ettirish — eski xatlar yo'qolmaydi, yangilari esa 2 barobar tez yetib boradi.


## Self-Exclusion Duplicate Filtering & Non-Destructive Edit Merge
- Tahrirlash rejimida tashqi manbadan (TMDb) ma'lumot tortilganda dublikat tekshiruvi tahrirlanayotgan yozuvning o'zini (`editingId`) filtrlab tashlashi, shuningdek `fillEmptyOnly` opsiyasi bilan avval qo'lda kiritilgan maydonlarni tasodifan ustidan yozib yubormaslik kerak.
- Analogy: Uy hujjatini yangilayotganda arxiv xodimi "bu manzilda allaqachon uy bor ekan" deb o'zingizning uyingizni o'zingizga raqobatchi qilib ko'rsatmasligi, va ustidan bo'yoq tortganda yangi devor bo'lsa eskisi saqlanib qolishi kabi.


## Route-Keyed Context Override (Zero-Fetch Server-to-Layout Title Propagation)
- Next.js App Router'da `layout.tsx` ichida turgan umumiy client UI (`Breadcrumb`) dinamik Server Component sahifalardan (`movie/[code]`, `series/[id]`) ma'lumot olishi uchun qayta `fetch()` qilish o'rniga `pathname` ga bog'langan Context va unmount da tozalanadigan `<BreadcrumbTitle />` ishlatish tarmoq yukini nolga tushiradi va eski nom qolib ketishini (stale label) oldini oladi.
- Analogy: Binoning qabulxona taxtachasi (layout) har bir xona eshigidan kelgan tayyor ism yozilgan qog'ozchani ko'rsatib turishi — qabulxonachi har safar arxivga qaytib so'rov yubormaydi, mehmon xonadan chiqqanda esa yozuv darhol yig'ishtiriladi.


## Script-Aware Translation Fallback (Never Transliterate Source Prose)
- Tarjima API lari (`Gemini`, `Google Translate`) vaqtincha ishlamay qolganda ruscha ta'rifni `cyrillic_to_latin` bilan harfma-harf lotinga o'girib `is_translated=True` qaytarish o'qib bo'lmaydigan matn (`V budushem...`) yaratadi va mavjud yaxshi matnni buzadi; faqat o'zbek kirill harflari (`ў, қ, ғ, ҳ`) bor matn transliteratsiya qilinishi, aks holda esa `(original, False)` qaytarilib UI da mavjud matn himoyalanishi kerak.
- Analogy: Tarjimon kelmay qolganda ruscha kitobni o'zbek alifbosidagi harflar bilan ko'chirib "tarjima tayyor" deb bermaslik — buning o'rniga zaxira tarjimonni chaqirish yoki asl matn hali tarjima qilinmaganini ochiq aytish.

- Concept: **MP4 `stco/co64` Index-Bounded Sparse Windowing** — Katta videodan kichik qism kesishda `moov` mundarijasidan klipning ham bosh, ham oxirgi sekundlari joylashgan bayt chegarasini hisoblab oqimli yuklash (RAM tejash va VBR sahna uzilib qolmasligi uchun).
- Analogy: Qalin kitobdan bitta sahna olishda taxminan 25 varaq sanab kesmasdan, mundarijadan bobning aniq boshlanish va tugash betini ko'rib o'sha oraliqni to'liq olish.

## Idempotent Per-Platform Retry & In-Process Immediate Dispatch
- Concept: **Idempotent Retry + BackgroundTasks Fallback** — Qayta urinishda avval muvaffaqiyatli chiqqan (`published`) tarmoqlarni o'tkazib yuborish dublikat postlarni oldini oladi; `publish_now` bosilganda esa fon worker kutmasdan `BackgroundTasks` orqali darhol ishga tushirish tez reaksiya beradi.
- Analogy: 5 ta do'konga posilka yuborganda 2 tasi allaqachon qabul qilgan bo'lsa, qayta jo'natishda faqat yetib bormagan 3 tasiga yuborish va kuryerni kechki mashinani kutmasdan hoziroq yo'lga chiqarish.

## Stateless HMAC Signed Stream Token
- Concept: **Stateless HMAC-SHA256 Token** — Render backend video baytlarini tashimasdan va VPS'ga Supabase bazasini ochmasdan, faqat `chat_id`, `message_id` va `exp` ni umumiy maxfiy kalit bilan imzolab beradi; stream server esa `hmac.compare_digest` bilan imzoni tekshirib to'g'ridan-to'g'ri MTProto'dan uzatadi.
- Analogy: Kassada maxsus muhr bosilgan va vaqti yozilgan kino chiptasi — eshikdagi nazoratchi markaziy bazaga qo'ng'iroq qilib tekshirmasdan, faqat muhr haqiqiyligi va chipta muddatini ko'rib zalga kiritadi.

## 1 MiB MTProto Chunk Slicing & Multi-Bot Failover
- Concept: **Chunk-to-Byte Range Mapping + Round-Robin Pool** — Pyrogram `stream_media` faqat 1 MiB bo'laklarda (`offset`/`limit`) o'qiydi, shuning uchun HTTP `Range: bytes=start-end` so'rovi kerakli 1 MiB bloklarga tarjima qilinib aniq baytgacha qirqiladi va `FloodWait` olgan bot vaqtincha chetlatilib keyingi botga uzatiladi.
- Analogy: Ombordan mahsulot faqat 1 tonnalik konteynerda kelsa ham xaridorga aniq 600 gramm tortib berish, bitta yuk tashuvchi navbatda ushlanib qolsa darhol keyingi bo'sh tashuvchini ishga solish.

## On-Demand Stream Signing + Codec Fallback
- Concept: **Client-Side Token Fetch (`no-store`) + HTML5 `<video>` `onError` Fallback** — ISR keshlangan Next.js sahifasi ichiga eskiradigan stream tokenni yozmasdan, tugma bosilganda yangi imzolangan URL olish va brauzer kodekni (`MKV`/`HEVC`) ocholmaganda Telegram bot havolasini ko'rsatish.
- Analogy: Mehmonxonada kalit kartani 1 kun oldin emas, mehmon eshik oldiga kelgan zahoti faollashtirib berish — agar eshik qulfi ishlamasa darhol qo'riqchi zaxira eshikni ochib beradi.

## Zero-Buffer Reverse Proxy Streaming
- Concept: **Unbuffered Reverse Proxy (`flush_interval -1`)** — Caddy/Nginx video baytlarini buferda ushlab qolmasdan har bir MTProto bo'lagini (`206 Partial Content`) darhol mijozga uzatishi shart, aks holda seeking kechikadi va proxy RAMi to'ladi.
- Analogy: Suvni avval katta hovuzga yig'ib keyin ochmasdan, nasosdan kelgan oqimni to'g'ridan-to'g'ri shlang orqali uzatish — jo'mrakni ochgan zahoti suv keladi.

## Dual-Bot Strangler Redirect (Deep-Link Payload Preservation)
- Concept: **Dual-Bot Strangler Pattern (`LEGACY_BOT_TOKEN` + `BOT_TOKEN`)** — Bot username almashtirilganda eski botni darhol o'chirish o'rniga alohida engil dispatcherda `?start=<payload>` ni saqlab yangi botga inline tugma bilan yo'naltirish eski SMM va veb havolalarning yo'qolishini oldini oladi.
- Analogy: Eski do'kon eshigini yopib tashlamasdan, kirgan xaridorni aynan qo'lidagi buyurtma cheki bilan yonidagi yangi do'kon peshtaxtasiga olib o'tadigan ko'rsatkich qo'yish.

## Hybrid View Tracking (Event Log + Materialized Counter + TTL Dedup)
- Concept: **Append-Only Event Log (`media_view_events`) + Counter (`view_count`) + Redis Dedup** — Ko'rishlarni vaqt kesimida ("Bugun/7 kun/30 kun") tahlil qilish uchun har bir hodisani manbasi (`bot`/`web`/`stream`) bilan alohida jadvalga yozib, tezkor saralash uchun umumiy hisoblagichni (`view_count`) oshirish va sahifa qayta yuklanishini (`F5`) Redis TTL kaliti bilan filtrlash.
- Analogy: Do'kon eshigidagi hisoblagich (jami kirganlar soni) bilan birga daftarga har bir mehmon qaysi soatda va qaysi eshikdan (Telegram yoki Sayt) kirganini yozib borish — bitta odam eshikni 5 marta ochib yopsa ham bir soat ichida 1 marta sanaladi.

## Zero-Query Discovery & Click-Through Search Attribution
- Concept: **Zero-Query Popular Feed + Click-Through Counter (`search_count`)** — Debounced autocomplete da har bir yozilayotgan chala harfni emas, faqat foydalanuvchi tanlab bosgan natijani 1 soatlik dedup bilan sanab, qidiruv bariga fokus bo'lishi bilanoq (`query=""`) eng ko'p qidirilganlarni chiqarish.
- Analogy: Kutubxonada odamlar hali kitob nomini aytib ulgurmasidan peshtaxta ustida eng ko'p so'ralayotgan 8 ta kitobni ko'zga ko'rinarli qilib qo'yish va faqat chindan olib o'qilgan kitoblarnigina hisobga yozish.

## Webhook Adapter Fallback for OAuth-Gated Platforms
- Concept: **Webhook Bridge Pattern (`MAKE_WEBHOOK_URL`)** — Shaxsiy Meta App SMS/App Review blokiga tushganda to'g'ridan-to'g'ri Graph API o'rniga tasdiqlangan partner platforma webhook'iga ochiq `video_url` va `caption` JSON uzatish barcha platforma avtopost shartnomasini (`PublishResult`) saqlab qolgan holda ishlaydi.
- Analogy: Pochta bo'limi o'z mashinangizni darvozadan kiritmay qo'yganda, posilkani akkreditatsiyadan o'tgan kuryer shoxobchasi orqali manzilga yetkazib berish.

## Runtime Public-Config Social Aggregation
- Concept: **Single-Source Public Config (`GET /api/v1/auth/public-config` + `buildSocialItems`)** — Barcha ijtimoiy tarmoq linklarini frontendda tarqoq qattiq yozish o'rniga backend `/public-config` va yagona sanitizatsiya funksiyasi orqali berib, faqat `https://` tasdiqlangan va bo'sh bo'lmagan tugmalarni render qilish 404/soxta linklarni oldini oladi.
- Analogy: Barcha filiallardagi e'lon taxtalariga manzillarni qo'lda yopishtirmasdan, bosh ofisdagi bitta rasmiy ro'yxatdan olib faqat ochiq turgan filiallarni ko'rsatish.

## Textless-First Poster Localization & Telegram File-ID Proxy
- Concept: **Textless-First + Vision/Inpaint Fallback + Immutable `file_id` Proxy (`/api/v1/posters/tg/{file_id}`)** — Tijoriy Image-to-Image AI lar mashhur aktyorlar yuzi/mualliflik huquqi sababli posterlarni bloklaganda, TMDb matnsiz posterini olib (yoki `cv2.inpaint` bilan tozalab) Pillow/TTF orqali o'zbekcha shrift chizish hamda Telegram'dagi eskiradigan `getFile` linki o'rniga proksi endpointdan doimiy URL berish.
- Analogy: Mehmonxonada 1 soatda yaroqsiz bo'ladigan vaqtinchalik qog'oz ruxsatnoma tarqatmasdan, qabulxonada doimiy raqam bo'yicha arxivdan rasmni olib beradigan darcha ochish.

## Single-Decode Low-RAM Rendering & CPU Priority Yield (`nice`)
- Concept: **Single-Pass `split=2` + `os.nice(15)` + Subprocess Timeout + Startup Grace Delay** — Bitta 512MB/0.1-vCPU konteynerda Uvicorn/Bot bilan yonma-yon FFmpeg yurganda `[0:v]` ni 2 marta ochish va cheksiz `subprocess.run` qo'yish serverni qotirib qo'yadi; 1 marta decode+downscale qilib bo'lish va Linux `nice(15)` bilan veb-serverga CPU ustuvorligini qoldirish konteynerni tirik saqlaydi.
- Analogy: Kichkina do'konda bitta sotuvchi ham kassa qilsa, ham omborda yuk tashisa — og'ir yuk ko'targanda kassadagi mijozlar kutib qolmasligi uchun yukni kichik qutilarga bo'lib, mijoz kelgan zahoti kassaga navbat berish.

## Private-Only Bot Dispatch (`F.chat.type == "private"`)
- Concept: **Chat-Scope Filter Isolation** — Yo'naltiruvchi bot barcha xabarlarni filtrsiz ushlasa, o'zi a'zo bo'lgan Storage superguruhidagi har bir mavzu/video ostiga ham javob yuborib axlatga to'ldiradi; faqat shaxsiy chat (`private`) bilan cheklash superguruhlarni toza saqlaydi.
- Analogy: Mehmonxonaning kirish eshigida turadigan yo'lko'rsatuvchini xodimlar ishlaydigan omborxona ichiga qo'yib qo'ysangiz, har safar quti olib kirilganda "Yangi manzilga ko'chdik!" deb xalaqit beraveradi.

## Style-Preserving Poster Edit + Vision OCR Gate
- Concept: **Exact Source First (`manual_poster_url`) + Cloudflare `flux-2-klein` (`4b`/`9b`) + OCR Verification & Pillow Fallback** — `4b` model (~`26–43` neyron/rasm) birinchi bo'lib kunlik 10,000 bepul neyron ichida ~`150–230` tagacha posterni o'giradi, faqat OCR imlo xatosida `9b` (~`1,545` neyron) ga chiqadi.
- Analogy: Kundalik muqovalarni arzon va tez bosadigan stanokda chiqarib, lupa (`OCR`) xato topsagina qimmat stanokka uzatish.

## Anti-Calque Title Translation & Clean Fallback Cache
- Concept: **Natural Cinema Prompt + Non-Poisoning Machine Fallback (`is_translated=False`)** — Tarjima modeliga inglizcha `en_title` va kalka taqiqini berish hamda Google Translate zaxira javobini `is_translated=False` deb belgilab `30` kunlik keshga yozmaslik `"Qochgan Yer"` kabi robot tarjimalarning donor o'zbekcha nomlarni buzishini to'xtatadi.
- Analogy: Vaqtincha tilmoch adashib so'zma-so'z tarjima qilsa, uni lug'atga 1 oyga muhrlab qo'ymaslik — aksincha, kutubxonadagi tayyor to'g'ri o'zbekcha nomni asrab qolish.

## Audited Partner Bridge for TikTok Direct Post (`Zernio`)
- Concept: **Presigned CDN Upload + Account/Profile Auto-Resolution (`/v1/accounts`)** — Auditdan o'tmagan TikTok ilovasi videoni `inbox` ga tashlasa, auditdan o'tgan partner API (`Zernio`) ga `/v1/media/presign` bilan `.mp4` yuklab, foydalanuvchi `profileId` bergan bo'lsa ham `platform == "tiktok"` ning haqiqiy `_id` sini topib `Direct Post` yuborish qo'lda tasdiqlashni yo'qotadi.
- Analogy: Yangi kuryer ombor darvozasidan kiritilmaganda, akkreditatsiyadan o'tgan bosh kuryer xizmatiga posilkani topshirib, uning bo'lim ID sini ro'yxatdan o'zi topib oladigan qilib qo'yish.

## Quota-Safe FULL_AUTO Catalog Auto-Pick (`UTC+5`)
- Concept: **Buffered Single-Clip Queue + Daily/Monthly Free-Tier Ceiling (`TASHKENT_TZ`)** — `auto_pick_from_catalog` bilan SMM navbati bo'shaganda faqat `1` ta klip kesib tayyorlab qo'yish hamda jadval soatlarini `UTC+5` da kuniga `3` ta / oyiga `90` ta (`SMM_MONTHLY_LIMIT`) ga cheklash `512MB` RAM crashini va `Make.com 1,000 op/oy` limiti oshib ketishini to'xtatadi.
- Analogy: Oshxonada `1,000` ta likopcha bo'lsa, kuniga `3` porsiyadan ortiq pishirmaslik va bitta porsiya stolga chiqmaguncha ikkinchisini qozonga solmaslik.

## Hybrid Forward-Only Worker (`copy_only=True`)
- Concept: **Server-Side Forward Capability Splitting** — Render'ning `512 MB` RAM konteynerida faqat `send_file` orqali ko'chiriladigan manbalarni (`uzmovi`, `asilmedia`) `copy_only=True` va kunlik limit (`4/kun`) bilan yurgizib, `fast_download` talab qiladigan `kinochilar` manbasini lokal kompyuterga qoldirish serverni RAM portlashidan saqlaydi.
- Analogy: Do'kondagi kichik kuryer faqat tayyor pochta qutilarini manzilga uzatib turadi, og'ir yuk mashinasini esa faqat ombor (noutbuk) yoqilganda ishlatiladi.

## Python 3.12 Eager Annotations vs Python 3.14 PEP 649
- Concept: **Pre-Push Undefined Name Audit (`ruff --select F821` + `get_type_hints`)** — Lokal `Python 3.14` (`PEP 649`) da kechiktirilgan tip annotatsiyalari (`-> Tuple[...]`) import paytida xato bermasa ham, Docker `Python 3.12` konteynerida darhol `NameError` chiqaradi; har bir push oldidan `F821` tekshiruvi buni oldindan tutadi.
- Analogy: Yangi mashina dvigateli bo'sh qo'yilgan murvatni sezmay haydab ketaverishi, eski dvigatel esa kalit burilishi bilanoq o'chib qolishi kabi — yo'lga chiqmasdan barcha murvatlarni asbob (`ruff F821`) bilan tekshirish shart.

## Supabase Session Pooler Ceiling (`<= 15` Clients During Rolling Deploy)
- Concept: **Rolling-Overlap Connection Budgeting (`pool_size<=5`) + Shared Session Factory** — Supabase Session Pooler ko'pi bilan `15` ta ulanish ko'taradi; Render yangilanayotganda eski va yangi konteyner bir necha soniya parallel turganda `pool_size=10` + alohida `NullPool` worker `EMAXCONNSESSION` beradi — `pool_size/max_overflow <= 5` va umumiy `async_session_factory` ni qayta ishlatish buni yo'qotadi.
- Analogy: `15` o'rinli avtobusga bir bekatda ham eski, ham yangi guruh kirganda janjal chiqmasligi uchun har bir guruhga ko'pi bilan `5` tadan joy ajratib berish.

## Bot-Scoped `file_id` Legacy Proxy Fallback
- Concept: **Token-Tagged Cache Key + Multi-Bot `getFile` Fallback** — Telegram `file_id` har bir bot tokeniga bog'langan bo'ladi; yangi `BOT_TOKEN` ga ko'chganda eski `LEGACY_BOT_TOKEN` yuklagan `/posters/tg/{file_id}` rasmlari `404` qaytarmasligi uchun kesh kalitini token xeshi bilan ajratib `LEGACY_BOT_TOKEN` zaxirasini ulash shart.
- Analogy: Eski ombor kaliti (`LEGACY_BOT_TOKEN`) bilan qulflangan hujjatlarni yangi omborxona mudiri ocha olmaganda, zaxira eski kalitni ham bog'lamda saqlab qo'yish.

## Motif-Preserving Structured Poster Prompting
- Concept: **Semantic Style & Motif Decomposition (`title_motifs`, `line_layout`, `badges_to_remove`)** — Arzon image-edit modellariga (`flux-2-klein-4b`) umumiy `"barcha eski sarlavhani o'chir"` buyrug'i o'rniga Vision tahlili orqali dekorativ emblema (`O` ichidagi qilich, tarozi, tally chiziqchalar), qator bo'linishi va ortiqcha reyting/kanal badjlarini alohida uzatish minimal token bilan logotip stilini saqlashni oshiradi.
- Analogy: Rassomga *"eski afishani butunlay o'chirib qayta yoz"* deyish o'rniga, *"tarozi rasmi va shrift rangini o'z holicha qoldirib, faqat harflarni o'zbekchasiga almashtir, burchakdagi muhrni esa olib tashla"* deb aniq reja berish.

## SRT-Guided Viral Scene Discovery & Non-Short-Circuiting Vision Ranking
- Concept: **Open-Source Subtitle Timecode Lookup (`0 MB` Video) + Targeted Sparse Windowing** — Butun filmni yoki tasodifiy `35%` nuqtasini ko'chirish o'rniga TMDb `imdb_id` orqali Stremio OpenSubtitles `.srt` (`~60 KB` matn) ni yuklab, Gemini Flash-Lite dan eng kuchli kulminatsiya/burilish taymkodi (`peak_sec`, `visual_cue`) ni olish, faqat o'sha nuqtadan `~35 MB` sparse bo'lak tushirib Vision'da barcha nomzodlarni `excitement_score` va `cue_match` bo'yicha o'zaro solishtirish Render `512MB` RAM ni saqlab qiziq sahnalarni aniq kesadi.
- Analogy: Qalin kitobning o'rtasidan tasodifan bitta sahifa yirtib o'qish o'rniga, avval mundarija va qisqa iqtiboslar ro'yxatidan eng keskin burilish bobini topib, faqat o'sha bobni ochib o'qish.

## Per-File Async Lock & `HEAD` Support for Webhook Media Proxies
- Concept: **Request Coalescing Lock + `uuid4` Temp Atomic Swap (`GET`/`HEAD`)** — Bir nechta tashqi webhook (`Instagram` va `Facebook` Make.com ssenariylari) bitta efemer media endpointini bir soniyada chaqirganda `os.getpid()` bir xil temp faylga yozib poyga (`race condition`) va `HEAD 405` yaratmasligi uchun har bir fayl yo'li bo'yicha `asyncio.Lock`, `uuid4` vaqtinchalik fayl va `HEAD 200` sarlavhasi majburiydir.
- Analogy: Ikki kuryer bir vaqtda ombordan bitta posilkani so'raganda ikkisi ham bitta qutini tortishib yirtib qo'ymasligi uchun avval birinchisi olib chiqib qo'yishi, ikkinchisi esa tayyor turganini 0 soniyada olishi kabi.

## Donor Bot Flood-Safe Requeue & Failure-Streak Backoff
- Concept: **Semantic Flood Recovery + Exponential/Streak Backoff** — Donor Telegram boti (`@asilmediabot`, `@UzmovieTV_Bot`) `BotFloodWaitError` berib `30 daqiqa` kutishni talab qilganda har `60s` da keyingi navbatni olib hammasini `failed` qilib tashlash o'rniga, itemni `queued` ga qaytarish va aynan kutish vaqtigacha (`1800s+`) uyquga ketish navbatni saqlab qoladi.
- Analogy: Do'kon eshigida "30 daqiqa tanaffus" yozuvi turganda har 1 daqiqada navbatdagi yuk mashinasini haydab kelib qaytarib yuborish o'rniga, tanaffus tugashini kutib birinchi mashinani o'zini olib kirish.

## Waveform Pause Alignment & Segmental Low-RAM Montage
- Concept: **RMS Silence Gap Alignment + Sequential Segment Concat** — Yagona TTS audiodagi real pauzalarni `20ms` RMS energiya bo'yicha topib gaplarni sinxronlash (`0` qo'shimcha ASR model) va video kesimlarni bitta og'ir `xfade` grafi o'rniga alohida qisqa `.mp4` bo'laklarda `concat demuxer` bilan birlashtirish `512 MB` RAM serverlarda OOM xavfisiz tezkor montaj beradi.
- Analogy: Butun poyezd vagonlarini bir kichik ustaxonada birga bo'yash o'rniga, har bir vagonni alohida-alohida tayyorlab chiqarib, oxirida ularni bitta temiryo'lda ulab qo'yish.

## Full MP4 `moov` Atom Header Parsing & Multi-Track `stco` Alignment
- Concept: **Dynamic `moov` Size Discovery (`parse_mp4_moov_end`) + Audio/Video `stco` Bounding** — Uzun filmlarda MP4 `moov` indeksi `4 MB` dan katta (`5.5–8 MB`) bo'lishi mumkin; boshidan qat'iy `4 MB` yuklash Video `stco` ni saqlab **2-trek (`Audio stco`)** ni nollab qo'yadi va `ffmpeg -map 0:a?` ovozsiz klip chiqaradi — shuning uchun `moov` o'lchamini o'qib oxirigacha yuklash va barcha asosiy treklarning `stco` chegarasini qamrash shart.
- Analogy: Kitobning mundarijasi 6 bet bo'lsa-yu, siz faqat birinchi 4 betini nusxalab olib ketsangiz — oxirgi ikki betdagi audio bobi ko'rinmay qolib, film jim-jit chiqadi.

## Cross-Candidate Corner Watermark Consensus & Reason Recovery
- Concept: **4-Corner Vision Prompt + Prose Recovery (`_infer_corner_watermark_boxes`) + Candidate Aggregation** — Yengil Vision modellari qorong'i kadrlarda burchak logotipini (`Kinochilar`) `reason` matnida yozib turib `blur_boxes: []` qoldirishi yoki nomzodlar orasida faqat bittasida topishi mumkin; matndan burchakni tiklash, ichkariga kengaytirish (`>= 0.75`) va barcha toza nomzodlar qutilarini jamlash watermark o'tib ketishini to'xtatadi.
- Analogy: Uchta kamera bitta binoni kuzatganda bittasi qo'riqchi o'ng burchakda begona belgini ko'rsa, qolgan kameralar qorong'ida payqamagan bo'lsa ham darhol o'sha burchakni yopib qo'yish.

## Single-Pass Frame-0 Branded Poster Cover & Gem-Priority Scoring
- Concept: **`overlay=eof_action=repeat:enable='lt(t,0.35)'` + Multi-Factor Gem Queue (`IMDb + Year + Views`)** — Alohida `concat` qilib audio desinxron chiqarish o'rniga `0.35s` poster muqovani bitta FFmpeg `overlay` o'tishida `0.0s` ga yopishtirish barcha `5` tarmoq panjarasiga professional ablojka beradi; avto-tanlovni esa `id.desc()` o'rniga reyting/yangilik balliga ko'chirish zerikarli mediaga kvota kuydirishni to'xtatadi.
- Analogy: Kitobning birinchi betiga chiroyli rangli muqova yopishtirib darhol asosiy voqeadan boshlash va vitrinaga omborga oxirgi kirgan eski kitobni emas, eng mashhur bestsellerlarni terish.

## End-Credits Anchor Cap (`<= 0.84`) & `is_credits` Midpoint Recovery
- Concept: **Pre-Credits Sparse Anchoring (`srt_end - 45s`, `ratio <= 0.84`) + Midpoint Retry** — Subtitr oxirgi qatorida (`srt_end`) titrlar bo'lmagani uchun `target_ratio = 0.95` to'g'ridan-to'g'ri titrlar ichiga tushib ketadi; `anchor = peak - 120s` ni `0.84` bilan cheklash va `is_credits=True` qaytganda `0.50` o'rta nuqtaga sakrash qora titr kesishni to'xtatadi.
- Analogy: Qissa kitobining mundarijasida oxirgi sahifa ko'rsatilgan bo'lsa ham orqasidagi 5 bet minnatdorchilik ro'yxatiga o'tib ketmaslik uchun doim kamida 2 bet oldindan ochish.





## Spoiler-Free Time-Windowed Hook & Sparse-Bounded Montage
- Concept: **Time-Windowed Hook Overlay (`between(t,0.35,5.50)`) + Sparse Window Bounding** — Birinchi 2–3 soniyada tomoshabin swipe qilishini to‘xtatish uchun `0.35s` poster muqovadan darhol keyin film nomini ochmaydigan (`sanitize_hook_text`) 1 qatorli intriga-hook matn ko‘rsatiladi; ko‘p kadrli `Bilasizmi?` montajida esa `moov` to‘liq davomiyligi emas, balki faqat sparse yuklangan haqiqiy bayt oralig‘i (`window_start..window_end`) kesiladi.
- Analogy: Gazeta sarlavhasida voqeaning oxirini yozib qo‘ymasdan qiziq savol qo‘yib o‘quvchini to‘xtatish va videomontajda faqat qo‘lda mavjud bo‘lgan kassetaning aniq daqiqalaridan kadr olish kabi.

## Title-Crop Typography Evaluation & Hue-Preserving Metallic Bevel
- Concept: **Hue-Preserving Specular Shading (`grad * contrast + hi^p`) + Title-Crop Evaluation** — Butun poster bo'ylab piksel taqqoslash 85% fon bir xilligi sababli shrift/rang xatolarini (`95%` deb) yashirib qo'yadi, qora-oq `+145` bevel esa to'q binafsha/oltin ranglarni oqartirib yuboradi; faqat sarlavha qismini qirqib baholash va yorug'likni asosiy rang nisbatida kuchaytirish haqiqiy sifatni beradi.
- Analogy: Faqat mashinaning diskini bo'yab turib, butun kuzovi yangi ko'rinadi deb o'zini aldamaslik — baho faqat bo'yalgan diskning o'ziga va uning haqiqiy chuqur rangiga qarab berilishi kerak.

## Morphological Stroke Inpainting & Residual Textless Audit
- Concept: **Stroke-Level Inpainting (`Top-Hat/Black-Hat + Canny`) + Residual Text Check (`_detect_residual_text_boxes`)** — Katta matn blokini to'liq bo'yash (`TELEA`) `X` shaklidagi xiralashuv beradi; faqat harf konturlarini o'chirish fonni (`45%+`) saqlaydi, residual tekshiruv esa TMDb "textless" deb aldaganda ham yozuvlarni tozalaydi.
- Analogy: Devordagi eski e'lonni bo'yashda butun xona devorini chaplab tashlamasdan, faqat harflarning o'zini mayda cho'tka bilan tekislash va boshqa usta bo'yab ketgan joyda hali yozuv qolmaganini alohida chiroq bilan tekshirish.

## Aspect-Aware Vertical Title Routing & Procedural Periodic Motif
- Concept: **Orientation Guard (`_is_vertical_title_box`) + Parametric Icon Motif (`_render_periodic_tile_poster`)** — Baland va ensiz quti (`height >= width * 1.4`) katta multfilm markaziy logotipi (`is_giant_logo`) emas, balki chap chetdagi `90°` vertikal sarlavhadir; aks holda fallback boshqa tekstsiz rasmga almashib qoladi. *Breaking Bad* kabi maxsus kimyoviy kataklar esa umumiy shriftni cho'zish o'rniga harf kengligiga mos dinamik kvadrat (`_calc_tile_size`) sifatida procedural chiziladi.
- Analogy: Uzun bo'yli bannerni "katta kvadrat reklama" deb o'ylab devordan yulib tashlamaslik, va maxsus kimyoviy emblemali peshtaxtani oddiy tekis yozuv bilan almashtirmasdan o'z ramkali qutisi bilan qayta yasash.

## Organic Brush Distortion & Fail-Closed Vision Quality Gate
- Concept: **Morphological Dilation + Displacement Warp (`_build_spray_stencil_mask`) + Fail-Closed Judge (`_verify_rendered_poster_quality`)** — Tayyor `.ttf` harflarini `cv2.dilate` bilan semirtirib `cv2.remap` va tumanli Gaussian buluti bilan cho'tka/sprey uslubiga yaqinlashtirish hamda har bir avtomatik renderni saqlashdan oldin Vision hakamidan (`score >= 7`) o'tkazish sifatsiz poster bazaga tushishini to'xtatadi.
- Analogy: Bosmaxonadan chiqqan harflarni trafaret bo'yoq bilan qo'lda yumshatib sepish va qadoqlashdan oldin nazoratchi ko'rigidan (`score >= 7`) o'tkazib, yaroqsizini peshtaxtaga chiqarmaslik.

## Subject-Flanking Split Layout & Bright-Emblem Interior Cleanup
- Concept: **`split_around_center` (Central `20%` Gap) + `_clean_bright_emblem_interior` (Saturation-Guarded Ellipse Fill)** — Markazdagi qahramonni yopmaslik uchun so'zlarni ikki yon qanotga (`0.03..0.39` va `0.61..0.97`) ajratish hamda doira/emblema ichidagi qora yozuvni OpenCV blur bilan qizil chegarani chaplamasdan, faqat past-to'yingan ichki ellips ichida tozalash badiiy muvozanatni saqlaydi; shuningdek deterministik Pillow matni uchun LLM imlo taxminini o'chirish yolg'on rad etishlarni to'xtatadi.
- Analogy: Sahna o'rtasida bosh qahramon turganda e'lon taxtasini uning ko'kragiga osmasdan ikki yoniga bo'lib yopishtirish, va muhr ichidagi yozuvni o'zgartirganda qizil muhr chizig'iga bo'yoq tekkizmasdan faqat oq o'rtasini tozalash.

## Peak-Centered Sparse Climax Windowing
- Concept: **Peak-Centered Sliding Window (`anchor = peak - 35s`, `ratio <= 0.91`)** — Agar `anchor = peak - 120s` olinib skan oynasi `63s` bilan cheklansa, `scan_end` kulminatsiya boshlanishidan `60s` oldin tugaydi (`0x00` emas, lekin bo'sh dialog!); oynani `peak - 35s .. peak + 30s` atrofida markazlash va `0.91` gacha ruxsat berish kechki kulminatsiyalarni to'g'ri ushlaydi.
- Analogy: Darvoza to'pini suratga olishda videoni goldan 2 daqiqa oldin yoqib, 1 daqiqa ichida o'chirib qo'ymaslik — kamerani zarbadan atigi 20–30 soniya oldin yoqib golning o'zini o'rtaga olish.
