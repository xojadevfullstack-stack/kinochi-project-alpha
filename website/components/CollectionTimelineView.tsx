"use client";

import React, { useState } from "react";
import Image from "next/image";
import Link from "next/link";

interface CollectionItem {
  id: number;
  chronological_order: number;
  release_order: number;
  timeline_event_desc?: string | null;
  movie?: {
    id: number;
    title: string;
    original_title?: string | null;
    code: string;
    poster_url?: string | null;
    release_year?: number | null;
    imdb_rating?: number | null;
  } | null;
  series?: {
    id: number;
    title: string;
    poster_url?: string | null;
    release_year?: number | null;
    imdb_rating?: number | null;
  } | null;
}

interface CollectionTimelineViewProps {
  initialItems: CollectionItem[];
  collectionName: string;
  collectionSlug: string;
}

export default function CollectionTimelineView({
  initialItems,
  collectionName,
  collectionSlug,
}: CollectionTimelineViewProps) {
  const [sortMode, setSortMode] = useState<"chronological" | "release">("chronological");

  // Sort items according to active mode
  const sortedItems = [...initialItems].sort((a, b) => {
    if (sortMode === "chronological") {
      return a.chronological_order - b.chronological_order;
    } else {
      return a.release_order - b.release_order;
    }
  });

  return (
    <div className="w-full">
      {/* Dual Mode Switcher Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 bg-surface-container-lowest/80 backdrop-blur-xl border border-white/10 rounded-2xl p-4 sm:p-5 mb-8 shadow-xl">
        <div className="flex items-center gap-2.5">
          <span className="material-symbols-outlined text-primary-container text-2xl">tune</span>
          <div>
            <h3 className="font-bold text-sm sm:text-base text-white">Tartiblash usuli</h3>
            <p className="text-xs text-text-secondary">
              {sortMode === "chronological"
                ? "Voqealar xronologiyasi — film ichidagi koinot voqealari vaqti bo'yicha"
                : "Kinoteatrlarga chiqqan yili — premyera sanalari bo'yicha"}
            </p>
          </div>
        </div>

        {/* Toggle Buttons */}
        <div className="flex items-center bg-black/60 p-1.5 rounded-xl border border-white/10 w-full sm:w-auto">
          <button
            onClick={() => setSortMode("chronological")}
            className={`flex-1 sm:flex-none flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
              sortMode === "chronological"
                ? "bg-primary-container text-white shadow-lg shadow-primary-container/20"
                : "text-text-secondary hover:text-white hover:bg-white/5"
            }`}
          >
            <span className="material-symbols-outlined text-[17px]">timeline</span>
            <span>📅 Voqealar Xronologiyasi</span>
          </button>

          <button
            onClick={() => setSortMode("release")}
            className={`flex-1 sm:flex-none flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
              sortMode === "release"
                ? "bg-primary-container text-white shadow-lg shadow-primary-container/20"
                : "text-text-secondary hover:text-white hover:bg-white/5"
            }`}
          >
            <span className="material-symbols-outlined text-[17px]">movie</span>
            <span>🎞️ Chiqarilgan yili</span>
          </button>
        </div>
      </div>

      {/* Timeline Steps Grid / List */}
      <div className="space-y-4">
        {sortedItems.map((item, idx) => {
          const activeOrder =
            sortMode === "chronological" ? item.chronological_order : item.release_order;
          const movie = item.movie;
          const series = item.series;
          const content = movie || series;
          const targetUrl = movie ? `/movie/${movie.code}` : series ? `/series/${series.id}` : "#";

          return (
            <div
              key={item.id}
              className="group flex flex-col md:flex-row items-stretch bg-surface-container-lowest/80 hover:bg-surface-container-low border border-white/10 hover:border-primary-container/40 rounded-2xl overflow-hidden transition-all duration-300 hover:shadow-xl hover:shadow-primary-container/5 relative"
            >
              {/* Order Number Badge Column */}
              <div className="md:w-20 bg-white/[0.02] md:border-r border-b md:border-b-0 border-white/5 flex items-center justify-between md:justify-center px-4 py-3 md:p-0 shrink-0">
                <div className="flex md:flex-col items-center gap-1.5 md:gap-0.5">
                  <span className="text-[10px] font-bold text-text-secondary uppercase tracking-widest md:hidden">
                    Tartib:
                  </span>
                  <span className="font-display-hero text-2xl md:text-3xl font-black text-primary-container group-hover:scale-110 transition-transform">
                    #{activeOrder}
                  </span>
                  <span className="text-[9px] text-text-secondary uppercase tracking-wider hidden md:block">
                    Qism
                  </span>
                </div>

                {/* Mobile-only year badge */}
                {content?.release_year && (
                  <span className="text-xs text-text-secondary font-semibold md:hidden">
                    {content.release_year}-yil
                  </span>
                )}
              </div>

              {/* Poster Thumbnail */}
              <div className="relative w-full md:w-36 h-48 md:h-auto shrink-0 bg-surface-container overflow-hidden">
                {content?.poster_url ? (
                  <Image
                    src={content.poster_url}
                    alt={content?.title || "Poster"}
                    fill
                    sizes="(max-width: 768px) 100vw, 150px"
                    unoptimized
                    className="object-cover group-hover:scale-105 transition-transform duration-500"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-white/20">
                    <span className="material-symbols-outlined text-4xl">movie</span>
                  </div>
                )}
                <div className="absolute inset-0 bg-gradient-to-t md:bg-gradient-to-r from-black/80 via-transparent to-transparent opacity-60"></div>
              </div>

              {/* Body Content */}
              <div className="p-4 sm:p-5 flex-1 flex flex-col justify-between">
                <div>
                  {/* Timeline lore event pill */}
                  {sortMode === "chronological" && item.timeline_event_desc && (
                    <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-amber-500/15 border border-amber-500/30 text-amber-300 font-semibold text-xs mb-2.5">
                      <span className="material-symbols-outlined text-[14px]">history</span>
                      <span>{item.timeline_event_desc}</span>
                    </div>
                  )}

                  <div className="flex flex-wrap items-center gap-2 mb-1.5">
                    <h4 className="font-bold text-base sm:text-xl text-white group-hover:text-primary-container transition-colors">
                      {content?.title || "Noma'lum film"}
                    </h4>
                    {movie?.original_title && (
                      <span className="text-xs text-text-secondary italic">
                        ({movie.original_title})
                      </span>
                    )}
                  </div>

                  {/* Metadata Badges */}
                  <div className="flex flex-wrap items-center gap-2.5 text-xs text-text-secondary my-2">
                    {content?.release_year && (
                      <span className="hidden md:inline-flex items-center gap-1 bg-white/5 px-2 py-0.5 rounded border border-white/10">
                        <span className="material-symbols-outlined text-[13px]">calendar_today</span>
                        <span>{content.release_year}</span>
                      </span>
                    )}

                    {movie?.imdb_rating && (
                      <span className="inline-flex items-center gap-1 bg-black/50 text-rating-gold px-2 py-0.5 rounded border border-white/10 font-bold">
                        <span
                          className="material-symbols-outlined text-[13px]"
                          style={{ fontVariationSettings: "'FILL' 1" }}
                        >
                          star
                        </span>
                        <span>{Number(movie.imdb_rating).toFixed(1)} IMDb</span>
                      </span>
                    )}

                    {movie?.code && (
                      <span className="font-mono text-[11px] bg-white/5 px-2 py-0.5 rounded text-white/60">
                        #{movie.code}
                      </span>
                    )}

                    {/* Dual order reference pill */}
                    <span className="text-[11px] text-text-secondary/70">
                      {sortMode === "chronological"
                        ? `(Chiqarilgan tartibi: #${item.release_order})`
                        : `(Voqealar tartibi: #${item.chronological_order})`}
                    </span>
                  </div>
                </div>

                {/* Bottom Action Button */}
                <div className="pt-3 border-t border-white/5 flex items-center justify-end">
                  <Link
                    href={targetUrl}
                    className="inline-flex items-center gap-2 px-5 py-2 rounded-xl bg-primary-container hover:bg-inverse-primary text-white font-bold text-xs uppercase tracking-wider transition-all duration-200 hover:scale-105 active:scale-95 shadow-md shadow-primary-container/20 cursor-pointer"
                  >
                    <span className="material-symbols-outlined text-base">play_circle</span>
                    <span>Tomosha qilish</span>
                  </Link>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
