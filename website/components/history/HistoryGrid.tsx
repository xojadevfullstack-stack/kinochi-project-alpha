"use client";

import { HistoryItem } from "@/lib/api/history";
import { CatalogItem } from "@/lib/api/catalog";
import MovieCard from "../catalog/MovieCard";

type Props = {
  items: HistoryItem[];
  emptyMessage?: string;
};

export default function HistoryGrid({ items, emptyMessage = "Hali hech narsani ko'rmadingiz" }: Props) {
  if (!items || items.length === 0) {
    return (
      <div className="text-center py-20 text-text-secondary bg-surface-container/20 rounded-2xl border border-white/5">
        <span className="material-symbols-outlined text-6xl mb-4 opacity-50">history</span>
        <p className="font-body-lg">{emptyMessage}</p>
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
