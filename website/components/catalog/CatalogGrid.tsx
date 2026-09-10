"use client";

import { useState } from "react";
import MovieCard from "./MovieCard";
import { CatalogItem, getPageContent } from "@/lib/api/catalog";

type Props = {
  initialItems: CatalogItem[];
  total: number;
  pageSlug: string;
};

export default function CatalogGrid({ initialItems, total, pageSlug }: Props) {
  const [items, setItems] = useState<CatalogItem[]>(initialItems);
  const [loading, setLoading] = useState(false);
  // The skip value passed to the backend APIs. Since each API receives the same skip,
  // we advance it by the fixed limit (20), NOT by the combined items length.
  const [skip, setSkip] = useState(20);

  const hasMore = items.length < total;

  const loadMore = async () => {
    if (loading || !hasMore) return;
    setLoading(true);
    try {
      // Fetch next 20 items (limit 20)
      const res = await getPageContent(pageSlug, skip, 20);
      if (res.items && res.items.length > 0) {
        setItems(prev => [...prev, ...res.items]);
        setSkip(prev => prev + 20);
      }
    } catch (error) {
      console.error("Failed to load more:", error);
    } finally {
      setLoading(false);
    }
  };

  if (!items || items.length === 0) {
    return (
      <div className="text-center py-20 text-text-secondary bg-surface-container/20 rounded-2xl border border-white/5">
        <span className="material-symbols-outlined text-6xl mb-4 opacity-50">movie</span>
        <p className="font-body-lg">Hozircha ushbu sahifada kontent mavjud emas.</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col">
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4 md:gap-6">
        {items.map(item => (
          <MovieCard key={`${item.is_series ? 's' : 'm'}-${item.id}`} item={item} />
        ))}
      </div>
      
      {hasMore && (
        <div className="mt-12 flex justify-center">
          <button 
            onClick={loadMore} 
            disabled={loading}
            className="flex items-center gap-2 px-8 py-3 bg-surface-container hover:bg-surface-container-high border border-white/10 rounded-full font-label-caps text-sm tracking-widest font-bold text-white transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <span className="w-5 h-5 border-2 border-primary-container border-t-transparent rounded-full animate-spin"></span>
            ) : (
              <span className="material-symbols-outlined text-[18px]">expand_more</span>
            )}
            Yana yuklash
          </button>
        </div>
      )}
    </div>
  );
}
