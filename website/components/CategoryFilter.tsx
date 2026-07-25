"use client";

import { useState } from "react";
import Link from "next/link";

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
  const [isExpanded, setIsExpanded] = useState(false);

  // Define how many categories to show initially
  const INITIAL_COUNT = 7;
  
  const visibleCategories = isExpanded ? categories : categories.slice(0, INITIAL_COUNT);
  const hasMore = categories.length > INITIAL_COUNT;

  return (
    <div className="flex flex-wrap gap-2 pb-2">
      <Link 
        href={baseUrl} 
        className={`px-6 py-2 rounded-full font-label-caps text-xs uppercase tracking-widest font-bold transition-colors ${!currentCategory ? "bg-primary-container text-white shadow-[0_0_15px_rgba(229,9,20,0.5)]" : "bg-white/5 border border-white/10 text-text-secondary hover:text-text-primary hover:bg-white/10"}`}
      >
        Barchasi
      </Link>
      
      {visibleCategories.map(cat => {
        const isActive = currentCategory === String(cat.id);
        return (
          <Link 
            key={cat.id} 
            href={`${baseUrl}?category=${cat.id}`}
            className={`px-6 py-2 rounded-full font-label-caps text-xs uppercase tracking-widest font-bold transition-colors ${isActive ? "bg-primary-container text-white shadow-[0_0_15px_rgba(229,9,20,0.5)]" : "bg-white/5 border border-white/10 text-text-secondary hover:text-text-primary hover:bg-white/10"}`}
          >
            {cat.name}
          </Link>
        );
      })}

      {hasMore && (
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="px-6 py-2 rounded-full font-label-caps text-xs uppercase tracking-widest font-bold transition-colors bg-white/5 border border-white/10 text-text-secondary hover:text-text-primary hover:bg-white/10 flex items-center gap-1"
        >
          {isExpanded ? "Kamroq" : "Ko'proq"}
          <span className="material-symbols-outlined text-[14px]">
            {isExpanded ? "expand_less" : "expand_more"}
          </span>
        </button>
      )}
    </div>
  );
}
