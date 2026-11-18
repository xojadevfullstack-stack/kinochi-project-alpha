# Project State (STATE.md)

## Current goal
Filtrlar bo'yicha foydalanuvchi talablarini to'liq bartaraf etish: 2 ta "Barchasi"ni bittaga keltirish, ortiqcha "Bo'lim" filtrini to'liq olib tashlash va "Eng yangilari" saralashini eng so'nggi yuklangan kontent bo'yicha to'g'irlash.

## In progress (slice, branch)
- Slice: F1-S74: Latest Additions Sort & Redundant Sections Cleanup (`cd3d273`).
- Branch: `main`.

## Blocked
- None.

## Next step (one task)
- Foydalanuvchi tekshiruvi va GitHub'ga push qilish tasdig'i.

## Last verification & check results (Terminal Evidence)
- **Pytest Filter Suite:** 5 passed in 4.14s (`test_filter_*.py`).
- **Backend Filter Oracle Suite:** 16 PASS | 0 FAIL | 1 MAVJUD EMAS (`python scratch/audit_backend_oracle.py`).
- **TypeScript Static Verification:**
  * Website: `tsc -p website/tsconfig.json --noEmit` -> 0 errors.
  * Admin-Panel: `tsc -p admin-panel/tsconfig.json --noEmit` -> 0 errors.
- **Sorting Verification:**
  * Movies `sort=latest`: `created_at DESC, id DESC` -> Eng yangi yuklangan kinolar (masalan, bugun yuklangan ID 912, 911, 910) eng tepada chiqadi.
  * Series `sort=latest`: `coalesce(updated_at, created_at) DESC, id DESC` -> Eng yangi fasl/qism yuklangan seriallar eng tepada chiqadi.
- **Redundant Sections & Duplicate "Barchasi" Removal:**
  * `website/app/category/[id]/page.tsx`: Qatorli eski kategoriya chiplari olib tashlandi, 2-chi "Barchasi" tugmasi yo'qotildi.
  * `website/app/catalog/page.tsx`: "Katalog bo'limlari" seksiyasi olib tashlandi.
  * `website/components/catalog/UnifiedFilterBar.tsx`: Saralash dropdownida ma'nosiz "Barchasi" olib tashlandi (`showAllOption={false}`).
