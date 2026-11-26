# Slice Report: 2026-11-26-smm-variant1-scenes

## What was done
1. `scraper/smm_scene_finder.py` yaratildi (`parse_srt_blocks`, `compress_srt_for_llm`, `fetch_imdb_id`, `fetch_stremio_srt`, `find_viral_scene_target`) — film/serial uchun TMDb -> `imdb_id` -> Stremio OpenSubtitles `.srt` orqali Gemini Flash-Lite yordamida eng kuchli kulminatsiya/burilish taymkodini (`target_ratio`, `peak_sec`, `visual_cue`) topadi.
2. `scraper/smm_scene_scorer.py` (`check_frames_for_ads_or_nsfw` + `select_best_scene_start` da `visual_cue` va `compare_candidates` bo'yicha eng yuqori `excitement_score`/`cue_match` tanlash + `ASLANBE STUDIO` watermark misoli) hamda `scraper/smm_pipeline.py` va `scraper/smm_worker.py` (`_resolve_scene_meta`) ulandi.
3. TDD testlar (`test_smm_scene_scorer.py`, `test_smm_pipeline_and_telegram_pub.py`), `STATE.md` va `docs/learned.md` yangilandi.

## Changed files
- `scraper/smm_scene_finder.py` - Open-source SRT scene-timecode lookup module
- `scraper/smm_scene_scorer.py` - Added `visual_cue` matching and multi-candidate ranking (`compare_candidates`)
- `scraper/smm_pipeline.py` - Integrated `find_viral_scene_target` + targeted sparse window + `compare_candidates=3`
- `scraper/smm_worker.py` - Added `_resolve_scene_meta` and wired TMDb/episode metadata to `create_smart_smm_clip`
- `backend/tests/test_smm_scene_scorer.py` - Added SRT timecode + multi-candidate excitement/cue ranking tests
- `backend/tests/test_smm_pipeline_and_telegram_pub.py` - Added pipeline integration test for targeted ratio & `visual_cue`
- `STATE.md`, `docs/learned.md`, `reports/2026-11-26-smm-variant1-scenes.md` - Progress & concept tracking

## check output
```text
ruff check & ruff --select F821 -> All checks passed!
alembic heads -> h8c9d0e1f2a3 (head)
pytest test_smm_scene_scorer.py + test_smm_pipeline_and_telegram_pub.py + test_smm_worker.py + test_smm_external_publishers.py + test_smm_clipper.py -> 65 passed
pytest test_smm_api.py (isolated) -> 8 passed (combined run after test_smm_worker hits pre-existing shared SQLite FULL_AUTO state on test_smm_settings_get_and_toggle_dual_mode)
pytest bot/tests/ -q -> 116 passed
```

## Risks and unknowns
- Ba'zi mahalliy yoki juda yangi filmlar uchun Stremio `.srt` topilmasligi mumkin (bunday holatda `target_ratio=0.35` va `compare_candidates=3` bilan avtomatik davom etadi).
- Dublyaj studiyasi kiritgan intro farqi katta bo'lsa (`> 70s`), `.srt` taymkodi siljishi mumkin — bu `mapped_peak - 95s .. +15s` oynasi bilan qoplangan.

## Concept to explain to the user
- **SRT-Guided Viral Scene Discovery & Multi-Candidate Vision Ranking** — Ochiq manbadan subtitr taymkodi orqali kulminatsiyani topib, faqat o'sha segmentdan sparse yuklash va Vision'da barcha nomzodlarni o'zaro solishtirish.
- Analogy: Qalin kitobdan tasodifiy varaq ochish o'rniga, avval mundarija va iqtiboslardan eng keskin bobni topib, faqat o'sha sahifalarni o'qish.

## Next step
- Render yangilangach (`git push origin feat/smm-autopilot` & `main`), navbatdagi SMM klipda yangi `Variant 1` qidiruvi va Make.com Facebook Reels holatini kuzatish.
