# Project State (STATE.md)

## Current goal
Filtrlar bo'yicha foydalanuvchi talablarini to'liq bartaraf etish: 2 ta "Barchasi"ni bittaga qisqartirish, ortiqcha "Bo'lim" filtrini olib tashlash va "Eng yangilari" saralashini to'g'irlash.

## In progress (slice, branch)
- Slice: F1-S73: Filter Bar Simplification & Latest Sort Consistency (`8137eb7`).
- Branch: `main`.

## Blocked
- None.

## Next step (one task)
- Foydalanuvchi tekshiruvi va GitHub'ga push qilish tasdig'i.

## Last verification & check results (Terminal Evidence)
- **Pytest Filter Suite:** 5 passed in 5.38s (`test_filter_*.py`).
- **Backend Filter Oracle Suite:** 16 PASS | 0 FAIL | 1 MAVJUD EMAS (`python scratch/audit_backend_oracle.py`).
- **TypeScript Static Verification:**
  * Website: `tsc -p website/tsconfig.json --noEmit` -> 0 errors.
  * Admin-Panel: `tsc -p admin-panel/tsconfig.json --noEmit` -> 0 errors.
  - `Uzmovi Spartak S1E1 (Series #1105)`: 3 frames verified (Msg 4441)
  - `AniToob Sening isming (Movie #867)`: 3 frames verified (Msg 4442)
  - `AniToob Hyouka S1E1 (Series #1106)`: 3 frames verified (Msg 4443)
  - `Kinochilar Fifty Shades (Movie #859)`: 3 frames verified (Msg 3893)
  - `Animeelar Siundzi S1E1 (Series #1099)`: 3 frames verified (Msg 3890)
- **Unit Test Gate:**
  - `pytest backend/tests/test_autopilot_vision_gate.py backend/tests/test_video_verifier.py backend/tests/test_admission_gate_quality_guards.py`: 16 passed in 4.57s.
