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
| **FLOW 3: ADMIN** | 3 | 0 | 1 | 2 | 0 | 0 | 0 | 0 | 3 |
| **FLOW 4: BOT** | 2 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 2 |
| **FLOW 5: BACKEND** | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 1 |
| **FLOW 6: INTEGRATION** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **FLOW 7: UI/UX** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **FLOW 8: REGRESSION** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **JAMI** | **16** | **2** | **6** | **8** | **0** | **0** | **0** | **0** | **16** |

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

---

## 4. FLOW 3: ADMIN ISSUES

### ADMIN-ISSUE-001 — Incomplete Admin Logout Session Leak (P1 Security)
- **Flow:** Flow 3 (Admin)
- **Modul:** Admin Shell & Sidebar Auth Lifecycle
- **Fayl:** `admin-panel/components/AdminShell.tsx:45`, `admin-panel/components/Sidebar.tsx:37`
- **Severity:** P1 High / Security
- **Root Cause:** When an admin clicks "Chiqish", only `access_token` is removed from `localStorage` and cookie. `refresh_token` is left in `localStorage`. If `getOrRefreshToken()` in `lib/api.ts` is called afterwards, it uses `localStorage.getItem("refresh_token")` to call `POST /auth/refresh`, automatically issuing a new `access_token` and resurrecting the authenticated admin session. Also, both components hardcode `const API_URL = "/api/v1"` instead of importing `API_URL` from `@/lib/api`.
- **Reproduction:** Admin logs in, clicks Logout. `localStorage.getItem("refresh_token")` still exists. Calling `fetchApi("/statistics/dashboard")` automatically re-authenticates without credentials.
- **Evidence:** Inspection of `AdminShell.tsx` and `Sidebar.tsx` shows `localStorage.removeItem("refresh_token")` is missing.
- **Fix Description:**
  1. In both `AdminShell.tsx` and `Sidebar.tsx`, import `API_URL` from `@/lib/api`.
  2. On logout, call `POST ${API_URL}/auth/logout` with `credentials: "include"`.
  3. Remove both `access_token` and `refresh_token` from `localStorage`.
  4. Explicitly delete cookie `access_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT`.
- **Test Reference:** `website/tests/admin_panel.spec.ts:9` (PASSED in 17ms).
- **Verification:** Both `localStorage.removeItem("refresh_token")` and `import { API_URL } from "@/lib/api"` verified in code and unit test.
- **Status:** `VERIFIED_FIX`

---

### ADMIN-ISSUE-002 — Sources Router Trailing Slash Inconsistency causing 307 Redirects (P2 Functional)
- **Flow:** Flow 3 (Admin)
- **Modul:** Backend / Sources Router
- **Fayl:** `backend/app/api/v1/sources.py:11, 19`
- **Severity:** P2 Medium
- **Root Cause:** `sources.py` declared `@router.get("/")` and `@router.post("/")` while included with prefix `/api/v1/sources`. All other routers use `""`. Requesting `GET /api/v1/sources` or `POST /api/v1/sources` from `admin-panel/app/sources/page.tsx:27, 92` triggered an HTTP 307 Temporary Redirect instead of returning directly.
- **Reproduction:** `GET /api/v1/sources` returns HTTP 307 with `Location: /api/v1/sources/`.
- **Evidence:** Terminal curl or test requesting `/api/v1/sources` returns status 307.
- **Fix Description:** Add `@router.get("")` and `@router.post("")` routes in `sources.py` (with `/` as backward-compatible aliases) to eliminate unnecessary redirects.
- **Test Reference:** `tests/audit2/test_admin_flow_repair.py:10` (PASSED in 2.11s).
- **Verification:** `GET /api/v1/sources` and `POST /api/v1/sources` return 200/201 directly without 307 status code.
- **Status:** `VERIFIED_FIX`

---

