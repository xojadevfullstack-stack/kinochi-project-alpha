# Slice Report: 2026-11-27-poster-v6-typography-fidelity

## What was done
1. `poster_localizer.py` dvigateli **Garri Potter** va **Sijjin 8** sifat standartiga ko'ra yangilandi: `letter_spacing` (`tight`/`normal`/`wide`/`ultra_wide`), `font_weight` (`regular`/`bold`/`heavy`), `texture_style` (`weathered`/`brushed`/`steel`/`clean`), rangni saqlovchi `metallic` shader (`+145` oqartirish o'rniga to'q-to'yingan gradyent saqlanadi), yaqin rangli shishgan `rim_color` filtri (`_should_apply_rim`), textless rasmlarga soxta blur tushishini to'xtatuvchi `has_visible_title` tekshiruvi, `line_layout` bo'yicha taglavha ajratish (`Qasoskorlar 4` + `INTIHO`) va kirill alifbosidagi natijalarni (`ШОГУН`) rad etuvchi lotin OCR tekshiruvi qo'shildi.
2. Yengil/o'rta OFL Google Fonts (`Cinzel-Regular.ttf`, `Cinzel-SemiBold.ttf`, `Montserrat-Medium.ttf`, `Montserrat-SemiBold.ttf`) va `4` ta yangi TDD test (`test_poster_localizer.py`) qo'shildi; `scratch/run_v5_batch_preview.py` da butun poster foizi o'rniga qat'iy faqat sarlavha qirqimi (`title-crop`) bo'yicha halol baholash joriy qilindi.
3. Jonli DB va Telegram da `#827` (*Qasoskorlar 4 Intiho*), `#1120` (*Shogun*) va `#1125` (*Institut*) posterlari yangilanib Redis keshi tozalandi hamda `STATE.md`, `docs/learned.md` va hisobot yangilandi.

## Changed files
- `backend/app/infrastructure/external/poster_localizer.py` - v6 shrift/tracking/bevel/rim/textless/Latin-OCR yangilanishlari.
- `backend/tests/test_poster_localizer.py` - v6 tracking, rim contrast, metallic hue, line_layout, clean textless va Cyrillic-OCR rad etish testlari.
- `backend/app/assets/fonts/Cinzel-{Regular,SemiBold}.ttf`, `Montserrat-{Medium,SemiBold}.ttf` - OFL o'rta qalinlikdagi serif va sans shriftlar.
- `STATE.md`, `docs/learned.md` - holat va texnik tushunchalar yozuvi.

## check output
```text
All checks passed!
i9d0e1f2a3b4 (head)
backend/tests/{test_poster_localizer,test_poster_triggers,test_posters_storage,test_fix_f013_swallowed_exceptions}.py -> 32 passed in 3.83s
bot/tests/ -> 116 passed in 7.47s
```

## Risks and unknowns
- Cloudflare `flux-2-klein-4b` ayrim blokbaster nomlarida (`Avengers`, `Garri Potter`, `Institut`) HTTP `400`/OCR xatoga tushib Studio Renderer'ga o'tadi; custom qo'l-chizma ramzlar (`THE [eye] INSTITUTE` ko'z belgisi yoki `将軍` yaponcha muhr) esa TMDb toza textless rasmida bo'lmaganligi uchun oddiy harflar bilan o'rnini bosadi.
- `eval_pair` da sarlavha-qirqimi Vision bahosi Gemini Flash-Lite nigohiga bog'liq; `make check` to'liq `backend/tests/` to'plami Windows lokalida ayrim tashqi/pool testlarda qotganligi sabab poster/f013 + bot to'plamlari alohida to'liq tekshirildi.

## Concept to explain to the user
- **Title-Crop Typography Evaluation & Hue-Preserving Metallic Bevel**: Butun rasmni solishtirish orqa fondagi o'zgarmas osmon/yuzlar hisobiga `95%` soxta baland baho beradi; faqat sarlavha hududini qirqib baholash va yaltiroq metallik effektni oq rang qo'shib yubormasdan asosiy rangning to'yinganligida berish haqiqiy o'xshashlikni oshiradi.

## Next step
- O'zgarishlarni `feat/smm-autopilot` branchiga kommit va push qilish.
