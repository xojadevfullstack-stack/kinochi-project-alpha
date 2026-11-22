"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import AdultPoster from "@/components/AdultPoster";
import AdultHeroBackground from "@/components/AdultHeroBackground";
import ShareButton from "@/components/ShareButton";
import { isAdultContent } from "@/lib/adult";
import { isLowEndDevice } from "@/lib/lowEnd";

interface HeroCarouselProps {
  items: any[];
  botUsername?: string;
}

export default function HeroCarousel({ items, botUsername }: HeroCarouselProps) {
  const slides = Array.isArray(items) ? items.filter(Boolean).slice(0, 6) : [];
  const [activeIdx, setActiveIdx] = useState(0);
  const [paused, setPaused] = useState(false);

  useEffect(() => {
    if (slides.length <= 1 || paused || isLowEndDevice()) return;
    const timer = setInterval(() => {
      setActiveIdx((prev) => (prev + 1) % slides.length);
    }, 6500);
    return () => clearInterval(timer);
  }, [slides.length, paused]);

  if (slides.length === 0) return null;

  const current = slides[activeIdx] || slides[0];
  const isSeries = current.is_series ?? !current.code;
  const is18Plus = isAdultContent(current);
  const href = isSeries ? `/series/${current.id}` : `/movie/${current.code}`;
  const shareCode = isSeries ? `s_${current.id}` : current.code;
  const rating = current.imdb_rating || current.tmdb_rating;
  const genreLabel =
    current.page_title ||
    (isSeries
      ? current.categories?.[0]?.name || "Serial"
      : current.genres?.split(",")?.[0]?.trim() || "Kino");

  const goPrev = () => setActiveIdx((prev) => (prev - 1 + slides.length) % slides.length);
  const goNext = () => setActiveIdx((prev) => (prev + 1) % slides.length);

  return (
    <section className="w-full pt-2 pb-3 sm:pb-5">
      <div className="max-w-container-max mx-auto px-gutter">
        <div
          id="heroSlide"
          onMouseEnter={() => setPaused(true)}
          onMouseLeave={() => setPaused(false)}
          className="hero-stage preserve-white relative w-full rounded-2xl sm:rounded-3xl overflow-hidden border border-slate-900/15 dark:border-white/10 bg-[#08090C] min-h-[235px] sm:min-h-[290px] md:min-h-[340px] flex items-center shadow-xl"
        >
          {/* Backdrop */}
          <div className="absolute inset-0 z-0 pointer-events-none">
            {current.poster_url ? (
              <AdultHeroBackground
                src={current.poster_url}
                alt={current.title}
                is18Plus={is18Plus}
              />
            ) : null}
            <div className="absolute inset-0 bg-gradient-to-t from-[#08090C]/85 via-[#08090C]/25 to-transparent" />
            <div className="absolute inset-0 bg-gradient-to-r from-[#08090C]/90 via-[#08090C]/55 to-transparent" />
          </div>

          {/* Carousel Controls */}
          {slides.length > 1 && (
            <>
              <button
                type="button"
                onClick={goPrev}
                aria-label="Oldingi slayd"
                className="hidden sm:flex absolute left-3 top-1/2 -translate-y-1/2 z-20 w-8 h-8 rounded-full bg-black/60 hover:bg-[#E50914] text-white items-center justify-center transition border border-white/15 cursor-pointer"
              >
                <span className="material-symbols-outlined text-[18px]">chevron_left</span>
              </button>
              <button
                type="button"
                onClick={goNext}
                aria-label="Keyingi slayd"
                className="hidden sm:flex absolute right-3 top-1/2 -translate-y-1/2 z-20 w-8 h-8 rounded-full bg-black/60 hover:bg-[#E50914] text-white items-center justify-center transition border border-white/15 cursor-pointer"
              >
                <span className="material-symbols-outlined text-[18px]">chevron_right</span>
              </button>
            </>
          )}

          {/* Foreground Slide Content */}
          <div className="relative z-10 w-full px-5 py-5 sm:px-14 sm:py-7 md:px-16 md:py-8 flex items-center justify-between gap-4 sm:gap-8">
            <div className="flex-1 max-w-lg min-w-0">
              <div className="flex flex-wrap items-center gap-2 mb-1.5 text-xs">
                <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-white/10 border border-white/15 text-[10px] font-bold uppercase tracking-wider text-white">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#E50914] animate-pulse" />
                  <span>{isSeries ? "Serial" : "Premyera"}</span>
                </span>
                {rating ? (
                  <span className="text-rating-gold font-bold">★ {rating}</span>
                ) : null}
                {current.release_year && (
                  <>
                    <span className="text-gray-400">•</span>
                    <span className="text-gray-300 font-medium">{current.release_year}</span>
                  </>
                )}
                <span className="text-gray-400">•</span>
                <span className="text-gray-300 font-medium truncate">{genreLabel}</span>
                {is18Plus && (
                  <span className="px-1.5 py-0.5 rounded bg-red-600/80 text-white text-[10px] font-bold">
                    18+
                  </span>
                )}
              </div>

              <h1 className="font-heading text-xl sm:text-3xl md:text-4xl font-extrabold text-white tracking-tight leading-tight mb-2 line-clamp-2">
                {current.title}
              </h1>

              <p className="text-slate-300 text-xs sm:text-sm leading-relaxed mb-4 line-clamp-2 max-w-md">
                {current.description ||
                  "Telegram tarmog'idagi eng katta va qulay kino bazasi. Sevimli filmlaringizni bepul tomosha qiling."}
              </p>

              <div className="flex items-center gap-2">
                <Link
                  href={href}
                  className="inline-flex items-center gap-1.5 bg-[#E50914] hover:bg-[#B80710] text-white px-4 sm:px-5 py-2 sm:py-2.5 rounded-xl font-bold text-xs uppercase tracking-wider transition shadow-lg shadow-primary/30 active:scale-95"
                >
                  <span
                    className="material-symbols-outlined text-[17px]"
                    style={{ fontVariationSettings: "'FILL' 1" }}
                  >
                    play_circle
                  </span>
                  <span>KO&apos;RISH</span>
                </Link>
                <ShareButton
                  title={current.title}
                  text={`${current.title} ni bepul tomosha qiling.`}
                  url={href}
                  code={shareCode}
                  botUsername={botUsername}
                  iconOnly={true}
                  className="w-9 h-9 rounded-xl bg-white/10 hover:bg-[#E50914] text-white flex items-center justify-center border border-white/15 hover:border-[#E50914] transition cursor-pointer shrink-0"
                />
              </div>
            </div>

            {current.poster_url && (
              <Link
                href={href}
                className="w-28 sm:w-36 md:w-40 shrink-0 hidden sm:block group"
              >
                <div className="aspect-[2/3] w-full rounded-xl overflow-hidden border border-white/15 group-hover:border-[#E50914] shadow-2xl relative bg-surface-container-high transition-colors">
                  <AdultPoster
                    src={current.poster_url}
                    alt={current.title}
                    is18Plus={is18Plus}
                    fill
                    priority
                    sizes="160px"
                    imageClassName="object-cover group-hover:scale-105 transition-transform duration-500"
                  />
                </div>
              </Link>
            )}
          </div>

          {/* Slide Dots */}
          {slides.length > 1 && (
            <div className="absolute bottom-2.5 left-1/2 -translate-x-1/2 z-20 flex items-center gap-1.5">
              {slides.map((_, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => setActiveIdx(idx)}
                  aria-label={`Slayd ${idx + 1}`}
                  className={`h-1.5 rounded-full transition-all cursor-pointer ${
                    idx === activeIdx
                      ? "w-5 bg-[#E50914]"
                      : "w-1.5 bg-white/40 hover:bg-white/75"
                  }`}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
