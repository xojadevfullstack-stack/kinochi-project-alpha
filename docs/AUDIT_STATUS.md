# KINOCHI — Audit & v.NEXT Cycle Status (2026-08-01)

## ✅ Resolved & verified with real evidence

**Original priority question — uvloop / Neon IPv6 DNS latency**
- Confirmed via real production logs (Render): DB engine creation ~1.20s, connection ping ~0.34s.
- Local 7.3s delay explained by geographic RTT (Tashkent ↔ us-east-1) + cold TLS handshake against Neon's **Direct** (non-pooled) endpoint.
- Production is fast enough that this is no longer an active problem, though the root cause (Direct endpoint, no pgbouncer pooling) is still technically present — see backlog.

**Phase 1 — Hotfixes**
- Bot HTML escape: all `parse_mode="HTML"` call sites audited and fixed. Test suite: 40/40 passed.
- Next.js build: `force-dynamic` applied to `/movies` and `/series` routes. `npm run build` — 0 errors, confirmed via real build log.

**Phase 2 — Bot rate limiting**
- Redis-backed throttling middleware (`bot/middlewares/throttling.py`), applied to `/start`, search, catalog. `BOT_RATE_LIMIT_PER_MINUTE` env var (default 20). Test: 1/1 passed.

**Phase 3 — Trailer auto-detection**
- `parse_trailer_url()` handles YouTube (both formats), Telegram (`t.me/`), MP4 (HEAD check, 5s timeout, graceful 400 on failure).
- Verified with 5 real inputs + real output log (including URL normalization confirmed compatible with frontend `TrailerModal.tsx`).
- Telegram trailer delivery uses `bot.copy_message()` (cleaner than forward — no "Forwarded from" tag).

**Phase 4 — Cache & lint**
- Redis catalog cache: 5 min TTL, invalidated on create/update/delete. Verified: cache-miss 7.34s → cache-hit 0.003s (2447x) locally, with `redis-cli` key confirmation.
- ESLint configured (`next/core-web-vitals` + `@typescript-eslint/recommended`). 0 errors, 6 unused-var warnings only.

## 🟡 Known backlog (deliberately deferred, not blocking)

| Item | Status | Note |
|---|---|---|
| Bot `getUpdates` conflict on deploy (~17s) | Deferred by decision | Self-recovers via aiogram retry; revisit if deploy frequency increases or user complaints appear |
| Neon Direct endpoint (not pooled) | Latent risk | Fine at current traffic; revisit if connection churn/cold-starts increase |
| 6 unused-var lint warnings | Low priority | Non-blocking |
| `GET /` returns 404 | Unconfirmed | Verify Render's health-check path isn't pointed at `/` |

## ⚠️ Not yet manually verified in production
- Trailer button real Telegram send (`copy_message`) against a real channel post
- Rate-limiting middleware under real concurrent user traffic (only unit-tested)
