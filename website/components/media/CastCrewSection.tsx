"use client";

import { useEffect, useState, useRef } from "react";
import Image from "next/image";
import { fetchApi } from "@/lib/api";
import ActorFilmographyModal, { ActorModalData } from "./ActorFilmographyModal";

export interface CastMember {
  id: number;
  name: string;
  role: string;
  character?: string;
  photo_url?: string | null;
  order?: number;
}

export interface TmdbDetails {
  original_title?: string | null;
  countries?: string[];
  companies?: string[];
  release_date?: string | null;
  status?: string | null;
  runtime?: string | null;
  budget?: string | null;
  revenue?: string | null;
  tagline?: string | null;
}

interface CastCrewSectionProps {
  mediaIdOrCode: string | number;
  mediaType: "movie" | "series";
  initialCredits?: CastMember[];
  initialDetails?: TmdbDetails | null;
}

export default function CastCrewSection({
  mediaIdOrCode,
  mediaType,
  initialCredits,
  initialDetails,
}: CastCrewSectionProps) {
  const [credits, setCredits] = useState<CastMember[]>(initialCredits || []);
  const [details, setDetails] = useState<TmdbDetails | null>(initialDetails || null);
  const [loading, setLoading] = useState(!initialCredits);

  // Slider & Drag state
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const [canScrollLeft, setCanScrollLeft] = useState(false);
  const [canScrollRight, setCanScrollRight] = useState(true);
  const [isDragging, setIsDragging] = useState(false);
  const [startX, setStartX] = useState(0);
  const [scrollLeftPos, setScrollLeftPos] = useState(0);
  const [selectedActor, setSelectedActor] = useState<ActorModalData | null>(null);
  const hasDraggedRef = useRef(false);

  useEffect(() => {
    if (initialCredits && initialCredits.length > 0) return;

    let isMounted = true;
    async function loadData() {
      try {
        const endpoint =
          mediaType === "series"
            ? `/series/${mediaIdOrCode}/credits`
            : `/movies/${mediaIdOrCode}/credits`;
        const res = await fetchApi(endpoint);
        if (isMounted) {
          if (res?.items && Array.isArray(res.items)) {
            setCredits(res.items);
          }
          if (res?.details) {
            setDetails(res.details);
          }
        }
      } catch (err) {
        // Silently catch - graceful degradation
      } finally {
        if (isMounted) setLoading(false);
      }
    }

    loadData();
    return () => {
      isMounted = false;
    };
  }, [mediaIdOrCode, mediaType, initialCredits]);

  // Update button enabled states on scroll
  const handleScroll = () => {
    if (!scrollContainerRef.current) return;
    const { scrollLeft, scrollWidth, clientWidth } = scrollContainerRef.current;
    setCanScrollLeft(scrollLeft > 10);
    setCanScrollRight(scrollLeft < scrollWidth - clientWidth - 10);
  };

  const scroll = (direction: "left" | "right") => {
    if (!scrollContainerRef.current) return;
    const offset = direction === "left" ? -360 : 360;
    scrollContainerRef.current.scrollBy({ left: offset, behavior: "smooth" });
  };

  // Mouse Drag-to-scroll handlers
  const onMouseDown = (e: React.MouseEvent) => {
    if (!scrollContainerRef.current) return;
    setIsDragging(true);
    hasDraggedRef.current = false;
    setStartX(e.pageX - scrollContainerRef.current.offsetLeft);
    setScrollLeftPos(scrollContainerRef.current.scrollLeft);
  };

  const onMouseMove = (e: React.MouseEvent) => {
    if (!isDragging || !scrollContainerRef.current) return;
    e.preventDefault();
    const x = e.pageX - scrollContainerRef.current.offsetLeft;
    if (Math.abs(x - startX) > 6) {
      hasDraggedRef.current = true;
    }
    const walk = (x - startX) * 1.5;
    scrollContainerRef.current.scrollLeft = scrollLeftPos - walk;
  };

  const handlePersonClick = (person: CastMember) => {
    if (hasDraggedRef.current) return;
    setSelectedActor({
      id: person.id,
      name: person.name,
      role: person.role,
      photo_url: person.photo_url,
    });
  };

  const onMouseUpOrLeave = () => {
    setIsDragging(false);
  };

  if (loading) {
    return (
      <section className="max-w-container-max mx-auto px-gutter my-8 relative z-20">
        <div className="rounded-2xl bg-white/[0.03] border border-white/5 p-6 animate-pulse">
          <div className="h-6 w-48 bg-white/10 rounded mb-4" />
          <div className="flex gap-4 overflow-x-auto pb-4">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <div key={i} className="flex flex-col items-center shrink-0 w-20">
                <div className="w-16 h-16 sm:w-20 sm:h-20 rounded-full bg-white/5 mb-2" />
                <div className="h-3 w-14 bg-white/5 rounded" />
              </div>
            ))}
          </div>
        </div>
      </section>
    );
  }

  if (credits.length === 0 && !details) {
    return null;
  }

  return (
    <section className="max-w-container-max mx-auto px-gutter my-8 sm:my-10 relative z-20">
      {/* Bitta jamlangan div: Suratga olish guruhi + TMDb Ma'lumotlari */}
      <div className="rounded-2xl bg-white/[0.03] border border-white/5 p-5 sm:p-7 backdrop-blur-sm shadow-xl flex flex-col gap-6">
        {/* 1. Suratga olish guruhi */}
        {credits.length > 0 && (
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg sm:text-xl font-bold text-white flex items-center gap-2">
                <span className="w-1.5 h-5 bg-primary rounded-full block"></span>
                Suratga olish guruhi
              </h2>

              {/* Desktop Slider Controls */}
              <div className="hidden sm:flex items-center gap-1.5">
                <button
                  type="button"
                  aria-label="Chapga"
                  onClick={() => scroll("left")}
                  disabled={!canScrollLeft}
                  className={`w-8 h-8 rounded-full border flex items-center justify-center transition-all ${
                    canScrollLeft
                      ? "bg-white/10 hover:bg-white/20 border-white/20 text-white cursor-pointer active:scale-95"
                      : "bg-white/5 border-white/5 text-white/20 cursor-not-allowed opacity-40"
                  }`}
                >
                  <span className="material-symbols-outlined text-lg">chevron_left</span>
                </button>
                <button
                  type="button"
                  aria-label="O'ngga"
                  onClick={() => scroll("right")}
                  disabled={!canScrollRight}
                  className={`w-8 h-8 rounded-full border flex items-center justify-center transition-all ${
                    canScrollRight
                      ? "bg-white/10 hover:bg-white/20 border-white/20 text-white cursor-pointer active:scale-95"
                      : "bg-white/5 border-white/5 text-white/20 cursor-not-allowed opacity-40"
                  }`}
                >
                  <span className="material-symbols-outlined text-lg">chevron_right</span>
                </button>
              </div>
            </div>

            {/* Slider container with drag and scroll */}
            <div
              ref={scrollContainerRef}
              onScroll={handleScroll}
              onMouseDown={onMouseDown}
              onMouseMove={onMouseMove}
              onMouseUp={onMouseUpOrLeave}
              onMouseLeave={onMouseUpOrLeave}
              className={`flex gap-3 sm:gap-5 overflow-x-auto hide-scrollbar pb-3 pt-1 select-none ${
                isDragging ? "cursor-grabbing" : "cursor-grab"
              }`}
            >
              {credits.map((person) => (
                <button
                  type="button"
                  key={`person-${person.id}-${person.role}`}
                  onClick={() => handlePersonClick(person)}
                  className="flex flex-col items-center shrink-0 w-20 sm:w-24 group pointer-events-auto cursor-pointer focus:outline-none transition-transform hover:scale-105 active:scale-95"
                  title={`${person.name} — Filmografiyasini ko'rish`}
                >
                  {/* Circular Avatar Container */}
                  <div className="w-16 h-16 sm:w-20 sm:h-20 rounded-full overflow-hidden bg-[#242424] border border-white/10 flex items-center justify-center shrink-0 relative shadow-md group-hover:border-primary/60 transition-all duration-300">
                    {person.photo_url ? (
                      <Image
                        src={person.photo_url}
                        alt={person.name}
                        fill
                        sizes="(max-width: 640px) 64px, 80px"
                        className="object-cover group-hover:scale-105 transition-transform duration-300 pointer-events-none"
                      />
                    ) : (
                      <span className="material-symbols-outlined text-white/40 text-3xl sm:text-4xl select-none">
                        person
                      </span>
                    )}
                  </div>

                  {/* Person Name */}
                  <span className="text-[11px] sm:text-xs font-semibold text-white/95 text-center line-clamp-2 mt-2 leading-tight max-w-[80px] sm:max-w-[92px] group-hover:text-primary transition-colors">
                    {person.name}
                  </span>

                  {/* Person Role */}
                  <span className="text-[10px] sm:text-[11px] text-white/50 text-center truncate max-w-[80px] sm:max-w-[92px] mt-0.5">
                    {person.role}
                  </span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* 2. TMDb Qo'shimcha Ma'lumotlari */}
        {details && (
          <>
            <div className="border-t border-white/5" />
            <div>
              <h3 className="text-sm sm:text-base font-bold text-white/90 mb-3.5 flex items-center gap-2">
                <span className="material-symbols-outlined text-rating-gold text-lg">info</span>
                {mediaType === "series" ? "Serial haqida ma'lumot" : "Film haqida ma'lumot"}
              </h3>

              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2.5 sm:gap-3.5">
                {/* Asl nomi */}
                {details.original_title && (
                  <div className="bg-white/[0.02] border border-white/5 rounded-xl p-3">
                    <span className="text-[11px] text-text-secondary block mb-0.5">Asl nomi</span>
                    <span className="text-xs sm:text-sm font-semibold text-white truncate block">
                      {details.original_title}
                    </span>
                  </div>
                )}

                {/* Mamlakat */}
                {details.countries && details.countries.length > 0 && (
                  <div className="bg-white/[0.02] border border-white/5 rounded-xl p-3">
                    <span className="text-[11px] text-text-secondary block mb-0.5">Mamlakat</span>
                    <span className="text-xs sm:text-sm font-semibold text-white truncate block">
                      {details.countries.join(", ")}
                    </span>
                  </div>
                )}

                {/* Studiya */}
                {details.companies && details.companies.length > 0 && (
                  <div className="bg-white/[0.02] border border-white/5 rounded-xl p-3">
                    <span className="text-[11px] text-text-secondary block mb-0.5">Studiya</span>
                    <span className="text-xs sm:text-sm font-semibold text-white truncate block">
                      {details.companies.join(", ")}
                    </span>
                  </div>
                )}

                {/* Premyera sanasi */}
                {details.release_date && (
                  <div className="bg-white/[0.02] border border-white/5 rounded-xl p-3">
                    <span className="text-[11px] text-text-secondary block mb-0.5">Premyera</span>
                    <span className="text-xs sm:text-sm font-semibold text-white truncate block">
                      {details.release_date}
                    </span>
                  </div>
                )}

                {/* Davomiyligi */}
                {details.runtime && (
                  <div className="bg-white/[0.02] border border-white/5 rounded-xl p-3">
                    <span className="text-[11px] text-text-secondary block mb-0.5">Davomiyligi</span>
                    <span className="text-xs sm:text-sm font-semibold text-white truncate block">
                      {details.runtime}
                    </span>
                  </div>
                )}

                {/* Holati */}
                {details.status && (
                  <div className="bg-white/[0.02] border border-white/5 rounded-xl p-3">
                    <span className="text-[11px] text-text-secondary block mb-0.5">Holati</span>
                    <span className="text-xs sm:text-sm font-semibold text-white truncate block">
                      {details.status}
                    </span>
                  </div>
                )}

                {/* Byudjet */}
                {details.budget && (
                  <div className="bg-white/[0.02] border border-white/5 rounded-xl p-3">
                    <span className="text-[11px] text-text-secondary block mb-0.5">Byudjet</span>
                    <span className="text-xs sm:text-sm font-semibold text-white truncate block">
                      {details.budget}
                    </span>
                  </div>
                )}

                {/* Daromad */}
                {details.revenue && (
                  <div className="bg-white/[0.02] border border-white/5 rounded-xl p-3">
                    <span className="text-[11px] text-text-secondary block mb-0.5">Daromad</span>
                    <span className="text-xs sm:text-sm font-semibold text-white truncate block">
                      {details.revenue}
                    </span>
                  </div>
                )}
              </div>
            </div>
          </>
        )}
      </div>

      {/* Filmography Modal (1-click from Cast & Crew) */}
      <ActorFilmographyModal
        actor={selectedActor}
        onClose={() => setSelectedActor(null)}
      />
    </section>
  );
}
