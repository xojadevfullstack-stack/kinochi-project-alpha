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
          {/* "Barchasi" Button */}
          <Link 
            href={baseUrl} 
            className={`px-4 sm:px-5 py-2 rounded-xl text-xs sm:text-sm font-semibold transition-all shrink-0 flex items-center gap-1.5 border active:scale-95 ${
              !currentCategory 
                ? "bg-primary-container text-white border-primary-container shadow-lg shadow-primary-container/25" 
                : "bg-white/5 border-white/10 text-text-secondary hover:text-text-primary hover:bg-white/10"
            }`}
          >
            <span className="material-symbols-outlined text-[17px]">apps</span>
            <span>Barchasi</span>
          </Link>
          
          {/* Quick Category Chips */}
          {displayQuickCategories.map(cat => {
            const isActive = currentCategory === String(cat.id);
            return (
              <Link 
                key={cat.id} 
                href={`${baseUrl}?category=${cat.id}`}
                className={`px-4 sm:px-5 py-2 rounded-xl text-xs sm:text-sm font-semibold transition-all shrink-0 border active:scale-95 ${
                  isActive 
                    ? "bg-primary-container text-white border-primary-container shadow-lg shadow-primary-container/25" 
                    : "bg-white/5 border-white/10 text-text-secondary hover:text-text-primary hover:bg-white/10"
                }`}
              >
                {cat.name}
              </Link>
            );
          })}

          {/* "Barcha janrlar" Modal Trigger Button */}
          {categories.length > 0 && (
            <button
              onClick={() => setModalOpen(true)}
              className="px-4 sm:px-5 py-2 rounded-xl text-xs sm:text-sm font-bold transition-all shrink-0 bg-white/10 hover:bg-white/15 border border-white/15 text-text-primary flex items-center gap-1.5 cursor-pointer active:scale-95 shadow-md shadow-black/20"
              aria-label="Barcha janrlarni ko'rish"
            >
              <span className="material-symbols-outlined text-[18px] text-primary-container">tune</span>
              <span>Barcha janrlar</span>
              <span className="ml-1 px-1.5 py-0.5 rounded-md bg-white/10 text-[11px] text-text-secondary">
                {categories.length}
              </span>
            </button>
          )}
        </div>
      </div>

      {/* Modal / Bottom Sheet for All Genres */}
      {modalOpen && (
        <div className="fixed inset-0 z-[120] flex items-end sm:items-center justify-center p-0 sm:p-4 overscroll-contain">
          {/* Backdrop overlay */}
          <div 
            className="absolute inset-0 bg-black/80 backdrop-blur-md transition-opacity"
            onClick={() => setModalOpen(false)}
          />

          {/* Modal Container */}
          <div className="relative z-10 w-full sm:max-w-2xl bg-background-obsidian/98 backdrop-blur-2xl border-t sm:border border-white/15 rounded-t-[28px] sm:rounded-3xl p-5 sm:p-6 shadow-2xl flex flex-col max-h-[85vh] sm:max-h-[80vh] animate-in slide-in-from-bottom duration-300">
            {/* Mobile Drag Indicator */}
            <div className="w-12 h-1.5 bg-white/20 rounded-full mx-auto mb-3 shrink-0 sm:hidden" />

            {/* Modal Header */}
            <div className="flex items-center justify-between pb-4 border-b border-white/10 shrink-0">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-[24px] text-primary-container">tune</span>
                <h3 className="font-extrabold text-lg sm:text-xl text-text-primary">
                  Janrlar va kategoriyalar
                </h3>
              </div>
              <button 
                onClick={() => setModalOpen(false)}
                className="w-9 h-9 rounded-full bg-white/10 hover:bg-white/20 text-text-primary flex items-center justify-center transition-colors cursor-pointer"
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
                  <button onClick={() => setFilterQuery("")} className="text-text-secondary hover:text-white text-xs">
                    <span className="material-symbols-outlined text-[16px]">close</span>
                  </button>
                )}
              </div>
            </div>

            {/* Scrollable Genres Grid */}
            <div className="overflow-y-auto flex-1 py-2 pr-1 hide-scrollbar overscroll-contain">
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                {/* Reset to All */}
                <button
                  onClick={() => {
                    router.push(baseUrl);
                    setModalOpen(false);
                  }}
                  className={`p-3 rounded-xl text-xs sm:text-sm font-semibold transition-all border text-left flex items-center justify-between cursor-pointer ${
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
                      className={`p-3 rounded-xl text-xs sm:text-sm font-semibold transition-all border text-left flex items-center justify-between cursor-pointer ${
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
            <div className="pt-3 mt-2 border-t border-white/10 flex justify-between items-center text-xs text-text-secondary shrink-0">
              <span>Jami {categories.length} ta kategoriya</span>
              <button 
                onClick={() => setModalOpen(false)}
                className="px-4 py-2 rounded-xl bg-white/10 hover:bg-white/15 text-text-primary font-bold transition-all cursor-pointer"
              >
                Yopish
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
