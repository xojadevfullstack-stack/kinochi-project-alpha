"use client";

import { useState, useRef, useCallback } from "react";
import Link from "next/link";
import Image from "next/image";
import BackButton from "@/components/BackButton";
import ExternalSearchSection from "@/components/ExternalSearchSection";
import { fetchApi } from "@/lib/api";

const POPULAR_SEARCH_TAGS = [
  "Jangari",
  "Komediya",
  "Fantastika",
  "Anime",
  "Dorama",
  "Multfilm",
  "Qo'rqinchli",
  "Melodrama",
  "Kriminal",
  "Tarixiy",
];

interface SearchClientViewProps {
  initialQuery?: string;
  initialType?: string;
  initialResults: any[];
  initialExternalResults: any[];
  defaultItems: any[];
  initialError?: string | null;
}

export default function SearchClientView({
  initialQuery = "",
  initialType,
  initialResults,
  initialExternalResults,
  defaultItems,
  initialError = null,
}: SearchClientViewProps) {
  const [query, setQuery] = useState(initialQuery);
  const [results, setResults] = useState<any[]>(initialResults);
  const [externalResults, setExternalResults] = useState<any[]>(initialExternalResults);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(initialError);

  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const performLiveSearch = useCallback(
    async (searchQuery: string) => {
      const cleanQ = searchQuery.trim();
      if (cleanQ.length < 2) {
        setResults([]);
        setExternalResults([]);
        setIsLoading(false);
        setErrorMsg(null);
        if (typeof window !== "undefined") {
          window.history.replaceState(null, "", "/search");
        }
        return;
      }

      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      abortControllerRef.current = new AbortController();

      setIsLoading(true);
      setErrorMsg(null);

      // Update URL without page reload
      if (typeof window !== "undefined") {
        window.history.replaceState(
          null,
          "",
          `/search?q=${encodeURIComponent(cleanQ)}${initialType ? `&type=${initialType}` : ""}`
        );
      }

      try {
        // Query local movies, local series, AND external TMDB simultaneously
        const [moviesRes, seriesRes, extRes] = await Promise.all([
          initialType === "series"
            ? Promise.resolve({ items: [] })
            : fetchApi(
                initialType === "movie"
                  ? `/movies/search?q=${encodeURIComponent(cleanQ)}&limit=40`
                  : `/movies/search?q=${encodeURIComponent(cleanQ)}&limit=24`
              ).catch(() => ({ items: [] })),
          initialType === "movie"
            ? Promise.resolve({ items: [] })
            : fetchApi(
                initialType === "series"
                  ? `/series/search?q=${encodeURIComponent(cleanQ)}&limit=40`
                  : `/series/search?q=${encodeURIComponent(cleanQ)}&limit=24`
              ).catch(() => ({ items: [] })),
          fetchApi(
            `/content-requests/external-search?q=${encodeURIComponent(cleanQ)}&limit=12`
          ).catch(() => ({ results: [] })),
        ]);

        const movies = (moviesRes?.items || []).map((i: any) => ({ ...i, isSeries: false }));
        const series = (seriesRes?.items || []).map((i: any) => ({ ...i, isSeries: true }));
        const combined = [...movies, ...series];
        setResults(combined);

        // Filter out TMDB results that are already in our local library
        const localTmdbIds = new Set(combined.map((m: any) => m.tmdb_id).filter(Boolean));
        const localTitles = new Set(combined.map((m: any) => m.title.toLowerCase().trim()));

        const filteredExt = (extRes?.results || []).filter((ext: any) => {
          if (ext.in_library) return false;
          if (ext.tmdb_id && localTmdbIds.has(ext.tmdb_id)) return false;
          if (localTitles.has(ext.title.toLowerCase().trim())) return false;
          return true;
        });

        setExternalResults(filteredExt);
      } catch (err: any) {
        if (err.name !== "AbortError") {
          setErrorMsg(err.message || "Qidiruvda xatolik yuz berdi");
        }
      } finally {
        setIsLoading(false);
      }
    },
    [initialType]
  );

  // Handle typing debounce
  const handleInputChange = (val: string) => {
    setQuery(val);
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }
    debounceTimerRef.current = setTimeout(() => {
      performLiveSearch(val);
    }, 280);
  };

  const handleClear = () => {
    setQuery("");
    setResults([]);
    setExternalResults([]);
    setIsLoading(false);
    setErrorMsg(null);
    if (typeof window !== "undefined") {
      window.history.replaceState(null, "", "/search");
    }
  };

  const handleTagClick = (tag: string) => {
    setQuery(tag);
    performLiveSearch(tag);
  };

  const isSearchActive = query.trim().length >= 2;
  const totalFound = results.length + externalResults.length;

  const renderCard = (item: any, idx: number) => {
    const isSeries = item.isSeries !== undefined ? item.isSeries : initialType === "series";
    const linkUrl = isSeries ? `/series/${item.id}` : `/movie/${item.code}`;
    const key = `${isSeries ? "s" : "m"}-${isSeries ? item.id : item.code}-${idx}`;
    const rating = item.imdb_rating || item.tmdb_rating || "N/A";

    return (
      <Link
        href={linkUrl}
        key={key}
        className="group relative aspect-[2/3] rounded-xl overflow-hidden cursor-pointer bg-surface-container hover:scale-105 transition-transform duration-300 shadow-lg ring-1 ring-white/10 hover:ring-white/25"
      >
        {item.poster_url ? (
          <Image
            src={item.poster_url}
            alt={item.title}
            fill
            sizes="(max-width: 640px) 50vw, (max-width: 1024px) 33vw, 16vw"
            className="object-cover"
          />
        ) : (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-surface-container-high text-gray-500 border border-white/5">
            <span className="material-symbols-outlined text-4xl mb-2 opacity-30">
              {isSeries ? "tv" : "movie"}
            </span>
          </div>
        )}

        <div className="absolute inset-0 bg-gradient-to-t from-background-obsidian via-background-obsidian/50 to-transparent opacity-80 group-hover:opacity-100 transition-opacity"></div>

        <div className="absolute top-2 right-2 px-2 py-1 bg-black/60 backdrop-blur-sm rounded text-rating-gold flex items-center gap-1 border border-white/10 font-bold text-xs">
          <span
            className="material-symbols-outlined text-[14px]"
            style={{ fontVariationSettings: "'FILL' 1" }}
          >
            star
          </span>
          <span>{rating}</span>
        </div>

        <div className="absolute bottom-0 left-0 w-full p-3 sm:p-4 transform translate-y-1 group-hover:translate-y-0 transition-transform">
          <div className="flex gap-1 mb-1 flex-wrap">
            <span className="px-1.5 py-0.5 bg-white/10 backdrop-blur-sm rounded text-[10px] font-bold text-text-secondary uppercase tracking-wider">
              {isSeries ? item.categories?.[0]?.name || "Serial" : item.genres?.split(",")[0] || "Kino"}
            </span>
            {item.release_year && (
              <span className="px-1.5 py-0.5 bg-white/10 backdrop-blur-sm rounded text-[10px] font-bold text-text-secondary uppercase tracking-wider">
                {item.release_year}
              </span>
            )}
          </div>
          <h3 className="font-body-lg text-sm sm:text-base text-text-primary font-bold line-clamp-2 drop-shadow-md">
            {item.title}
          </h3>
        </div>
      </Link>
    );
  };

  return (
    <div className="min-h-screen pt-20 sm:pt-24 md:pt-28 pb-margin-desktop px-gutter bg-background-obsidian">
      <div className="max-w-container-max mx-auto">
        {/* Smart Back Navigation */}
        <div className="mb-4 sm:mb-6">
          <BackButton fallbackUrl="/" />
        </div>

        {/* Header */}
        <div className="mb-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl md:text-4xl font-display-hero font-bold text-white mb-2">
              {isSearchActive
                ? initialType === "series"
                  ? "Seriallar bo'yicha qidiruv natijalari"
                  : initialType === "movie"
                  ? "Kinolar bo'yicha qidiruv natijalari"
                  : "Qidiruv natijalari"
                : "Qidiruv va Kashf etish"}
            </h1>
            <p className="text-text-secondary text-sm sm:text-base">
              {isLoading
                ? "Baza va xalqaro katalogdan qidirilmoqda..."
                : isSearchActive
                ? `"${query}" so'rovi bo'yicha ${totalFound} ta natija topildi (Bazamizda: ${results.length}, TMDB: ${externalResults.length})`
                : "Sevimli kinolaringiz, seriallaringiz yoki janrlarni oson toping"}
            </p>
          </div>

          <Link
            href="/requests"
            className="self-start sm:self-auto px-4 py-2.5 rounded-2xl bg-primary/15 hover:bg-primary text-primary hover:text-white border border-primary/30 text-xs sm:text-sm font-bold transition-all flex items-center gap-2 shadow-lg"
          >
            <span className="material-symbols-outlined text-[18px]">add_to_queue</span>
            <span>Kino so&apos;rash / Buyurtma</span>
          </Link>
        </div>

        {/* Live Debounced Search Input */}
        <div className="mb-6 max-w-2xl">
          <div className="flex items-center bg-white/5 hover:bg-white/10 rounded-full px-5 py-3 border border-white/10 focus-within:border-primary/60 focus-within:bg-white/10 transition-all shadow-inner relative">
            {isLoading ? (
              <span className="material-symbols-outlined text-primary mr-3 text-[22px] animate-spin">
                sync
              </span>
            ) : (
              <span className="material-symbols-outlined text-text-secondary mr-3 text-[22px]">
                search
              </span>
            )}
            <input
              type="text"
              value={query}
              onChange={(e) => handleInputChange(e.target.value)}
              className="bg-transparent border-none focus:ring-0 text-text-primary text-base w-full outline-none placeholder:text-text-secondary"
              placeholder="Kinolar va seriallarni qidirish (yozish bilan darhol chiqadi)..."
              autoFocus
            />
            {query && (
              <button
                type="button"
                onClick={handleClear}
                className="text-text-secondary hover:text-white p-1 rounded-full hover:bg-white/10 transition-colors ml-2"
                title="Qidiruvni tozalash"
              >
                <span className="material-symbols-outlined text-[18px]">close</span>
              </button>
            )}
          </div>
        </div>

        {/* Popular Category Chips */}
        <div className="mb-8">
          <div className="flex items-center gap-1.5 mb-2.5 text-xs text-text-secondary font-medium">
            <span className="material-symbols-outlined text-[16px] text-amber-400">
              local_fire_department
            </span>
            <span>Ommabop qidiruvlar:</span>
          </div>
          <div className="flex items-center gap-2 overflow-x-auto pb-2 hide-scrollbar">
            {POPULAR_SEARCH_TAGS.map((tag) => {
              const isSelected = query.toLowerCase() === tag.toLowerCase();
              return (
                <button
                  key={tag}
                  type="button"
                  onClick={() => handleTagClick(tag)}
                  className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all shrink-0 active:scale-95 border ${
                    isSelected
                      ? "bg-white/20 text-white border-white/30 font-bold shadow-md"
                      : "bg-white/5 hover:bg-white/10 text-text-secondary hover:text-white border-white/10 hover:border-white/20"
                  }`}
                >
                  {tag}
                </button>
              );
            })}
          </div>
        </div>

        {/* Search Results State */}
        {errorMsg ? (
          <div className="text-red-400 p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-base mb-8">
            Xatolik yuz berdi: {errorMsg}
          </div>
        ) : isSearchActive ? (
          <div>
            {/* Section 1: Internal Results (Bazamizdagi kinolar) */}
            {results.length > 0 && (
              <div className="mb-10">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg sm:text-xl font-bold text-white flex items-center gap-2">
                    <span className="w-1.5 h-4.5 bg-emerald-500 rounded-full"></span>
                    <span>Bazamizda mavjud natijalar ({results.length})</span>
                  </h2>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3 sm:gap-4 md:gap-6 mb-8">
                  {results.map((item, idx) => renderCard(item, idx))}
                </div>
              </div>
            )}

            {/* Section 2: External TMDB/Kinopoisk Results (Bazada yo'q bo'lgan variantlar) */}
            {externalResults.length > 0 && (
              <div className="mb-12">
                <ExternalSearchSection
                  query={query}
                  items={externalResults}
                  title={
                    results.length > 0
                      ? `"${query}" bo'yicha boshqa variantlar (TMDB • Bazada yo'q)`
                      : `"${query}" bo'yicha xalqaro qidiruv natijalari (TMDB)`
                  }
                  subtitle={
                    results.length > 0
                      ? "Ushbu filmlar hali platformamizga yuklanmagan. Biror variantini ko'rmoqchi bo'lsangiz, 'Qo'shishni so'rash' tugmasini bosing — adminlarimiz uni yuklaydi!"
                      : `"${query}" filmi bizning bazada hali mavjud emas, lekin TMDB / Kinopoisk jahon katalogidan topildi. Quyidagilardan tanlab 'Qo'shishni so'rash' tugmasini bosing:`
                  }
                />
              </div>
            )}

            {/* If neither local nor external results found */}
            {results.length === 0 && externalResults.length === 0 && !isLoading && (
              <div className="text-center py-16 px-6 bg-white/[0.03] rounded-3xl border border-white/10 max-w-xl mx-auto mb-12">
                <span className="material-symbols-outlined text-6xl text-text-secondary mb-3 opacity-60">
                  search_off
                </span>
                <h3 className="text-xl font-bold text-white mb-2">Hech narsa topilmadi</h3>
                <p className="text-sm text-text-secondary leading-relaxed mb-6">
                  &ldquo;{query}&rdquo; so&apos;rovi bo&apos;yicha film topilmadi. Uni adminlarimizga buyurtma qilishingiz mumkin!
                </p>
                <Link
                  href="/requests"
                  className="inline-flex items-center gap-2 px-6 py-3 bg-primary text-white font-bold rounded-2xl hover:bg-inverse-primary active:scale-95 transition-all text-sm shadow-lg"
                >
                  <span className="material-symbols-outlined text-[20px]">add_to_queue</span>
                  <span>Kino qo&apos;shishni so&apos;rash</span>
                </Link>
              </div>
            )}

            {/* Suggestions below empty state */}
            {results.length === 0 && externalResults.length === 0 && defaultItems.length > 0 && !isLoading && (
              <div>
                <div className="mb-5 flex items-center justify-between">
                  <h2 className="font-headline-md text-xl sm:text-2xl font-bold text-text-primary flex items-center gap-2.5">
                    <span className="w-1 h-5 bg-primary rounded-full block"></span>
                    <span>Sizga yoqishi mumkin bo&apos;lgan premyeralar</span>
                  </h2>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3 sm:gap-4 md:gap-6">
                  {defaultItems.slice(0, 12).map((item, idx) => renderCard(item, idx))}
                </div>
              </div>
            )}
          </div>
        ) : (
          /* Default state when user just opened /search */
          <div>
            <div className="mb-5 flex items-center justify-between">
              <div>
                <h2 className="font-headline-md text-xl sm:text-2xl font-bold text-text-primary flex items-center gap-2.5">
                  <span className="w-1 h-5 sm:h-6 bg-primary rounded-full block"></span>
                  <span>Tavsiya etilayotgan premyeralar</span>
                </h2>
                <p className="text-xs sm:text-sm text-text-secondary mt-1">
                  Eng so&apos;nggi va sara kino hamda seriallar to&apos;plami
                </p>
              </div>
            </div>

            {defaultItems.length > 0 ? (
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3 sm:gap-4 md:gap-6">
                {defaultItems.map((item, idx) => renderCard(item, idx))}
              </div>
            ) : (
              <div className="text-center py-20 text-text-secondary">
                <span className="material-symbols-outlined text-5xl mb-2 opacity-30">movie</span>
                <p>Kinolar yuklanmoqda...</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
