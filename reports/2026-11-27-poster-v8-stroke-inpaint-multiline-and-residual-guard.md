# Slice Report: 2026-11-27-poster-v8-stroke-inpaint-multiline-and-residual-guard

## What was done
1. `poster_localizer.py` dagi barcha ko'rsatilgan vizual xatoliklarning tizimli ildizlari tuzatildi: `_inpaint_boxes` da kontur-asosli matn o'chirish (`TOPHAT`/`BLACKHAT`/`Canny` — `X`-smear yo'qoldi), mislabeled TMDb `"null"` posterlarda `_detect_residual_text_boxes` tekshiruvi, `_clean_poster_display_title` orqali `(Solo Leveling)` kabi qavslarni tozalash, `title_stack_mode="stacked_equal"` bilan 2 qatorli bosh sarlavha renderyeri, hamda katta multfilm logotiplari (`box_h >= 0.22`) uchun toza rasmiy TMDb art (`_pick_cleanest_band`) zaxirasi qo'shildi.
2. `test_poster_localizer.py` ga `4` ta yangi TDD test (`test_v8_clean_display_title_and_stacked_equal_multiline`, `test_v8_stroke_inpaint_preserves_background_between_letters`, `test_v8_cleans_mislabeled_textless_even_when_manual_url_present`, `test_v8_giant_cartoon_logo_falls_back_to_clean_tmdb_art`) qo'shildi (`74 passed`).
3. Jonli DB va Telegram da barcha 7 ta media (`Movie #831, #917, #919`, `Series #998, #1001, #1015, #1119`) yangilanib vizual tasdiqlandi hamda `Job #9..#16` (`start_sec=0.0`) qayta render uchun navbatga qaytarildi.

## Changed files
- `backend/app/infrastructure/external/poster_localizer.py` - v8 stroke-inpaint, stacked multi-line, alias strip, residual-textless cleaner va giant-logo clean art zaxirasi.
- `backend/tests/test_poster_localizer.py` - 4 ta yangi v8 TDD testi (jami 28 ta test).
- `STATE.md`, `reports/2026-11-27-poster-v8-stroke-inpaint-multiline-and-residual-guard.md` - holat va hisobot.

## check output
```text
All checks passed!
i9d0e1f2a3b4 (head)
backend/tests/{test_smm_pipeline_and_telegram_pub,test_smm_worker,test_poster_localizer,test_poster_triggers,test_posters_storage,test_fix_f013_swallowed_exceptions}.py -> 74 passed in 12.65s
bot/tests/ -> 116 passed in 7.71s
```

## Risks and unknowns
- `SMM` da avvalgi `start_sec > 0` bilan qayta renderlashda `download_sparse_clip_source` `0.35` oralig'ini yuklab qolgani uchun `Job #9..#16` `failed` bo'lgandi; `start_sec=0.0` ga qaytarish bu xatoni hal qiladi (lekin kelajakda qo'lda `start_sec` kiritish uchun ham sparse-offset moslashuvi foydali bo'ladi).

## Concept to explain to the user
- **Morphological Stroke Inpainting & Residual Textless Audit**: Matn qutisini butunicha bo'yab tashlash o'rniga `Top-Hat/Black-Hat` bilan faqat harf konturlarini topib o'chirish atrofdagi rasm fonini (`45%+`) saqlab qoladi va `X`-blur paydo bo'lishini to'xtatadi; qo'shimcha residual tekshiruv esa TMDb "textless" deb belgilagan ammo aslida yozuvi bor posterlarni ham darhol tozalaydi.

## Next step
- O'zgarishlarni `feat/smm-autopilot` va `main` ga push qilish.
