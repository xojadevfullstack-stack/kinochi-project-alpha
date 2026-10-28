"use client";

import React, { useState, useRef, useEffect, useMemo } from "react";
import Image from "next/image";
import Link from "next/link";
import { useAuth } from "../lib/auth/AuthProvider";
import { fetchApi } from "../lib/api";
import { openTelegramUrl } from "@/lib/telegram";

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
  collectionId?: number;
  initialItems: CollectionItem[];
  collectionName?: string;
  collectionSlug?: string;
}

export default function CollectionTimelineView({
  collectionId,
  initialItems,
  collectionName,
  collectionSlug,
}: CollectionTimelineViewProps) {
  const [viewMode, setViewMode] = useState<"list" | "map">("list");
  const [sortMode, setSortMode] = useState<"chronological" | "release">("chronological");
  const { user } = useAuth();
  const [isSubscribed, setIsSubscribed] = useState(false);
  const [subLoading, setSubLoading] = useState(false);

  // Selected node for Universe Map modal preview
  const [selectedItem, setSelectedItem] = useState<CollectionItem | null>(null);

  // Map Pan & Zoom states
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 50, y: 150 });
  const [isDragging, setIsDragging] = useState(false);
  const dragStartRef = useRef({ x: 0, y: 0 });
  const mapContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (user?.telegram_id && collectionId) {
      fetchApi(`/collections/${collectionId}/subscription-status?telegram_user_id=${user.telegram_id}`)
        .then((res: any) => setIsSubscribed(Boolean(res?.is_subscribed)))
        .catch(() => {});
    }
  }, [user?.telegram_id, collectionId]);

  const handleToggleSub = async () => {
    if (!collectionId) return;
    if (!user?.telegram_id) {
      const botUser = process.env.NEXT_PUBLIC_BOT_USERNAME || "kinochi_mvp_bot";
      openTelegramUrl(`https://t.me/${botUser}?start=col_${collectionId}`);
      return;
    }
    setSubLoading(true);
    try {
      const res: any = await fetchApi(`/collections/${collectionId}/subscribe`, {
        method: "POST",
        body: JSON.stringify({ telegram_user_id: user.telegram_id }),
      });
      setIsSubscribed(Boolean(res?.is_subscribed));
    } catch (e) {
      console.error(e);
    } finally {
      setSubLoading(false);
    }
  };

  // Sort items according to active sortMode
  const sortedItems = useMemo(() => {
    return [...initialItems]
      .filter((item) => Boolean(item.movie || item.series))
      .sort((a, b) => {
        if (sortMode === "chronological") {
          return a.chronological_order - b.chronological_order;
        } else {
          return a.release_order - b.release_order;
        }
      });
  }, [initialItems, sortMode]);

  // Coordinates calculation for the Universe Map
  // Generates an alternating constellation pathway through time
  const mapNodes = useMemo(() => {
    const spacingX = 320;
    return sortedItems.map((item, index) => {
      // Wave pattern: center, slightly up, slightly down
      const wave = Math.sin(index * 1.2) * 90;
      const x = 100 + index * spacingX;
      const y = 240 + wave;
      return { item, index, x, y };
    });
  }, [sortedItems]);

  // Pan handlers for Universe Map
  const handleMouseDown = (e: React.MouseEvent) => {
    if ((e.target as HTMLElement).closest('.interactive-node')) return;
    setIsDragging(true);
    dragStartRef.current = { x: e.clientX - pan.x, y: e.clientY - pan.y };
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging) return;
    setPan({
      x: e.clientX - dragStartRef.current.x,
      y: e.clientY - dragStartRef.current.y,
    });
  };

  const handleMouseUp = () => setIsDragging(false);

  // Touch Handlers for Mobile slide & pinch-zoom
  const touchStartRef = useRef<{ x: number; y: number; dist?: number }>({ x: 0, y: 0 });

  const handleTouchStart = (e: React.TouchEvent) => {
    if ((e.target as HTMLElement).closest('.interactive-node')) return;
    if (e.touches.length === 1) {
      setIsDragging(true);
      touchStartRef.current = {
        x: e.touches[0].clientX - pan.x,
        y: e.touches[0].clientY - pan.y
      };
    } else if (e.touches.length === 2) {
      setIsDragging(true);
      const dx = e.touches[0].clientX - e.touches[1].clientX;
      const dy = e.touches[0].clientY - e.touches[1].clientY;
      touchStartRef.current.dist = Math.hypot(dx, dy);
    }
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    if (!isDragging) return;
    if (e.touches.length === 1) {
      setPan({
        x: e.touches[0].clientX - touchStartRef.current.x,
        y: e.touches[0].clientY - touchStartRef.current.y
      });
    } else if (e.touches.length === 2 && touchStartRef.current.dist) {
      const dx = e.touches[0].clientX - e.touches[1].clientX;
      const dy = e.touches[0].clientY - e.touches[1].clientY;
      const newDist = Math.hypot(dx, dy);
      const factor = newDist / touchStartRef.current.dist;
      setZoom((prev) => Math.min(Math.max(prev * factor, 0.4), 2.2));
      touchStartRef.current.dist = newDist;
    }
  };

  const handleTouchEnd = () => setIsDragging(false);

  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    const zoomFactor = e.deltaY < 0 ? 1.1 : 0.9;
    setZoom((prev) => Math.min(Math.max(prev * zoomFactor, 0.4), 2.2));
  };

  const handleResetMap = () => {
    setZoom(1);
    setPan({ x: 50, y: 150 });
  };

  return (
    <div className="w-full">
      {/* Top Controls & Mode Switcher Bar */}
      <div className="flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-4 bg-surface-container-lowest/80 backdrop-blur-xl border border-white/10 rounded-2xl p-4 sm:p-5 mb-8 shadow-xl">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-primary-container/20 border border-primary-container/40 flex items-center justify-center shrink-0">
            <span className="material-symbols-outlined text-primary-container text-2xl">
              {viewMode === "map" ? "explore" : "view_timeline"}
            </span>
          </div>
          <div>
            <h3 className="font-bold text-sm sm:text-base text-white flex items-center gap-2">
              <span>{collectionName || "Koinot Xronologiyasi"}</span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-white/10 text-text-secondary border border-white/5">
                {sortedItems.length} ta film
              </span>
            </h3>
            <p className="text-xs text-text-secondary">
              {viewMode === "map"
                ? "Interaktiv Voqealar Xaritasi: Koinot yo'nalishini siljiting va kattalashtiring"
                : sortMode === "chronological"
                ? "Voqealar xronologiyasi — film ichidagi koinot voqealari vaqti bo'yicha"
                : "Kinoteatrlarga chiqqan yili — premyera sanalari bo'yicha"}
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Subscription Button */}
          {collectionId && (
            <button
              onClick={handleToggleSub}
              disabled={subLoading}
              className={`flex items-center gap-2 px-3.5 py-2.5 rounded-xl font-bold text-xs transition-all shadow-md cursor-pointer ${
                isSubscribed
                  ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 hover:bg-emerald-500/30"
                  : "bg-primary-container text-white hover:bg-inverse-primary shadow-primary-container/20"
              }`}
              title={isSubscribed ? "Obunani bekor qilish" : "Yangi film chiqsa Telegram orqali xabar olish"}
            >
              <span className="material-symbols-outlined text-[17px]">
                {isSubscribed ? "notifications_active" : "notification_add"}
              </span>
              <span>{isSubscribed ? "Obuna faol" : "Obuna bo'lish"}</span>
            </button>
          )}

          {/* View Mode Toggle: List vs Map */}
          <div className="flex items-center bg-black/60 p-1 rounded-xl border border-white/10">
            <button
              onClick={() => setViewMode("list")}
              className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                viewMode === "list"
                  ? "bg-primary-container text-white shadow-md shadow-primary-container/20"
                  : "text-text-secondary hover:text-white"
              }`}
              title="Klassik ro'yxat ko'rinishi (Low-end va Telegram TMA uchun)"
            >
              <span className="material-symbols-outlined text-[16px]">view_list</span>
              <span>Ro'yxat</span>
            </button>

            <button
              onClick={() => setViewMode("map")}
              className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                viewMode === "map"
                  ? "bg-primary-container text-white shadow-md shadow-primary-container/20"
                  : "text-text-secondary hover:text-white"
              }`}
              title="Dinamik Voqealar Xaritasi (Canvas/Universe Explorer)"
            >
              <span className="material-symbols-outlined text-[16px]">map</span>
              <span>Xarita 3D</span>
            </button>
          </div>

          {/* Sort Mode Toggle: Chronological vs Release */}
          <div className="flex items-center bg-black/60 p-1 rounded-xl border border-white/10">
            <button
              onClick={() => setSortMode("chronological")}
              className={`px-3 py-2 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                sortMode === "chronological"
                  ? "bg-white/15 text-white"
                  : "text-text-secondary hover:text-white"
              }`}
              title="Voqealar xronologiyasi bo'yicha"
            >
              📅 Voqealar
            </button>

            <button
              onClick={() => setSortMode("release")}
              className={`px-3 py-2 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                sortMode === "release"
                  ? "bg-white/15 text-white"
                  : "text-text-secondary hover:text-white"
              }`}
              title="Premyera yili bo'yicha"
            >
              🎞️ Premyera
            </button>
          </div>
        </div>
      </div>

      {/* VIEW 1: DYNAMIC INTERACTIVE UNIVERSE MAP */}
      {viewMode === "map" && (
        <div className="relative w-full h-[620px] rounded-3xl overflow-hidden border border-white/10 bg-[#070b14] shadow-2xl select-none">
          {/* Map Controls Floating Overlay */}
          <div className="absolute top-4 right-4 z-20 flex flex-col gap-2 bg-black/70 backdrop-blur-md p-1.5 rounded-2xl border border-white/10 shadow-xl">
            <button
              onClick={() => setZoom((z) => Math.min(z * 1.2, 2.2))}
              className="w-9 h-9 rounded-xl bg-white/5 hover:bg-white/15 text-white flex items-center justify-center transition-all cursor-pointer"
              title="Kattalashtirish (+)"
            >
              <span className="material-symbols-outlined text-lg">zoom_in</span>
            </button>
            <button
              onClick={() => setZoom((z) => Math.max(z * 0.8, 0.4))}
              className="w-9 h-9 rounded-xl bg-white/5 hover:bg-white/15 text-white flex items-center justify-center transition-all cursor-pointer"
              title="Kichiklashtirish (-)"
            >
              <span className="material-symbols-outlined text-lg">zoom_out</span>
            </button>
            <button
              onClick={handleResetMap}
              className="w-9 h-9 rounded-xl bg-white/5 hover:bg-white/15 text-white flex items-center justify-center transition-all cursor-pointer"
              title="Markazga qaytarish"
            >
              <span className="material-symbols-outlined text-lg">restart_alt</span>
            </button>
          </div>

          {/* Interactive Legend & Guide Banner */}
          <div className="absolute top-4 left-4 z-20 flex items-center gap-2 bg-black/60 backdrop-blur-md px-3.5 py-2 rounded-xl border border-white/10 text-xs text-text-secondary pointer-events-none">
            <span className="material-symbols-outlined text-primary-container text-sm">touch_app</span>
            <span>Xaritani barmog'ingiz yoki sichqoncha bilan suring, kattalashtiring yoki tugunlarni bosing</span>
          </div>

          {/* Universe Interactive Canvas Area */}
          <div
            ref={mapContainerRef}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseUp}
            onTouchStart={handleTouchStart}
            onTouchMove={handleTouchMove}
            onTouchEnd={handleTouchEnd}
            onTouchCancel={handleTouchEnd}
            onWheel={handleWheel}
            className={`w-full h-full cursor-grab ${isDragging ? "cursor-grabbing" : ""} relative overflow-hidden touch-none`}
          >
            {/* Background Grid & Stars */}
            <div 
              className="absolute inset-0 pointer-events-none opacity-40"
              style={{
                backgroundImage: "radial-gradient(circle at 1px 1px, rgba(255,255,255,0.15) 1px, transparent 0)",
                backgroundSize: `${40 * zoom}px ${40 * zoom}px`,
                backgroundPosition: `${pan.x}px ${pan.y}px`,
              }}
            />

            {/* Transform Container */}
            <div
              className="absolute inset-0 origin-top-left transition-transform duration-75 ease-out"
              style={{
                transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
              }}
            >
              {/* Connecting Constellation Curves (SVG) */}
              <svg 
                className="absolute top-0 left-0 pointer-events-none overflow-visible"
                style={{ width: "100%", height: "100%" }}
              >
                <defs>
                  <linearGradient id="pathGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stopColor="#e50914" stopOpacity="0.8" />
                    <stop offset="50%" stopColor="#f59e0b" stopOpacity="0.8" />
                    <stop offset="100%" stopColor="#38bdf8" stopOpacity="0.8" />
                  </linearGradient>
                  <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
                    <feGaussianBlur stdDeviation="3" result="glow" />
                    <feMerge>
                      <feMergeNode in="glow" />
                      <feMergeNode in="SourceGraphic" />
                    </feMerge>
                  </filter>
                </defs>

                {/* Connecting Curved Lines */}
                {mapNodes.map((curr, idx) => {
                  if (idx === mapNodes.length - 1) return null;
                  const next = mapNodes[idx + 1];
                  const midX = (curr.x + next.x) / 2;
                  const d = `M ${curr.x} ${curr.y} C ${midX} ${curr.y}, ${midX} ${next.y}, ${next.x} ${next.y}`;
                  return (
                    <g key={`path_${idx}`}>
                      {/* Outer Glow Line */}
                      <path
                        d={d}
                        fill="none"
                        stroke="url(#pathGradient)"
                        strokeWidth="5"
                        strokeOpacity="0.3"
                        filter="url(#glow)"
                      />
                      {/* Main Glowing Dashed Constellation Line */}
                      <path
                        d={d}
                        fill="none"
                        stroke="url(#pathGradient)"
                        strokeWidth="2.5"
                        strokeDasharray="6 4"
                      />
                    </g>
                  );
                })}
              </svg>

              {/* Story Nodes */}
              {mapNodes.map(({ item, index, x, y }) => {
                const content = item.movie || item.series;
                const isSelected = selectedItem?.id === item.id;
                const nodeYear = content?.release_year || "Yil";
                const activeOrder = index + 1;

                return (
                  <div
                    key={`node_${item.id}`}
                    onClick={(e) => {
                      e.stopPropagation();
                      setSelectedItem(item);
                    }}
                    style={{ left: `${x}px`, top: `${y}px` }}
                    className="interactive-node absolute -translate-x-1/2 -translate-y-1/2 cursor-pointer group z-10"
                  >
                    {/* Pulsating Orbit Ring */}
                    <div className="absolute inset-0 -m-3 rounded-full border border-primary-container/40 animate-ping opacity-25 pointer-events-none" />

                    {/* Node Core Card */}
                    <div className={`relative w-44 rounded-2xl p-2.5 transition-all duration-300 transform group-hover:-translate-y-2 group-hover:scale-105 shadow-2xl border ${
                      isSelected 
                        ? "bg-surface-container-high border-primary-container ring-4 ring-primary-container/20" 
                        : "bg-[#111928]/90 border-white/15 hover:border-primary-container/60"
                    }`}>
                      {/* Step Number Badge */}
                      <div className="absolute -top-3.5 -left-2 bg-primary-container text-white font-black text-xs px-2.5 py-0.5 rounded-full shadow-lg border border-white/20 flex items-center gap-1">
                        <span>#{activeOrder}</span>
                      </div>

                      {/* Poster Thumbnail */}
                      <div className="relative w-full h-24 rounded-xl overflow-hidden bg-black/40 mb-2">
                        {content?.poster_url ? (
                          <img
                            src={content.poster_url}
                            alt={content?.title || "Poster"}
                            className="w-full h-full object-cover"
                            loading="lazy"
                          />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center text-white/30 text-xs">
                            Kinochi
                          </div>
                        )}
                        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent" />
                        <span className="absolute bottom-1 right-1.5 text-[10px] font-mono font-bold text-white bg-black/70 px-1.5 py-0.5 rounded">
                          {nodeYear}
                        </span>
                      </div>

                      {/* Title & Lore snippet */}
                      <h4 className="font-bold text-xs text-white truncate group-hover:text-primary-container transition-colors">
                        {content?.title || "Film"}
                      </h4>

                      {item.timeline_event_desc ? (
                        <p className="text-[10px] text-text-secondary truncate mt-0.5">
                          {item.timeline_event_desc}
                        </p>
                      ) : (
                        <p className="text-[10px] text-text-secondary truncate mt-0.5">
                          {content?.release_year ? `${content.release_year}-yil premyera` : "Voqea"}
                        </p>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Interactive Universe Item Modal / Popup */}
          {selectedItem && (
            <div className="absolute bottom-6 left-6 right-6 md:left-auto md:right-6 md:w-96 z-30 bg-[#161f30]/95 backdrop-blur-xl border border-white/20 rounded-2xl p-4 shadow-2xl animate-in fade-in slide-in-from-bottom-4 duration-200">
              <div className="flex items-start justify-between gap-3 mb-2">
                <div className="flex items-center gap-2">
                  <span className="bg-primary-container/20 text-primary-container border border-primary-container/30 text-[10px] font-bold px-2 py-0.5 rounded-md uppercase">
                    Voqea Tafsiloti
                  </span>
                  {selectedItem.movie?.imdb_rating && (
                    <span className="text-rating-gold text-xs font-bold flex items-center gap-0.5">
                      ★ {Number(selectedItem.movie.imdb_rating).toFixed(1)}
                    </span>
                  )}
                </div>
                <button
                  onClick={() => setSelectedItem(null)}
                  className="text-text-secondary hover:text-white p-1 rounded-lg transition-colors cursor-pointer"
                >
                  <span className="material-symbols-outlined text-sm">close</span>
                </button>
              </div>

              <h3 className="font-bold text-base text-white mb-1">
                {selectedItem.movie?.title || selectedItem.series?.title}
              </h3>

              {selectedItem.timeline_event_desc && (
                <div className="p-2.5 rounded-xl bg-primary-container/10 border border-primary-container/20 text-white text-xs my-2 font-medium">
                  ⏳ <strong>Koinot voqeasi:</strong> {selectedItem.timeline_event_desc}
                </div>
              )}

              <div className="flex items-center justify-between text-xs text-text-secondary mt-3 pt-3 border-t border-white/10">
                <span>Tartib: #{selectedItem.chronological_order}</span>
                <Link
                  href={selectedItem.movie ? `/movie/${selectedItem.movie.code}` : selectedItem.series ? `/series/${selectedItem.series.id}` : "#"}
                  className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-primary-container hover:bg-inverse-primary text-white font-bold text-xs transition-all shadow-md cursor-pointer"
                >
                  <span className="material-symbols-outlined text-sm">play_circle</span>
                  <span>Tomosha qilish</span>
                </Link>
              </div>
            </div>
          )}
        </div>
      )}

      {/* VIEW 2: CLASSIC TIMELINE LIST (LIGHTWEIGHT & RESPONSIVE) */}
      {viewMode === "list" && (
        <div className="space-y-4">
          {sortedItems.map((item, idx) => {
            const activeOrder = idx + 1;
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
                      {activeOrder}
                    </span>
                    <span className="text-[9px] text-text-secondary uppercase tracking-wider hidden md:block">
                      Qism
                    </span>
                  </div>

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
                    {sortMode === "chronological" && item.timeline_event_desc && (
                      <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-primary-container/15 border border-primary-container/30 text-white font-semibold text-xs mb-2.5">
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
      )}
    </div>
  );
}
