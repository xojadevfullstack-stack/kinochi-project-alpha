"use client";

import { useState, useEffect } from "react";
import MovieCard from "./MovieCard";
import { CatalogItem, getPageContent } from "@/lib/api/catalog";
import { fetchApi } from "@/lib/api";

export type CatalogGridProps = {
  initialItems: CatalogItem[];
  total: number;
  type?: "movies" | "series" | "page";
  pageSlug?: string;
  pageId?: number;
  categoryId?: string;
  pageSize?: number;
  emptyMessage?: string;
};

export default function CatalogGrid({
  initialItems,
  total: initialTotal,
  type = "movies",
  pageSlug = "",
  pageId,
  categoryId,
  pageSize = 36,
  emptyMessage = "Hozircha ma'lumotlar mavjud emas."
}: CatalogGridProps) {
  const [items, setItems] = useState<CatalogItem[]>(initialItems);
  const [total, setTotal] = useState(initialTotal);
  const [loading, setLoading] = useState(false);

  // Sync state if initialItems or total changes from parent SSR
  useEffect(() => {
    setItems(initialItems);
    setTotal(initialTotal);
  }, [initialItems, initialTotal]);

  const hasMore = items.length < total;

  const loadMore = async () => {
    if (loading || !hasMore) return;
    setLoading(true);

    try {
      let newItems: CatalogItem[] = [];
      let nextTotal = total;

      if (type === "movies") {
        let url = `/movies?skip=${items.length}&limit=${pageSize}&exclude_paged=true`;
        if (categoryId) url += `&category_id=${categoryId}`;
        const res = await fetchApi(url);
        newItems = (res?.items || []).map((m: any) => ({ ...m, is_series: false }));
        if (res?.total !== undefined) nextTotal = res.total;
      } else if (type === "series") {
        let url = `/series?skip=${items.length}&limit=${pageSize}&exclude_paged=true`;
        if (categoryId) url += `&category_id=${categoryId}`;
        const res = await fetchApi(url);
        newItems = (res?.items || []).map((s: any) => ({ ...s, is_series: true }));
        if (res?.total !== undefined) nextTotal = res.total;
      } else if (type === "page" && pageSlug) {
        const res = await getPageContent(pageSlug, items.length, pageSize, categoryId);
        newItems = res.items || [];
        if (res.total !== undefined) nextTotal = res.total;
      }

      if (newItems.length > 0) {
        setItems(prev => {
          const seen = new Set(prev.map(i => `${i.is_series ? 's' : 'm'}-${i.id || i.code}`));
          const unique = newItems.filter(i => !seen.has(`${i.is_series ? 's' : 'm'}-${i.id || i.code}`));
          return [...prev, ...unique];
        });
        setTotal(nextTotal);
      } else {
        // If no new items returned, prevent endless loading button
        setTotal(items.length);
      }
    } catch (error) {
      console.error("Failed to load more items:", error);
    } finally {
      setLoading(false);
    }
  };

  if (!items || items.length === 0) {
    return (
      <div className="text-center py-20 text-text-secondary bg-surface-container/20 rounded-2xl border border-white/5">
        <span className="material-symbols-outlined text-6xl mb-4 opacity-50">movie</span>
        <p className="font-body-lg">{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col">
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4 md:gap-6">
        {items.map((item, idx) => (
          <MovieCard 
            key={`${item.is_series ? 's' : 'm'}-${item.id || item.code}-${idx}`} 
            item={item} 
          />
        ))}
      </div>
      
      {hasMore ? (
        <div className="mt-12 flex flex-col items-center justify-center gap-2">
          <button 
            onClick={loadMore} 
            disabled={loading}
            className="flex items-center justify-center gap-2 h-12 px-8 bg-white/10 hover:bg-white/15 border border-white/15 hover:border-white/30 rounded-xl font-label-caps text-xs sm:text-sm uppercase tracking-widest font-bold text-white shadow-md shadow-black/20 transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100 disabled:hover:translate-y-0 cursor-pointer"
          >
            {loading ? (
              <span className="w-5 h-5 border-2 border-primary-container border-t-transparent rounded-full animate-spin"></span>
            ) : (
              <span className="material-symbols-outlined text-[18px]">expand_more</span>
            )}
            <span>Yana yuklash</span>
          </button>
          <span className="text-xs text-text-secondary font-medium tracking-wide">
            {total > 0 ? `Jami ${total} tadan ${items.length} tasi ko'rsatilmoqda` : `${items.length} ta kontent yuklandi`}
          </span>
        </div>
      ) : (
        items.length > 12 && (
          <div className="mt-12 text-center text-xs text-text-secondary/70">
            <span>Barcha {items.length} ta kontent ko'rsatildi</span>
          </div>
        )
      )}
    </div>
  );
}
