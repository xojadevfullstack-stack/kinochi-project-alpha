"use client";

import { useState, useMemo } from "react";
import Image from "next/image";
import Link from "next/link";
import ShareButton from "@/components/ShareButton";

interface Item {
  id: number;
  title: string;
  poster_url: string | null;
  description?: string | null;
  imdb_rating?: number | null;
  tmdb_rating?: number | null;
  release_year?: number | null;
  genres?: string | null;
  code?: string;
  is_series?: boolean;
  page_title?: string;
}

interface Props {
  movies: any[];
  series: any[];
  pages?: any[];
}

export default function RandomRecommendationWidget({ movies = [], series = [], pages = [] }: Props) {
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [currentIndex, setCurrentIndex] = useState<number>(0);
  const [isSpinning, setIsSpinning] = useState<boolean>(false);

  // Filter items according to selected category
  const filteredItems = useMemo(() => {
    let list: Item[] = [];

    const formattedMovies: Item[] = (movies || []).map(m => ({
      id: m.id,
      title: m.title,
      poster_url: m.poster_url,
      description: m.description,
      imdb_rating: m.imdb_rating || m.tmdb_rating,
      release_year: m.release_year,
      genres: m.genres,
      code: m.code,
      is_series: false
    }));

    const formattedSeries: Item[] = (series || []).map(s => ({
      id: s.id,
      title: s.title,
      poster_url: s.poster_url,
      description: s.description,
      imdb_rating: s.imdb_rating || s.tmdb_rating,
      release_year: s.release_year,
      genres: s.categories?.map((c: any) => c.name).join(", ") || "Serial",
      code: String(s.id),
      is_series: true
    }));

    if (selectedCategory === "all") {
      list = [...formattedMovies, ...formattedSeries];
    } else if (selectedCategory === "movies") {
      list = formattedMovies;
    } else if (selectedCategory === "series") {
      list = formattedSeries;
    } else if (selectedCategory.startsWith("page_")) {
      const pageId = Number(selectedCategory.replace("page_", ""));
      const targetPage = pages.find(p => p.id === pageId);
      if (targetPage && targetPage.items) {
        list = targetPage.items.map((it: any) => ({
          id: it.id,
          title: it.title,
          poster_url: it.poster_url,
          description: it.description,
          imdb_rating: it.imdb_rating || it.tmdb_rating,
          release_year: it.release_year,
          genres: it.genres || targetPage.title,
          code: it.code || String(it.id),
          is_series: !!it.is_series,
          page_title: targetPage.title
        }));
      }
    }

    return list;
  }, [selectedCategory, movies, series, pages]);

  const activeItem = filteredItems.length > 0 ? filteredItems[currentIndex % filteredItems.length] : null;

  const handleNext = () => {
    if (filteredItems.length <= 1) return;
    setIsSpinning(true);
    setTimeout(() => {
      setCurrentIndex(prev => (prev + 1) % filteredItems.length);
      setIsSpinning(false);
    }, 200);
  };

  const handleCategoryChange = (cat: string) => {
    setSelectedCategory(cat);
    setCurrentIndex(0);
  };

  if (!activeItem && filteredItems.length === 0) {
    return null;
  }

  const watchUrl = activeItem?.is_series ? `/series/${activeItem.id}` : `/movie/${activeItem?.code || activeItem?.id}`;

  return (
    <section className="max-w-container-max mx-auto px-gutter my-10 relative z-20">
      <div className="relative overflow-hidden rounded-2xl sm:rounded-3xl bg-white/[0.03] border border-white/10 p-5 sm:p-8 backdrop-blur-md">
        {/* Section Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6 sm:mb-8">
          <div>
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-text-secondary text-xs font-medium mb-2">
              <span className="material-symbols-outlined text-[16px] text-primary-container">shuffle</span>
              <span>Tavsiya Generator</span>
            </div>
            <h2 className="text-xl sm:text-2xl md:text-3xl font-bold text-text-primary tracking-tight">
              Nima ko'rishni bilmayapsizmi?
            </h2>
            <p className="text-text-secondary text-xs sm:text-sm mt-1">
              Yo'nalishni tanlang va qiziqarli kino yoki serial toping
            </p>
          </div>
        </div>

        {/* Category Pills */}
        <div className="relative mb-6 md:mb-8 -mx-1 px-1">
          <div className="flex items-center gap-2 overflow-x-auto pb-2 pt-1 hide-scrollbar scroll-smooth">
            <button
              onClick={() => handleCategoryChange("all")}
              className={`px-4 py-2 rounded-xl text-xs sm:text-sm font-medium transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5 shrink-0 flex items-center gap-2 border cursor-pointer active:scale-95 ${
                selectedCategory === "all"
                  ? "bg-primary-container/20 text-white border-primary-container/50 font-semibold"
                  : "bg-white/5 text-text-secondary border-white/10 hover:bg-white/10 hover:text-text-primary"
              }`}
            >
              <span className="material-symbols-outlined text-[18px]">apps</span>
              Hammasi
            </button>

            <button
              onClick={() => handleCategoryChange("movies")}
              className={`px-4 py-2 rounded-xl text-xs sm:text-sm font-medium transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5 shrink-0 flex items-center gap-2 border cursor-pointer active:scale-95 ${
                selectedCategory === "movies"
                  ? "bg-primary-container/20 text-white border-primary-container/50 font-semibold"
                  : "bg-white/5 text-text-secondary border-white/10 hover:bg-white/10 hover:text-text-primary"
              }`}
            >
              <span className="material-symbols-outlined text-[18px]">movie</span>
              Kinolar
            </button>

            <button
              onClick={() => handleCategoryChange("series")}
              className={`px-4 py-2 rounded-xl text-xs sm:text-sm font-medium transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5 shrink-0 flex items-center gap-2 border cursor-pointer active:scale-95 ${
                selectedCategory === "series"
                  ? "bg-primary-container/20 text-white border-primary-container/50 font-semibold"
                  : "bg-white/5 text-text-secondary border-white/10 hover:bg-white/10 hover:text-text-primary"
              }`}
            >
              <span className="material-symbols-outlined text-[18px]">tv</span>
              Seriallar
            </button>

            {pages.map((p) => {
              const pKey = `page_${p.id}`;
              const titleLower = (p.title || "").toLowerCase();
              let icon = "folder";
              if (titleLower.includes("anime")) icon = "animation";
              else if (titleLower.includes("dorama")) icon = "theater_comedy";
              else if (titleLower.includes("mult")) icon = "smart_toy";

              return (
                <button
                  key={p.id}
                  onClick={() => handleCategoryChange(pKey)}
                  className={`px-4 py-2 rounded-xl text-xs sm:text-sm font-medium transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5 shrink-0 flex items-center gap-2 border cursor-pointer active:scale-95 ${
                    selectedCategory === pKey
                      ? "bg-primary-container/20 text-white border-primary-container/50 font-semibold"
                      : "bg-white/5 text-text-secondary border-white/10 hover:bg-white/10 hover:text-text-primary"
                  }`}
                >
                  <span className="material-symbols-outlined text-[18px]">{icon}</span>
                  {p.title}
                </button>
              );
            })}
          </div>
        </div>

        {/* Featured Recommendation Card */}
        {activeItem && (
          <div className="flex flex-col sm:flex-row gap-5 sm:gap-7 md:gap-8 items-center sm:items-start">
            {/* Poster */}
            <div className="w-36 sm:w-44 md:w-52 aspect-[2/3] shrink-0 rounded-xl overflow-hidden relative shadow-lg border border-white/10 group">
              {activeItem.poster_url ? (
                <Image
                  src={activeItem.poster_url}
                  alt={activeItem.title}
                  fill
                  className="object-cover group-hover:scale-105 transition-transform duration-500"
                />
              ) : (
                <div className="w-full h-full bg-surface-container flex items-center justify-center text-text-secondary">
                  <span className="material-symbols-outlined text-5xl opacity-40">movie</span>
                </div>
              )}
              <div className="absolute top-2.5 right-2.5 px-2 py-0.5 rounded-md bg-black/70 backdrop-blur-md border border-white/10 text-rating-gold text-xs font-bold flex items-center gap-1">
                <span className="material-symbols-outlined text-[13px]" style={{ fontVariationSettings: "'FILL' 1" }}>
                  star
                </span>
                {activeItem.imdb_rating ? Number(activeItem.imdb_rating).toFixed(1) : "N/A"}
              </div>
            </div>

            {/* Info and Actions */}
            <div className="flex-1 flex flex-col items-center sm:items-start text-center sm:text-left w-full">
              {/* Badges */}
              <div className="flex flex-wrap items-center justify-center sm:justify-start gap-2 mb-2.5">
                <span className="px-2.5 py-0.5 rounded-md text-[10px] sm:text-[11px] font-semibold uppercase tracking-wider bg-white/5 text-text-secondary border border-white/10">
                  {activeItem.is_series ? "Serial" : "Film"}
                </span>
                {activeItem.release_year && (
                  <span className="px-2.5 py-0.5 rounded-md text-[10px] sm:text-[11px] font-semibold uppercase tracking-wider bg-white/5 text-text-secondary border border-white/10">
                    {activeItem.release_year}
                  </span>
                )}
                {activeItem.genres && (
                  <span className="px-2.5 py-0.5 rounded-md text-[10px] sm:text-[11px] font-medium bg-white/5 text-text-secondary border border-white/10">
                    {activeItem.genres.split(",")[0]}
                  </span>
                )}
              </div>

              <h3 className="text-lg sm:text-xl md:text-2xl font-bold text-text-primary tracking-tight mb-2 sm:mb-2.5">
                {activeItem.title}
              </h3>

              <p className="text-text-secondary text-xs sm:text-sm line-clamp-2 sm:line-clamp-3 md:line-clamp-4 max-w-2xl mb-5 leading-relaxed font-normal">
                {activeItem.description || "Ushbu film haqida to'liq ma'lumot olish va tomosha qilish uchun pastdagi tugmani bosing."}
              </p>

              {/* Action Buttons - Soft, eye-friendly styles */}
              <div className="flex flex-wrap sm:flex-nowrap items-center gap-2.5 w-full sm:w-auto">
                <Link
                  href={watchUrl}
                  className="flex-1 sm:flex-initial sm:min-w-[140px] h-11 px-5 rounded-xl bg-primary-container/90 hover:bg-primary-container text-white font-semibold text-xs sm:text-sm tracking-wide flex items-center justify-center gap-2 transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5 active:scale-95 cursor-pointer shadow-lg shadow-primary-container/20"
                >
                  <span className="material-symbols-outlined text-[18px]" style={{ fontVariationSettings: "'FILL' 1" }}>
                    play_circle
                  </span>
                  <span>Tomosha qilish</span>
                </Link>

                <button
                  onClick={handleNext}
                  disabled={isSpinning || filteredItems.length <= 1}
                  className="flex-1 sm:flex-initial sm:min-w-[110px] h-11 px-4 rounded-xl bg-white/5 hover:bg-white/10 text-text-primary font-semibold text-xs sm:text-sm tracking-wide border border-white/10 hover:border-white/20 flex items-center justify-center gap-2 transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5 active:scale-95 cursor-pointer disabled:opacity-40 disabled:hover:scale-100 disabled:hover:translate-y-0"
                >
                  <span className={`material-symbols-outlined text-[18px] text-rating-gold ${isSpinning ? "animate-spin" : ""}`}>
                    autorenew
                  </span>
                  <span>Keyingi</span>
                </button>

                <ShareButton
                  title={activeItem.title}
                  text={`${activeItem.title} ni bepul tomosha qiling!`}
                  url={watchUrl}
                  code={activeItem.is_series ? `s_${activeItem.id}` : (activeItem.code || String(activeItem.id))}
                  className="flex-1 sm:flex-initial sm:min-w-[110px] h-11 px-4 rounded-xl bg-white/5 hover:bg-white/10 text-text-primary font-semibold text-xs sm:text-sm tracking-wide border border-white/10 hover:border-white/20 flex items-center justify-center gap-2 transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5 active:scale-95 cursor-pointer"
                  buttonText="Ulashish"
                />
              </div>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
