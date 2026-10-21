"use client";

import Link from "next/link";
import Image from "next/image";

export interface ThemedCollectionCardProps {
  id?: string | number;
  title: string;
  count: number | string;
  href: string;
  posters: string[];
  description?: string | null;
  badge?: string | null;
}

export default function ThemedCollectionCard({
  title,
  count,
  href,
  posters = [],
  description,
  badge
}: ThemedCollectionCardProps) {
  // Ensure we have 3 poster items for the fan deck (fallback gracefully if fewer provided)
  const p1 = posters[0] || "https://image.tmdb.org/t/p/w500/yF1eOkaYvwiORauRCPWznV9xVvi.jpg";
  const p2 = posters[1] || posters[0] || "https://image.tmdb.org/t/p/w500/wuMc08IPKEatf9rnMNXvIDxqP4W.jpg";
  const p3 = posters[2] || posters[0] || "https://image.tmdb.org/t/p/w500/fiVW06jE7z9YnO4trhaMEdclSiC.jpg";

  const displayCount = typeof count === "number" ? `${count} ta kino` : count;

  return (
    <Link
      href={href}
      className="group relative flex flex-col justify-between bg-[#121317] hover:bg-[#161820] border border-white/10 hover:border-white/20 rounded-2xl p-4 sm:p-5 transition-all duration-300 hover:scale-[1.02] hover:shadow-2xl hover:shadow-black/60 cursor-pointer overflow-hidden"
    >
      {/* 3D Fanned 3-Poster Showcase Deck (Iconic Asilmedia Style) */}
      <div className="relative w-full h-44 sm:h-48 mb-4 flex items-center justify-center perspective-1000 select-none">
        
        {/* Left Angled Poster */}
        <div className="absolute w-24 sm:w-28 aspect-[2/3] rounded-xl overflow-hidden shadow-xl border border-white/10 transform -rotate-12 -translate-x-8 sm:-translate-x-10 scale-90 opacity-75 group-hover:-rotate-[16deg] group-hover:-translate-x-12 sm:group-hover:-translate-x-14 transition-all duration-300 bg-surface-container">
          <Image
            src={p1}
            alt=""
            fill
            unoptimized
            className="object-cover"
          />
          <div className="absolute inset-0 bg-black/30 pointer-events-none" />
        </div>

        {/* Right Angled Poster */}
        <div className="absolute w-24 sm:w-28 aspect-[2/3] rounded-xl overflow-hidden shadow-xl border border-white/10 transform rotate-12 translate-x-8 sm:translate-x-10 scale-90 opacity-75 group-hover:rotate-[16deg] group-hover:translate-x-12 sm:group-hover:translate-x-14 transition-all duration-300 bg-surface-container">
          <Image
            src={p3}
            alt=""
            fill
            unoptimized
            className="object-cover"
          />
          <div className="absolute inset-0 bg-black/30 pointer-events-none" />
        </div>

        {/* Center Dominant Poster */}
        <div className="relative z-10 w-28 sm:w-32 aspect-[2/3] rounded-xl overflow-hidden shadow-2xl border-2 border-white/20 transform scale-100 group-hover:scale-105 transition-transform duration-300 bg-surface-container-high">
          <Image
            src={p2}
            alt={title}
            fill
            unoptimized
            className="object-cover"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent pointer-events-none" />
          
          {badge && (
            <span className="absolute top-1.5 left-1.5 px-1.5 py-0.5 rounded bg-black/75 backdrop-blur-md text-[9px] font-bold text-white uppercase border border-white/10">
              {badge}
            </span>
          )}
        </div>
      </div>

      {/* Title & Item Count */}
      <div className="mt-auto space-y-1">
        <h3 className="font-bold text-sm sm:text-base text-white group-hover:text-white transition-colors line-clamp-2 leading-snug">
          {title}
        </h3>
        
        {description && (
          <p className="text-xs text-text-secondary line-clamp-1 leading-normal">
            {description}
          </p>
        )}

        <div className="pt-1 flex items-center justify-between text-xs text-text-secondary">
          <span className="font-medium text-zinc-400">
            {displayCount}
          </span>
          <span className="material-symbols-outlined text-[16px] text-zinc-500 group-hover:text-white group-hover:translate-x-0.5 transition-all">
            arrow_forward
          </span>
        </div>
      </div>
    </Link>
  );
}
