---
name: bot-thin-client
activation: glob
glob: "kinochi bot/**"
---
- Bot handlerlarida biznes-logika YOZILMAYDI. Har qanday hisob-kitob,
  filtrlash, validatsiya — backend API orqali amalga oshiriladi.
- Bot PostgreSQL yoki Redis'ga TO'G'RIDAN-TO'G'RI ULANMAYDI.
- Barcha backend chaqiruvlari bot/services/api_client.py orqali
  o'tadi — handler'lar to'g'ridan-to'g'ri httpx/aiohttp chaqirmaydi.
- Agar handler ichida if/else bilan murakkab shart yoki hisoblash
  ko'rinsa — bu logika backendga (application layer'ga) ko'chiriladi.
