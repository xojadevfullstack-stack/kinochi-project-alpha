# Slice Report: 2026-11-22-website-breadcrumb-real-titles

## What was done
1. `website/lib/breadcrumbHelpers.mjs` + `.d.ts` va `website/components/BreadcrumbContext.tsx` (`BreadcrumbProvider`, `BreadcrumbTitle`) yaratilib, `Breadcrumb.tsx` va `layout.tsx` ga ulandi.
2. Barcha 5 ta dinamik sahifaga (`movie/[code]`, `series/[id]`, `category/[id]`, `collections/[slug]`, `p/[slug]`) `<BreadcrumbTitle />` qo'shilib, kod/ID o'rniga haqiqiy nomlar (masalan `Bosh sahifa / Film / Qasoskorlar`) qo'shimcha API so'rovisiz ko'rsatildi.
3. Unit testlar (`website/tests/breadcrumbHelpers.test.mjs`), typecheck, lint va production build (`31/31`) o'tkazildi, `STATE.md` va `docs/learned.md` yangilandi.

## Changed files
- `website/lib/breadcrumbHelpers.mjs` - `normalizeBreadcrumbPath`, `formatSegmentLabel`, `buildBreadcrumbs`.
- `website/lib/breadcrumbHelpers.d.ts` - TypeScript interfeyslari.
- `website/tests/breadcrumbHelpers.test.mjs` - 3 ta unit test (`node --test`).
- `website/components/BreadcrumbContext.tsx` - `BreadcrumbProvider`, `useBreadcrumbOverrides`, `BreadcrumbTitle`.
- `website/components/Breadcrumb.tsx` - `buildBreadcrumbs` va `overrides` bilan ishlash hamda desktop kengligi (`sm:max-w-md`).
- `website/app/layout.tsx` - `<BreadcrumbProvider>` o'rashi.
- `website/app/movie/[code]/page.tsx` - `movie.title` uzatish.
- `website/app/series/[id]/page.tsx` - `series.title` uzatish.
- `website/app/category/[id]/page.tsx` - `categoryName` uzatish.
- `website/app/collections/[slug]/page.tsx` - `collection.name` uzatish.
- `website/app/p/[slug]/page.tsx` - `page.title` uzatish.
- `STATE.md`, `docs/learned.md` - Slice yozuvlari.

## check output
```text
> node --test website/tests/breadcrumbHelpers.test.mjs
# tests 3, pass 3, fail 0

> .\website\node_modules\.bin\tsc.cmd -p website\tsconfig.json --noEmit
(exit code 0)

> npm --prefix website run lint
(exit code 0, pre-existing warnings only)

> npm --prefix website run build
 ✓ Generating static pages (31/31)
(exit code 0)

> node --test admin-panel/tests/tmdbFormHelpers.test.mjs
# tests 3, pass 3, fail 0

> backend\.venv\Scripts\python.exe -m pytest backend/tests/test_movie_service.py backend/tests/test_public_routes_publish_status.py -q
8 passed in 3.04s

> bot\.venv\Scripts\python.exe -m pytest bot/tests/ -q
106 passed in 7.94s
```

## Risks and unknowns
- `loading.tsx` va SSR birinchi kadrda `useEffect` ishga tushgunga qadar qisqa muddat fallback (`#PJH3KH`) ko'rinib darhol kino nomiga almashadi; hydration mismatch chiqmasligi uchun ataylab `useEffect` ishlatildi.
- `make` Windows muhitida o'rnatilmaganligi sabab `Makefile` tekshiruvlari alohida buyruqlar bilan bajarildi.

## Concept to explain to the user
- **Route-Keyed Context Override (Zero-Fetch Server-to-Layout Title Propagation):** Umumiy `layout.tsx` da turgan `Breadcrumb` komponentiga dinamik sahifalarda serverda olingan nomni `pathname` kaliti bo'yicha uzatish orqali ortiqcha API so'rovisiz aniq sarlavha ko'rsatish va sahifa yopilganda eski nomni tozalash.
- **O'xshatish:** Qabulxona taxtasi har bir xona eshigidan tayyor ism yozilgan kartochkani olib ko'rsatishi — qabulxonachi arxivga qaytib so'rov yubormaydi, xona bo'shaganda esa kartochkani olib qo'yadi.

## Next step
- Vercel/Render deploy yangilangach `/movie/...`, `/series/...`, `/category/...`, `/collections/...` va `/p/...` sahifalarida breadcrumbda haqiqiy nomlar chiqishini jonli tekshirish.
