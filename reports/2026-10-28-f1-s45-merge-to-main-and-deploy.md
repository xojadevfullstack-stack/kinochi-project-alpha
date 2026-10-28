# Slice Report: 2026-10-28-f1-s45-merge-to-main-and-deploy

## What was done
1. Pushed branch `v2-f1-catalog-and-ux`, fixed a Vercel type error (`Episode.display_code`), then fast-forward merged into `main` and pushed `6b27bbc..248e6b3`.
2. Verified before merge: 28 UI tests passed, `tsc --noEmit` clean, lint 0 errors. Probed the live backend: `content_requests` (4 rows) and `broadcasts` already exist in prod, so no migration is needed.
3. Paused at the user's request. State saved in `STATE.md`, `docs/failures.md` (Failure 007).

## Changed files
- `website/components/media/SeasonEpisodesSection.tsx` - added optional `display_code` to `Episode`
- `STATE.md` - F1-S45 entry, paused status, open question
- `docs/failures.md` - Failure 007
- `reports/2026-10-28-f1-s45-merge-to-main-and-deploy.md` - this report

## check output
```text
pytest (UI + catalog suites): 28 passed, 0 failed
tsc --noEmit -p website/tsconfig.json: exit 0, no output
npm run lint: 0 errors (warnings only, pre-existing)
git push origin main: 6b27bbc..248e6b3 main -> main
Live backend probe (before deploy): /movies 200 (18), /series 200 (11), /categories 200 (35), /content-requests 200 (4), /actors 404 (old backend)
```
`make check` was not run in this slice; the commands above were run individually.

## Risks and unknowns
- UNKNOWN: whether Render finished redeploying the new backend (watcher stopped).
- The 7 F0 commits reach prod for the first time (asyncpg pooler settings, Telegram throttle). They passed local tests only.
- HYPOTHESIS: Vercel Preview env `NEXT_PUBLIC_API_URL` points to the dead host `kinochi-project-alpha.onrender.com` (503).
- 2 frozen baseline test failures from F0 remain (ADR-007); the CI run on `main` may show them red.

## Concept to explain to the user
- Fast-forward merge: `main` simply moves forward to the branch tip with no merge commit, because the branch is a direct descendant. Analogy: moving the "current page" bookmark forward in a book without adding a new page.

## Next step
- Probe `/api/v1/actors` on the live backend until it returns 200, then re-check the five core endpoints.
