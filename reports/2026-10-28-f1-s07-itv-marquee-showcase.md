# Slice Report: 2026-10-28-f1-s07-itv-marquee-showcase

## What was done
1. Designed and built `MediaMarqueeSection.tsx` delivering an iTV-style continuous 3-row rotating showcase for movies and series with compact cards matching reference dimensions.
2. Tuned GPU hardware-accelerated CSS animations (`animate-marquee-left`, `animate-marquee-right`, `animate-marquee-left-fast`) in `globals.css` to run at a calm, 3x slower pace (115s-138s).
3. Removed "(mozaikasi)" from the section title, leaving clean "Kinolar va seriallar" with chevron link.
4. Created compact square (`w-24 h-24` / `w-28 h-28`) and wide cards (`w-48 h-24`) with `HD`/`FHD` badges and hover pause.

## Changed files
- `website/components/home/MediaMarqueeSection.tsx` - Continuous multi-row scrolling movie mosaic
- `website/app/globals.css` - GPU translate3d marquee keyframes and pause-on-hover rules
- `website/app/page.tsx` - Mounted MediaMarqueeSection on home page
- `backend/tests/test_media_marquee_section.py` - TDD regression tests

## check output
```text
backend/tests/test_media_marquee_section.py ..                           [100%]
======================== 2 passed, 1 warning in 0.17s =========================
npm --prefix website run lint: exit code 0
HTTP Status: 200 (Length: 436KB, Live home page compilation verified)
```

## Risks and unknowns
- Low-end mobile devices might experience thermal or battery drain if too many unoptimized DOM nodes animate simultaneously; mitigated by CSS compositing on GPU thread and keeping duplicate lists bounded.

## Concept to explain to the user
- GPU Hardware Acceleration (translate3d): Animatsiyani kompyuterning asosiy protsessoriga (CPU) emas, balki video kartasiga (GPU) topshirish orqali qotmasdan, silliq aylanishini ta'minlash.

## Next step
- Present changes and evidence to the user.
