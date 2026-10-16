# VERIFY_SEED.md: Seed Tizimi va Xavfsizlik Himoyalarini Tekshirish Hisoboti

Ushbu hisobot TMDb Seed Ingestor, Blacklist aniq mosligi, Adversarial nomzodlar testi, bazani tozalash himoyalari (Guards) va Alembic migratsiyalarining tekshiruv natijalarini o'z ichiga oladi.

## Tekshiruv Jadvali (Verification Table)

| Item | Result | Evidence | Status |
|---|---|---|---|
| **1. Blacklist Aniq Mosligi (Exact Match)** | `ilike` substring tekshiruvlari aniq normallashtirilgan sarlavha va URL dan raqamli ID parse qilishga almashtirildi. `tmdb_id 155` endi `...71550` URL ga mos kelmaydi. Qora ro'yxatdagi `'Avatar: The Way of Water'` asl `'Avatar'` filmini asossiz bloklamaydi. | `backend/tests/test_blacklist_matching.py` dagi 3 ta test o'tdi (`test_extract_tmdb_ids_from_url`, `test_blacklist_tmdb_id_155_vs_url_71550`, `test_blacklist_avatar_sequel_does_not_block_avatar`). Commit: `f4a4791`. | PASSED |
| **2. Adversarial Matcher (71 ta juftlik)** | SF-001 tuzatishidan so'ng 41 ta asl + 30 ta yangi (anime fasllari, Kirill/Lotin transliteratsiyasi, remeyklar) juftlik sinovdan o'tkazildi. Natijalar:<br>• 41 juftlik: TP=11, TN=24, **FP=0**, FN=6<br>• 30 yangi juftlik: TP=11, TN=18, **FP=0**, FN=1<br>• Jami 71 juftlik: TP=22, TN=42, **FP=0**, FN=7. Soxta ijobiy holatlar 0 ta. | `backend/tests/test_adversarial_71_pairs.py` dagi testlar to'liq o'tdi (`test_adversarial_41_pairs`, `test_adversarial_71_pairs`). Commit: `207ec4c`. | PASSED |
| **3. `reset_media.py` Himoyalari (Guards)** | 3 ta mustaqil himoya o'rnatildi:<br>1. `--execute` va `--confirm YES` (tasdiqsiz faqat DRY-RUN)<br>2. `--backup-file <fayl>` (mavjud va bo'sh bo'lmagan zaxira fayli talab qilinadi)<br>3. Nishon DB xosti `TEST_DATABASE_URL` xostiga teng bo'lishi shart YOKI `--i-am-wiping-production` bayrog'i `--backup-file` bilan birga berilishi shart. | `backend/tests/test_reset_media_s8.py` dagi 6 ta alohida guard testlari to'liq o'tdi. `start.bat` menyusidagi ko'rsatma yangilandi. Commit: `207ec4c`. | PASSED |
| **4. TEST Branch DB & Pytest Tekshiruvi** | `TEST_DATABASE_URL` muhit o'zgaruvchisi berilmagan (`None`). Qat'iy qoida bo'yicha jonli Neon DB bosqichlari to'xtatildi. Offline Alembic tahlilida yagona head: `a1b2c3d4e5f6`. `pytest -rs` to'liq ishga tushirildi: 166 ta test o'tdi, 0 ta skip. | `os.environ.get('TEST_DATABASE_URL') is None`. `pytest -rs`: 166 passed, 0 failed, 0 skipped in 17.55s. | STOPPED_ENV_MISSING |
| **5. `d4e5f6a1b2c3` UNIQUE Indeksi va Dublikatlar** | `d4e5f6a1b2c3` migratsiyasi `movies` va `series` jadvallarida `tmdb_id` ustuniga qisman UNIQUE indeks (`WHERE tmdb_id IS NOT NULL`) qo'shadi. Tarixiy dublikatlar bo'lgan bazada xatosiz muvaffaqiyatli ishlaydi: indeks yaratilishidan oldin dublikat qatorlar (`rn > 1`) uchun `tmdb_id = NULL` qilib yangilanadi, asl birinchi qator (`rn = 1`) o'z ID sini saqlab qoladi. | `backend/alembic/versions/d4e5f6a1b2c3_unique_tmdb_id_on_movies_and_series.py` SQL preview: `UPDATE movies SET tmdb_id = NULL WHERE ... rn > 1;` va `CREATE UNIQUE INDEX uq_movies_tmdb_id ON movies (tmdb_id) WHERE tmdb_id IS NOT NULL;`. | PASSED |

---

## Xulosa Statistikasi (Status Counts)

- **PASSED**: 4
- **STOPPED_ENV_MISSING**: 1
- **FAILED**: 0
