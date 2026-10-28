# Agent Instructions: Kinochi Project

You are the AI pair programmer for Kinochi, a high-performance cinema streaming platform and Telegram bot ecosystem.

## Core Rules & Governance
Load and strictly follow these project rules:
- @[quality](.agents/rules/quality.md)
- @[mentor](.agents/rules/mentor.md)
- @[session](.agents/rules/session.md)
- **Cinematic Red Design Standard Law:** Sariq/oltin rang (`rating-gold`, `amber-*`) FAQAT reyting yulduzlari va ballari (IMDb/Kinopoisk) uchun ruxsat etilgan. Hech qachon CTA tugmalari, aktiv mavsum/qism tanlovlari, kartochka hoverlari, kartochka sarlavhalari ("Kalmar O'yini" va b.) yoki borderlar uchun sariq rang qo'llanmasin. Barcha faol holatlar, asosiy tugmalar va hoverlar FAQAT Primary Red (`#E50914`) bo'lishi shart.
- **No Unverified / Mock Parameters Law:** Bazada yoki backend sxemasida mavjud bo'lmagan yangi parametrlar, yorliqlar yoki filtrlarni (masalan: subtitr, audiotrek, mamlakat, soxta yosh ko'rsatmalari, soxta Obuna yozuvlari, soxta platforma reytinglari) hech qachon o'zboshimchalik bilan qo'shma. Har safar yangi narsa kerak bo'lsa, AVVAL foydalanuvchidan so'ra: "Shu narsani qo'shamizmi yoki yo'q, qo'shsak bazada va tizimda qanday bo'ladi?" deb tushuntirib, faqat uning tasdig'idan keyin kirit.

## Source of Truth & Project Context
- Facts & Constraints: read `facts.md` before making any assumptions.
- Current Status & Work Tracking: always read and maintain `STATE.md`.
- Architectural Decisions: consult `docs/decisions.md` before designing changes.
- Incident & Failure History: consult `docs/failures.md` to avoid past mistakes.
- Templates: use `reports/TEMPLATE.md` for slice progress reporting.

## Project Structure
- `backend/`: FastAPI application, SQLAlchemy 2.0 (asyncpg), Alembic migrations, PostgreSQL, Redis.
- `bot/`: aiogram 3 Telegram bot (thin client interacting with backend API).
- `website/`: Next.js 14 (App Router), React 18, Tailwind CSS web portal.
- `admin-panel/`: Next.js 14 administrative dashboard.
- `scraper/`: Autopilot media catalog scrapers.
- `scripts/`: Operational, migration, and verification utilities.

## Verification & Execution Gates
- Never mark a slice complete without executing `make check`.
- Preserve existing tests; never weaken assertions, disable linters, or bypass migrations.
- Commit messages must follow Conventional Commits (`feat:`, `fix:`, `test:`, `chore:`, `perf:`).
- Keep changes atomic: diff <= 200 lines per slice. Update `STATE.md` on every slice.
