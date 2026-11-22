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
  categories?: CategoryItem[];
  genres?: GenreItem[];
  years?: number[];
  types?: MediaTypeItem[];
  selectedCategory?: string;
  selectedGenre?: string;
  selectedYear?: string;
  selectedType?: string;
  selectedSort?: string;
  baseUrl?: string;
  totalItems?: number;
}

interface DropdownOption {
  id: string;
  name: string;
}

interface FilterDropdownProps {
  label: string;
  options: DropdownOption[];
  selectedValue?: string | null;
  isOpen: boolean;
  onToggle: () => void;
  onClose: () => void;
  onSelect: (value: string | null) => void;
  showAllOption?: boolean;
}

function FilterDropdown({
  label,
  options,
  selectedValue,
  isOpen,
  onToggle,
  onClose,
  onSelect,
  showAllOption = true,
}: FilterDropdownProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  // Click outside listener
  useEffect(() => {
    function handleClickOutside(event: MouseEvent | TouchEvent) {
      if (
        containerRef.current &&
        !containerRef.current.contains(event.target as Node)
      ) {
        onClose();
      }
    }

    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
      document.addEventListener("touchstart", handleClickOutside);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("touchstart", handleClickOutside);
    };
  }, [isOpen, onClose]);

  const activeOption = options.find((opt) => opt.id === selectedValue);
  const displayText = activeOption ? activeOption.name : label;

  return (
    <div ref={containerRef} className="relative flex-1 min-w-[120px] sm:min-w-[140px]">
      {/* ── Dropdown Trigger Box (iTV / Apple Glass style) ── */}
      <button
        type="button"
        onClick={onToggle}
        className={`w-full border rounded-xl px-3.5 py-2.5 text-left flex items-center justify-between gap-1.5 transition-all select-none cursor-pointer group ${
          isOpen
            ? "bg-slate-50 dark:bg-[#191b24] border-slate-400 dark:border-white/30 text-slate-900 dark:text-white ring-1 ring-slate-300 dark:ring-white/20 shadow-lg"
            : selectedValue
            ? "border-[#D20A13] dark:border-primary text-[#D20A13] dark:text-white bg-red-50 dark:bg-primary/10 font-bold"
            : "bg-white dark:bg-[#13151b] hover:bg-slate-50 dark:hover:bg-[#191b24] border-slate-200 dark:border-white/10 text-slate-700 dark:text-text-secondary hover:text-slate-900 dark:hover:text-white shadow-sm dark:shadow-none"
        }`}
      >
        <span className="text-xs sm:text-[13px] truncate">
          {displayText}
        </span>
        <span
          className={`material-symbols-outlined text-[18px] opacity-70 transition-transform duration-200 shrink-0 ${
            isOpen ? "rotate-180 text-slate-900 dark:text-white" : ""
          }`}
        >
          expand_more
        </span>
      </button>

      {/* ── Popover Option List ── */}
      {isOpen && (
        <div className="absolute left-0 top-full mt-1.5 z-30 min-w-full sm:min-w-[190px] max-h-64 overflow-y-auto hide-scrollbar bg-white dark:bg-[#161822] border border-slate-200 dark:border-white/15 rounded-xl p-1.5 shadow-xl dark:shadow-[0_20px_50px_rgba(0,0,0,0.9)] backdrop-blur-2xl animate-in fade-in duration-150">
          {/* Reset / Barchasi item (Only if showAllOption is enabled) */}
          {showAllOption && (
            <button
              type="button"
              onClick={() => {
                onSelect(null);
                onClose();
              }}
              className={`w-full px-3 py-2 rounded-lg text-xs font-medium flex items-center justify-between transition cursor-pointer text-left ${
                !selectedValue || selectedValue === "all"
                  ? "bg-[#D20A13] dark:bg-primary text-white font-bold"
                  : "text-slate-700 dark:text-zinc-300 hover:bg-slate-100 dark:hover:bg-white/10 hover:text-slate-900 dark:hover:text-white"
              }`}
            >
              <span>Barchasi</span>
              {(!selectedValue || selectedValue === "all") && (
                <span className="material-symbols-outlined text-[15px]">check</span>
              )}
            </button>
          )}

          {/* Options (exclude any duplicate 'all' or 'barchasi') */}
          {options
            .filter((opt) => opt.id !== "all" && opt.name.toLowerCase() !== "barchasi")
            .map((opt) => {
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
                    ? "bg-[#D20A13] dark:bg-primary text-white font-bold"
                    : "text-slate-700 dark:text-zinc-300 hover:bg-slate-100 dark:hover:bg-white/10 hover:text-slate-900 dark:hover:text-white"
                }`}
              >
                <span className="truncate">{opt.name}</span>
                {isSelected && (
                  <span className="material-symbols-outlined text-[15px] shrink-0">
                    check
                  </span>
                )}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

const SORT_OPTIONS: DropdownOption[] = [
  { id: "latest", name: "Eng yangilari" },
  { id: "rating", name: "Reyting bo'yicha" },
];

export default function UnifiedFilterBar({
  categories = [],
  genres = DEFAULT_GENRES,
  years = DEFAULT_YEARS,
  types = DEFAULT_MEDIA_TYPES,
  selectedCategory,
  selectedGenre,
  selectedYear,
  selectedType,
  selectedSort,
  baseUrl = "/catalog",
  totalItems,
}: UnifiedFilterBarProps) {
  const router = useRouter();

  // Active open dropdown tracker
  const [openDropdown, setOpenDropdown] = useState<
    "genre" | "type" | "year" | "sort" | null
  >(null);

  const getCurrentParams = () => {
    if (typeof window !== "undefined") {
      return new URLSearchParams(window.location.search);
    }
    const params = new URLSearchParams();
    if (selectedCategory) params.set("category", String(selectedCategory));
    if (selectedType) params.set("type", selectedType);
    if (selectedGenre) params.set("genre", selectedGenre);
    if (selectedYear) params.set("year", String(selectedYear));
    if (selectedSort) params.set("sort", selectedSort);
    return params;
  };

  const updateFilter = (key: string, value?: string | number | null) => {
    const params = getCurrentParams();
    if (value !== undefined && value !== null && value !== "" && value !== "all") {
      params.set(key, String(value));
    } else {
      params.delete(key);
    }
    params.delete("page");
    params.delete("skip");
    const queryString = params.toString();
    router.push(queryString ? `${baseUrl}?${queryString}` : baseUrl);
  };

  const clearAllFilters = () => {
    setOpenDropdown(null);
    router.push(baseUrl);
  };

  // Convert real categories from DB
  const categoryOptions: DropdownOption[] = categories.map((c) => ({
    id: String(c.id),
    name: c.name,
  }));

  const genreOptions: DropdownOption[] = genres.map((g) => ({
    id: g.id,
    name: g.name,
  }));

  const typeOptions: DropdownOption[] = types.map((t) => ({
    id: t.id,
    name: t.name,
  }));

  const yearOptions: DropdownOption[] = years.map((y) => ({
    id: String(y),
    name: String(y),
  }));

  const hasAnyActiveFilter = Boolean(
    selectedGenre ||
    selectedType ||
    selectedYear ||
    (selectedSort && selectedSort !== "all")
  );

  return (
    <div className="w-full space-y-3 relative z-20">
      {/* ── ROW 1: 4-DROPDOWN HORIZONTAL BAR (Janr, Turi, Yil, Saralash) ── */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 sm:gap-2.5">
        {/* 1. Janr */}
        <FilterDropdown
          label="Janr"
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

        {/* 2. Turi */}
        <FilterDropdown
          label="Turi"
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

        {/* 3. Yil */}
        <FilterDropdown
          label="Yil"
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

        {/* 4. Saralash */}
        <FilterDropdown
          label="Saralash"
          options={SORT_OPTIONS}
          selectedValue={selectedSort}
          showAllOption={false}
          isOpen={openDropdown === "sort"}
          onToggle={() =>
            setOpenDropdown((cur) => (cur === "sort" ? null : "sort"))
          }
          onClose={() =>
            setOpenDropdown((cur) => (cur === "sort" ? null : cur))
          }
          onSelect={(val) => updateFilter("sort", val)}
        />
      </div>

      {/* ── ROW 2: ACTIONS (Clear filters & Results counter) ── */}
      <div className="flex items-center justify-between gap-3 pt-0.5 min-h-[28px]">
        {hasAnyActiveFilter ? (
          <button
            type="button"
            onClick={clearAllFilters}
            className="text-xs text-text-secondary hover:text-red-400 flex items-center gap-1 transition-colors select-none cursor-pointer py-1"
          >
            <span className="text-[13px]">✕</span>
            <span>Filtrlarni tozalash</span>
          </button>
        ) : (
          <div />
        )}

        {/* Topilgan kinolar soni */}
        {typeof totalItems === "number" && (
          <div className="text-xs text-zinc-400 font-medium">
            Topilgan: <span className="font-bold text-white">{totalItems} ta</span>
          </div>
        )}
      </div>
    </div>
  );
}
