# KINOCHI STABILIZATION ISSUE REGISTRY

**Loyiha:** Kinochi Full Ecosystem Stabilization  
**Hujjat:** Master Issue Registry  
**Oxirgi yangilanish:** 2026-11-14  

---

## 1. ISSUE REGISTRY STATUS OVERVIEW

| Flow | Umumiy | P0 | P1 | P2 | P3 | OPEN | IN_PROGRESS | BLOCKED | VERIFIED_FIX |
|---|---|---|---|---|---|---|---|---|---|
| **FLOW 1: GUEST** | 6 | 2 | 2 | 2 | 0 | 0 | 0 | 0 | 6 |
| **FLOW 2: USER** | 4 | 0 | 2 | 2 | 0 | 0 | 0 | 0 | 4 |
| **FLOW 3: ADMIN** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **FLOW 4: BOT** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **FLOW 5: BACKEND** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **FLOW 6: INTEGRATION** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **FLOW 7: UI/UX** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **FLOW 8: REGRESSION** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **JAMI** | **10** | **2** | **4** | **4** | **0** | **0** | **0** | **0** | **10** |

---

## 2. FLOW 1: GUEST ISSUES

### GUEST-ISSUE-001 — Movie Search NameError (P0)
- **Flow:** Flow 1 (Guest)
- **Modul:** Backend / Search
- **Fayl:** `backend/app/infrastructure/db/repositories/movie_repo.py:341`
- **Severity:** P0 Blocker
- **Root Cause:** Missing `import re` caused `NameError: name 're' is not defined` when executing regex splitting for search queries.
- **Reproduction:** `GET /api/v1/movies/search?q=kino` returned HTTP 500.
- **Evidence:** Pytest failure `tests/audit2/test_guest_flow_repair.py::test_guest_issue_001_movie_search_no_name_error`.
- **Fix Description:** Added `import re` to top-level imports in `movie_repo.py`.
- **Test Reference:** `tests/audit2/test_guest_flow_repair.py:14` (PASSED). Live query returns 36 results.
- **Verification:** HTTP 200, search results return expected movies without exception.
- **Status:** `VERIFIED_FIX` (Commit `9877842`)

---

### GUEST-ISSUE-002 — Collections N+1 DB Queries & 15s Timeout (P0)
- **Flow:** Flow 1 (Guest)
- **Modul:** Backend / Collections
- **Fayl:** `backend/app/api/v1/collections.py:185-235`
- **Severity:** P0 Blocker
- **Root Cause:** Nested loops for each collection item issuing individual `count` and `item` queries, combined with eager `selectinload` on `CollectionModel` relationships (`movies`, `categories`, `translations`, `pages`). 5 collections triggered 37 queries over the wire.
- **Reproduction:** Calling `GET /api/v1/collections` exceeded HTTP client timeouts (15s).
- **Evidence:** `AssertionError: Expected <= 4 DB queries, but executed 37 queries`.
- **Fix Description:** Applied `noload(CollectionModel.items), noload(CollectionModel.subscriptions)`. Batched collection item counts via single grouped query (`GROUP BY collection_id`). Batched top 3 preview posters using window function (`ROW_NUMBER() OVER (PARTITION BY collection_id ORDER BY chronological_order ASC)`). Reduced queries to O(1) (exactly 3 queries total).
- **Test Reference:** `tests/audit2/test_guest_flow_repair.py:44` (PASSED in 1.93s).
- **Verification:** `backend/tests/test_filter_collections_item_count.py` passed with 100%.
- **Status:** `VERIFIED_FIX` (Commit `422be3c`)

---

### GUEST-ISSUE-003 — TelegramWatchButton Fake Success Dispatch Message (P1)
- **Flow:** Flow 1 (Guest)
- **Modul:** Website / Media Actions
- **Fayl:** `website/components/TelegramWatchButton.tsx:230-246`
- **Severity:** P1 High
- **Root Cause:** Modal claimed "Muvaffaqiyatli yuborildi!" and "Telegram botingizga video fayl va tomosha qilish havolasi yuborildi" when only a client-side deep-link was triggered without bot confirmation.
- **Reproduction:** Clicking "Telegram orqali ko'rish" showed fake dispatch message before bot interaction.
- **Evidence:** Playwright test asserting absence of fake claims failed.
- **Fix Description:** Replaced fake success chip with `#229ED9` branded badge `Telegram bot ochilmoqda`, modal title `Telegram botda davom eting`, and clear instructions to tap Start in Telegram.
- **Test Reference:** `website/tests/telegram_watch_modal.spec.ts` (PASSED in 954ms).
- **Verification:** Modal copy accurately reflects client deep-link initiation.
- **Status:** `VERIFIED_FIX` (Commit `05d4216`)

