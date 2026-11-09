# Slice Report: 2026-11-09-f1-s67-mediaplus-crud-consolidation

## What was done
1. Resolved `series.py` seasons and episodes `publish_status` blocking bug by connecting `list_seasons`, `get_season`, and `list_episodes` to `resolve_publish_status`, enabling admin panel access to pending series.
2. Added missing CRUD operations: movie translation update (`PUT /movies/translations/{id}`), broadcast draft update (`PUT /broadcasts/{id}`) and deletion (`DELETE /broadcasts/{id}`), review moderation deletion (`DELETE /reviews/{id}`) and global feed (`GET /reviews/admin`), and watch history user deletion (`DELETE /users/me/history/{id}`, `DELETE /users/me/history`, `DELETE /users/by-telegram/{telegram_id}/history`).
3. Built new `admin-panel/app/users/page.tsx` with user search and 1-click ban/unban controls, added "Foydalanuvchilar" to admin sidebar, added broadcast delete button adhering to Cinematic Red standard, and cleaned empty conflicting directory `admin-panel/app/series/[id]`.
4. Telegram Bot Synchronizations (resolving user screenshot issues):
   - Eliminated duplicate buttons (`📁 Kino`, `📁 Serial`, `📁 Filmlar`) from `/katalog` by applying strict deduplication in `bot/keyboards/inline.py` and reorganizing grid row layout into `[2, 1, 2..., 1]`.
   - Built `bot/middlewares/ban_check.py` to block banned users from sending messages or triggering callbacks with informative alert.
   - Connected `submit_report` in `api_client` and `reports.py` to pass `telegram_user_id` to `/reports`.
   - Integrated watch history clearance in `bot/handlers/profile.py` with confirmation dialog and automatic profile refresh.
5. Verified with 18 automated backend CRUD tests and 87 automated bot tests (100% GREEN pass rate).

## Changed files
- `backend/app/api/v1/series.py` - Connected `publish_status: Depends(resolve_publish_status)` to `list_seasons`, `get_season`, and `list_episodes`.
- `backend/app/api/v1/movies.py` - Added `UpdateMovieTranslationRequest` and `update_movie_translation` endpoint.
- `backend/app/application/movies/service.py` - Added `update_movie_translation`.
- `backend/app/infrastructure/db/repositories/movie_repo.py` - Added `update_translation`.
- `backend/app/api/v1/broadcasts.py` - Added `BroadcastUpdate` schema, `update_broadcast`, and `delete_broadcast` endpoints.
- `backend/app/application/broadcasts/service.py` - Added `update_broadcast` and `delete_broadcast`.
- `backend/app/infrastructure/db/repositories/broadcast_repo.py` - Added `update` and `delete`.
- `backend/app/domain/broadcasts/repository.py` - Added protocol definitions for `update` and `delete`.
- `backend/app/core/reviews.py` - Added `delete_review` with auto-recalculation of ratings, and `list_admin_reviews`.
- `backend/app/api/v1/reviews.py` - Added `remove_review` and `get_admin_reviews`.
- `backend/app/api/v1/users.py` - Added `delete_history_item`, `clear_my_history`, and `clear_user_history_by_telegram`; added `is_banned` to user summary.
- `admin-panel/app/users/page.tsx` - Created new Users management page with search, stats, and ban/unban.
- `admin-panel/components/Sidebar.tsx` - Added "Foydalanuvchilar" to navigation.
- `admin-panel/app/broadcasts/page.tsx` - Added delete button and fixed Cinematic Red design standard.
- `bot/keyboards/inline.py` - Deduplicated catalog pages and standardized layout.
- `bot/handlers/catalog.py` - Dynamic page title resolution.
- `bot/middlewares/ban_check.py` - Created BanCheckMiddleware.
- `bot/main.py` - Registered BanCheckMiddleware.
- `bot/services/api_client.py` - Added `check_user_banned`, `clear_user_history`, and `telegram_user_id` support in `submit_report`.
- `bot/handlers/reports.py` - Passed `telegram_user_id` when reporting.
- `bot/handlers/profile.py` - Added watch history clearing flow.
- `bot/handlers/start.py` - Added banned check on `/start`.
- `backend/tests/test_series_publish_status_admin_access.py` - TDD suite for series/season publish status.
- `backend/tests/test_movie_translation_update.py` - TDD suite for movie translation update.
- `backend/tests/test_broadcast_crud_update_delete.py` - TDD suite for broadcast update and delete.
- `backend/tests/test_review_moderation_crud.py` - TDD suite for review moderation.
- `backend/tests/test_watch_history_delete_crud.py` - TDD suite for user watch history deletion.
- `backend/tests/test_telegram_history_clear_endpoint.py` - TDD suite for bot telegram history delete & is_banned summary.
- `bot/tests/test_ban_middleware_sync.py` - TDD suite for ban middleware.
- `bot/tests/test_profile_history_clear_sync.py` - TDD suite for profile history clear button & flow.
- `bot/tests/test_report_submission_tg_id_sync.py` - TDD suite for report telegram user id submission.
- `bot/tests/test_catalog_keyboards_sync.py` - TDD suite for catalog deduplication.

## check output
```text
=== Bot Test Suite ===
============================= 87 passed in 5.98s ==============================

=== Backend CRUD Test Suite ===
backend\tests\test_telegram_history_clear_endpoint.py ...                [ 16%]
backend\tests\test_watch_history_delete_crud.py ...                      [ 33%]
backend\tests\test_review_moderation_crud.py ...                         [ 50%]
backend\tests\test_broadcast_crud_update_delete.py ....                  [ 72%]
backend\tests\test_movie_translation_update.py ..                        [ 83%]
backend\tests\test_series_publish_status_admin_access.py ...             [100%]

======================= 18 passed, 23 warnings in 3.40s =======================
```

## Risks and unknowns
- When reviewing or deleting spam reviews, if a review has already factored into Kinochi score, `delete_review` recalculates the average score in a single atomic transaction.
- Admin Panel on port 3001 should be refreshed to render the newly added "Foydalanuvchilar" navigation item.

## Concept to explain to the user
- Atomik CRUD va Bog'liqlik Izolyatsiyasi (Atomic CRUD & Contextual Isolation): Tizimdagi har bir resurs (xoh xabarnoma, xoh izoh, xoh tarjima bo'lsin) to'liq 4 ta mustaqil operatsiyaga (Yaratish, O'qish, Tahrirlash, O'chirish) ega bo'lishi kerak. Biri etishmasa (masalan faqat qo'shish bor-u, o'chirish yo'q bo'lsa), tizim vaqt o'tishi bilan "o'lik ma'lumotlar" bilan to'lib, ma'muriy boshqaruv izdan chiqadi.

## Next step
- Launch Admin Panel and verify new `/users` screen and broadcast deletion in live browser session.
