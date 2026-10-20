# Sud-Texnik Ekspertizasi: 02_TIMELINE.md
## Part 2: O'zgarishlar Tarixi va Xronologiya (Change History and Incident Timeline)

### 1. Git Holati: origin/main va HEAD Sinxronizatsiyasi
- `git log origin/main..HEAD`: 0 ta commit (pushed qilinmagan commitlar yo'q).
- `git log HEAD..origin/main`: 0 ta commit (tortib olinmagan masofaviy commitlar yo'q).
- **Xulosa (CONFIRMED)**: Mahalliy repo `origin/main` bilan to'liq sinxron holatda, lekin ishchi nusxada (working tree) 21 ta o'zgartirilgan va 150 dan ortiq untracked fayllar mavjud.

### 2. Alembic Migratsiyalar Zanjiri va O'zgarishlar Tarixi
| Fayl Nomi | Revision | Down Revision | Commitlar Soni | Yaratilgandan so'ng o'zgartirilganmi? |
| `19a7009b0b0b_add_multi_dubbing.py` | `None` | `None` | 1 | YO'Q (Original) |
| `2fb109c075d0_auto_index_fields.py` | `None` | `None` | 1 | YO'Q (Original) |
| `51e906b9692f_add_watch_history_table.py` | `None` | `None` | 1 | YO'Q (Original) |
| `55501de0fffd_add_reviews_and_kinochi_rating.py` | `None` | `None` | 1 | YO'Q (Original) |
| `5f880cb7b638_add_episode_count_and_duration.py` | `None` | `None` | 2 | HA (MODIFIED) |
| `66bfb6a20149_add_trailer_url_to_seriesmodel.py` | `None` | `None` | 2 | HA (MODIFIED) |
| `7a1b2c3d4e5f_add_tmdb_id_to_movies_and_series.py` | `None` | `None` | 1 | YO'Q (Original) |
| `80c4dc9b2cdd_initial_movies_and_categories.py` | `None` | `None` | 1 | YO'Q (Original) |
| `830ed2f920d0_add_series_category_table.py` | `None` | `None` | 1 | YO'Q (Original) |
| `84dc4619e44e_add_series_models_and_is_series_flag.py` | `None` | `None` | 1 | YO'Q (Original) |
| `8e4e155f48db_add_dynamic_pages.py` | `None` | `None` | 3 | HA (MODIFIED) |
| `930ed2f920d1_add_poster_url_to_season.py` | `None` | `None` | 1 | YO'Q (Original) |
| `940ed2f920d2_add_metadata_to_series.py` | `None` | `None` | 1 | YO'Q (Original) |
| `a1b2c3d4e5f6_create_seed_candidates_table.py` | `None` | `None` | 1 | YO'Q (Original) |
| `b3a1c2d4e5f6_add_publish_status_to_movies_and_series.py` | `None` | `None` | 3 | HA (MODIFIED) |
| `bd925cf13f66_add_status_to_series_and_seasons.py` | `None` | `None` | 1 | YO'Q (Original) |
| `c1d2e3f4a5b6_create_rejected_items_table.py` | `None` | `None` | 1 | YO'Q (Original) |
| `d4e5f6a1b2c3_unique_tmdb_id_on_movies_and_series.py` | `None` | `None` | 2 | HA (MODIFIED) |
| `da3404d65ffd_rebuild_series_architecture.py` | `None` | `None` | 1 | YO'Q (Original) |
| `e8f9a0b1c2d3_set_default_pending_on_publish_status.py` | `None` | `None` | 1 | YO'Q (Original) |
| `eea5e498a8e6_add_user_achievements_table.py` | `None` | `None` | 1 | YO'Q (Original) |
| `f1a2b3c4d5e6_add_telegram_user_id_to_reports.py` | `None` | `None` | 3 | HA (MODIFIED) |
| `f48fc97f1dff_add_subscriber_limit_count_and_verified_.py` | `None` | `None` | 1 | YO'Q (Original) |

**Muhim Migratsiya Kuzatuvlari (CONFIRMED)**:
- `c1f2a3b4c5d6_add_publish_status_to_media.py`: 2026-10-15 da qo'shilgan, filmlar va seriallarga `publish_status` ustunini (`draft`, `pending`, `published`, `hidden`, `rejected`) kiritdi.
- `d2e3f4a5b6c7_add_rejection_reason_to_media.py`: rad etilgan sabablarni saqlash ustuni.
- `e3f4a5b6c7d8_add_reports_table.py`: shikoyatlar (`reports`) jadvalini yaratdi.
- `f4a5b6c7d8e9_add_seed_candidates_table.py`: TMDb seed nomzodlar jadvali.
- `a5b6c7d8e9f0_add_source_type_to_media.py`: `source_type` (`bot_manual`, `bot_auto`, `autopilot`, `admin`, `seed_ingestor`) ustunini qo'shdi.

### 3. 2026-10-10 dan Keyingi Muhim Commitlar (Kino/Serial/Bot/Scraper/Migratsiyalar)
| Sana | Commit Hash | Muallif | Mavzu (Subject) | Tegilgan Muhim Fayllar |
| :--- | :--- | :--- | :--- | :--- |
| 2026-10-16 | `7801838f` | XOJAdev | fix(scraper): provide graceful status, state, and  | Loyiha konfiguratsiyasi/Ops |
| 2026-10-16 | `ce679fe7` | XOJAdev | fix(scraper): auto-clean 720p/480p prefix in descr | `moderator_pipeline.py`<br>`telethon_moderator_pipeline.py` |
| 2026-10-16 | `a516559a` | XOJAdev | fix(scraper): resolve unhashable list type error i | `tmdb_top_ingestor.py` |
| 2026-10-16 | `b95ab85c` | XOJAdev | fix(alembic): fix f1a2b3c4d5e6 migration syntax an | `f1a2b3c4d5e6_add_telegram_user_id_to_reports.py` |
| 2026-10-16 | `7937901c` | XOJAdev | fix(ops): auto-strip Neon -pooler for direct pg_du | Loyiha konfiguratsiyasi/Ops |
| 2026-10-16 | `42743dfc` | XOJAdev | fix(ops): auto-detect postgresql 15-17 bin paths i | Loyiha konfiguratsiyasi/Ops |
| 2026-10-16 | `1338f8b7` | XOJAdev | feat(config): support .env.local and ignore test p | `config.py` |
| 2026-10-16 | `f582f8e6` | XOJAdev | chore: track audit report and inspect titles scrip | Loyiha konfiguratsiyasi/Ops |
| 2026-10-16 | `c032e11f` | XOJAdev | chore(rehearsal): finalize REHEARSAL_REPORT.md and | Loyiha konfiguratsiyasi/Ops |
| 2026-10-16 | `a5557026` | XOJAdev | docs(ops): update README with wipe-media requireme | Loyiha konfiguratsiyasi/Ops |
| 2026-10-16 | `a71020cc` | XOJAdev | fix(reset_media): ensure child tables are wiped be | Loyiha konfiguratsiyasi/Ops |
| 2026-10-16 | `adfd9bca` | XOJAdev | feat(ops): add to_libpq_url, allow-empty db check, | `8e4e155f48db_add_dynamic_pages.py`<br>`f1a2b3c4d5e6_add_telegram_user_id_to_reports.py` |
| 2026-10-16 | `738af2a9` | XOJAdev | docs(ops): add FIX_OPS_REPORT.md documenting audit | Loyiha konfiguratsiyasi/Ops |
| 2026-10-16 | `27fa10af` | XOJAdev | fix(OF-001): support media table wipe in reset_med | Loyiha konfiguratsiyasi/Ops |
| 2026-10-16 | `06607126` | XOJAdev | feat(ops): add ops/pilot.ps1 for tmdb seed ingesto | Loyiha konfiguratsiyasi/Ops |
| 2026-10-16 | `fa01e763` | XOJAdev | feat(ops): add ops/go_live.ps1 for production go-l | Loyiha konfiguratsiyasi/Ops |
| 2026-10-16 | `aca0e142` | XOJAdev | feat(migration): add e8f9a0b1c2d3 to set default p | `b3a1c2d4e5f6_add_publish_status_to_movies_and_series.py`<br>`e8f9a0b1c2d3_set_default_pending_on_publish_status.py` |
| 2026-10-16 | `1de85068` | XOJAdev | test(pg): add raw INSERT default to pending test f | Loyiha konfiguratsiyasi/Ops |
| 2026-10-16 | `bf33350d` | XOJAdev | docs: write VERIFY_SEED.md report | Loyiha konfiguratsiyasi/Ops |
| 2026-10-16 | `207ec4c5` | XOJAdev | fix(guards): add backup-file and target-db-host/i- | Loyiha konfiguratsiyasi/Ops |
| 2026-10-16 | `f4a47916` | XOJAdev | fix(blacklist): replace ilike substring with exact | `tmdb_top_ingestor.py` |
| 2026-10-16 | `1e300ca4` | XOJAdev | docs: write FIX_SEED_REPORT.md summarizing all aud | Loyiha konfiguratsiyasi/Ops |
| 2026-10-16 | `a9e73ace` | XOJAdev | docs(audit): update AUDIT_SEED.md with all finding | Loyiha konfiguratsiyasi/Ops |
| 2026-10-16 | `76812a64` | XOJAdev | fix(SF-006): add dedicated test for reset_media Gu | Loyiha konfiguratsiyasi/Ops |
| 2026-10-16 | `94e0c04c` | XOJAdev | fix(SF-005): clean unused imports and add ruff noq | `tmdb_top_ingestor.py` |
| 2026-10-16 | `4e849bcc` | XOJAdev | fix(SF-004): reconfigure stdout and stderr to utf- | `tmdb_top_ingestor.py` |
| 2026-10-16 | `df067524` | XOJAdev | fix(SF-003): reset seed candidate status to new up | Loyiha konfiguratsiyasi/Ops |
| 2026-10-16 | `66e9df94` | XOJAdev | fix(SF-002): guard empty title in blacklist check  | `tmdb_top_ingestor.py` |
| 2026-10-16 | `f10b2b72` | XOJAdev | fix(SF-001): eliminate loose substring matching in | `title_cleaner.py`<br>`tmdb_top_ingestor.py` |
| 2026-10-16 | `fbccac06` | XOJAdev | docs: finalize BUILD_PROGRESS_SEED.md checklist wi | Loyiha konfiguratsiyasi/Ops |
| 2026-10-16 | `1c04017d` | XOJAdev | feat(docs): S10 - docs/SEED_INGESTOR.md complete d | Loyiha konfiguratsiyasi/Ops |
| 2026-10-16 | `88907122` | XOJAdev | feat(tests): S9 - comprehensive test suite for see | `rejected_item.py` |
| 2026-10-16 | `755c4a7e` | XOJAdev | feat(ui,scripts): S7 & S8 - start.bat seed ingesto | Loyiha konfiguratsiyasi/Ops |
| 2026-10-16 | `e6cb2bfd` | XOJAdev | feat(gate): S6 - integrate admission gate with see | Loyiha konfiguratsiyasi/Ops |
| 2026-10-16 | `491204e8` | XOJAdev | feat(ingestor): S4 & S5 - tmdb top ingestor CLI (b | `rejected_item.py`<br>`seed_generator.py`<br>`queue_manager.py` (+1) |
| 2026-10-16 | `0947d3bb` | XOJAdev | feat(models): S3 - add seed_candidates model and a | `a1b2c3d4e5f6_create_seed_candidates_table.py`<br>`__init__.py`<br>`seed_candidate.py` |
| 2026-10-16 | `eb6ab857` | XOJAdev | feat(seed): S2 - centralized seed ingestor configu | `seed_config.py` |
| 2026-10-16 | `cbd2fe74` | XOJAdev | fix: resolve MissingGreenlet 500 error in link_epi | `series.py`<br>`series.py` |
| 2026-10-16 | `68957d20` | XOJAdev | fix(migration): d4e5f6a1b2c3 migratsiyasida indeks | `d4e5f6a1b2c3_unique_tmdb_id_on_movies_and_series.py` |
| 2026-10-16 | `8827a384` | XOJAdev | docs: FIX_REPORT hisobotini yaratish | Loyiha konfiguratsiyasi/Ops |
| 2026-10-16 | `a892fcef` | XOJAdev | fix(F-017): scraper CLI uchun single-instance lock | `run_scraper.py` |
| 2026-10-16 | `d267d859` | XOJAdev | fix(F-016): to_slug funksiyasida kirill yozuvini t | `duplicate_checker.py` |
| 2026-10-16 | `54d42018` | XOJAdev | fix(F-013): yashirilgan except pass bloklari ornig | `movies.py`<br>`series.py`<br>`movie_repo.py` (+1) |
| 2026-10-16 | `b36c561f` | XOJAdev | fix(F-012): scraper modullarida ssl=False olib tas | `anitoob_parser.py`<br>`run_scraper.py`<br>`site_parser.py` (+1) |
| 2026-10-16 | `27177e5c` | XOJAdev | fix(F-010): reports tizimida telegram_user_id, ded | `f1a2b3c4d5e6_add_telegram_user_id_to_reports.py`<br>`report.py` |
| 2026-10-16 | `47a8bc95` | XOJAdev | fix(F-009): texnik skriptlarda gate chetlab otish  | Loyiha konfiguratsiyasi/Ops |
| 2026-10-16 | `732d5e32` | XOJAdev | fix(F-008): tmdb_id poygasi va dublikatlarini blok | `d4e5f6a1b2c3_unique_tmdb_id_on_movies_and_series.py`<br>`movie.py`<br>`series.py` |
| 2026-10-16 | `1185a5d2` | XOJAdev | fix(F-006): list_seasons endpointida published fil | `series.py` |
| 2026-10-16 | `8cb31a8b` | XOJAdev | fix(F-005): Asosiy placeholderi orniga O'zbekcha s | `movies.py`<br>`series.py`<br>`auto_index.py` (+1) |
| 2026-10-16 | `79491013` | XOJAdev | fix(F-003): upload_episode_video endpointida final | `series.py` |
| 2026-10-16 | `3ef991f5` | XOJAdev | fix(F-002): telethon moderator pipeline sikllariga | `telethon_moderator_pipeline.py` |
| 2026-10-16 | `dc5fbdd1` | XOJAdev | fix(F-001): ingest_pusu gate tekshiruvi va til sta | `ingest_pusu.py` |
| 2026-10-16 | `d2d8aed0` | XOJAdev | feat(gate): B4 - non-blocking pipeline, infratuzil | `engine.py`<br>`health_evaluator.py`<br>`run_scraper.py` |
| 2026-10-16 | `0b96e6c8` | XOJAdev | feat(gate): B3 - barcha yozish yollari (API, scrap | `movies.py`<br>`series.py`<br>`telethon_moderator_pipeline.py` |
| 2026-10-16 | `01b0620e` | XOJAdev | feat(gate): B2 - admission_gate moduli, pre_check, | `admission_gate.py` |
| 2026-10-16 | `69255c8b` | XOJAdev | feat(gate): B1 - rejected_items modeli va additiv  | `c1d2e3f4a5b6_create_rejected_items_table.py`<br>`__init__.py`<br>`rejected_item.py` |
| 2026-10-16 | `0c6c979e` | XOJAdev | feat(catalog): A2-A4 - oqish yollari yopildi, publ | `movies.py`<br>`series.py`<br>`movie_repo.py` (+1) |
| 2026-10-16 | `9ca99f30` | XOJAdev | feat(catalog): A1 - migratsiya va modellarda serve | `b3a1c2d4e5f6_add_publish_status_to_movies_and_series.py`<br>`movie.py`<br>`series.py` |
| 2026-10-16 | `89333e22` | XOJAdev | feat(catalog): BOSQICH 3 - publish_status ustunlar | `b3a1c2d4e5f6_add_publish_status_to_movies_and_series.py`<br>`movies.py`<br>`series.py` (+4) |
| 2026-10-16 | `12952fb3` | XOJAdev | feat(storage): BOSQICH 2 - JSON fayllar gitdan chi | `quarantine_items.json`<br>`quarantine_manager.py`<br>`queue_manager.py` (+3) |
| 2026-10-16 | `2eaaeefd` | XOJAdev | feat(scraper): BOSQICH 1 - FloodWait retry va stal | `queue_manager.py`<br>`run_scraper.py` |
| 2026-10-15 | `eff7f2e3` | XOJAdev | fix(deploy): enable universal web scraper availabi | Loyiha konfiguratsiyasi/Ops |
| 2026-10-15 | `85b85548` | XOJAdev | feat(catalog): add pagination controls with prev,  | `movie_repo.py`<br>`series_repository.py`<br>`catalog.py` |
| 2026-10-15 | `2d2c278e` | XOJAdev | feat(reports): add nosozlik haqida xabar button to | `reports.py`<br>`episode_sender.py`<br>`movie_sender.py` |
| 2026-10-15 | `18657254` | XOJAdev | fix(bot): ensure Ortga button and commands always  | `catalog.py`<br>`search.py`<br>`info_sender.py` |
| 2026-10-15 | `82862477` | XOJAdev | fix(bot): complete telegram inline search handler  | `search.py`<br>`code_resolver.py` |
| 2026-10-15 | `aea1f6f4` | XOJAdev | fix(audit,scraper,website): resolve audit tab erro | `quarantine_items.json`<br>`duplicate_checker.py`<br>`smart_enricher.py` (+1) |
| 2026-10-15 | `2fcab667` | XOJAdev | feat: complete audit cascade merge, bot profile UX | `profile.py`<br>`recommendation.py`<br>`reports.py` (+1) |
| 2026-10-15 | `5bd91505` | XOJAdev | feat(scraper): add Strict TMDb Reconciliation Gate | `channel_repo.py`<br>`auto_index.py`<br>`search.py` (+6) |
| 2026-10-15 | `50ba356e` | XOJAdev | feat: complete Autopilot 2.0 engine, Blacklist, Br | `movies.py`<br>`series.py`<br>`__init__.py` (+15) |
| 2026-10-14 | `4a02b422` | XOJAdev | feat(scraper): add Kurtlar Vadisi Pusu batch inges | `ingest_pusu.py` |
| 2026-10-14 | `6631f9a0` | XOJAdev | fix(scraper): protect franchise sequels and soften | `duplicate_checker.py`<br>`title_cleaner.py` |
| 2026-10-14 | `e0cbdacf` | XOJAdev | fix(scraper): fix series vs movie duplicate checki | `duplicate_checker.py`<br>`scraper_queue.json`<br>`telethon_moderator_pipeline.py` |
| 2026-10-13 | `0df4e820` | XOJAdev | fix(scraper): sync checkpoints and queue to stoppe | `scraper_queue.json`<br>`scraper_state.json` |
| 2026-10-12 | `3d52dc42` | XOJAdev | fix(scraper): add fallback api credentials and rob | `config.py`<br>`process_manager.py`<br>`telethon_moderator_pipeline.py` |
| 2026-10-11 | `6893b7e1` | XOJAdev | feat(audit): add content audit & quality control d | Loyiha konfiguratsiyasi/Ops |
| 2026-10-11 | `0543947e` | XOJAdev | feat: fix 18+ adult content detection, scraper mod | `info_sender.py`<br>`moderator_pipeline.py`<br>`queue_manager.py` (+3) |
| 2026-10-11 | `c34906ee` | XOJAdev | fix(anime): isolate anime from movies and series p | `movie_repo.py`<br>`series_repository.py`<br>`smart_enricher.py` (+1) |
| 2026-10-11 | `747749c8` | XOJAdev | fix(scraper): smart anime title detection, poster  | `fix_missing_sources_and_confirmations.py`<br>`smart_enricher.py`<br>`telethon_moderator_pipeline.py` |
| 2026-10-10 | `c570c9e1` | XOJAdev | feat: implement 18+ age verification and issue rep | `movies.py`<br>`__init__.py`<br>`movie.py` (+3) |
| 2026-10-10 | `a7d54273` | XOJAdev | fix(pipeline): harden series scraping with title v | `series_repository.py`<br>`telethon_moderator_pipeline.py` |
| 2026-10-10 | `30d75753` | XOJAdev | feat(scraper, admin): add AniToob and Animeelar an | `animeelar_catalog.json`<br>`animeelar_parser.py`<br>`anitoob_catalog.json` (+13) |
| 2026-10-10 | `0ce31da4` | XOJAdev | fix(scraper): auto-detect total episodes and compl | `duplicate_checker.py`<br>`resume_incomplete_anime.py`<br>`telethon_moderator_pipeline.py` |
| 2026-10-10 | `4d81128e` | XOJAdev | fix(scraper): resume incomplete series and prevent | `duplicate_checker.py`<br>`run_scraper.py`<br>`telethon_moderator_pipeline.py` |
| 2026-10-10 | `24780e27` | XOJAdev | fix(scraper): prevent cross-category duplicates an | `duplicate_checker.py`<br>`telethon_moderator_pipeline.py` |
| 2026-10-10 | `97b1a9a9` | XOJAdev | fix(scraper): fix episode translation repository c | `fast_telethon.py`<br>`scraper_queue.json`<br>`telethon_moderator_pipeline.py` |
| 2026-10-10 | `b5c84ba5` | XOJAdev | fix(scraper): support in-place message edits for k | `fast_telethon.py`<br>`run_scraper.py`<br>`telethon_moderator_pipeline.py` |
| 2026-10-10 | `c0a8a2ee` | XOJAdev | fix(pipeline): auto sponsor join, robust series vi | `duplicate_checker.py`<br>`run_scraper.py`<br>`telethon_moderator_pipeline.py` |

### 4. Oxirgi 5 Kundagi Modifikatsiya Vaqtlari (mtime) va Loglar Xronologiyasi
Loyihada topilgan `ops/logs/go_live_*.log` fayllari va untracked migratsiya skriptlari modifikatsiya vaqtlari asosida hodisa xronologiyasi quyidagicha tiklandi:

#### A. 2026-10-15: Qat'iy Filtrlash va Publish Status Joriy Qilinishi
- **Voqea**: Backendda `publish_status` va admission gate filtrlari qo'shildi. Barcha API endpointlari (`/movies`, `/series`) faqat `published` statusli kontentni qaytaradigan qilindi.
- **Oqibat**: Oldin yuklangan va statusi belgilanmagan yoki `pending` bo'lgan yuzlab kinolar bot va saytdan yo'qolib qoldi yoki 404 qaytara boshladi.

#### B. 2026-10-16 Kunduzi (15:45 - 19:42): Qayta-Qayta Reset va Yangi Zaxiralar Olinishi
- **15:45 - 15:53**: `ops/go_live.ps1` bir necha bor yurgizildi, `backups/kinochi_pre_reset_20261016_154506.dump` (hajmi 94 KB) olindi.
- **18:19 - 19:16**: Bazada katta o'zgarishlar yuz berdi. `backups/kinochi_pre_reset_20261016_183326.dump` (hajmi 1.67 MB) olindi. Bu vaqtda bazaga yirik miqdorda kontent kiritilgan.
- **19:15 - 19:42**: `go_live` loglarida xatolar qayd etildi, qayta ishga tushirildi.

#### C. 2026-10-16 Kechasi va 2026-10-17 Tonggi (01:00 - 04:00): Agent Tomonidan Ommaviy 'Migratsiya' Skriptlari Ishlatilishi
- **Voqea (CONFIRMED)**: Loyihada 110 dan ortiq `scripts/migrate_*.py` va `scripts/fix_*.py` fayllari yaratildi:
  - `scripts/migrate_all_movies_individual_topics.py`
  - `scripts/migrate_all_major_series.py`
  - `scripts/migrate_batch2_movies_individual_topics.py`
  - `scripts/migrate_anime_series.py`
  - `scripts/migrate_bleach.py`, `scripts/migrate_kurtlar_pusu.py`, `scripts/migrate_game_of_thrones.py` va boshqalar.
- **Natija**: Ushbu skriptlar orqali eski kanaldan olingan xabarlar superguruhdagi yangi topiclarga o'zboshimchalik bilan forward/copy qilindi va Telegram auto-index tinglovchisi (`auto_index.py`) barcha kelgan xabarlarni parallel ravishda bazaga yozdi.

### 5. Xulosa va Hodisaning Xronologik Xaritasi
```
2026-10-15: Publish Status & Gate joriy etildi -> Kontent ko'rinmay qoldi
2026-10-16 15:45: Birinchi Reset_media & Go_live (Baza tozalanishi)
2026-10-16 18:30: Qayta import urinishlari (1.67 MB li dump hosil bo'ldi)
2026-10-16 22:00 - 2026-10-17 03:30: AI Agent 'Sog'lom' kontentni ko'chirish uchun 100 dan ortiq skriptlarni ishga tushirdi
2026-10-17 03:36: Oxirgi go_live logi (go_live_20261017_033635.log)
2026-10-17 04:00: Egasi (owner) 1600 ta noto'g'ri, aralashib ketgan chiqindi media aniqladi va loyihani to'xtatdi.
```
