"use client";

import React, { useState } from "react";
import Link from "next/link";
import Image from "next/image";

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
}

interface CollectionsClientViewProps {
  initialCollections: Collection[];
}

export default function CollectionsClientView({
  initialCollections,
}: CollectionsClientViewProps) {
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState<string>("");

  const categories = [
    { id: "all", label: "Barchasi", icon: "apps" },
    { id: "franchise", label: "🌌 Franshizalar (Barcha qismlari)", icon: "movie" },
    { id: "thematic", label: "📂 Mavzuli to'plamlar", icon: "folder_special" },
    { id: "actor", label: "👤 Aktyor & Rejissyorlar", icon: "person" },
    { id: "genre", label: "🎭 Janrlar bo'yicha", icon: "theater_comedy" },
    { id: "country", label: "🌍 Davlatlar bo'yicha", icon: "public" },
  ];

  const filtered = initialCollections.filter((col) => {
    // Category filter
    if (selectedCategory !== "all") {
      const colCat = col.category_type || (col.is_franchise ? "franchise" : "thematic");
      if (colCat !== selectedCategory) return false;
    }

    // Search filter
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchName = col.name.toLowerCase().includes(q);
      const matchDesc = col.description?.toLowerCase().includes(q);
      return matchName || matchDesc;
    }

    return true;
  });

  return (
    <div className="space-y-8">
      {/* Search and Tabs Filter Bar */}
      <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4 bg-surface-container-lowest/80 backdrop-blur-xl border border-white/10 p-4 sm:p-5 rounded-2xl shadow-xl">
        {/* Categories Tabs */}
        <div className="flex items-center gap-2 overflow-x-auto pb-2 md:pb-0 scrollbar-none">
          {categories.map((cat) => (
            <button
              key={cat.id}
              onClick={() => setSelectedCategory(cat.id)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold whitespace-nowrap transition-all cursor-pointer ${
                selectedCategory === cat.id
                  ? "bg-primary-container text-white shadow-lg shadow-primary-container/20"
                  : "bg-white/5 text-text-secondary hover:text-white hover:bg-white/10"
              }`}
            >
              <span>{cat.label}</span>
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
            placeholder="To'plamlardan qidirish..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-white/5 border border-white/10 rounded-xl pl-10 pr-4 py-2 text-white text-xs outline-none focus:border-primary-container transition-colors"
          />
        </div>
      </div>

      {/* Grid of Collections */}
      {filtered.length === 0 ? (
        <div className="text-center py-16 bg-surface-container-lowest/40 border border-white/5 rounded-3xl p-8">
          <span className="material-symbols-outlined text-4xl text-text-secondary mb-3">
            folder_off
          </span>
          <h3 className="text-white font-bold text-base mb-1">Hech qanday to'plam topilmadi</h3>
          <p className="text-text-secondary text-xs">
            Qidiruv so'rovingizni o'zgartirib ko'ring yoki boshqa toifani tanlang.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 sm:gap-8">
          {filtered.map((col) => (
            <Link
              key={col.id}
              href={`/collections/${col.slug}`}
              className="group flex flex-col bg-surface-container-lowest/80 hover:bg-surface-container-low/90 border border-white/10 hover:border-primary-container/50 rounded-2xl overflow-hidden transition-all duration-300 hover:scale-[1.02] hover:shadow-2xl hover:shadow-primary-container/10"
            >
              {/* Banner / Poster Section */}
              <div className="relative aspect-[16/9] w-full bg-surface-container overflow-hidden">
                {col.banner_url || col.poster_url ? (
                  <Image
                    src={col.banner_url || col.poster_url || ""}
                    alt={col.name}
                    fill
                    sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
                    unoptimized
                    className="object-cover group-hover:scale-105 transition-transform duration-500"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-white/20">
                    <span className="material-symbols-outlined text-5xl">auto_awesome_motion</span>
                  </div>
                )}
                <div className="absolute inset-0 bg-gradient-to-t from-background-obsidian via-background-obsidian/40 to-transparent"></div>

                {/* Items Count Badge */}
                <div className="absolute top-3 right-3 px-2.5 py-1 rounded-lg bg-black/75 backdrop-blur-md border border-white/15 text-white text-xs font-bold flex items-center gap-1.5 shadow-lg">
                  <span className="material-symbols-outlined text-[14px] text-primary-container">
                    movie
                  </span>
                  <span>{col.items_count} ta qism</span>
                </div>

                {/* Category Badge */}
                <div className="absolute top-3 left-3 px-2.5 py-1 rounded-lg bg-primary-container/90 backdrop-blur-md text-white text-[10px] font-extrabold uppercase tracking-wider shadow-lg">
                  {col.category_type === "thematic"
                    ? "Mavzuli"
                    : col.category_type === "actor"
                    ? "Aktyor"
                    : col.category_type === "genre"
                    ? "Janr"
                    : col.category_type === "country"
                    ? "Davlat"
                    : "Franshiza"}
                </div>
              </div>

              {/* Content Body */}
              <div className="p-5 flex-1 flex flex-col justify-between">
                <div>
                  <h3 className="text-lg font-bold text-white group-hover:text-primary-container transition-colors mb-2 line-clamp-1">
                    {col.name}
                  </h3>
                  <p className="text-text-secondary text-xs line-clamp-2 leading-relaxed">
                    {col.description || "Ushbu to'plamdagi barcha filmlar va ularning tartibi."}
                  </p>
                </div>

                <div className="mt-4 pt-4 border-t border-white/5 flex items-center justify-between text-xs font-bold text-primary-container">
                  <span className="flex items-center gap-1 group-hover:underline">
                    <span>Xronologiyani ko'rish</span>
                    <span className="material-symbols-outlined text-[16px] group-hover:translate-x-1 transition-transform">
                      arrow_forward
                    </span>
                  </span>
                  <span className="text-white/40 text-[11px] font-normal font-mono">
                    #{col.slug}
                  </span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
