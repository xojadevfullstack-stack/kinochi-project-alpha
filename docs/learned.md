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