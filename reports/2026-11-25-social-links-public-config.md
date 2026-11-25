# Slice Report: 2026-11-25-social-links-public-config

## What was done
1. `backend/app/api/v1/telegram_auth.py` dagi `/api/v1/auth/public-config` endpointi `social_links` maydoni bilan kengaytirildi (`telegram_bot`, `telegram_channel`, `instagram`, `youtube`, `facebook` tasdiqlangan manzillari hamda env orqali `TIKTOK_URL`).
2. `website/lib/socialLinks.mjs`, `website/components/SocialIcon.tsx`, `website/lib/api.ts`, `website/components/Footer.tsx`, `website/components/Navbar.tsx` va `website/app/layout.tsx` da yagona dinamik ijtimoiy tarmoq havolalari hamda Light/Dark tugmalari qo'shildi.
3. Backend va frontend TDD testlari (`test_telegram_auth.py`, `website/tests/socialLinks.test.mjs`) yozildi, `STATE.md` va `docs/learned.md` yangilandi.

## Changed files
- `backend/app/api/v1/telegram_auth.py` - Added `_resolve_social_links()` in `/auth/public-config`
- `backend/tests/test_telegram_auth.py` - Added `test_public_config_includes_social_links_with_env_overrides`
- `website/lib/socialLinks.mjs` - Added `buildSocialItems()` & `isSafeHttpUrl()` helper
- `website/tests/socialLinks.test.mjs` - Added 2 unit tests for social link filtering/ordering
- `website/components/SocialIcon.tsx` - Shared SVG brand icons for Telegram/Kanal/Instagram/YouTube/Facebook/TikTok
- `website/lib/api.ts`, `website/components/Footer.tsx`, `website/components/Navbar.tsx`, `website/app/layout.tsx` - Wired `socialLinks` across Footer & Sidebar

## check output
```text
ruff check backend/app/api/v1/telegram_auth.py backend/tests/test_telegram_auth.py: All checks passed!
pytest backend/tests/test_telegram_auth.py -q: 9 passed, 4 warnings in 1.51s
node --test website/tests/*.test.mjs: 9 passed, 0 failed
tsc --noEmit & next build: Exit 0 (31/31 routes)
```

## Risks and unknowns
- `TIKTOK_URL` env o'rnatilmaguncha TikTok tugmasi soxta havola ko'rsatmaslik uchun yashirin turadi (`TIKTOK_URL` Render'da qo'shilishi bilan avtomatik chiqadi).

## Concept to explain to the user
- **Single-Source Public Config + Safe URL Guard**: Ijtimoiy linklarni `/auth/public-config` va yagona `buildSocialItems` yordamida markazlashtirib, bo'sh/notog'ri URL larni yashirish saytni qayta deploy qilmasdan linklarni yangilash va soxta 404 tugmalardan saqlanish imkonini beradi.
  - Analogy: Har bir sahifaga alohida telefon raqam yozib chiqmasdan, bitta umumiy ma'lumotlar bazasidan olish va raqami bo'lmagan bo'limni ro'yxatga chiqarmaslik.

## Next step
- Render va Vercel deploy yakunlangach jonli sayt Footer va Sidebar'ida 5 ta tasdiqlangan tarmoq (`Telegram Bot`, `Kanal`, `Instagram`, `YouTube`, `Facebook`) ko'rinishini tekshirish va foydalanuvchidan `TIKTOK_URL` qo'shishni so'rash.
