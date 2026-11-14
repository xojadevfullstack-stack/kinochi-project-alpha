# Kinochi QA & Engineering Incident Triage Lifecycle (SOP)

Ushbu hujjat loyihada yuzaga keladigan har qanday nosozlik, xatolik yoki talab chetlanishini (Defect) aniqlashdan tortib yopilishigacha bo'lgan 7 bosqichli standart operatsion tartibni (SOP) belgilaydi. Tizim Elite Engineering global ko'nikmalari bilan to'liq integratsiya qilingan.

---

## 7 Bosqichli Sikl va Elite Ko'nikmalar Xaritasi

```text
MUAMMO TOPILDI (Issue Discovered)
│
├── 1. Screenshot / Video / Log ──────────────► [/telemetry]
│   ├── Vizual dalil (Desktop / Mobile skrinshot yoki video)
│   ├── Server loglari (FastAPI stdout, bot trace, DB exception)
│   └── Tarmoq trace (HTTP status code, cURL yoki devtools HAR)
│
├── 2. Reproduction ──────────────────────────► [/tdd] + [/search]
│   ├── Qadamlar (Step-by-step reproduktsiya yo'li)
│   ├── Minimal qulovchi test (RED test: assert fail)
│   └── Kutilgan (Expected) vs Real (Actual) natijani solishtirish
│
├── 3. Classification ────────────────────────► [/ux] + [/sec] + [/arch]
│   ├── UI (Ranglar palitrasi, shrift, Cinematic Red buzilishi)
│   ├── UX (Kognitiv yuklama, navigatsiya noqulayligi, bo'sh holatlar)
│   ├── Button / Interaction (Bosilmaydigan [Btn], noto'g'ri callback, stale state)
│   ├── Functional (API 500, DB constraint, noto'g'ri biznes mantiq)
│   ├── Responsive (Mobil ekranda sig'maslik, 44px touch target)
│   └── Navigation (404 marshrut, FSM qotib qolishi, deep-link uzilishi)
│
├── 4. Developer ─────────────────────────────► [8-Axis Filter] + [/tanqid]
│   ├── Root Cause Analysis (RCA: Asl ildiz sababini aniqlash)
│   ├── Minimal atomik tuzatish (Diff <= 200 qator)
│   └── Build & Type check (`tsc --noEmit`, linters)
│
├── 5. QA Retest ─────────────────────────────► [Verification Gate]
│   ├── PASS ──► 6-bosqichga o'tish (Regression)
│   └── FAIL ──► 4-bosqichga qaytarish (Developer RCA)
│
├── 6. Regression ────────────────────────────► [/premortem] + [Full Suite]
│   ├── Shu feature: Mazkur modulning barcha holatlari
│   ├── Bog'liq feature: API iste'molchilari (Bot, Web, Admin)
│   └── Qurilmalar: Mobile vs Desktop, Touch vs Click
│
└── 7. CLOSED ────────────────────────────────► [docs/failures.md] + [STATE.md]
    ├── Failure logiga kiritish (Xato, sabab, yechim, qoida)
    ├── STATE.md ni yangilash
    └── Conventional Commit (`fix(...)` / `test(...)`)
```

---

## Har bir bosqichning qat'iy talablari (Checklist)

### 1. Screenshot / Video / Log (`/telemetry`)
- Hech qanday taxmin yo'q: terminaldan olingan xato izi (traceback), konsol logi yoki vizual skrinshot talab etiladi.
- Logda parametrlar, request payload va timestamp aniq ko'rsatilishi shart.

### 2. Reproduction (`/tdd`)
- Muammo avval izolyatsiyalangan testda takrorlanishi (FAIL / RED) shart.
- Agar test qizil bo'lmasa, tuzatish yozish taqiqlanadi.

### 3. Classification
- Muammo 6 toifadan biriga aniq biriktiriladi. Bir vaqtning o'zida bir nechta toifaga tushsa, eng yuqori xavfli (Security > Functional > UX/UI) bosh mezon etib olinadi.

### 4. Developer (`/tanqid`)
- 8-o'qli filtr orqali baholash.
- Bitta slaysta o'zgarishlar hajmi diff <= 200 qatordan oshmasligi shart.
- Hech qanday `except: pass` yoki yashirin istisnolarga yo'l qo'yilmaydi.

### 5. QA Retest
- Mustaqil muhitda (`clean_test` bazasi yoki izolyatsiyalangan runner) test qayta ishga tushiriladi va yashil (PASS / GREEN) bo'lishi tekshiriladi.

### 6. Regression (`/premortem`)
- Butun tizim regressiya qoplamasidan o'tadi:
  - Backend: `pytest`
  - Bot: `pytest bot/tests/`
  - Website: `npx tsc --noEmit`
  - Admin: `npx tsc --noEmit`
- Chekka holatlar (timeout, rate limit, tarmoq uzilishi) pre-mortem orqali tekshiriladi.

### 7. CLOSED
- `docs/failures.md` fayliga xato, uning sababi va loyiha uchun yangi qoida qayd etiladi.
- `STATE.md` yangilanadi.