---

### GUEST-ISSUE-004 — Bot Misleading "Video yuklanmoqda..." When Media Has No Video (P1)
- **Flow:** Flow 1 (Guest)
- **Modul:** Telegram Bot / Browsing Handlers
- **Fayl:** `bot/handlers/browsing.py:34, 60`
- **Severity:** P1 High
- **Root Cause:** When `send_movie_to_user` or `send_episode_to_user` returned `False` due to empty `translations` (no video file attached), bot displayed misleading `"⏳ Video yuklanmoqda..."` as if background ingestion was running.
- **Reproduction:** Clicking "Ko'rish" on a catalog item with no uploaded video displayed fake loading message.
- **Evidence:** Pytest failure in `bot/tests/test_browsing_missing_video.py` asserting absence of "Video yuklanmoqda".
- **Fix Description:** Explicitly checked `movie.get("translations")` and `episode.get("translations")` to truthfully reply `"⚠️ Ushbu film uchun video fayl hali yuklanmagan."` or report sending errors honestly.
- **Test Reference:** `bot/tests/test_browsing_missing_video.py` (2 passed in 3.93s). All 98 bot tests passed.
- **Verification:** Truthful message displayed when video translations are absent.
- **Status:** `VERIFIED_FIX` (Commit `b5e0b9c`)

---

### GUEST-ISSUE-005 — Hardcoded Continue Watching Progress Percentages (P2)
- **Flow:** Flow 1 (Guest)
- **Modul:** Website / Continue Watching
- **Fayl:** `website/components/home/ContinueWatchingSection.tsx:61, 74, 117`
- **Severity:** P2 Medium
- **Root Cause:** Code hardcoded synthetic `55%`, `65%`, and `60%` progress values for items lacking second-by-second playback state.
- **Reproduction:** Any item in continue watching had hardcoded 60% progress regardless of actual watch state.
- **Evidence:** Playwright test failure `Expected undefined, Received: 60`.
- **Fix Description:** Preserved real numeric progress if provided, otherwise left progress undefined and rendered clean `Davom etmoqda` status badge.
- **Test Reference:** `website/tests/continue_watching_sync.spec.ts` (4 passed in 1.6s).
- **Verification:** Clean `Davom etmoqda` status badge without synthetic percentages.
- **Status:** `VERIFIED_FIX` (Commit `6f5026e`)

---

### GUEST-ISSUE-006 — Diagnostic `/test-auth` Route Exposed in Production (P2 Security)
- **Flow:** Flow 1 (Guest)
- **Modul:** Website / Routing & Security
- **Fayl:** `website/app/test-auth/page.tsx:1-16`
- **Severity:** P2 Security
- **Root Cause:** Diagnostic authentication status page displaying raw tokens and session details was accessible without environment restrictions.
- **Reproduction:** Navigating to `/test-auth` in production rendered auth tokens and user details.
- **Evidence:** Playwright test asserting presence of `notFound()` guard failed.
- **Fix Description:** Added `if (process.env.NODE_ENV === "production") { notFound(); }` guard at top of component.
- **Test Reference:** `website/tests/auth_security.spec.ts` (PASSED in 910ms).
- **Verification:** Route triggers standard Next.js 404 in production mode.
- **Status:** `VERIFIED_FIX` (Commits `22bda32`, `815515d`)

---

## 3. FLOW 2: USER ISSUES (AUTHENTICATED USER)

### USER-ISSUE-001 — Incomplete Logout Session Leak (P1 Security)
- **Flow:** Flow 2 (User)
- **Modul:** Auth & Session Lifecycle
- **Fayl:** `backend/app/api/v1/auth.py:75`, `backend/app/api/v1/telegram_auth.py`, `website/lib/auth/AuthProvider.tsx:125`
- **Severity:** P1 High / Security
- **Root Cause:** `telegram_auth.py` sets httpOnly cookie `user_access_token`. On logout, `website/lib/auth/AuthProvider.tsx` only removes `localStorage` token, and `backend/app/api/v1/auth.py:logout` does not clear `user_access_token`. `deps.py:get_current_user` checks cookie first, meaning subsequent cookie-based requests remain authenticated after logout.
- **Reproduction:** User logs in, user clicks "Chiqish" (Logout). Cookie `user_access_token` remains in browser and `/api/v1/users/me` still succeeds via cookie.
- **Evidence:** Browser cookie storage inspection and API call without Authorization header but with cookie.
- **Fix Description:**
  1. Add `user_access_token` deletion to `_clear_auth_cookies` in `backend/app/api/v1/auth.py`.
  2. Add `@router.post("/logout")` in `backend/app/api/v1/telegram_auth.py` that clears `user_access_token`.
  3. In `website/lib/auth/AuthProvider.tsx`, call `POST /auth/logout` and remove `user_access_token` cookie on logout.
