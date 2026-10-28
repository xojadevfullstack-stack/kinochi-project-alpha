# Slice Report: 2026-10-28-f1-s21-actors-tmdb-filmography-and-requests

## What was done
1. Aktyorlar sahifasi (`/actors`) TMDb API ga ulandi: mashhur aktyorlar suratlari, haqiqiy ismlari va rollari chiqarildi.
2. Aktyor tanlanganda uning TMDb filmografiyasi yuklanadi va bizning ma'lumotlar bazamiz bilan solishtiriladi:
   - Agar film bazada mavjud bo'lsa -> Yashil "Bazada mavjud" va "Tomosha qilish" havolasi.
   - Agar film bazada hali bo'lmasa -> "Bazada yo'q" va "Buyurtma berish" tugmasi chiqadi.
3. "Buyurtma berish" bosilganda mavjud `POST /api/v1/content-requests` ga so'rov yuboriladi va foydalanuvchiga tasdiqlovchi xabar (toast) chiqadi.

## Changed files
- `backend/app/infrastructure/external/tmdb_client.py` - Added `get_person_filmography` and `get_person_details`.
- `backend/app/api/v1/actors.py` - Created `/actors` and `/actors/{id}/movies` endpoints with local DB cross-referencing.
- `backend/app/main.py` - Registered actors router.
- `website/app/actors/page.tsx` - Connected real actor photos, filmography modal, and order/request action.
- `backend/tests/test_actors_filmography_bridge.py` - TDD test suite (2 passing tests).

## check output
```text
backend\tests\test_actors_filmography_bridge.py ..                       [100%]
======================== 2 passed, 1 warning in 2.53s =========================
```

## Risks and unknowns
- TMDb person filmografiyasi har doim ham o'zbek tilida tarjimaga ega bo'lmasligi mumkin, shuning uchun rus/ingliz fallback ta'minlangan.

## Concept to explain to the user
- **Catalog Cross-Referencing & Content Demand Loop:** Tashqi katalog (TMDb) orqali aktyor filmlarini ko'rsatib, o'zimizda borlarini darhol tomosha qilishga, yo'qlariga esa foydalanuvchidan talab yig'ish (demand generation) orqali platformani o'stirish.

## Next step
- To'plamlarni 3 ta toifaga ajratish hisoboti.
