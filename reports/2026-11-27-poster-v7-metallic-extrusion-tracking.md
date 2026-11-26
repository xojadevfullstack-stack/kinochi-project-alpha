# Slice Report: 2026-11-27-poster-v7-metallic-extrusion-tracking

## What was done
1. `poster_localizer.py` kuchliroq **v7** bosqichiga o'tkazildi: `blockbuster` uslubiga keng geometrik action shriftlari (`Exo2-ExtraBold.ttf`, `RussoOne-Regular.ttf`, `Montserrat-ExtraBold.ttf`), dinamik `is_italic` qiyalik (`0.16` affine shear), `metallic` uchun 3D bronza/oltin yon-devor ekstruziyasi va xrom chiziqli yaltiroqlik, toza textless manbada majburiy markazlashtirish (`force_center=True`), keng qisqa sarlavhalarda dinamik `box-fill` harf oralig'i, `<Nom> <Raqam> <Taglavha>` uchun deterministik 2 qatorli ajratish (`QASOSKORLAR 4` + `INTIHO`) va Cloudflare 4b sarlavhadan tashqarida sahna/yuzni buzsa (`MAE > 10.5`) rad etuvchi `_is_scene_preserved_outside_title` himoyasi qo'shildi.
2. `test_poster_localizer.py` da `force_center`, `box-fill tracking`, `italic shear`, `_is_scene_preserved_outside_title` va deterministik `Qasoskorlar 4 Intiho` ajratish testlari (`RED -> GREEN`) yozildi va tekshirildi.
3. Jonli PostgreSQL + Telegram + Redis da `#827` (*Qasoskorlar 4 Intiho*), `#1120` (*Shogun*) va `#1125` (*Institut*) qayta yuklanib Telegram baytlari vizual tekshirildi; `STATE.md` yangilandi.

## Changed files
- `backend/app/infrastructure/external/poster_localizer.py` - v7 shrift, kursiv qiyalik, 3D ekstruziya, box-fill tracking, markazlashtirish, deterministik taglavha split va CF sahna MAE himoyasi.
- `backend/tests/test_poster_localizer.py` - v7 TDD testlari (3 ta yangi tekshiruv bilan jami 22 ta test).
- `backend/app/assets/fonts/{Exo2-ExtraBold,RussoOne-Regular,Montserrat-ExtraBold}.ttf` - OFL geometrik blockbuster shriftlar.
- `STATE.md` - v7 holati va natijalar qayd etildi.

## check output
```text
All checks passed!
i9d0e1f2a3b4 (head)
backend/tests/{test_poster_localizer,test_poster_triggers,test_posters_storage,test_fix_f013_swallowed_exceptions}.py -> 34 passed in 7.04s
bot/tests/ -> 116 passed in 9.29s
```

## Risks and unknowns
- Umumiy `backend/tests/` yig'ma ishga tushirishda Windows lokalidagi bog'liq bo'lmagan eski testlar 60s da qotgani uchun faqat poster/f013 (`34 passed`) va `bot/tests` (`116 passed`) to'liq yugurtirildi.
- Kichik `500x750` ruxsatdagi ko'p so'zli blockbuster nomlarda (`QASOSKORLAR 4`) custom qo'l-chizma halqa (`A`) o'rniga standart keng geometrik shrift qo'llanadi.

## Concept to explain to the user
- **Affine Italic Shear + 3D Stepped Extrusion + Scene-MAE Guard**: Harflarni yon tomonga engashtirib (`shear`) ostiga qadam-baqadam qoraytirilgan 3D devor qo'yish yassi matnni hajmli Marvel uslubiga olib chiqadi; piksel `MAE` himoyasi esa AI model qahramon yuzini buzgan zahoti uni rad etib toza textless rendererga o'tkazadi.

## Next step
- O'zgarishlarni `feat/smm-autopilot` ga push qilish va foydalanuvchi ko'zdan kechirishini kutish.