### ADMIN-ISSUE-003 — Legacy "MediaPlus" Branding in Admin Layout and Login (P2 Consistency)
- **Flow:** Flow 3 (Admin)
- **Modul:** Admin Panel Layout & Login
- **Fayl:** `admin-panel/app/layout.tsx:10-11`, `admin-panel/app/login/page.tsx:72`
- **Severity:** P2 Medium / Identity
- **Root Cause:** Leftover "MediaPlus Admin Panel" metadata and "MediaPlus Admin" heading from previous generation violating Kinochi platform identity.
- **Reproduction:** Inspect browser tab title on admin panel (`MediaPlus Admin Panel`) and login screen heading.
- **Evidence:** `admin-panel/app/layout.tsx` metadata and `admin-panel/app/login/page.tsx` line 72.
- **Fix Description:** Update metadata title to "Kinochi Admin Panel" and heading to "Kinochi Admin".
- **Test Reference:** `website/tests/admin_panel.spec.ts:25` (PASSED in 5ms).
- **Verification:** No occurrences of "MediaPlus" remain in layout or login headings; branded as "Kinochi Admin".
- **Status:** `VERIFIED_FIX`

---

## 5. FLOW 4: BOT ISSUES

### BOT-ISSUE-001 — Welcome Message Legacy Branding (P2 Identity)
- **Flow:** Flow 4 (Telegram Bot)
- **Modul:** Bot Start Handler
- **Fayl:** `bot/handlers/start.py:89`
- **Severity:** P2 Medium / Identity
- **Root Cause:** In `/start` without deep-link parameters, welcome message hardcoded `"👋 <b>MediaPlus botiga xush kelibsiz!</b>\n\n"`.
- **Reproduction:** Sending `/start` to the bot greets user with "MediaPlus botiga xush kelibsiz!".
- **Evidence:** Code inspection of `bot/handlers/start.py:89`.
- **Fix Description:** Update greeting to `"👋 <b>Kinochi botiga xush kelibsiz!</b>\n\n"`.
- **Test Reference:** `bot/tests/test_bot_flow_repair.py:8` (PASSED in 4.04s).
- **Verification:** Welcome text strictly contains "Kinochi" and zero references to obsolete "MediaPlus".
- **Status:** `VERIFIED_FIX`

---

### BOT-ISSUE-002 — Fake "Tez kunda" Placeholder on Recommendation Query (P1 Functional)
- **Flow:** Flow 4 (Telegram Bot)
- **Modul:** Bot Search Handler & Recommendation Integration
- **Fayl:** `bot/handlers/search.py:31-33`
- **Severity:** P1 High / Functional
- **Root Cause:** When user types or clicks `"🎲 Tavsiya kino"`, `search.py` intercepted it with a fake placeholder: `"🔥 <b>Tez kunda...</b>\n\nSiz uchun maxsus tavsiyalar, yilning eng qizg'in premyeralari ro'yxatini tayyorlayapmiz!..."`, even though a full recommendation engine already exists in `bot/handlers/recommendation.py`.
- **Reproduction:** Sending message `"🎲 Tavsiya kino"` or `"🎲 Tavsiya"` returns placeholder "Tez kunda" message.
- **Evidence:** `search.py:31-33`.
- **Fix Description:** Intercept recommendation text intent and display the real recommendation menu (`InlineKeyboardMarkup` with AI personal, movies, series, dynamic pages, and random) directly to the user.
- **Test Reference:** `bot/tests/test_bot_flow_repair.py:29` (PASSED in 4.04s).
- **Verification:** Actionable inline keyboard with real recommendation choices displayed; no placeholder text.
- **Status:** `VERIFIED_FIX`

---

## 6. FLOW 5: BACKEND ISSUES

### BACKEND-ISSUE-001 — Unlogged Swallowed Exceptions (P2 Quality)
- **Flow:** Flow 5 (Backend / API / DB)
- **Modul:** Core Error Handling
- **Fayl:** `backend/app/api/v1/reports.py:513`, `backend/app/api/v1/scraper.py:217`, `backend/app/main.py:55`, `backend/app/core/cache.py:21`
- **Severity:** P2 Medium / Quality
- **Root Cause:** Bare `except Exception: pass` blocks without logging or tracking silently swallowed errors during file cleanup, config checks, and state retrieval, violating the project constitution's zero-swallowed-exceptions rule.
- **Reproduction:** Inspection of backend code reveals 4 unlogged `except Exception: pass` statements.
- **Evidence:** Code lines in `reports.py`, `scraper.py`, `main.py`, and `cache.py`.
- **Fix Description:** Replace silent `pass` blocks with structured `logger.warning(...)` or `logger.debug(...)` calls.
- **Test Reference:** `tests/audit2/test_backend_flow_repair.py:4` (PASSED in 0.03s).
- **Verification:** Regex validation confirms 0 bare unlogged `except Exception: pass` blocks in target files.
- **Status:** `VERIFIED_FIX`




