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

function getPageIcon(title: string): string {
  const t = title.toLowerCase();
  if (t.includes("anime")) return "animation";
  if (t.includes("dorama") || t.includes("koreys")) return "theater_comedy";
  if (t.includes("mult") || t.includes("kartun") || t.includes("bolalar")) return "smart_toy";
  if (t.includes("marvel") || t.includes("dc") || t.includes("komiks")) return "shield";
  if (t.includes("turk")) return "language";
  if (t.includes("retro") || t.includes("klassik")) return "videocam";
  if (t.includes("top") || t.includes("hit") || t.includes("trend")) return "local_fire_department";
  if (t.includes("hujjatli") || t.includes("doc")) return "history_edu";
  if (t.includes("fantastik")) return "rocket_launch";
  if (t.includes("jangari") || t.includes("jang")) return "military_tech";
  if (t.includes("horror") || t.includes("qo'rqinchli")) return "skull";
  return "category";
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

  const activePages = pages.filter((p) => p.is_active !== false);

  return (
    <section className="max-w-container-max mx-auto px-gutter my-10 relative z-20">
      <div className="relative overflow-hidden rounded-2xl sm:rounded-3xl bg-surface-container/30 border border-white/10 p-5 sm:p-8 backdrop-blur-md">
        {/* Section Header - Matching site style */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-6">
          <div>
            <h2 className="font-headline-md text-xl sm:text-2xl md:text-3xl text-text-primary flex items-center gap-2.5 font-bold tracking-tight">
              <span className="w-1 h-6 bg-rating-gold rounded-full block"></span>
              Tasodifiy Tavsiya
            </h2>
            <p className="text-text-secondary text-xs sm:text-sm mt-1">
              Yo&apos;nalishni tanlang va qiziqarli kino yoki serialni kashf eting
            </p>
          </div>
        </div>

        {/* Category Pills - Identical to CatalogTypeNav */}
        <div className="relative mb-6 md:mb-8 -mx-1 px-1">
          <div className="flex items-center gap-2 overflow-x-auto pb-2 pt-1 hide-scrollbar scroll-smooth">
            <button
              onClick={() => handleCategoryChange("all")}
              className={`px-4 sm:px-5 py-2.5 rounded-xl text-xs sm:text-sm font-semibold transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5 active:scale-95 shrink-0 flex items-center gap-2 border cursor-pointer ${
                selectedCategory === "all"
                  ? "bg-white/20 text-white border-white/30 shadow-lg shadow-black/20 font-bold backdrop-blur-md"
                  : "bg-white/5 border-white/10 text-text-secondary hover:text-text-primary hover:bg-white/10"
              }`}
            >
              <span className="material-symbols-outlined text-[18px]">auto_awesome</span>
              <span>Hammasi</span>
            </button>

            <button
              onClick={() => handleCategoryChange("movies")}
              className={`px-4 sm:px-5 py-2.5 rounded-xl text-xs sm:text-sm font-semibold transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5 active:scale-95 shrink-0 flex items-center gap-2 border cursor-pointer ${
                selectedCategory === "movies"
                  ? "bg-white/20 text-white border-white/30 shadow-lg shadow-black/20 font-bold backdrop-blur-md"
                  : "bg-white/5 border-white/10 text-text-secondary hover:text-text-primary hover:bg-white/10"
              }`}
            >
              <span className="material-symbols-outlined text-[18px]">movie</span>
              <span>Kinolar</span>
            </button>

            <button
              onClick={() => handleCategoryChange("series")}
              className={`px-4 sm:px-5 py-2.5 rounded-xl text-xs sm:text-sm font-semibold transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5 active:scale-95 shrink-0 flex items-center gap-2 border cursor-pointer ${
                selectedCategory === "series"
                  ? "bg-white/20 text-white border-white/30 shadow-lg shadow-black/20 font-bold backdrop-blur-md"
                  : "bg-white/5 border-white/10 text-text-secondary hover:text-text-primary hover:bg-white/10"
              }`}
            >
              <span className="material-symbols-outlined text-[18px]">tv</span>
              <span>Seriallar</span>
            </button>

            {activePages.map((p) => {
              const pKey = `page_${p.id}`;
              const icon = getPageIcon(p.title || "");

              return (
                <button
                  key={p.id}
                  onClick={() => handleCategoryChange(pKey)}
                  className={`px-4 sm:px-5 py-2.5 rounded-xl text-xs sm:text-sm font-semibold transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5 active:scale-95 shrink-0 flex items-center gap-2 border cursor-pointer ${
                    selectedCategory === pKey
                      ? "bg-white/20 text-white border-white/30 shadow-lg shadow-black/20 font-bold backdrop-blur-md"
                      : "bg-white/5 border-white/10 text-text-secondary hover:text-text-primary hover:bg-white/10"
                  }`}
                >
                  <span className="material-symbols-outlined text-[18px]">{icon}</span>
                  <span>{p.title}</span>
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

              <p className="text-text-secondary text-xs sm:text-sm line-clamp-2 sm:line-clamp-3 md:line-clamp-4 max-w-2xl mb-6 leading-relaxed font-normal">
                {activeItem.description || "Ushbu film haqida to'liq ma'lumot olish va tomosha qilish uchun pastdagi tugmani bosing."}
              </p>

              {/* Action Buttons - Fully unified with Hero & Movie details */}
              <div className="flex flex-wrap sm:flex-nowrap items-center gap-3 w-full sm:w-auto">
                <Link
                  href={watchUrl}
                  className="flex-1 sm:flex-initial h-12 sm:h-14 px-6 sm:px-8 rounded-xl bg-primary-container hover:bg-inverse-primary text-white font-label-caps text-xs sm:text-sm uppercase tracking-widest font-bold shadow-lg shadow-primary-container/25 hover:shadow-primary-container/35 transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5 active:scale-95 flex items-center justify-center gap-2.5 cursor-pointer"
                >
                  <span className="material-symbols-outlined text-[20px]" style={{ fontVariationSettings: "'FILL' 1" }}>
                    play_circle
                  </span>
                  <span>TOMOSHA QILISH</span>
                </Link>

                <button
                  onClick={handleNext}
                  disabled={isSpinning || filteredItems.length <= 1}
                  className="flex-1 sm:flex-initial h-12 sm:h-14 px-5 sm:px-6 rounded-xl bg-white/10 hover:bg-white/15 text-white border border-white/15 hover:border-white/30 font-label-caps text-xs sm:text-sm uppercase tracking-widest font-bold shadow-md shadow-black/20 transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5 active:scale-95 flex items-center justify-center gap-2 cursor-pointer disabled:opacity-40 disabled:hover:scale-100 disabled:hover:translate-y-0"
                >
                  <span className={`material-symbols-outlined text-[18px] text-rating-gold ${isSpinning ? "animate-spin" : ""}`}>
                    autorenew
                  </span>
                  <span>KEYINGI</span>
                </button>

                <ShareButton
                  title={activeItem.title}
                  text={`${activeItem.title} ni bepul tomosha qiling!`}
                  url={watchUrl}
                  code={activeItem.is_series ? `s_${activeItem.id}` : (activeItem.code || String(activeItem.id))}
                  className="flex-1 sm:flex-initial h-12 sm:h-14 px-5 sm:px-6 rounded-xl bg-white/10 hover:bg-white/15 text-white border border-white/15 hover:border-white/30 font-label-caps text-xs sm:text-sm uppercase tracking-widest font-bold shadow-md shadow-black/20 transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5 active:scale-95 flex items-center justify-center gap-2 cursor-pointer"
                  buttonText="ULASHISH"
                />
              </div>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
