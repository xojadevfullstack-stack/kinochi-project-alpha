"use client";

import { useState, useRef, useEffect } from "react";
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

interface SelectOption {
  id: string;
  name: string;
  icon?: string;
}

interface SearchableDropdownProps {
  label: string;
  icon: string;
  placeholder: string;
  searchPlaceholder: string;
  options: SelectOption[];
  selectedValue?: string | null;
  isOpen: boolean;
  onToggle: () => void;
  onClose: () => void;
  onSelect: (value: string | null) => void;
}

function SearchableDropdown({
  label,
  icon,
  placeholder,
  searchPlaceholder,
  options,
  selectedValue,
  isOpen,
  onToggle,
  onClose,
  onSelect,
}: SearchableDropdownProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Close dropdown on click outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        containerRef.current &&
        !containerRef.current.contains(event.target as Node)
      ) {
        onClose();
      }
    }

    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isOpen, onClose]);

  // Autofocus input when dropdown opens
  useEffect(() => {
    if (isOpen) {
      setSearchQuery("");
      const timer = setTimeout(() => {
        inputRef.current?.focus();
      }, 50);
      return () => clearTimeout(timer);
    }
  }, [isOpen]);

  const activeOption = options.find((opt) => opt.id === selectedValue);

  // Filter options based on typed query
  const filteredOptions = options.filter((opt) =>
    opt.name.toLowerCase().includes(searchQuery.toLowerCase().trim())
  );

  return (
    <div ref={containerRef} className="relative w-full">
      {/* ── Input Trigger Button ── */}
      <div
        onClick={onToggle}
        className={`w-full bg-[#141720] hover:bg-[#1a1e2a] border transition-all duration-200 rounded-xl px-3.5 py-2.5 text-left flex items-center justify-between cursor-pointer select-none group ${
          isOpen
            ? "border-primary-container shadow-md shadow-primary-container/10 ring-1 ring-primary-container/40"
            : selectedValue
            ? "border-primary-container/50 bg-primary-container/5"
            : "border-white/10 hover:border-white/20"
        }`}
      >
        <div className="flex items-center gap-2.5 min-w-0 pr-2">
          <span
            className={`material-symbols-outlined text-[19px] shrink-0 transition-colors ${
              selectedValue || isOpen
                ? "text-primary-container"
                : "text-zinc-400 group-hover:text-zinc-200"
            }`}
          >
            {activeOption?.icon || icon}
          </span>
          <div className="min-w-0 flex flex-col">
            <span className="text-[10px] uppercase font-bold tracking-wider text-zinc-400 leading-tight truncate">
              {label}
            </span>
            <span
              className={`text-xs sm:text-sm font-semibold truncate leading-snug ${
                selectedValue
                  ? "text-white font-bold"
                  : "text-zinc-400 font-normal"
              }`}
            >
              {activeOption ? activeOption.name : placeholder}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-1 shrink-0 ml-1">
          {/* Quick Clear Button (✕) if value is selected */}
          {selectedValue && (
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                onSelect(null);
              }}
              className="w-5 h-5 rounded-full hover:bg-white/15 text-zinc-400 hover:text-white flex items-center justify-center transition text-xs"
              title="Tozalash"
            >
              ✕
            </button>
          )}

          <span
            className={`material-symbols-outlined text-[18px] text-zinc-400 transition-transform duration-200 ${
              isOpen ? "rotate-180 text-primary-container" : ""
            }`}
          >
            expand_more
          </span>
        </div>
      </div>

      {/* ── Dropdown Popover (Combobox) ── */}
      {isOpen && (
        <div className="absolute left-0 right-0 top-full mt-2 z-50 bg-[#12151d] border border-white/15 rounded-2xl p-2.5 shadow-2xl backdrop-blur-2xl animate-in fade-in slide-in-from-top-1 duration-150 min-w-[220px]">
          {/* 1. Quick Search Input at top of dropdown */}
          <div className="relative mb-2">
            <span className="material-symbols-outlined absolute left-2.5 top-1/2 -translate-y-1/2 text-zinc-500 text-[17px] pointer-events-none">
              search
            </span>
            <input
              ref={inputRef}
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder={searchPlaceholder}
              className="w-full bg-white/5 border border-white/10 rounded-xl pl-8 pr-7 py-1.5 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-primary-container focus:ring-1 focus:ring-primary-container transition"
            />
            {searchQuery && (
              <button
                type="button"
                onClick={() => setSearchQuery("")}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-white text-xs p-0.5"
              >
                ✕
              </button>
            )}
          </div>

          {/* 2. Scrollable / Touch-friendly List of Options */}
          <div className="max-h-56 overflow-y-auto custom-scrollbar space-y-0.5 pr-1">
            {/* "Barchasi" (Reset) option */}
            <button
              type="button"
              onClick={() => {
                onSelect(null);
                onClose();
              }}
              className={`w-full px-3 py-2 rounded-lg text-xs font-medium flex items-center justify-between transition cursor-pointer text-left ${
                !selectedValue
                  ? "bg-primary-container text-white font-bold shadow-sm"
                  : "text-zinc-300 hover:bg-white/10 hover:text-white"
              }`}
            >
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-[16px] opacity-75">
                  apps
                </span>
                <span>{placeholder}</span>
              </div>
              {!selectedValue && (
                <span className="material-symbols-outlined text-[16px]">
                  check
                </span>
              )}
            </button>

            {/* Filtered options list */}
            {filteredOptions.map((opt) => {
              const isSelected = selectedValue === opt.id;
              return (
                <button
                  key={opt.id}
                  type="button"
                  onClick={() => {
                    onSelect(opt.id);
                    onClose();
                  }}
                  className={`w-full px-3 py-2 rounded-lg text-xs font-medium flex items-center justify-between transition cursor-pointer text-left ${
                    isSelected
                      ? "bg-primary-container text-white font-bold shadow-sm"
                      : "text-zinc-300 hover:bg-white/10 hover:text-white"
                  }`}
                >
                  <div className="flex items-center gap-2 truncate">
                    {opt.icon && (
                      <span className="material-symbols-outlined text-[16px] opacity-75 shrink-0">
                        {opt.icon}
                      </span>
                    )}
                    <span className="truncate">{opt.name}</span>
                  </div>
                  {isSelected && (
                    <span className="material-symbols-outlined text-[16px] shrink-0">
                      check
                    </span>
                  )}
                </button>
              );
            })}

            {filteredOptions.length === 0 && (
              <div className="text-center py-4 text-xs text-zinc-500">
                Mos variant topilmadi
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
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
  totalItems,
}: UnifiedFilterBarProps) {
  const router = useRouter();

  // Unified panel open state
  const [isOpen, setIsOpen] = useState(
    Boolean(selectedCategory || selectedGenre || selectedYear || selectedType)
  );

  // Track which dropdown is currently open (only one at a time)
  const [openDropdown, setOpenDropdown] = useState<
    "category" | "type" | "genre" | "year" | null
  >(null);

  // Calculate active filter count
  const activeCount = [
    selectedCategory,
    selectedType,
    selectedGenre,
    selectedYear,
  ].filter(Boolean).length;

  // Find active labels for display badges
  const activeCategoryObj = categories.find(
    (c) => String(c.id) === String(selectedCategory)
  );
  const activeTypeObj = types.find((t) => t.id === selectedType);
  const activeGenreObj = genres.find((g) => g.id === selectedGenre);

  // Helper to obtain current URL search params without triggering SSR bailout
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
  const updateFilter = (
    type: "category" | "type" | "genre" | "year",
    value?: string | number | null
  ) => {
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

  // Convert categories to SelectOption format
  const categoryOptions: SelectOption[] = categories.map((c) => ({
    id: String(c.id),
    name: c.name,
  }));

  // Convert types to SelectOption format
  const typeOptions: SelectOption[] = types.map((t) => ({
    id: t.id,
    name: t.name,
    icon: t.icon,
  }));

  // Convert genres to SelectOption format
  const genreOptions: SelectOption[] = genres.map((g) => ({
    id: g.id,
    name: g.name,
    icon: g.icon,
  }));

  // Convert years to SelectOption format
  const yearOptions: SelectOption[] = years.map((y) => ({
    id: String(y),
    name: String(y),
  }));

  return (
    <div className="w-full space-y-3">
      {/* ── 1. MAIN FILTRLAR HEADER ROW ── */}
      <div className="flex flex-wrap items-center justify-between gap-3 bg-[#111318]/90 backdrop-blur-md border border-white/10 rounded-2xl p-3 sm:p-4 shadow-lg">
        <div className="flex flex-wrap items-center gap-2">
          {/* THE MASTER FILTRLAR TOGGLE BUTTON */}
          <button
            type="button"
            onClick={() => setIsOpen((prev) => !prev)}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl font-bold text-xs sm:text-sm transition-all duration-200 cursor-pointer shadow-md select-none ${
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
            <span
              className={`material-symbols-outlined text-[18px] opacity-70 transition-transform duration-200 ${
                isOpen ? "rotate-180" : ""
              }`}
            >
              expand_more
            </span>
          </button>

          {/* ACTIVE FILTER BADGE CHIPS (Removable tags) */}
          {activeCategoryObj && (
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/10 border border-white/15 text-xs font-semibold text-white animate-fade-in">
              <span className="text-zinc-400">Bo'lim:</span>
              <span className="text-red-400 font-bold">
                {activeCategoryObj.name}
              </span>
              <button
                type="button"
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
                type="button"
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
              <span className="text-red-400 font-bold">
                {activeGenreObj.name}
              </span>
              <button
                type="button"
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
                type="button"
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
              type="button"
              onClick={clearAllFilters}
              className="text-xs text-text-secondary hover:text-red-400 underline decoration-dotted transition px-2 py-1 cursor-pointer"
            >
              Barchasini tozalash
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

      {/* ── 2. EXPANDABLE 4-INPUT FILTER PANEL (When "Filtrlar" is toggled open) ── */}
      {isOpen && (
        <div className="bg-[#101217]/95 backdrop-blur-xl border border-white/10 rounded-2xl p-4 sm:p-5 shadow-2xl animate-in fade-in slide-in-from-top-2 duration-200">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
            {/* Input 1: Bo'limlar (Toifalar) */}
            <SearchableDropdown
              label="Bo'lim (Toifa)"
              icon="category"
              placeholder="Barcha bo'limlar"
              searchPlaceholder="Bo'lim qidirish..."
              options={categoryOptions}
              selectedValue={selectedCategory}
              isOpen={openDropdown === "category"}
              onToggle={() =>
                setOpenDropdown((cur) => (cur === "category" ? null : "category"))
              }
              onClose={() =>
                setOpenDropdown((cur) => (cur === "category" ? null : cur))
              }
              onSelect={(val) => updateFilter("category", val)}
            />

            {/* Input 2: Turi (Format) */}
            <SearchableDropdown
              label="Turi (Format)"
              icon="video_library"
              placeholder="Barcha turlar"
              searchPlaceholder="Tur qidirish..."
              options={typeOptions}
              selectedValue={selectedType}
              isOpen={openDropdown === "type"}
              onToggle={() =>
                setOpenDropdown((cur) => (cur === "type" ? null : "type"))
              }
              onClose={() =>
                setOpenDropdown((cur) => (cur === "type" ? null : cur))
              }
              onSelect={(val) => updateFilter("type", val)}
            />

            {/* Input 3: Janrlar */}
            <SearchableDropdown
              label="Janr"
              icon="theater_comedy"
              placeholder="Barcha janrlar"
              searchPlaceholder="Janr qidirish... (masalan, Jangari)"
              options={genreOptions}
              selectedValue={selectedGenre}
              isOpen={openDropdown === "genre"}
              onToggle={() =>
                setOpenDropdown((cur) => (cur === "genre" ? null : "genre"))
              }
              onClose={() =>
                setOpenDropdown((cur) => (cur === "genre" ? null : cur))
              }
              onSelect={(val) => updateFilter("genre", val)}
            />

            {/* Input 4: Chiqarilgan yili */}
            <SearchableDropdown
              label="Chiqarilgan yili"
              icon="calendar_month"
              placeholder="Barcha yillar"
              searchPlaceholder="Yil qidirish... (masalan, 2024)"
              options={yearOptions}
              selectedValue={selectedYear}
              isOpen={openDropdown === "year"}
              onToggle={() =>
                setOpenDropdown((cur) => (cur === "year" ? null : "year"))
              }
              onClose={() =>
                setOpenDropdown((cur) => (cur === "year" ? null : cur))
              }
              onSelect={(val) => updateFilter("year", val)}
            />
          </div>
        </div>
      )}
    </div>
  );
}
