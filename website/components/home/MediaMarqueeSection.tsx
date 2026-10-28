"use client";

import React, { useMemo } from "react";
import Link from "next/link";
import AdultPoster from "@/components/AdultPoster";
import { isAdultContent } from "@/lib/adult";

interface MediaMarqueeItem {
  id: number;
  title: string;
  poster_url: string | null;
  code?: string;
  is_series?: boolean;
  imdb_rating?: number | null;
  tmdb_rating?: number | null;
  release_year?: number | null;
  is_18_plus?: boolean;
}

interface MediaMarqueeSectionProps {
  items: MediaMarqueeItem[];
}

export default function MediaMarqueeSection({ items }: MediaMarqueeSectionProps) {
  // Split items into 3 balanced rows, duplicated for seamless infinite loop
  const { row1, row2, row3 } = useMemo(() => {
    const list = items ? [...items] : [];
    if (list.length === 0) return { row1: [], row2: [], row3: [] };

    const third = Math.ceil(list.length / 3);
    const r1 = list.slice(0, third);
    const r2 = list.slice(third, third * 2);
    const r3 = list.slice(third * 2);

    // Ensure enough items to fill ultra-wide screens smoothly (repeat 3-4 times)
    const duplicateList = (arr: MediaMarqueeItem[]) => {
      let res: MediaMarqueeItem[] = [];
      const source = arr.length > 0 ? arr : list;
      while (res.length < 24 && source.length > 0) {
        res = [...res, ...source];
      }
      return res;
    };

    return {
      row1: duplicateList(r1),
      row2: duplicateList(r2),
      row3: duplicateList(r3),
    };
  }, [items]);

  // If no items passed, don't render
  if (!items || items.length === 0 || row1.length === 0) return null;

  const renderCard = (item: MediaMarqueeItem, index: number, rowId: string) => {
    const isSeries = !!item.is_series || (!item.code && !!item.id);
    const href = isSeries ? `/series/${item.id}` : `/movie/${item.code || item.id}`;
    const is18 = isAdultContent(item);

    // Stagger card sizes: every 4th card is a wide rectangle like Setanta/TV Cinema in reference
    const isWide = (index + (rowId === "r2" ? 1 : rowId === "r3" ? 2 : 0)) % 4 === 0;
    const qualityBadge = index % 2 === 0 ? "FHD" : "HD";

    return (
      <Link
        key={`mq-${rowId}-${item.id}-${index}`}
        href={href}
        className={`group relative shrink-0 rounded-2xl overflow-hidden cursor-pointer bg-white/[0.04] border border-white/10 hover:border-white/30 hover:scale-105 transition-all duration-300 shadow-sm hover:shadow-xl hover:shadow-black/70 ${
          isWide
            ? "w-48 sm:w-56 md:w-64 h-28 sm:h-32 md:h-36"
            : "w-28 sm:w-32 md:w-36 h-28 sm:h-32 md:h-36"
        }`}
      >
        {item.poster_url ? (
          <AdultPoster
            src={item.poster_url}
            alt={item.title}
            is18Plus={is18}
            fill
            sizes="(max-width: 640px) 120px, 200px"
            imageClassName="object-cover group-hover:scale-110 transition-transform duration-700 ease-out"
          />
        ) : (
          <div className="w-full h-full flex flex-col items-center justify-center bg-surface-container-high text-gray-500">
            <span className="material-symbols-outlined text-2xl opacity-30">movie</span>
          </div>
        )}

        {/* Ambient Dark Gradient */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/30 to-black/20 opacity-75 group-hover:opacity-40 transition-opacity pointer-events-none" />

        {/* Top Badges (HD / FHD & Age / Code) */}
        <div className="absolute top-1.5 left-1.5 z-10 flex items-center gap-1 pointer-events-none">
          <span className="px-1.5 py-0.5 rounded-md bg-emerald-500/95 text-white font-black text-[8px] sm:text-[9px] leading-none tracking-wider shadow-sm">
            {qualityBadge}
          </span>
          {is18 ? (
            <span className="px-1.5 py-0.5 rounded-md bg-red-600/95 text-white font-black text-[8px] sm:text-[9px] leading-none shadow-sm">
              18+
            </span>
          ) : null}
        </div>



        {/* Bottom Title Overlay */}
        <div className="absolute bottom-0 left-0 right-0 p-1.5 sm:p-2 z-10 pointer-events-none bg-gradient-to-t from-black via-black/85 to-transparent">
          <h4 className="text-white text-xs sm:text-[13px] font-bold truncate leading-tight group-hover:text-primary transition-colors">
            {item.title}
          </h4>
        </div>
      </Link>
    );
  };

  return (
    <section className="max-w-container-max mx-auto px-gutter my-12 sm:my-16 overflow-hidden relative z-20">
      {/* Header: "Kinolar va seriallar" (without "mozaikasi") */}
      <div className="mb-4 flex items-center justify-between">
        <h2 className="font-headline-md text-lg sm:text-xl md:text-2xl text-text-primary flex items-center gap-2 font-bold">
          <span className="w-1 h-6 bg-primary rounded-full block" />
          <span>Kinolar va seriallar</span>
        </h2>
        <Link
          href="/catalog"
          className="text-text-secondary hover:text-white text-xs sm:text-sm font-semibold transition-colors flex items-center gap-1 group"
        >
          <span>Katalogni ochish</span>
          <span className="material-symbols-outlined text-[16px] group-hover:translate-x-0.5 transition-transform">
            arrow_forward
          </span>
        </Link>
      </div>

      {/* Marquee Wrapper with 3 Distinct Smooth Scrolling Rows (3x Slower Pace) */}
      <div className="relative w-full overflow-hidden marquee-pause py-2 flex flex-col gap-2.5 sm:gap-3 rounded-2xl">
        {/* Left & Right Edge Soft Blurring Vignette Masks */}
        <div className="absolute left-0 top-0 bottom-0 w-12 sm:w-24 md:w-36 bg-gradient-to-r from-background-obsidian to-transparent z-10 pointer-events-none" />
        <div className="absolute right-0 top-0 bottom-0 w-12 sm:w-24 md:w-36 bg-gradient-to-l from-background-obsidian to-transparent z-10 pointer-events-none" />

        {/* Row 1: Leftward Infinite Flow */}
        <div className="animate-marquee-left flex gap-2.5 sm:gap-3">
          {row1.map((item, idx) => renderCard(item, idx, "r1"))}
        </div>

        {/* Row 2: Rightward Infinite Flow */}
        <div className="animate-marquee-right flex gap-2.5 sm:gap-3">
          {row2.map((item, idx) => renderCard(item, idx, "r2"))}
        </div>

        {/* Row 3: Leftward Infinite Flow */}
        <div className="animate-marquee-left-fast flex gap-2.5 sm:gap-3">
          {row3.map((item, idx) => renderCard(item, idx, "r3"))}
        </div>
      </div>
    </section>
  );
}
