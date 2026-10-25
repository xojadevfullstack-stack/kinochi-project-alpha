"use client";

import React, { useState } from "react";
import ThemedCollectionCard from "@/components/catalog/ThemedCollectionCard";
import { CURATED_CATALOG_THEMES, CatalogTheme } from "@/lib/catalogThemes";

interface Collection {
  id: number;
  name: string;
  slug: string;
  description?: string | null;
  poster_url?: string | null;
  banner_url?: string | null;
  is_franchise: boolean;
  category_type?: string;
  is_active: boolean;
  sort_order: number;
  items_count: number;
  posters?: string[];
}

interface CollectionsClientViewProps {
  initialCollections: Collection[];
}

export default function CollectionsClientView({
  initialCollections = [],
}: CollectionsClientViewProps) {
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState<string>("");

  const categories = [
    { id: "all", label: "Barchasi" },
    { id: "theme", label: "Qiziqarli mavzular" },
    { id: "franchise", label: "Franshizalar" },
    { id: "genre", label: "Janrlar bo'yicha" },
  ];

  // Map backend collections into theme card format (strictly real collections with items_count > 0)
  const allThemes: CatalogTheme[] = (initialCollections || [])
    .filter((col) => col.is_active !== false && (col.items_count === undefined || col.items_count > 0))
    .map((col) => {
      const posterList = col.posters && col.posters.length > 0 
        ? col.posters 
        : [
            col.poster_url || col.banner_url || "https://image.tmdb.org/t/p/w500/yF1eOkaYvwiORauRCPWznV9xVvi.jpg",
            col.banner_url || col.poster_url || "https://image.tmdb.org/t/p/w500/wuMc08IPKEatf9rnMNXvIDxqP4W.jpg",
            col.poster_url || "https://image.tmdb.org/t/p/w500/fiVW06jE7z9YnO4trhaMEdclSiC.jpg"
          ];

      return {
        id: `col-${col.id}`,
        title: col.name,
        count: `${col.items_count || 0} ta kino`,
        href: `/collections/${col.slug}`,
        category: (col.is_franchise ? "franchise" : "theme") as "franchise" | "theme",
        description: col.description || "Ushbu to'plamdagi barcha filmlar va ularning tartibi.",
        posters: posterList
      };
    });

  const filtered = allThemes.filter((item) => {
    // Category filter
    if (selectedCategory !== "all" && item.category !== selectedCategory) {
      return false;
    }

    // Search filter
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchTitle = item.title.toLowerCase().includes(q);
      const matchDesc = item.description?.toLowerCase().includes(q);
      return matchTitle || matchDesc;
    }

    return true;
  });

  return (
    <div className="space-y-6">
      {/* Header Description & Search Bar */}
      <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4 bg-white/5 border border-white/10 p-4 sm:p-5 rounded-2xl shadow-xl">
        {/* Categories Filter Tabs */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 md:pb-0 scrollbar-none">
          {categories.map((cat) => (
            <button
              key={cat.id}
              onClick={() => setSelectedCategory(cat.id)}
              className={`px-3.5 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition-all cursor-pointer ${
                selectedCategory === cat.id
                  ? "bg-white/15 text-white font-bold border border-white/20 shadow-sm"
                  : "bg-white/5 text-text-secondary hover:text-white hover:bg-white/10 border border-white/5"
              }`}
            >
              {cat.label}
            </button>
          ))}
        </div>

        {/* Live Search */}
        <div className="relative min-w-[240px]">
          <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-text-secondary text-lg pointer-events-none">
            search
          </span>
          <input
            type="text"
            placeholder="To'plam yoki mavzuni qidirish..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-white/5 border border-white/10 rounded-xl pl-10 pr-4 py-2 text-white text-xs outline-none focus:border-white/20 transition-colors"
          />
        </div>
      </div>

      {/* Grid of Themed Collections with Fanned 3-Poster Decks (Iconic Asilmedia Layout) */}
      {filtered.length === 0 ? (
        <div className="text-center py-16 bg-white/5 border border-white/10 rounded-3xl p-8">
          <span className="material-symbols-outlined text-4xl text-text-secondary mb-3">
            folder_off
          </span>
          <h3 className="text-white font-bold text-base mb-1">Hech qanday to'plam topilmadi</h3>
          <p className="text-text-secondary text-xs">
            Qidiruv so'rovingizni o'zgartirib ko'ring yoki boshqa toifani tanlang.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 sm:gap-6">
          {filtered.map((item) => (
            <ThemedCollectionCard
              key={item.id}
              title={item.title}
              count={item.count}
              href={item.href}
              posters={item.posters}
              description={item.description}
            />
          ))}
        </div>
      )}
    </div>
  );
}
