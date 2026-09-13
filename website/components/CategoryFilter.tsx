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
                ? "bg-primary-container text-white border-primary-container shadow-md shadow-primary-container/20 font-bold" 
                : "bg-white/5 border-white/10 text-text-secondary hover:text-text-primary hover:bg-white/10"
            }`}
          >
            <span>✨</span>
            <span>Barchasi</span>
          </Link>

          {/* 2. "Barcha janrlar" Modal Trigger Button - Instantly visible on Mobile */}
          {categories.length > 0 && (
            <button
              onClick={() => setModalOpen(true)}
              className={`px-4 sm:px-5 py-2.5 rounded-xl text-xs sm:text-sm font-semibold transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5 active:scale-95 shrink-0 border flex items-center gap-2 cursor-pointer shadow-md shadow-black/20 ${
                currentCategory
                  ? "bg-white/20 text-white border-white/30 font-bold"
                  : "bg-white/10 hover:bg-white/15 border-white/15 text-text-primary"
              }`}
              aria-label="Barcha janrlarni ko'rish"
            >
              <span className="material-symbols-outlined text-[18px] text-text-secondary">tune</span>
              <span>Barcha janrlar</span>
              <span className="ml-0.5 px-1.5 py-0.5 rounded-md bg-white/10 text-[11px] text-text-secondary font-bold">
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
                    ? "bg-primary-container text-white border-primary-container shadow-md shadow-primary-container/20 font-bold" 
                    : "bg-white/5 border-white/10 text-text-secondary hover:text-text-primary hover:bg-white/10"
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
            className="fixed inset-0 bg-black/80 backdrop-blur-md transition-opacity" 
            onClick={() => setModalOpen(false)} 
          />

          {/* Dialog Container */}
          <div className="relative w-full sm:max-w-2xl max-h-[85vh] bg-background-obsidian/95 border border-white/15 rounded-t-3xl sm:rounded-3xl shadow-2xl backdrop-blur-2xl flex flex-col p-5 sm:p-6 z-10 overflow-hidden">
            {/* Mobile Drag Indicator */}
            <div className="w-12 h-1.5 bg-white/20 rounded-full mx-auto mb-3 shrink-0 sm:hidden" />

            {/* Modal Header */}
            <div className="flex items-center justify-between pb-4 border-b border-white/10 shrink-0">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-[22px] text-text-secondary">tune</span>
                <h3 className="font-extrabold text-lg sm:text-xl text-text-primary">
                  Janrlar va kategoriyalar
                </h3>
              </div>
              <button 
                onClick={() => setModalOpen(false)}
                className="w-9 h-9 rounded-full bg-white/10 hover:bg-white/20 text-text-primary flex items-center justify-center transition-all duration-200 hover:scale-105 active:scale-95 cursor-pointer"
                aria-label="Yopish"
              >
                <span className="material-symbols-outlined text-2xl">close</span>
              </button>
            </div>

            {/* Quick Search inside Modal */}
            <div className="pt-4 pb-3 shrink-0">
              <div className="flex items-center bg-white/5 border border-white/10 rounded-xl px-3.5 py-2.5 focus-within:border-primary-container transition-colors">
                <span className="material-symbols-outlined text-text-secondary text-[20px] mr-2.5">search</span>
                <input 
                  type="text"
                  value={filterQuery}
                  onChange={(e) => setFilterQuery(e.target.value)}
                  placeholder="Janr nomini qidirish..."
                  className="bg-transparent border-none text-sm text-text-primary placeholder:text-text-secondary w-full outline-none"
                />
                {filterQuery && (
                  <button 
                    onClick={() => setFilterQuery("")}
                    className="text-text-secondary hover:text-text-primary p-0.5 cursor-pointer"
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
                  onClick={() => {
                    router.push(baseUrl);
                    setModalOpen(false);
                  }}
                  className={`p-3 rounded-xl text-xs sm:text-sm font-semibold transition-all duration-200 hover:scale-[1.01] hover:-translate-y-0.5 active:scale-95 border text-left flex items-center justify-between cursor-pointer ${
                    !currentCategory 
                      ? "bg-primary-container text-white border-primary-container font-bold shadow-md shadow-primary-container/20" 
                      : "bg-white/5 border-white/10 text-text-secondary hover:text-text-primary hover:bg-white/10"
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
                      onClick={() => {
                        router.push(`${baseUrl}?category=${cat.id}`);
                        setModalOpen(false);
                      }}
                      className={`p-3 rounded-xl text-xs sm:text-sm font-semibold transition-all duration-200 hover:scale-[1.01] hover:-translate-y-0.5 active:scale-95 border text-left flex items-center justify-between cursor-pointer ${
                        isActive 
                          ? "bg-primary-container text-white border-primary-container font-bold shadow-md shadow-primary-container/20" 
                          : "bg-white/5 border-white/10 text-text-secondary hover:text-text-primary hover:bg-white/10"
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
                <div className="text-center py-8 text-text-secondary text-sm">
                  "{filterQuery}" bo'yicha janr topilmadi.
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="pt-3 mt-2 border-t border-white/10 flex items-center justify-between text-xs text-text-secondary shrink-0">
              <span>Jami {categories.length} ta kategoriya</span>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
