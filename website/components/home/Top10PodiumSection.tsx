"use client";

import { useMemo, useRef, useState } from "react";
import Link from "next/link";
import AdultPoster from "@/components/AdultPoster";
import { isAdultContent } from "@/lib/adult";

interface Top10PodiumItem {
  id: number;
  title: string;
  poster_url?: string | null;
  code?: string;
  is_series?: boolean;
  imdb_rating?: number | null;
  tmdb_rating?: number | null;
  views_count?: number | null;
  is_18_plus?: boolean;
}

export default function Top10PodiumSection({ items }: { items: Top10PodiumItem[] }) {
  const [filterType, setFilterType] = useState<"all" | "movie" | "series">("all");
  const sliderRef = useRef<HTMLDivElement>(null);

  const rankedItems = useMemo(() => {
    if (!Array.isArray(items) || items.length === 0) return [];
    const filtered = items.filter((item) => {
      const isSeries = !!item.is_series || !item.code;
      if (filterType === "movie") return !isSeries;
      if (filterType === "series") return isSeries;
      return true;
    });
    const sorted = [...filtered].sort((a, b) => {
      const scoreA = (Number(a.imdb_rating || a.tmdb_rating || 0) * 10) + (Number(a.views_count || 0) > 0 ? 5 : 0);
      const scoreB = (Number(b.imdb_rating || b.tmdb_rating || 0) * 10) + (Number(b.views_count || 0) > 0 ? 5 : 0);
      return scoreB - scoreA;
    });
    return sorted.slice(0, 10);
  }, [items, filterType]);

  if (!rankedItems || rankedItems.length === 0) return null;

  const scrollSlider = (dir: -1 | 1) => {
    sliderRef.current?.scrollBy({ left: dir * 420, behavior: "smooth" });
  };

  return (
    <section className="max-w-container-max mx-auto px-gutter my-6 sm:my-10 cv-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 mb-3">
        <div>
          <h2 className="font-heading text-2xl sm:text-3xl font-black text-slate-900 dark:text-white tracking-tight leading-none mb-0.5 flex items-center gap-2">
            <span>TOP 10</span>
          </h2>
          <p className="text-xs text-slate-500 dark:text-gray-400">
            Eng sara va ommabop media asarlar reytingi.
          </p>
        </div>

        <div className="flex items-center gap-1 bg-slate-200/80 dark:bg-[#121317] p-0.5 rounded-full border border-slate-300/70 dark:border-white/10 self-start sm:self-auto">
          {[
            { key: "all" as const, label: "Barchasi" },
            { key: "movie" as const, label: "Kinolar" },
            { key: "series" as const, label: "Seriallar" },
          ].map((tab) => {
            const active = filterType === tab.key;
            return (
              <button
                key={tab.key}
                type="button"
                onClick={() => setFilterType(tab.key)}
                className={`px-3 py-1 rounded-full text-[11px] font-bold transition-all cursor-pointer ${
                  active
                    ? "bg-[#D20A13] dark:bg-[#E50914] text-white shadow-sm"
                    : "text-slate-600 dark:text-gray-400 hover:text-slate-900 dark:hover:text-white"
                }`}
              >
                {tab.label}
              </button>
            );
          })}
        </div>
      </div>

      <div className="relative group/slider">
        <button
          type="button"
          onClick={() => scrollSlider(-1)}
          aria-label="Chapga"
          className="hidden sm:flex absolute -left-3 top-1/2 -translate-y-1/2 z-20 w-8 h-8 rounded-full bg-white/95 dark:bg-black/80 hover:bg-[#B80710] dark:hover:bg-[#E50914] text-slate-900 dark:text-white hover:text-white items-center justify-center transition border border-slate-300 dark:border-white/15 shadow-xl opacity-0 group-hover/slider:opacity-100 cursor-pointer"
        >
          <span className="material-symbols-outlined text-[18px]">chevron_left</span>
        </button>
        <button
          type="button"
          onClick={() => scrollSlider(1)}
          aria-label="O'ngga"
          className="hidden sm:flex absolute -right-3 top-1/2 -translate-y-1/2 z-20 w-8 h-8 rounded-full bg-white/95 dark:bg-black/80 hover:bg-[#B80710] dark:hover:bg-[#E50914] text-slate-900 dark:text-white hover:text-white items-center justify-center transition border border-slate-300 dark:border-white/15 shadow-xl opacity-0 group-hover/slider:opacity-100 cursor-pointer"
        >
          <span className="material-symbols-outlined text-[18px]">chevron_right</span>
        </button>

        <div
          ref={sliderRef}
          className="flex items-start gap-2 sm:gap-5 overflow-x-auto hide-scrollbar snap-x pb-3 pt-2 px-0.5"
        >
          {rankedItems.map((item, idx) => {
            const isSeries = !!item.is_series || !item.code;
            const href = isSeries ? `/series/${item.id}` : `/movie/${item.code || item.id}`;
            const is18 = isAdultContent(item);
            const rating = item.imdb_rating || item.tmdb_rating;
            const rankClass =
              idx === 0
                ? "is-gold"
                : idx === 1
                ? "is-silver"
                : idx === 2
                ? "is-bronze"
                : "";

            return (
              <Link
                key={`top-${isSeries ? "s" : "m"}-${item.id}`}
                href={href}
                className="shrink-0 snap-start w-[calc((100%-16px)/3)] sm:w-[170px] md:w-[200px] flex flex-col group cursor-pointer select-none"
              >
                <div className="aspect-[2/3] w-full rounded-xl sm:rounded-2xl overflow-hidden border border-slate-200 dark:border-white/10 group-hover:border-[#E50914] transition duration-300 shadow-lg relative bg-surface-container-high">
                  {item.poster_url ? (
                    <AdultPoster
                      src={item.poster_url}
                      alt={item.title}
                      is18Plus={is18}
                      fill
                      sizes="(max-width: 640px) 130px, 200px"
                      imageClassName="object-cover group-hover:scale-105 transition duration-500"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-gray-500">
                      <span className="material-symbols-outlined text-3xl opacity-30">
                        {isSeries ? "live_tv" : "movie"}
                      </span>
                    </div>
                  )}
                  {rating ? (
                    <span className="preserve-white absolute top-1.5 right-1.5 bg-black/80 backdrop-blur-md text-rating-gold text-[9px] sm:text-[10px] font-bold px-1.5 py-0.5 rounded-md border border-white/15">
                      ★ {rating}
                    </span>
                  ) : null}
                </div>

                <div className="flex items-center gap-1.5 sm:gap-2.5 mt-2 px-0.5 min-w-0">
                  <span
                    className={`top-rank-num ${rankClass} text-2xl sm:text-4xl font-black leading-none shrink-0 select-none`}
                  >
                    {idx + 1}
                  </span>
                  <h4 className="font-bold text-[11px] sm:text-sm text-slate-900 dark:text-white group-hover:text-[#D20A13] dark:group-hover:text-[#E50914] transition truncate leading-snug min-w-0">
                    {item.title}
                  </h4>
                </div>
              </Link>
            );
          })}
        </div>
      </div>
    </section>
  );
}
