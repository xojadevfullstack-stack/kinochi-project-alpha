"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  CategoryItem,
  GenreItem,
  MediaTypeItem,
  DEFAULT_GENRES,
  DEFAULT_YEARS,
  DEFAULT_MEDIA_TYPES,
} from "@/lib/filterConstants";

export type { CategoryItem, GenreItem, MediaTypeItem };
export { DEFAULT_GENRES, DEFAULT_YEARS, DEFAULT_MEDIA_TYPES };

export interface UnifiedFilterBarProps {
  categories: CategoryItem[];
  genres?: GenreItem[];
  years?: number[];
  types?: MediaTypeItem[];
  selectedCategory?: string;
  selectedGenre?: string;
  selectedYear?: string;
  selectedType?: string;
  baseUrl?: string;
  totalItems?: number;
}

export default function UnifiedFilterBar({
  categories = [],
  genres = DEFAULT_GENRES,
  years = DEFAULT_YEARS,
  types = DEFAULT_MEDIA_TYPES,
  selectedCategory,
  selectedGenre,
  selectedYear,
  selectedType,
  baseUrl = "/catalog",
  totalItems
}: UnifiedFilterBarProps) {
  const router = useRouter();

  // Unified panel open state
  const [isOpen, setIsOpen] = useState(
    Boolean(selectedCategory || selectedGenre || selectedYear || selectedType)
  );
  
  // Currently active filter group tab: "categories" | "types" | "genres" | "years"
  const [activeTab, setActiveTab] = useState<"categories" | "types" | "genres" | "years">(
    selectedType
      ? "types"
      : selectedGenre
      ? "genres"
      : selectedYear
      ? "years"
      : "categories"
  );

  // Calculate active filter count
  const activeCount = [selectedCategory, selectedType, selectedGenre, selectedYear].filter(Boolean).length;

  // Find active labels
  const activeCategoryObj = categories.find((c) => String(c.id) === String(selectedCategory));
  const activeTypeObj = types.find((t) => t.id === selectedType);
  const activeGenreObj = genres.find((g) => g.id === selectedGenre);

  // Helper to obtain current URL search params without triggering Next.js useSearchParams SSR bailout
  const getCurrentParams = () => {
    if (typeof window !== "undefined") {
      return new URLSearchParams(window.location.search);
    }
    const params = new URLSearchParams();
    if (selectedCategory) params.set("category", String(selectedCategory));
    if (selectedType) params.set("type", selectedType);
    if (selectedGenre) params.set("genre", selectedGenre);
    if (selectedYear) params.set("year", String(selectedYear));
    return params;
  };

  // Helper to update query parameters
  const updateFilter = (type: "category" | "type" | "genre" | "year", value?: string | number | null) => {
    const params = getCurrentParams();
    
    if (value !== undefined && value !== null && value !== "") {
      params.set(type, String(value));
    } else {
      params.delete(type);
    }

    const queryString = params.toString();
    const targetUrl = queryString ? `${baseUrl}?${queryString}` : baseUrl;
    router.push(targetUrl);
  };

  const clearAllFilters = () => {
    const params = getCurrentParams();
    params.delete("category");
    params.delete("type");
    params.delete("genre");
    params.delete("year");
    params.delete("search");
    const queryString = params.toString();
    router.push(queryString ? `${baseUrl}?${queryString}` : baseUrl);
  };

  return (
    <div className="w-full space-y-3">
      {/* 1. MAIN UNIFIED "FILTRLAR" BUTTON ROW */}
      <div className="flex flex-wrap items-center justify-between gap-3 bg-[#111318]/90 backdrop-blur-md border border-white/10 rounded-2xl p-3 sm:p-4 shadow-lg">
        <div className="flex flex-wrap items-center gap-2">
          {/* THE MASTER FILTRLAR BUTTON */}
          <button
            onClick={() => setIsOpen((prev) => !prev)}
            className={`flex items-center gap-2.5 px-4 py-2.5 rounded-xl font-bold text-xs sm:text-sm transition-all duration-200 cursor-pointer shadow-md select-none ${
              isOpen || activeCount > 0
                ? "bg-primary-container text-white border border-primary-container/40 shadow-primary-container/20 scale-[1.02]"
                : "bg-white/10 hover:bg-white/15 text-white border border-white/10"
            }`}
          >
            <span className="material-symbols-outlined text-[19px]">tune</span>
            <span>Filtrlar</span>
            {activeCount > 0 && (
              <span className="w-5 h-5 rounded-full bg-white text-black font-extrabold text-[11px] flex items-center justify-center shadow">
                {activeCount}
              </span>
            )}
            <span className="material-symbols-outlined text-[18px] opacity-70 transition-transform duration-200">
              {isOpen ? "expand_less" : "expand_more"}
            </span>
          </button>

          {/* ACTIVE FILTER BADGE CHIPS (Removable tags) */}
          {activeCategoryObj && (
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/10 border border-white/15 text-xs font-semibold text-white animate-fade-in">
              <span className="text-zinc-400">Bo'lim:</span>
              <span className="text-red-400 font-bold">{activeCategoryObj.name}</span>
              <button
                onClick={() => updateFilter("category", null)}
                className="hover:text-red-400 transition ml-1"
                title="Tozalash"
              >
                ✕
              </button>
            </div>
          )}

          {activeTypeObj && (
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/10 border border-white/15 text-xs font-semibold text-white animate-fade-in">
              <span className="text-zinc-400">Turi:</span>
              <span className="text-red-400 font-bold">{activeTypeObj.name}</span>
              <button
                onClick={() => updateFilter("type", null)}
                className="hover:text-red-400 transition ml-1"
                title="Tozalash"
              >
                ✕
              </button>
            </div>
          )}

          {activeGenreObj && (
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/10 border border-white/15 text-xs font-semibold text-white animate-fade-in">
              <span className="text-zinc-400">Janr:</span>
              <span className="text-red-400 font-bold">{activeGenreObj.name}</span>
              <button
                onClick={() => updateFilter("genre", null)}
                className="hover:text-red-400 transition ml-1"
                title="Tozalash"
              >
                ✕
              </button>
            </div>
          )}

          {selectedYear && (
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/10 border border-white/15 text-xs font-semibold text-white animate-fade-in">
              <span className="text-zinc-400">Yil:</span>
              <span className="text-red-400 font-bold">{selectedYear}</span>
              <button
                onClick={() => updateFilter("year", null)}
                className="hover:text-red-400 transition ml-1"
                title="Tozalash"
              >
                ✕
              </button>
            </div>
          )}

          {activeCount > 0 && (
            <button
              onClick={clearAllFilters}
              className="text-xs text-text-secondary hover:text-red-400 underline decoration-dotted transition px-2 py-1"
            >
              Tozalash
            </button>
          )}
        </div>

        {/* Counter of matching results */}
        {typeof totalItems === "number" && (
          <div className="text-xs text-zinc-400 font-medium">
            Topilgan: <span className="font-bold text-white">{totalItems} ta</span>
          </div>
        )}
      </div>

      {/* 2. EXPANDABLE FILTER CONTAINER (When "Filtrlar" is active) */}
      {isOpen && (
        <div className="bg-[#101217]/95 backdrop-blur-xl border border-white/10 rounded-2xl p-4 sm:p-5 shadow-2xl space-y-4 animate-in fade-in slide-in-from-top-2 duration-200">
          
          {/* THE 4 EXTENSIBLE SUB-FILTER BUTTONS / TABS */}
          <div className="flex items-center gap-2 border-b border-white/10 pb-3 overflow-x-auto hide-scrollbar">
            
            {/* Sub-button 1: Bo'limlar (Toifalar) */}
            <button
              onClick={() => setActiveTab("categories")}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs sm:text-sm font-bold transition-all cursor-pointer whitespace-nowrap ${
                activeTab === "categories"
                  ? "bg-primary-container text-white border border-primary-container/40 shadow-md shadow-primary-container/20"
                  : "bg-white/5 hover:bg-white/10 text-zinc-400 hover:text-white border border-white/5"
              }`}
            >
              <span className="material-symbols-outlined text-[17px]">category</span>
              <span>Bo'limlar (Toifalar)</span>
              {selectedCategory && (
                <span className="w-2 h-2 rounded-full bg-white" />
              )}
            </button>

            {/* Sub-button 2: Turi (Format) */}
            <button
              onClick={() => setActiveTab("types")}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs sm:text-sm font-bold transition-all cursor-pointer whitespace-nowrap ${
                activeTab === "types"
                  ? "bg-primary-container text-white border border-primary-container/40 shadow-md shadow-primary-container/20"
                  : "bg-white/5 hover:bg-white/10 text-zinc-400 hover:text-white border border-white/5"
              }`}
            >
              <span className="material-symbols-outlined text-[17px]">video_library</span>
              <span>Turi (Format)</span>
              {selectedType && (
                <span className="w-2 h-2 rounded-full bg-white" />
              )}
            </button>

            {/* Sub-button 3: Janrlar */}
            <button
              onClick={() => setActiveTab("genres")}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs sm:text-sm font-bold transition-all cursor-pointer whitespace-nowrap ${
                activeTab === "genres"
                  ? "bg-primary-container text-white border border-primary-container/40 shadow-md shadow-primary-container/20"
                  : "bg-white/5 hover:bg-white/10 text-zinc-400 hover:text-white border border-white/5"
              }`}
            >
              <span className="material-symbols-outlined text-[17px]">theater_comedy</span>
              <span>Janrlar</span>
              {selectedGenre && (
                <span className="w-2 h-2 rounded-full bg-white" />
              )}
            </button>

            {/* Sub-button 4: Chiqarilgan yili */}
            <button
              onClick={() => setActiveTab("years")}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs sm:text-sm font-bold transition-all cursor-pointer whitespace-nowrap ${
                activeTab === "years"
                  ? "bg-primary-container text-white border border-primary-container/40 shadow-md shadow-primary-container/20"
                  : "bg-white/5 hover:bg-white/10 text-zinc-400 hover:text-white border border-white/5"
              }`}
            >
              <span className="material-symbols-outlined text-[17px]">calendar_month</span>
              <span>Chiqarilgan yili</span>
              {selectedYear && (
                <span className="w-2 h-2 rounded-full bg-white" />
              )}
            </button>
          </div>

          {/* 3. SELECTABLE OPTION VARIANTS FOR ACTIVE TAB */}
          <div>
            {/* OPTIONS FOR: BO'LIMLAR (TOIFALAR) */}
            {activeTab === "categories" && (
              <div className="flex flex-wrap items-center gap-2 max-h-56 overflow-y-auto pr-1 py-1 custom-scrollbar">
                <button
                  onClick={() => updateFilter("category", null)}
                  className={`px-3.5 py-2 rounded-xl text-xs transition-all cursor-pointer ${
                    !selectedCategory
                      ? "bg-primary-container text-white font-black shadow-md border border-primary-container/40"
                      : "bg-white/5 hover:bg-white/15 text-zinc-300 border border-white/5 font-medium"
                  }`}
                >
                  Barcha Bo'limlar
                </button>
                {categories.map((cat) => {
                  const isSelected = String(selectedCategory) === String(cat.id);
                  return (
                    <button
                      key={cat.id}
                      onClick={() => updateFilter("category", isSelected ? null : cat.id)}
                      className={`px-3.5 py-2 rounded-xl text-xs transition-all cursor-pointer ${
                        isSelected
                          ? "bg-primary-container text-white font-black shadow-md border border-primary-container/40 scale-105"
                          : "bg-white/5 hover:bg-white/15 text-zinc-300 border border-white/5 font-medium"
                      }`}
                    >
                      {cat.name}
                    </button>
                  );
                })}
              </div>
            )}

            {/* OPTIONS FOR: TURI (FORMAT) */}
            {activeTab === "types" && (
              <div className="flex flex-wrap items-center gap-2 max-h-56 overflow-y-auto pr-1 py-1 custom-scrollbar">
                <button
                  onClick={() => updateFilter("type", null)}
                  className={`px-3.5 py-2 rounded-xl text-xs transition-all cursor-pointer ${
                    !selectedType
                      ? "bg-primary-container text-white font-black shadow-md border border-primary-container/40"
                      : "bg-white/5 hover:bg-white/15 text-zinc-300 border border-white/5 font-medium"
                  }`}
                >
                  Barcha Turlar
                </button>
                {types.map((t) => {
                  const isSelected = selectedType === t.id;
                  return (
                    <button
                      key={t.id}
                      onClick={() => updateFilter("type", isSelected ? null : t.id)}
                      className={`flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs transition-all cursor-pointer ${
                        isSelected
                          ? "bg-primary-container text-white font-black shadow-md border border-primary-container/40 scale-105"
                          : "bg-white/5 hover:bg-white/15 text-zinc-300 border border-white/5 font-medium"
                      }`}
                    >
                      {t.icon && <span className="material-symbols-outlined text-[15px] opacity-80">{t.icon}</span>}
                      <span>{t.name}</span>
                    </button>
                  );
                })}
              </div>
            )}

            {/* OPTIONS FOR: JANRLAR */}
            {activeTab === "genres" && (
              <div className="flex flex-wrap items-center gap-2 max-h-56 overflow-y-auto pr-1 py-1 custom-scrollbar">
                <button
                  onClick={() => updateFilter("genre", null)}
                  className={`px-3.5 py-2 rounded-xl text-xs transition-all cursor-pointer ${
                    !selectedGenre
                      ? "bg-primary-container text-white font-black shadow-md border border-primary-container/40"
                      : "bg-white/5 hover:bg-white/15 text-zinc-300 border border-white/5 font-medium"
                  }`}
                >
                  Barcha Janrlar
                </button>
                {genres.map((g) => {
                  const isSelected = selectedGenre === g.id;
                  return (
                    <button
                      key={g.id}
                      onClick={() => updateFilter("genre", isSelected ? null : g.id)}
                      className={`flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs transition-all cursor-pointer ${
                        isSelected
                          ? "bg-primary-container text-white font-black shadow-md border border-primary-container/40 scale-105"
                          : "bg-white/5 hover:bg-white/15 text-zinc-300 border border-white/5 font-medium"
                      }`}
                    >
                      {g.name}
                    </button>
                  );
                })}
              </div>
            )}

            {/* OPTIONS FOR: CHIQARILGAN YILI */}
            {activeTab === "years" && (
              <div className="flex flex-wrap items-center gap-2 max-h-56 overflow-y-auto pr-1 py-1 custom-scrollbar">
                <button
                  onClick={() => updateFilter("year", null)}
                  className={`px-3.5 py-2 rounded-xl text-xs transition-all cursor-pointer ${
                    !selectedYear
                      ? "bg-primary-container text-white font-black shadow-md border border-primary-container/40"
                      : "bg-white/5 hover:bg-white/15 text-zinc-300 border border-white/5 font-medium"
                  }`}
                >
                  Barcha Yillar
                </button>
                {years.map((y) => {
                  const isSelected = String(selectedYear) === String(y);
                  return (
                    <button
                      key={y}
                      onClick={() => updateFilter("year", isSelected ? null : y)}
                      className={`px-3.5 py-2 rounded-xl text-xs transition-all cursor-pointer ${
                        isSelected
                          ? "bg-primary-container text-white font-black shadow-md border border-primary-container/40 scale-105"
                          : "bg-white/5 hover:bg-white/15 text-zinc-300 border border-white/5 font-medium"
                      }`}
                    >
                      {y}
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