- **Test Reference:** `tests/audit2/test_user_flow_repair.py:14` (PASSED in 1.87s).
- **Verification:** Set-Cookie header contains `user_access_token=; Max-Age=0; Path=/; SameSite=lax`.
- **Status:** `VERIFIED_FIX` (Commit `cd3d3e4`)

---

### USER-ISSUE-002 — History Endpoint Total Count Returns Page Size (P1 Functional)
- **Flow:** Flow 2 (User)
- **Modul:** Backend / Watch History
- **Fayl:** `backend/app/api/v1/users.py:151`
- **Severity:** P1 High
- **Root Cause:** `GET /users/me/history` hardcodes `"total": len(items)` instead of querying the true total count of history records for the user (`select(func.count(WatchHistoryModel.id)).where(...)`).
- **Reproduction:** A user with 25 history records requesting `?limit=20` receives `"total": 20`, breaking frontend pagination controls.
- **Evidence:** Code comment explicitly says `# Accurate total requires a separate count query, simplified for now.`
- **Fix Description:** Execute `func.count(WatchHistoryModel.id)` query filtered by `user_id` and return true total.
- **Test Reference:** `tests/audit2/test_user_flow_repair.py:46` (PASSED in 2.08s).
- **Verification:** True count of all user records is returned regardless of `limit` or `offset`.
- **Status:** `VERIFIED_FIX` (Commit `d32f2b4`)

---

### USER-ISSUE-003 — Dead Notification Settings Label in Profile (P2 UX)
- **Flow:** Flow 2 (User)
- **Modul:** Website / User Profile Settings
- **Fayl:** `website/app/profile/page.tsx:701-714`
- **Severity:** P2 Medium
- **Root Cause:** Settings tab shows a static label `<span className="text-xs text-emerald-400 font-bold">Yoqilgan</span>` without an interactive toggle or preference persistence.
- **Reproduction:** Clicking the notification badge in profile settings does nothing.
- **Evidence:** Code inspection of `website/app/profile/page.tsx:711`.
- **Fix Description:** Implement an interactive toggle switch stored in `localStorage` (`kinochi_notifications_enabled`), with immediate visual feedback and toast confirmation.
- **Test Reference:** `website/tests/profile_ux.spec.ts:9` (PASSED).
- **Verification:** Interactive toggle button updates state and renders on/off appropriately.
- **Status:** `VERIFIED_FIX` (Commit `a5455bf`)

---

### USER-ISSUE-004 — Dead Favorites Tab Reading Non-Existent `kinochi_favorites` (P2 UX)
- **Flow:** Flow 2 (User)
- **Modul:** Website / Profile Favorites Tab
- **Fayl:** `website/app/profile/page.tsx:163, 451-482`
- **Severity:** P2 Medium
- **Root Cause:** Tab 2 (Favorites) reads from `kinochi_favorites` and tells users `O'zingizga yoqqan kinolarni "+ Sevimlilarga" tugmasi orqali saqlab qo'yishingiz mumkin.`, but no "+ Sevimlilarga" button exists anywhere on movie/series cards.
- **Reproduction:** Navigating to `profile?tab=favorites` always shows empty state with instructions for a non-existent button.
- **Evidence:** Full-codebase search reveals `kinochi_favorites` is never written to anywhere.
- **Fix Description:** Update Favorites tab to clearly explain that saving and tracking is handled via Subscriptions ("Obunalar") with a one-click CTA to view and manage subscribed series and franchises, removing the phantom "+ Sevimlilarga" instruction.
- **Test Reference:** `website/tests/profile_ux.spec.ts:15` (PASSED).
- **Verification:** Empty state renders helpful Subscriptions explanation and navigation CTA without phantom button reference.
- **Status:** `VERIFIED_FIX` (Commit `a5455bf`)

