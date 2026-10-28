"use client";

import { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { CatalogItem } from "@/lib/api/catalog";
import { isAdultContent } from "@/lib/adult";
import AdultPoster from "@/components/AdultPoster";
import SourceBadge from "@/components/SourceBadge";

export default function MovieCard({
  item,
  statusBadge,
  href: customHref,
}: {
  item: CatalogItem;
  statusBadge?: "completed" | "in_progress";
  href?: string;
}) {
  const [isHoverPreview, setIsHoverPreview] = useState(false);
  const [videoActive, setVideoActive] = useState(false);
  const hoverTimerRef = useRef<NodeJS.Timeout | null>(null);
  const videoActiveTimerRef = useRef<NodeJS.Timeout | null>(null);
  const holdTriggeredRef = useRef(false);
  const touchStartPosRef = useRef<{ x: number; y: number } | null>(null);

  const isSeries = !!item.is_series || (!item.code && !!item.id);
  const is18Plus = isAdultContent(item);
  const targetSeriesId = (item.id && Number(item.id) > 0) ? item.id : (item.code || item.id);
  const defaultHref = isSeries ? `/series/${targetSeriesId}` : `/movie/${item.code || item.id}`;
  const href = customHref || defaultHref;

  const primaryGenre = item.genres?.split(",")[0]?.trim() || (isSeries ? "Serial" : "Kino");
  const rawRating = item.imdb_rating || item.tmdb_rating;
  const displayRating = rawRating && Number(rawRating) > 0 ? Number(rawRating).toFixed(1) : null;

  // Trailer detection
  const cleanTrailer = (item.trailer_url || "").trim();
  const getYoutubeId = (url: string) => {
    const regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|&v=)([^#&?]*).*/;
    const match = url.match(regExp);
    return match && match[2].length === 11 ? match[2] : null;
  };
  const isYoutube = cleanTrailer.includes("youtube.com") || cleanTrailer.includes("youtu.be");
  const youtubeId = isYoutube ? getYoutubeId(cleanTrailer) : null;
  const isDirectMp4 = cleanTrailer.endsWith(".mp4") || cleanTrailer.includes(".mp4?");
  const hasTrailer = Boolean(youtubeId || isDirectMp4);

  const closePreview = () => {
    if (hoverTimerRef.current) clearTimeout(hoverTimerRef.current);
    if (videoActiveTimerRef.current) clearTimeout(videoActiveTimerRef.current);
    setIsHoverPreview(false);
    setVideoActive(false);
  };

  useEffect(() => {
    return () => {
      if (hoverTimerRef.current) clearTimeout(hoverTimerRef.current);
      if (videoActiveTimerRef.current) clearTimeout(videoActiveTimerRef.current);
    };
  }, []);

  // When preview is active, close it if the user scrolls the page
  useEffect(() => {
    if (!isHoverPreview) return;
    const handleScroll = () => {
      closePreview();
    };
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, [isHoverPreview]);

  const handleMouseEnter = () => {
    if (!hasTrailer) return;
    hoverTimerRef.current = setTimeout(() => {
      setIsHoverPreview(true);
    }, 450);
  };

  const handleMouseLeave = () => {
    closePreview();
  };

  const handleTouchStart = (e: React.TouchEvent) => {
    if (!hasTrailer) return;
    holdTriggeredRef.current = false;
    if (e.touches && e.touches[0]) {
      touchStartPosRef.current = { x: e.touches[0].clientX, y: e.touches[0].clientY };
    }
    if (hoverTimerRef.current) clearTimeout(hoverTimerRef.current);
    hoverTimerRef.current = setTimeout(() => {
      holdTriggeredRef.current = true;
      setIsHoverPreview(true);
    }, 1000); // 1 soniya hold qilinganda faollashadi
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    if (!touchStartPosRef.current || !e.touches || !e.touches[0]) return;
    const dx = Math.abs(e.touches[0].clientX - touchStartPosRef.current.x);
    const dy = Math.abs(e.touches[0].clientY - touchStartPosRef.current.y);
    if (dx > 10 || dy > 10) {
      // User is scrolling the catalog: cancel hold timer so preview is not triggered
      if (hoverTimerRef.current) {
        clearTimeout(hoverTimerRef.current);
      }
    }
  };

  const handleTouchEnd = () => {
    // 1 soniyaga yetmasdan qo'yib yuborilsa taymer bekor qilinadi
    if (hoverTimerRef.current) {
      clearTimeout(hoverTimerRef.current);
    }
    touchStartPosRef.current = null;
    // Agar video boshlangan bo'lsa, tinimsiz ushlab turish shart emas, davom etadi
  };

  const handleClick = (e: React.MouseEvent) => {
    if (holdTriggeredRef.current) {
      // Prevent opening details page upon releasing the 1s preview hold
      e.preventDefault();
      e.stopPropagation();
      holdTriggeredRef.current = false;
    }
  };

  return (
    <Link
      href={href}
      onClick={handleClick}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
      onTouchCancel={handleTouchEnd}
      className="group relative flex flex-col cursor-pointer transition-all duration-300"
    >
      {/* 1. Poster Container with rounded-2xl */}
      <div className="relative aspect-[2/3] w-full rounded-2xl overflow-hidden bg-surface-container shadow-md ring-1 ring-white/10 group-hover:ring-white/30 group-hover:shadow-2xl transition-all duration-300">
        {item.poster_url ? (
          <AdultPoster
            src={item.poster_url}
            alt={item.title}
            is18Plus={is18Plus}
            fill
            sizes="(max-width: 640px) 140px, (max-width: 768px) 180px, 220px"
            imageClassName="object-cover group-hover:scale-105 transition-transform duration-500 ease-out"
          />
        ) : (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-surface-container-high text-gray-500">
            <span className="material-symbols-outlined text-4xl mb-2 opacity-30">
              {isSeries ? "live_tv" : "movie"}
            </span>
          </div>
        )}

        {/* Ambient Dark Gradient */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent opacity-60 group-hover:opacity-40 transition-opacity duration-300 pointer-events-none" />

        {/* Hover / Touch Trailer Preview Overlay (YouTube UI cropped beyond card bounds & touch shielded) */}
        {isHoverPreview && hasTrailer && (
          <div
            className={`absolute inset-0 z-20 overflow-hidden rounded-2xl pointer-events-none transition-opacity duration-700 ease-in-out ${
              videoActive ? "opacity-100 bg-black" : "opacity-0"
            }`}
          >
            {youtubeId ? (
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[300%] h-[160%] pointer-events-none flex items-center justify-center">
                <iframe
                  src={`https://www.youtube-nocookie.com/embed/${youtubeId}?autoplay=1&mute=1&controls=0&playsinline=1&rel=0&showinfo=0&modestbranding=1&enablejsapi=1&iv_load_policy=3&disablekb=1&fs=0`}
                  style={{
                    width: "1280px",
                    height: "720px",
                    maxWidth: "none",
                    pointerEvents: "none",
                  }}
                  className="scale-[0.35] xs:scale-[0.4] sm:scale-[0.45] md:scale-[0.5] pointer-events-none select-none border-0"
                  allow="autoplay"
                  tabIndex={-1}
                  onLoad={() => {
                    if (videoActiveTimerRef.current) clearTimeout(videoActiveTimerRef.current);
                    videoActiveTimerRef.current = setTimeout(() => {
                      setVideoActive(true);
                    }, 2400); // YouTube o'zining dastlabki 2 soniyalik pauza belgisini to'liq yashirib bo'lgach video ochiladi
                  }}
                />
              </div>
            ) : isDirectMp4 ? (
              <video
                autoPlay
                muted
                loop
                playsInline
                onCanPlay={() => setVideoActive(true)}
                className="w-full h-full object-cover pointer-events-none"
                src={cleanTrailer}
              />
            ) : null}
          </div>
        )}

        {/* Global Transparent Touch/Click Shield: sits at z-30 over the entire card so touches/clicks NEVER hit the YouTube player */}
        {isHoverPreview && (
          <div
            className="absolute inset-0 z-30 cursor-pointer select-none"
            style={{ backgroundColor: "rgba(0, 0, 0, 0.001)", touchAction: "manipulation" }}
          />
        )}

        {/* Top Left Badges: Status (Completed / In Progress) */}
        <div className="absolute top-2.5 left-2.5 z-10 flex flex-col gap-1 items-start pointer-events-none">
          {statusBadge === "completed" && (
            <div className="px-2 py-0.5 bg-emerald-500/90 backdrop-blur-md rounded-md text-white text-[10px] font-bold uppercase tracking-wider border border-emerald-400/30 flex items-center gap-1 shadow-sm">
              <span className="material-symbols-outlined text-[11px]">check_circle</span>
              Ko&apos;rilgan
            </div>
          )}
          {statusBadge === "in_progress" && (
            <div className="px-2 py-0.5 bg-sky-500/90 backdrop-blur-md rounded-md text-white text-[10px] font-bold uppercase tracking-wider border border-sky-400/30 flex items-center gap-1 shadow-sm">
              <span className="material-symbols-outlined text-[11px]">schedule</span>
              Davom etmoqda
            </div>
          )}
        </div>

        {/* Bottom Left: Source badge */}
        {item.source_type && (
          <div className="absolute bottom-2.5 left-2.5 z-10 pointer-events-none">
            <SourceBadge
              sourceType={item.source_type}
              customSourceName={item.custom_source_name}
              customSourceLogo={item.custom_source_logo}
              size="sm"
              className="px-2 py-0.5 bg-black/80 backdrop-blur-md rounded-md text-[10px] font-bold tracking-wider border border-white/15 flex items-center gap-1 shadow-sm text-white"
            />
          </div>
        )}

        {/* Bottom Right: ONLY real 18+ badge when applicable */}
        {is18Plus && (
          <div className="absolute bottom-2.5 right-2.5 z-10 pointer-events-none">
            <div className="px-2 py-0.5 rounded-md text-[10px] font-extrabold border shadow-sm backdrop-blur-md bg-red-600/90 text-white border-red-500/40">
              18+
            </div>
          </div>
        )}

        {/* Hover / Expanded State: Real Meta & Real Ratings */}
        <div className="absolute inset-x-0 bottom-0 p-3 bg-gradient-to-t from-black via-black/95 to-black/30 backdrop-blur-sm opacity-0 group-hover:opacity-100 transition-all duration-300 transform translate-y-2 group-hover:translate-y-0 z-20 flex flex-col justify-end pointer-events-none">
          {/* Metadata line: Real Year and Genre only */}
          <div className="text-[11px] font-medium text-white/90 truncate mb-1">
            {item.release_year ? `${item.release_year} • ` : ""}{primaryGenre}
          </div>

          {/* Ratings row: Unified IMDb score */}
          {displayRating ? (
            <div className="flex items-center gap-2 text-xs font-black tracking-tight">
              <span className="flex items-center gap-1">
                <span className="px-1.5 py-0.5 bg-[#f5c518] text-black font-extrabold rounded text-[9px] leading-none tracking-wider">
                  IMDb
                </span>
                <span className="text-white font-bold">
                  {displayRating}
                </span>
              </span>
            </div>
          ) : null}
        </div>
      </div>

      {/* 2. Content underneath the poster */}
      <div className="pt-2 px-0.5 flex flex-col">
        <h3 className="font-bold text-sm sm:text-[15px] text-white leading-snug line-clamp-1 group-hover:text-primary transition-colors">
          {item.title}
        </h3>
      </div>
    </Link>
  );
}
