"use client";

import Link from "next/link";
import { HistoryItem } from "@/lib/api/history";
import { CatalogItem } from "@/lib/api/catalog";
import MovieCard from "../catalog/MovieCard";

type Props = {
  items: HistoryItem[];
  emptyMessage?: string;
  emptyType?: "in_progress" | "completed";
};

export default function HistoryGrid({ 
  items, 
  emptyMessage = "Hali hech narsani ko'rmadingiz",
  emptyType = "in_progress" 
}: Props) {
  if (!items || items.length === 0) {
    return (
      <div className="text-center py-12 sm:py-16 px-6 bg-white/[0.03] backdrop-blur-md rounded-3xl border border-white/10 flex flex-col items-center justify-center my-4">
        <div className="w-16 h-16 sm:w-20 sm:h-20 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center text-text-secondary mb-4 shadow-inner">
          <span className="material-symbols-outlined text-3xl sm:text-4xl opacity-60">
            {emptyType === "in_progress" ? "schedule" : "history"}
          </span>
        </div>
        <h3 className="text-base sm:text-lg font-bold text-text-primary mb-1.5">
          {emptyMessage}
        </h3>
        <p className="text-xs sm:text-sm text-text-secondary max-w-sm mb-6 leading-relaxed">
          {emptyType === "in_progress"
            ? "Sizda hozircha davom etayotgan film yoki serial yo'q. Yangi premyeralarni tomosha qilishni boshlang!"
            : "Siz tomosha qilib yakunlagan barcha kinolar va seriallar shu yerda saqlanadi."}
        </p>
        <Link
          href="/movies"
          className="h-11 px-5 rounded-xl bg-white/10 hover:bg-white/15 text-white font-semibold text-xs sm:text-sm border border-white/15 flex items-center gap-2 transition-all active:scale-95 shadow-md shadow-black/20 cursor-pointer"
        >
          <span className="material-symbols-outlined text-[18px]">movie</span>
          <span>Katalogni ochish</span>
        </Link>
      </div>
    );
  }

  // Convert HistoryItem to CatalogItem for MovieCard
  const mappedItems = items.map(item => {
    let catalogItem: CatalogItem;
    if (item.type === "movie" && item.movie) {
      catalogItem = {
        id: item.movie.id,
        title: item.movie.title,
        original_title: null,
        imdb_rating: null,
        tmdb_rating: null,
        release_year: null,
        poster_url: item.movie.poster_url,
        code: item.movie.code,
        is_series: false,
        genres: null
      };
    } else if (item.type === "episode" && item.episode) {
      catalogItem = {
        // Link to the series page
        id: item.episode.series_id,
        title: `${item.episode.series_title} - ${item.episode.display_code}`,
        original_title: null,
        imdb_rating: null,
        tmdb_rating: null,
        release_year: null,
        poster_url: item.episode.series_poster,
        code: item.episode.code,
        is_series: true,
        genres: null
      };
    } else {
      // Fallback in case of missing data
      catalogItem = {
        id: 0, title: "Unknown", is_series: false, code: "0"
      } as any;
    }
    return { historyItem: item, catalogItem };
  });

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4 md:gap-6">
      {mappedItems.map(({ historyItem, catalogItem }, index) => (
        <MovieCard 
          key={`${historyItem.id}-${index}`} 
          item={catalogItem} 
          statusBadge={historyItem.status} 
        />
      ))}
    </div>
  );
}
