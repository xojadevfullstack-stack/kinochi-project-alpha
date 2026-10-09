"use client";

import React, { useState } from "react";
import Link from "next/link";
import Image from "next/image";

interface FranchiseItem {
  id: number;
  chronological_order: number;
  release_order: number;
  timeline_event_desc?: string | null;
  movie?: {
    id: number;
    title: string;
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
  } | null;
}

interface FranchiseContext {
  collection_id: number;
  collection_name: string;
  collection_slug: string;
  is_franchise: boolean;
  current_chronological_order: number;
  current_release_order: number;
  timeline_event_desc?: string | null;
  total_parts: number;
  prev_item?: FranchiseItem | null;
  next_item?: FranchiseItem | null;
  timeline_items: FranchiseItem[];
}

export default function FranchiseTimelineBar({
  context,
  currentMovieCode,
}: {
  context: FranchiseContext | null;
  currentMovieCode: string;
}) {
  const [showFullTimeline, setShowFullTimeline] = useState(false);

  if (!context || !context.timeline_items || context.timeline_items.length <= 1) {
    return null;
  }

  return (
    <div className="w-full my-6 bg-gradient-to-r from-red-950/40 via-surface-container-high/60 to-black/60 backdrop-blur-xl border border-primary-container/25 rounded-2xl p-4 sm:p-6 shadow-2xl relative overflow-hidden">
      {/* Decorative ambient glow */}
      <div className="absolute top-0 right-0 w-64 h-64 bg-primary-container/10 rounded-full blur-3xl pointer-events-none -mr-20 -mt-20"></div>

      {/* Header Row */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 mb-4 border-b border-white/10 pb-3">
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-xl bg-primary-container/20 border border-primary-container/40 flex items-center justify-center text-primary-container shrink-0">
            <span className="material-symbols-outlined text-xl">auto_awesome_motion</span>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-extrabold uppercase tracking-widest text-primary-container bg-primary-container/15 px-2 py-0.5 rounded-full border border-primary-container/30">
                Voqealar Xronologiyasi
              </span>
              <span className="text-xs text-text-secondary">
                {context.current_chronological_order} / {context.total_parts}-qism
              </span>
            </div>
            <Link
              href={`/collections/${context.collection_slug}`}
              className="font-bold text-base sm:text-lg text-white hover:text-primary-container transition-colors flex items-center gap-1 group"
            >
              <span>{context.collection_name}</span>
              <span className="material-symbols-outlined text-sm group-hover:translate-x-1 transition-transform">
                arrow_forward
              </span>
            </Link>
          </div>
        </div>

        {/* Timeline lore badge & toggle */}
        <div className="flex items-center gap-2 w-full sm:w-auto justify-between sm:justify-end">
          {context.timeline_event_desc && (
            <span className="text-xs text-amber-300/90 font-medium bg-amber-500/10 px-3 py-1 rounded-lg border border-amber-500/20 max-w-[280px] sm:max-w-[340px] truncate">
              ⏳ {context.timeline_event_desc}
            </span>
          )}
          <button
            onClick={() => setShowFullTimeline(!showFullTimeline)}
            className="text-xs text-text-secondary hover:text-white px-2.5 py-1 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 transition-colors shrink-0 flex items-center gap-1"
          >
            <span>{showFullTimeline ? "Qisqartirish" : "To'liq xarita"}</span>
            <span className="material-symbols-outlined text-sm">
              {showFullTimeline ? "expand_less" : "expand_more"}
            </span>
          </button>
        </div>
      </div>

      {/* Prev / Next Instant Navigation Buttons */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-2">
        {context.prev_item?.movie ? (
          <Link
            href={`/movie/${context.prev_item.movie.code}`}
            className="flex items-center gap-3 p-2.5 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 transition-all text-left group"
          >
            <span className="material-symbols-outlined text-xl text-text-secondary group-hover:-translate-x-1 transition-transform">
              arrow_back
            </span>
            <div className="w-9 h-12 rounded bg-surface-container-high overflow-hidden relative shrink-0">
              {context.prev_item.movie.poster_url && (
                <Image
                  src={context.prev_item.movie.poster_url}
                  alt={context.prev_item.movie.title}
                  fill
                  sizes="36px"
                  className="object-cover"
                />
              )}
            </div>
            <div className="overflow-hidden">
              <span className="text-[10px] text-text-secondary uppercase tracking-wider block">
                Oldingi qism (#{context.prev_item.chronological_order})
              </span>
              <span className="text-xs font-bold text-white truncate block">
                {context.prev_item.movie.title}
              </span>
            </div>
          </Link>
        ) : (
          <div className="p-2.5 rounded-xl bg-white/[0.02] border border-white/5 text-left text-xs text-text-secondary/50 flex items-center gap-2">
            <span className="material-symbols-outlined text-lg">flag</span>
            <span>Ushbu saga birinchi qismidan boshlanadi</span>
          </div>
        )}

        {context.next_item?.movie ? (
          <Link
            href={`/movie/${context.next_item.movie.code}`}
            className="flex items-center justify-between gap-3 p-2.5 rounded-xl bg-primary-container/20 hover:bg-primary-container/30 border border-primary-container/40 transition-all text-right group shadow-lg shadow-primary-container/10"
          >
            <div className="flex items-center gap-3 overflow-hidden text-left">
              <div className="w-9 h-12 rounded bg-surface-container-high overflow-hidden relative shrink-0">
                {context.next_item.movie.poster_url && (
                  <Image
                    src={context.next_item.movie.poster_url}
                    alt={context.next_item.movie.title}
                    fill
                    sizes="36px"
                    className="object-cover"
                  />
                )}
              </div>
              <div className="overflow-hidden">
                <span className="text-[10px] text-primary-container font-extrabold uppercase tracking-wider block">
                  Keyingi qism (#{context.next_item.chronological_order})
                </span>
                <span className="text-xs font-bold text-white truncate block">
                  {context.next_item.movie.title}
                </span>
              </div>
            </div>
            <span className="material-symbols-outlined text-xl text-primary-container group-hover:translate-x-1 transition-transform">
              arrow_forward
            </span>
          </Link>
        ) : (
          <div className="p-2.5 rounded-xl bg-white/[0.02] border border-white/5 text-right text-xs text-text-secondary/50 flex items-center justify-end gap-2">
            <span>Saga yakuniy qismidasiz</span>
            <span className="material-symbols-outlined text-lg">check_circle</span>
          </div>
        )}
      </div>

      {/* Expandable Filmstrip Sequence of Entire Franchise */}
      {showFullTimeline && (
        <div className="mt-4 pt-4 border-t border-white/10">
          <span className="text-[11px] font-bold text-text-secondary uppercase tracking-wider block mb-3">
            Butun xronologiya chizig'i ({context.timeline_items.length} ta film):
          </span>
          <div className="flex items-center gap-3 overflow-x-auto pb-3 pt-1 custom-scrollbar">
            {context.timeline_items.map((item) => {
              const isCurrent = item.movie?.code?.toUpperCase() === currentMovieCode.toUpperCase();
              return (
                <Link
                  key={item.id}
                  href={item.movie ? `/movie/${item.movie.code}` : `/collections/${context.collection_slug}`}
                  className={`flex flex-col items-center shrink-0 w-24 p-2 rounded-xl transition-all relative ${
                    isCurrent
                      ? "bg-primary-container/30 border-2 border-primary-container shadow-lg shadow-primary-container/30 scale-105"
                      : "bg-white/5 hover:bg-white/15 border border-white/10"
                  }`}
                >
                  <span
                    className={`absolute -top-2 left-2 text-[10px] font-extrabold px-1.5 py-0.2 rounded-full ${
                      isCurrent
                        ? "bg-primary-container text-white"
                        : "bg-black/80 text-white/70 border border-white/20"
                    }`}
                  >
                    #{item.chronological_order}
                  </span>
                  <div className="w-16 h-22 rounded-lg bg-surface-container-high overflow-hidden relative mb-1.5 border border-white/10">
                    {item.movie?.poster_url && (
                      <Image
                        src={item.movie.poster_url}
                        alt={item.movie.title}
                        fill
                        sizes="64px"
                        className="object-cover"
                      />
                    )}
                  </div>
                  <span className="text-[11px] font-bold text-white text-center line-clamp-2 leading-tight">
                    {item.movie?.title || "Noma'lum"}
                  </span>
                  {item.movie?.release_year && (
                    <span className="text-[10px] text-text-secondary">{item.movie.release_year}</span>
                  )}
                </Link>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
