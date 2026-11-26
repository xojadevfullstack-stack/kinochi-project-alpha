# Slice Report: 2026-11-26-poster-motif-prompt

## What was done
1. `analyze_poster_style` (`backend/app/infrastructure/external/poster_localizer.py`) endi dekorativ logotip motivlarini (`title_motifs`), qator bo'linishini (`line_layout`) va ortiqcha reyting/TV badjlarini (`badges_to_remove`) ajratadi hamda `_normalize_str_list` orqali normallashtiradi.
2. `_build_cf_edit_prompt` qo'shilib, `edit_poster_with_cloudflare` so'rovida original emblemalar (`O` ichidagi qilich, tarozi, tally chiziqlari) ni saqlash, qatorlarni moslashtirish, burchak badjlarini olib tashlash va o'zbekcha apostroflarni (`O'`, `G'`, `'`) aniq saqlash ta'minlandi; `config.py` da `CLOUDFLARE_ENABLE_9B: bool = False` qo'shilib `14k`-neyron sakrashini beradigan `9b` defolt bloklandi (`4b` qayta urinishi saqlandi).
3. `backend/tests/test_poster_localizer.py` da 3 ta RED -> GREEN test qo'shildi, `STATE.md` va `docs/learned.md` yangilandi.

## Changed files
- `backend/app/core/config.py` - Added `CLOUDFLARE_ENABLE_9B: bool = False` default guard
- `backend/app/infrastructure/external/poster_localizer.py` - Added `title_motifs`, `line_layout`, `badges_to_remove` extraction + `_normalize_str_list` + `_build_cf_edit_prompt` + `4b`-only default loop + apostrophe check in OCR verification
- `backend/tests/test_poster_localizer.py` - Added 3 unit tests covering motif/layout/badge extraction, prompt output, and `9b` default block
- `STATE.md` - Recorded verification results and live queue notes
- `docs/learned.md` - Documented `Motif-Preserving Structured Poster Prompting`
- `reports/2026-11-26-poster-motif-prompt.md` - Slice report

## check output
```text
ruff check backend/app/core/config.py backend/app/infrastructure/external/poster_localizer.py backend/tests/test_poster_localizer.py
All checks passed!

ruff check --select F821 backend/app/core/config.py backend/app/infrastructure/external/poster_localizer.py
All checks passed!

alembic heads
h8c9d0e1f2a3 (head)

pytest backend/tests/test_poster_localizer.py backend/tests/test_posters_storage.py backend/tests/test_poster_triggers.py backend/tests/test_alembic.py -v
======================== 28 passed, 1 warning in 6.45s ========================
```

## Risks and unknowns
- Cloudflare Workers AI `Nov 25, 23:30 UTC+5` dagi `14.25k` (`9b: 14k`) sarf sababli REST API da hozir `429 code 4006` blokida; yangilangan `4b` prompti bilan jonli generatsiya natijasi faqat limit ochilgandan keyin tasdiqlanadi.

## Concept to explain to the user
- **Semantic Style & Motif Decomposition + Model Quota Ceiling** — Arzon `4b` modelga emblema (`title_motifs`), qator (`line_layout`) va badjlarni (`badges_to_remove`) alohida ko'rsatib, katta `9b` (`14k` neyron) eskalatsiyasini env flag (`CLOUDFLARE_ENABLE_9B=False`) bilan yopib qo'yish.
- Analogy: Rassomga aniq chizma berib, kunlik budjetni birgina qimmat ustaga sarflab yubormaslik uchun qimmat xizmatni faqat ruxsat bilan yoqiladigan kalit ostiga olish.

## Next step
- Cloudflare `24h` / `05:00+05:00` limiti yechilgach *Taxtlar o'yini* posterida faqat `flux-2-klein-4b` bilan jonli sinov o'tkazish.
