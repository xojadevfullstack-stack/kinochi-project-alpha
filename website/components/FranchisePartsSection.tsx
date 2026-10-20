"use client";

import React, { useRef } from "react";
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
    genres?: string | null;
  } | null;
  series?: {
    id: number;
    title: string;
    poster_url?: string | null;
    release_year?: number | null;
    imdb_rating?: number | null;
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

export default function FranchisePartsSection({
  context,
  currentMovieCode,
}: {
  context: FranchiseContext | null;
  currentMovieCode: string;
}) {
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  if (!context || !context.timeline_items || context.timeline_items.length <= 1) {
    return null;
  }

  const scroll = (direction: "left" | "right") => {
    if (!scrollContainerRef.current) return;
    const scrollAmount = 450;
    scrollContainerRef.current.scrollBy({
      left: direction === "left" ? -scrollAmount : scrollAmount,
      behavior: "smooth",
    });
  };

  return (
    <div className="w-full my-8 bg-surface-container/60 backdrop-blur-xl border border-white/10 rounded-2xl p-5 sm:p-7 shadow-2xl relative overflow-hidden">
      {/* Ambient background accent */}
      <div className="absolute top-0 right-0 w-80 h-80 bg-primary/5 rounded-full blur-3xl pointer-events-none -mr-24 -mt-24"></div>

      {/* Header Row */}
      <div className="flex items-center justify-between gap-4 mb-6 pb-4 border-b border-white/10">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-primary/10 border border-primary/25 flex items-center justify-center text-primary shrink-0">
            <svg
              className="w-5 h-5 fill-current"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path d="M4 6H2v14c0 1.1.9 2 2 2h14v-2H4V6zm16-4H8c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H8V4h12v12z" />
            </svg>
          </div>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h2 className="text-lg sm:text-xl md:text-2xl font-bold tracking-tight text-white">
                Franshizaning boshqa qismlari
              </h2>
              <span className="text-[11px] font-semibold text-text-secondary bg-white/[0.06] px-2.5 py-0.5 rounded-full border border-white/10">
                {context.timeline_items.length} ta qism
              </span>
            </div>
            <p className="text-xs sm:text-sm text-text-secondary mt-0.5">
              {context.collection_name}
            </p>
          </div>
        </div>

        {/* Carousel Scroll Navigation Buttons */}
        <div className="hidden sm:flex items-center gap-2 shrink-0">
          <button
            onClick={() => scroll("left")}
            aria-label="Oldingi qismlar"
            className="w-9 h-9 rounded-xl bg-white/5 hover:bg-white/10 active:scale-95 border border-white/10 text-white/80 hover:text-white transition-all flex items-center justify-center cursor-pointer"
          >
            <svg className="w-5 h-5 fill-current" viewBox="0 0 24 24">
              <path d="M15.41 7.41L14 6l-6 6 6 6 1.41-1.41L10.83 12z" />
            </svg>
          </button>
          <button
            onClick={() => scroll("right")}
            aria-label="Keyingi qismlar"
            className="w-9 h-9 rounded-xl bg-white/5 hover:bg-white/10 active:scale-95 border border-white/10 text-white/80 hover:text-white transition-all flex items-center justify-center cursor-pointer"
          >
            <svg className="w-5 h-5 fill-current" viewBox="0 0 24 24">
              <path d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z" />
            </svg>
          </button>
        </div>
      </div>

      {/* Cards Track */}
      <div
        ref={scrollContainerRef}
        className="flex items-stretch gap-4 sm:gap-5 overflow-x-auto pb-3 pt-1 scrollbar-thin scroll-smooth"
        style={{ scrollbarWidth: "thin" }}
      >
        {context.timeline_items.map((item) => {
          const movie = item.movie;
          const series = item.series;
          const itemTitle = movie?.title || series?.title || "Noma'lum film";
          const itemCode = movie?.code || "";
          const isCurrent =
            itemCode.length > 0 &&
            itemCode.toUpperCase() === currentMovieCode.toUpperCase();
          const posterUrl = movie?.poster_url || series?.poster_url;
          const releaseYear = movie?.release_year || series?.release_year;
          const primaryGenre = movie?.genres
            ? movie.genres.split(",")[0].trim()
            : "Tarjima kino";
          const targetUrl = movie
            ? `/movie/${movie.code}`
            : `/collections/${context.collection_slug}`;

          return (
            <Link
              key={item.id}
              href={targetUrl}
              className={`group flex flex-col shrink-0 w-40 sm:w-48 transition-all duration-300 rounded-xl ${
                isCurrent ? "pointer-events-none" : "hover:-translate-y-1.5"
              }`}
            >
              {/* Poster Card */}
              <div
                className={`relative aspect-[2/3] w-full rounded-xl overflow-hidden bg-surface-container-high transition-all duration-300 ${
                  isCurrent
                    ? "border-2 border-primary shadow-xl shadow-primary/25 ring-2 ring-primary/30"
                    : "border border-white/10 group-hover:border-primary/50 group-hover:shadow-xl group-hover:shadow-black/70"
                }`}
              >
                {/* Part index badge */}
                <div className="absolute top-2.5 left-2.5 z-10">
                  <span className="text-[11px] font-bold px-2 py-0.5 rounded-md bg-black/80 backdrop-blur-md text-white/90 border border-white/15 shadow-sm">
                    {item.chronological_order}-qism
                  </span>
                </div>

                {/* Current watching badge */}
                {isCurrent && (
                  <div className="absolute top-2.5 right-2.5 z-10">
                    <span className="inline-flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-md bg-primary text-white shadow-md shadow-primary/40">
                      <span className="w-1.5 h-1.5 rounded-full bg-white animate-pulse"></span>
                      Hozirgi
                    </span>
                  </div>
                )}

                {/* Poster image */}
                {posterUrl ? (
                  <Image
                    src={posterUrl}
                    alt={itemTitle}
                    fill
                    sizes="(max-width: 640px) 160px, 192px"
                    className="object-cover transition-transform duration-500 group-hover:scale-105"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-white/30 bg-surface-variant">
                    <svg className="w-12 h-12 fill-current" viewBox="0 0 24 24">
                      <path d="M18 4l2 4h-3l-2-4h-2l2 4h-3l-2-4H8l2 4H7L5 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V4h-4z" />
                    </svg>
                  </div>
                )}

                {/* Play Icon / Overlay */}
                {isCurrent ? (
                  <div className="absolute inset-0 flex items-center justify-center bg-black/30 pointer-events-none">
                    <div className="w-11 h-11 rounded-full bg-primary text-white flex items-center justify-center shadow-lg shadow-black/80 ring-2 ring-white/30">
                      <svg className="w-5 h-5 ml-0.5 fill-current" viewBox="0 0 24 24">
                        <path d="M8 5v14l11-7z" />
                      </svg>
                    </div>
                  </div>
                ) : (
                  <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-center justify-center">
                    <div className="w-11 h-11 rounded-full bg-white/20 backdrop-blur-md border border-white/30 text-white flex items-center justify-center transform scale-75 group-hover:scale-100 transition-transform duration-300 shadow-lg shadow-black/60">
                      <svg className="w-5 h-5 ml-0.5 fill-current" viewBox="0 0 24 24">
                        <path d="M8 5v14l11-7z" />
                      </svg>
                    </div>
                  </div>
                )}
              </div>

              {/* Title and Metadata */}
              <div className="pt-2.5 px-0.5 flex flex-col flex-grow">
                <h3
                  className={`text-sm font-bold line-clamp-2 leading-snug transition-colors ${
                    isCurrent
                      ? "text-primary"
                      : "text-white group-hover:text-primary"
                  }`}
                  title={itemTitle}
                >
                  {itemTitle}
                </h3>
                <div className="flex items-center gap-2 text-xs text-text-secondary mt-1">
                  <span>{primaryGenre}</span>
                  {releaseYear && (
                    <>
                      <span className="w-1 h-1 rounded-full bg-white/30"></span>
                      <span>{releaseYear}</span>
                    </>
                  )}
                </div>
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
