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
    <section className="max-w-container-max mx-auto px-gutter my-14 relative z-20">
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-white/[0.07] to-white/[0.02] border border-white/10 p-6 md:p-10 backdrop-blur-xl shadow-2xl">
        {/* Background Ambient Glow */}
        <div className="absolute -top-24 -right-24 w-80 h-80 bg-primary-container/20 rounded-full blur-3xl pointer-events-none"></div>
        <div className="absolute -bottom-24 -left-24 w-80 h-80 bg-amber-500/10 rounded-full blur-3xl pointer-events-none"></div>

        {/* Section Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary-container/10 border border-primary-container/20 text-primary-container text-xs font-bold uppercase tracking-wider mb-2">
              <span className="material-symbols-outlined text-[16px]">casino</span>
              Tavsiya Generator
            </div>
            <h2 className="text-2xl md:text-3xl font-extrabold text-text-primary tracking-tight">
              Nima ko'rishni bilmayapsizmi?
            </h2>
            <p className="text-text-secondary text-sm md:text-base mt-1">
              Yo'nalishni tanlang va qiziqarli kino yoki serial toping
            </p>
          </div>
        </div>

        {/* Category Pills */}
        <div className="flex items-center gap-2 overflow-x-auto pb-4 mb-8 hide-scrollbar">
          <button
            onClick={() => handleCategoryChange("all")}
            className={`px-4 py-2 rounded-xl text-xs md:text-sm font-semibold transition-all shrink-0 flex items-center gap-2 border cursor-pointer ${
              selectedCategory === "all"
                ? "bg-primary-container text-white border-primary-container shadow-lg shadow-primary-container/20"
                : "bg-white/5 text-text-secondary border-white/10 hover:bg-white/10 hover:text-text-primary"
            }`}
          >
            <span className="material-symbols-outlined text-[18px]">apps</span>
            Hammasi
          </button>

          <button
            onClick={() => handleCategoryChange("movies")}
            className={`px-4 py-2 rounded-xl text-xs md:text-sm font-semibold transition-all shrink-0 flex items-center gap-2 border cursor-pointer ${
              selectedCategory === "movies"
                ? "bg-primary-container text-white border-primary-container shadow-lg shadow-primary-container/20"
                : "bg-white/5 text-text-secondary border-white/10 hover:bg-white/10 hover:text-text-primary"
            }`}
          >
            <span className="material-symbols-outlined text-[18px]">movie</span>
            Kinolar
          </button>

          <button
            onClick={() => handleCategoryChange("series")}
            className={`px-4 py-2 rounded-xl text-xs md:text-sm font-semibold transition-all shrink-0 flex items-center gap-2 border cursor-pointer ${
              selectedCategory === "series"
                ? "bg-primary-container text-white border-primary-container shadow-lg shadow-primary-container/20"
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
                className={`px-4 py-2 rounded-xl text-xs md:text-sm font-semibold transition-all shrink-0 flex items-center gap-2 border cursor-pointer ${
                  selectedCategory === pKey
                    ? "bg-primary-container text-white border-primary-container shadow-lg shadow-primary-container/20"
                    : "bg-white/5 text-text-secondary border-white/10 hover:bg-white/10 hover:text-text-primary"
                }`}
              >
                <span className="material-symbols-outlined text-[18px]">{icon}</span>
                {p.title}
              </button>
            );
          })}
        </div>

        {/* Featured Recommendation Card */}
        {activeItem && (
          <div className="flex flex-col md:flex-row gap-6 md:gap-10 items-center">
            {/* Poster */}
            <div className="w-48 sm:w-56 md:w-64 aspect-[2/3] shrink-0 rounded-2xl overflow-hidden relative shadow-2xl border border-white/10 group">
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
              <div className="absolute top-3 right-3 px-2 py-1 rounded-md bg-black/70 backdrop-blur-md border border-white/10 text-rating-gold text-xs font-bold flex items-center gap-1">
                <span className="material-symbols-outlined text-[14px]" style={{ fontVariationSettings: "'FILL' 1" }}>
                  star
                </span>
                {activeItem.imdb_rating ? Number(activeItem.imdb_rating).toFixed(1) : "N/A"}
              </div>
            </div>

            {/* Info and Actions */}
            <div className="flex-1 flex flex-col items-center md:items-start text-center md:text-left">
              {/* Badges */}
              <div className="flex flex-wrap items-center justify-center md:justify-start gap-2 mb-3">
                <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold uppercase tracking-wider bg-white/10 text-text-secondary">
                  {activeItem.is_series ? "Serial" : "Film"}
                </span>
                {activeItem.release_year && (
                  <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold uppercase tracking-wider bg-white/10 text-text-secondary">
                    {activeItem.release_year}
                  </span>
                )}
                {activeItem.genres && (
                  <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-primary-container/10 text-primary-container border border-primary-container/20">
                    {activeItem.genres.split(",")[0]}
                  </span>
                )}
              </div>

              <h3 className="text-2xl md:text-4xl font-extrabold text-text-primary tracking-tight mb-3">
                {activeItem.title}
              </h3>

              <p className="text-text-secondary text-sm md:text-base line-clamp-3 md:line-clamp-4 max-w-2xl mb-6 leading-relaxed">
                {activeItem.description || "Ushbu film haqida to'liq ma'lumot olish va tomosha qilish uchun pastdagi tugmani bosing."}
              </p>

              {/* Action Buttons */}
              <div className="flex flex-col sm:flex-row items-center justify-center md:justify-start gap-3 w-full sm:w-auto">
                <Link
                  href={watchUrl}
                  className="w-full sm:w-[180px] h-12 rounded-2xl bg-primary-container hover:bg-inverse-primary text-white font-bold text-sm tracking-wide flex items-center justify-center gap-2.5 shadow-lg shadow-primary-container/25 hover:shadow-primary-container/40 hover:scale-[1.02] active:scale-95 transition-all cursor-pointer"
                >
                  <span className="material-symbols-outlined text-[20px]" style={{ fontVariationSettings: "'FILL' 1" }}>
                    play_circle
                  </span>
                  <span>Tomosha qilish</span>
                </Link>

                <button
                  onClick={handleNext}
                  disabled={isSpinning || filteredItems.length <= 1}
                  className="w-full sm:w-[180px] h-12 rounded-2xl bg-white/10 hover:bg-white/15 text-white font-bold text-sm tracking-wide border border-white/10 hover:border-white/20 flex items-center justify-center gap-2.5 shadow-lg shadow-black/20 hover:scale-[1.02] active:scale-95 transition-all cursor-pointer disabled:opacity-50"
                >
                  <span className={`material-symbols-outlined text-[20px] text-rating-gold ${isSpinning ? "animate-spin" : ""}`}>
                    autorenew
                  </span>
                  <span>Keyingi</span>
                </button>

                <ShareButton
                  title={activeItem.title}
                  text={`${activeItem.title} ni bepul tomosha qiling!`}
                  url={watchUrl}
                  code={activeItem.is_series ? `s_${activeItem.id}` : (activeItem.code || String(activeItem.id))}
                  className="w-full sm:w-[180px] h-12 rounded-2xl bg-white/10 hover:bg-white/15 text-white font-bold text-sm tracking-wide border border-white/10 hover:border-white/20 flex items-center justify-center gap-2.5 shadow-lg shadow-black/20 hover:scale-[1.02] active:scale-95 transition-all cursor-pointer"
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
