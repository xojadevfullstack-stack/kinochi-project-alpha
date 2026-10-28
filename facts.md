# Facts (source of truth; change only if the user writes "update facts: ...")
- User name: Xoja (nickname xojadevops). Do not accept another name unless this file is updated.
- Reply language: Uzbek. Code, commits, file names: English.
- Stack: Django REST Framework, FastAPI, aiogram, React/Vite/Tailwind, PostgreSQL, Redis. Deploy: Render, Vercel.
- Project: Kinochi (cinema streaming ecosystem with FastAPI backend, aiogram 3 Telegram bot, Next.js 14 web and admin portals, PostgreSQL with Alembic, Redis caching, deployed on Render and Vercel)
- Admin Panel: Next.js 14 on port 3001 (http://localhost:3001)
- Decisions: see docs/decisions.md
- Cinematic Red Design Standard: Sariq/oltin rang (`rating-gold`, `amber-*`) FAQAT reyting yulduzlari va ballari (IMDb/Kinopoisk) uchun ishlatiladi. CTA tugmalari, aktiv mavsum/qismlar, hover effektlari, kartochka sarlavhalari yoki borderlar uchun sariq rang qo'llash qat'iyan man etiladi. Barcha faol holatlar, asosiy tugmalar va hoverlar FAQAT Primary Red (`#E50914`) bo'lishi shart.
- Parameter / Schema Law: Hech qachon loyihada (bazada yoki backendda) mavjud bo'lmagan parametrlar, maydonlar yoki mock yorliqlar (masalan: subtitr, audiotrek, mamlakat, soxta yosh toifalari, soxta Obuna yozuvlari, soxta platforma reytinglari) o'zboshimchalik bilan qo'shilmasin. Yangi parametr yoki funksiya kerak bo'lsa, har safar AVVAL foydalanuvchidan aniq so'ralsin: "Shu narsani qo'shamizmi yoki yo'q, agar qo'shsak qanday bo'ladi?" deb tushuntirilib, rozilik olingandan keyingina kiritiladi.
