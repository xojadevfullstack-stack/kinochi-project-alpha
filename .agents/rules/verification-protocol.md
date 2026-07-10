---
name: verification-protocol
activation: always_on
---
# Ishlash qoidalari (har qanday model uchun, hech qanday istisnosiz)

1. HECH QACHON "tayyor", "ishladi", "muvaffaqiyatli" deb yozma, agar
   sen buyruqni ISHGA TUSHIRMAGAN bo'lsang va terminal chiqishini
   O'ZING ko'rmagan bo'lsang. Fayl yozish = tugash emas. Test/build/
   migration ishga tushib, xatosiz o'tgani ko'rilgandan keyin
   "tayyor" deyiladi.

2. Har bir vazifa oxirida albatta shu ketma-ketlikni bajar:
   - alembic upgrade head (agar migration o'zgargan bo'lsa)
   - pytest — barcha test yashil bo'lgunicha
   Agar birortasi xato bersa — TO'XTA, foydalanuvchiga "tayyor" demay,
   xatoni tahlil qil va tuzat, keyin qayta ishga tushir.

3. Bitta promptda faqat SO'RALGAN qatlamlarga/papkalarga teg.

4. Har vazifa oxirida .agents/PROJECT_STATE.md ni yangila.

5. Agar vazifa noaniq bo'lsa yoki mavjud arxitekturaga zid ketsa —
   savol ber, taxmin qilib ketma.

6. Yangi CREATE/UPDATE/DELETE endpoint yozilganda, unit test o'tishidan
   tashqari, albatta Swagger yoki curl orqali HAQIQIY so'rov yuborib,
   keyin to'g'ridan-to'g'ri "docker exec ... psql ... SELECT" bilan
   ma'lumot bazada saqlanganini tasdiqlash SHART.

7. Tashqi API (Telegram, va h.k.) bilan ishlashdagi try/except bloklarida
   xatoni jimgina yutish taqiqlanadi — har doim log yozilishi shart
   (logging.warning() yoki error()), aks holda muammoni aniqlash
   imkonsiz bo'lib qoladi.
