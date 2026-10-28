# Slice Report: 2026-10-28-f1-s16-fix-cw-series-zero-id

## What was done
1. **Root cause aniqlandi:** Foydalanuvchining rasmidagi URL: `localhost:3000/series/0`. Brauzerning `localStorage` da epizod kodi (`gb3SGSCj`) saqlangan bo'lsa, `ContinueWatchingSection` uni `CatalogItem` ga o'tkazayotganda `Number("gb3SGSCj") || 0` tufayli `id = 0` bo'lib qolayotgan edi va `MovieCard` uni `/series/0` deb havola yasab, 404 ga tushirayotgan edi.
2. **`MovieCard.tsx` himoyalandi:**
   - Ixtiyoriy `href?: string` propini qabul qiladigan qilindi.
   - `targetSeriesId = (item.id && Number(item.id) > 0) ? item.id : (item.code || item.id)`. Agar `item.id === 0` bo'lsa, hech qachon `/series/0` havolasi yasalmaydi, o'rniga mavjud `code` olinadi.
3. **`ContinueWatchingSection.tsx` himoyalandi:**
   - `0` va `"0"` qiymatli eski yozuvlar `localStorage` dan o'qilayotganda butunlay filtrlash qo'shildi.
   - Har bir kartochka uchun aniq `targetHref` hisoblanadi (`/series/${target}`) va `MovieCard` ga to'g'ridan-to'g'ri `href={targetHref}` uzatiladi.
4. **TDD regression test:** `test_fix_continue_watching_zero_id.py` yozildi va ikkala holat assert qilindi (jami 35 passed).

## Changed files
- `website/components/catalog/MovieCard.tsx`
- `website/components/home/ContinueWatchingSection.tsx`
- `backend/tests/test_fix_continue_watching_zero_id.py`

## Verification output
```text
pytest backend/tests/test_fix_continue_watching_zero_id.py: 2 passed in 0.16s
pytest full UI suite: 35 passed in 0.40s
next lint: 0 errors
```
