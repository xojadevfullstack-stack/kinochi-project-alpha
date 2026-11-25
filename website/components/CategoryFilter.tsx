"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

type Category = {
  id: number;
  name: string;
};

interface CategoryFilterProps {
  categories: Category[];
  currentCategory?: string;
  baseUrl: string;
}

export default function CategoryFilter({ categories, currentCategory, baseUrl }: CategoryFilterProps) {
  const router = useRouter();
  const [modalOpen, setModalOpen] = useState(false);
  const [filterQuery, setFilterQuery] = useState("");

  const handleSelectCategory = (url: string) => {
    router.push(url);
    setTimeout(() => {
      setModalOpen(false);
    }, 100);
  };

  // Lock scroll when modal is open
  useEffect(() => {
    if (modalOpen) {
      const original = document.body.style.overflow;
      document.body.style.overflow = "hidden";
      return () => {
        document.body.style.overflow = original;
      };
    }
  }, [modalOpen]);

  // Keep top 10 categories for the quick horizontal scroll
  const topCategories = categories.slice(0, 10);
  
  // Find currently active category object if any
  const activeCategoryObj = categories.find(c => String(c.id) === currentCategory);
  
  // If active category is beyond top 10, include it in quick chips
  const displayQuickCategories = [...topCategories];
  if (activeCategoryObj && !displayQuickCategories.some(c => c.id === activeCategoryObj.id)) {
    displayQuickCategories.splice(1, 0, activeCategoryObj);
  }

  // Filter categories for the modal search
  const filteredModalCategories = categories.filter(c =>
    c.name.toLowerCase().includes(filterQuery.toLowerCase().trim())
  );

  return (
    <>
      {/* Horizontal Quick-Filter Bar */}
      <div className="relative w-full mb-6">
        <div className="flex items-center gap-2 overflow-x-auto pb-2 pt-1 hide-scrollbar scroll-smooth">
          {/* 1. "Barchasi" Button */}
          <Link 
            href={baseUrl} 
            className={`px-4 sm:px-5 py-2.5 rounded-xl text-xs sm:text-sm font-semibold transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5 active:scale-95 shrink-0 flex items-center gap-2 border ${
              !currentCategory 
                ? "bg-[#E50914] text-white border-[#E50914] shadow-lg shadow-[#E50914]/25 font-bold" 
                : "bg-white dark:bg-white/5 border-slate-200 dark:border-white/10 text-slate-700 dark:text-text-secondary hover:text-slate-900 dark:hover:text-text-primary hover:bg-slate-50 dark:hover:bg-white/10"
            }`}
          >
            <span>✨</span>
            <span>Barchasi</span>
          </Link>

          {/* 2. "Barcha janrlar" Modal Trigger Button - Instantly visible on Mobile */}
          {categories.length > 0 && (
            <button
              onClick={() => setModalOpen(true)}
              className={`px-4 sm:px-5 py-2.5 rounded-xl text-xs sm:text-sm font-semibold transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5 active:scale-95 shrink-0 border flex items-center gap-2 cursor-pointer shadow-sm dark:shadow-md dark:shadow-black/20 ${
                currentCategory
                  ? "bg-[#E50914] text-white border-[#E50914] font-bold"
                  : "bg-white dark:bg-white/10 hover:bg-slate-50 dark:hover:bg-white/15 border-slate-200 dark:border-white/15 text-slate-900 dark:text-text-primary"
              }`}
              aria-label="Barcha janrlarni ko'rish"
            >
              <span className={`material-symbols-outlined text-[18px] ${currentCategory ? "text-white" : "text-slate-600 dark:text-text-secondary"}`}>tune</span>
              <span>Barcha janrlar</span>
              <span className={`ml-0.5 px-1.5 py-0.5 rounded-md text-[11px] font-bold ${
                currentCategory
                  ? "bg-white/20 text-white"
                  : "bg-slate-100 dark:bg-white/10 text-slate-600 dark:text-text-secondary"
              }`}>
                {categories.length}
              </span>
            </button>
          )}
          
          {/* 3. Quick Category Chips */}
          {displayQuickCategories.map(cat => {
            const isActive = currentCategory === String(cat.id);
            return (
              <Link 
                key={cat.id} 
                href={`${baseUrl}?category=${cat.id}`}
                className={`px-4 sm:px-5 py-2.5 rounded-xl text-xs sm:text-sm font-semibold transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5 active:scale-95 shrink-0 border ${
                  isActive 
                    ? "bg-[#E50914] text-white border-[#E50914] shadow-lg shadow-[#E50914]/25 font-bold" 
                    : "bg-white dark:bg-white/5 border-slate-200 dark:border-white/10 text-slate-700 dark:text-text-secondary hover:text-slate-900 dark:hover:text-text-primary hover:bg-slate-50 dark:hover:bg-white/10"
                }`}
              >
                {cat.name}
              </Link>
            );
          })}
        </div>
      </div>

      {/* Modal / Bottom Sheet for All Genres */}
      {modalOpen && (
        <div className="fixed inset-0 z-[120] flex items-end sm:items-center justify-center p-0 sm:p-4 overscroll-contain">
          {/* Backdrop */}
          <div 
            className="fixed inset-0 bg-slate-900/55 dark:bg-black/80 backdrop-blur-md transition-opacity" 
            onClick={() => setModalOpen(false)} 
          />

          {/* Dialog Container */}
          <div className="relative w-full sm:max-w-2xl max-h-[85vh] bg-white/95 dark:bg-[#12141D]/95 border border-slate-200 dark:border-white/15 rounded-t-3xl sm:rounded-3xl shadow-2xl backdrop-blur-2xl flex flex-col p-5 sm:p-6 z-10 overflow-hidden">
            {/* Mobile Drag Indicator */}
            <div className="w-12 h-1.5 bg-slate-300 dark:bg-white/20 rounded-full mx-auto mb-3 shrink-0 sm:hidden" />

            {/* Modal Header */}
            <div className="flex items-center justify-between pb-4 border-b border-slate-200 dark:border-white/10 shrink-0">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-[22px] text-slate-600 dark:text-text-secondary">tune</span>
                <h3 className="font-extrabold text-lg sm:text-xl text-slate-900 dark:text-text-primary">
                  Janrlar va kategoriyalar
                </h3>
              </div>
              <button 
                onClick={() => setModalOpen(false)}
                className="w-9 h-9 rounded-full bg-slate-100 hover:bg-slate-200 dark:bg-white/10 dark:hover:bg-white/20 text-slate-700 dark:text-text-primary flex items-center justify-center transition-all duration-200 hover:scale-105 active:scale-95 cursor-pointer"
                aria-label="Yopish"
              >
                <span className="material-symbols-outlined text-2xl">close</span>
              </button>
            </div>

            {/* Quick Search inside Modal */}
            <div className="pt-4 pb-3 shrink-0">
              <div className="flex items-center bg-slate-100 dark:bg-white/5 border border-slate-200 dark:border-white/10 rounded-xl px-3.5 py-2.5 focus-within:border-primary-container transition-colors">
                <span className="material-symbols-outlined text-slate-500 dark:text-text-secondary text-[20px] mr-2.5">search</span>
                <input 
                  type="text"
                  value={filterQuery}
                  onChange={(e) => setFilterQuery(e.target.value)}
                  placeholder="Janr nomini qidirish..."
                  className="bg-transparent border-none text-sm text-slate-900 dark:text-text-primary placeholder:text-slate-500 dark:placeholder:text-text-secondary w-full outline-none"
                />
                {filterQuery && (
                  <button 
                    onClick={() => setFilterQuery("")}
                    className="text-slate-500 hover:text-slate-900 dark:text-text-secondary dark:hover:text-text-primary p-0.5 cursor-pointer"
                  >
                    <span className="material-symbols-outlined text-[18px]">close</span>
                  </button>
                )}
              </div>
            </div>

            {/* Category Grid */}
            <div className="overflow-y-auto flex-1 pr-1 -mr-1 custom-scrollbar py-2">
              <div className="grid grid-cols-2 gap-2 sm:gap-2.5">
                {/* Reset to All */}
                <button
                  onClick={() => handleSelectCategory(baseUrl)}
                  className={`p-3 rounded-xl text-xs sm:text-sm font-semibold transition-all duration-200 hover:scale-[1.01] hover:-translate-y-0.5 active:scale-95 border text-left flex items-center justify-between cursor-pointer ${
                    !currentCategory 
                      ? "bg-[#E50914] text-white border-[#E50914] font-bold shadow-md shadow-[#E50914]/20" 
                      : "bg-slate-50 dark:bg-white/5 border-slate-200 dark:border-white/10 text-slate-700 dark:text-text-secondary hover:text-slate-900 dark:hover:text-text-primary hover:bg-slate-100 dark:hover:bg-white/10"
                  }`}
                >
                  <span>Barchasi</span>
                  {!currentCategory && (
                    <span className="material-symbols-outlined text-[16px]">check</span>
                  )}
                </button>

                {filteredModalCategories.map(cat => {
                  const isActive = currentCategory === String(cat.id);
                  return (
                    <button
                      key={cat.id}
                      onClick={() => handleSelectCategory(`${baseUrl}?category=${cat.id}`)}
                      className={`p-3 rounded-xl text-xs sm:text-sm font-semibold transition-all duration-200 hover:scale-[1.01] hover:-translate-y-0.5 active:scale-95 border text-left flex items-center justify-between cursor-pointer ${
                        isActive 
                          ? "bg-[#E50914] text-white border-[#E50914] font-bold shadow-md shadow-[#E50914]/20" 
                          : "bg-slate-50 dark:bg-white/5 border-slate-200 dark:border-white/10 text-slate-700 dark:text-text-secondary hover:text-slate-900 dark:hover:text-text-primary hover:bg-slate-100 dark:hover:bg-white/10"
                      }`}
                    >
                      <span className="truncate mr-1">{cat.name}</span>
                      {isActive && (
                        <span className="material-symbols-outlined text-[16px] shrink-0">check</span>
                      )}
                    </button>
                  );
                })}
              </div>

              {filteredModalCategories.length === 0 && (
                <div className="text-center py-8 text-slate-500 dark:text-text-secondary text-sm">
                  &quot;{filterQuery}&quot; bo&apos;yicha janr topilmadi.
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="pt-3 mt-2 border-t border-slate-200 dark:border-white/10 flex items-center justify-between text-xs text-slate-500 dark:text-text-secondary shrink-0">
              <span>Jami {categories.length} ta kategoriya</span>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
