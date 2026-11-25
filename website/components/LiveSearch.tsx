"use client";

import React, { useState, useEffect, useRef } from "react";
import Image from "next/image";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import RequestMovieModal, { RequestTargetItem } from "./RequestMovieModal";
import { API_URL, readClientAdultPreference } from "@/lib/api";
import { suppressOverlayHistoryBack } from "@/lib/hooks/useOverlayBackClose";
import {
  buildSearchTrackPayload,
  getDisplaySearchCode,
  getSearchResultHref,
} from "@/lib/searchHelpers.mjs";

interface SearchResultItem {
  id: number;
  title: string;
  original_title?: string | null;
  code: string;
  short_code?: string | null;
  year?: number | null;
  poster_url?: string | null;
  imdb_rating?: number | null;
  type: "movie" | "series" | "collection";
  extra?: string | null;
  search_count?: number;
  view_count?: number;
}

interface ExternalResultItem {
  tmdb_id?: number | null;
  kinopoisk_id?: number | null;
  title: string;
  original_title?: string | null;
  media_type: "movie" | "series";
  release_year?: number | null;
  poster_url?: string | null;
  overview?: string | null;
  vote_average?: number | null;
  in_library: boolean;
  library_code?: string | null;
  library_id?: number | null;
  request_count: number;
  is_requested: boolean;
}

interface LiveSearchProps {
  placeholder?: string;
  className?: string;
  inputClassName?: string;
  onNavigate?: () => void;
  isMobileDrawer?: boolean;
  isMobileBar?: boolean;
  autoFocus?: boolean;
  onClose?: () => void;
}

function SearchPoster({ item }: { item: SearchResultItem }) {
  const [hasError, setHasError] = useState(false);

  if (!item.poster_url || hasError) {
    return (
      <div className="w-full h-full flex items-center justify-center text-white/30 text-xs bg-white/5">
        <span className="material-symbols-outlined text-lg">
          {item.type === "movie"
            ? "movie"
            : item.type === "series"
            ? "live_tv"
            : "auto_awesome_motion"}
        </span>
      </div>
    );
  }

  return (
    <Image
      src={item.poster_url}
      alt={item.title}
      fill
      sizes="40px"
      className="object-cover"
      unoptimized={item.poster_url.includes("uzmovi") || item.poster_url.includes("asilmedia")}
      onError={() => setHasError(true)}
    />
  );
}

function ExternalPoster({ item }: { item: ExternalResultItem }) {
  const [hasError, setHasError] = useState(false);

  if (!item.poster_url || hasError) {
    return (
      <div className="w-full h-full flex items-center justify-center text-white/30 text-xs bg-white/5">
        <span className="material-symbols-outlined text-lg">
          {item.media_type === "series" ? "live_tv" : "movie"}
        </span>
      </div>
    );
  }

  return (
    <Image
      src={item.poster_url}
      alt={item.title}
      fill
      sizes="40px"
      className="object-cover"
      onError={() => setHasError(true)}
    />
  );
}

const getExtKey = (it: { tmdb_id?: number | null; kinopoisk_id?: number | null; title: string }) => {
  if (it.tmdb_id) return `tmdb:${it.tmdb_id}`;
  if (it.kinopoisk_id) return `kp:${it.kinopoisk_id}`;
  return `title:${it.title.toLowerCase().trim()}`;
};

export default function LiveSearch({
  placeholder = "Kino, serial yoki #kod qidirish...",
  className = "",
  inputClassName = "",
  onNavigate,
  isMobileDrawer = false,
  isMobileBar = false,
  autoFocus = false,
  onClose,
}: LiveSearchProps) {
  const router = useRouter();
  const pathname = usePathname();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResultItem[]>([]);
  const [externalResults, setExternalResults] = useState<ExternalResultItem[]>([]);
  const [popularResults, setPopularResults] = useState<SearchResultItem[]>([]);
  const [loadingPopular, setLoadingPopular] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState<number>(-1);
  const [isKeyboardNavigating, setIsKeyboardNavigating] = useState(false);

  const [selectedRequestItem, setSelectedRequestItem] = useState<RequestTargetItem | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [requestedKeys, setRequestedKeys] = useState<Set<string>>(new Set());

  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const suppressPopupRef = useRef(false);
  const popularCacheMetaRef = useRef<{ loaded: boolean; includeAdult: boolean }>({
    loaded: false,
    includeAdult: false,
  });

  const loadPopularSearches = async () => {
    const includeAdult = readClientAdultPreference();
    if (
      popularCacheMetaRef.current.loaded &&
      popularCacheMetaRef.current.includeAdult === includeAdult
    ) {
      return;
    }
    setLoadingPopular(true);
    try {
      const res = await fetch(
        `${API_URL}/search/popular?limit=8&include_adult=${includeAdult ? "true" : "false"}`
      );
      if (res.ok) {
        const data = await res.json();
        setPopularResults(data?.results || []);
        popularCacheMetaRef.current = { loaded: true, includeAdult };
      }
    } catch {
      // Keep previous list if offline
    } finally {
      setLoadingPopular(false);
    }
  };

  // Close quick-search popup immediately whenever route changes (e.g. navigating to /search)
  useEffect(() => {
    suppressPopupRef.current = true;
    setIsOpen(false);
    setIsKeyboardNavigating(false);
  }, [pathname]);

  // Auto focus input when autoFocus prop is enabled (e.g. Mobile search overlay opens)
  useEffect(() => {
    if (autoFocus && inputRef.current) {
      suppressPopupRef.current = false;
      inputRef.current.focus();
      if (!query.trim()) {
        loadPopularSearches();
        setIsOpen(true);
      }
    }
  }, [autoFocus]);



  // Load requested keys from localStorage
  useEffect(() => {
    try {
      const saved = localStorage.getItem("kinochi_requested_content_keys");
      if (saved) {
        setRequestedKeys(new Set(JSON.parse(saved)));
      }
    } catch {}
  }, []);

  // Debounced live fetch
  useEffect(() => {
    const clean = query.trim();
    if (clean.length < 1) {
      setResults([]);
      setExternalResults([]);
      setIsLoading(false);
      if (
        !suppressPopupRef.current &&
        typeof document !== "undefined" &&
        document.activeElement === inputRef.current
      ) {
        loadPopularSearches();
        setIsOpen(true);
      } else if (!autoFocus) {
        setIsOpen(false);
      }
      return;
    }

    setIsLoading(true);
    const handler = setTimeout(async () => {
      try {
        // 1. Fetch live local results
        const includeAdult = readClientAdultPreference();
        const res = await fetch(
          `${API_URL}/search/live?q=${encodeURIComponent(clean)}&limit=5&include_adult=${includeAdult ? "true" : "false"}`
        );
        let localItems: SearchResultItem[] = [];
        if (res.ok) {
          const data = await res.json();
          localItems = data.results || [];
          setResults(localItems);
        } else {
          setResults([]);
        }

        // 2. Fetch TMDB results whenever query length >= 2
        if (clean.length >= 2) {
          try {
            const extRes = await fetch(
              `${API_URL}/content-requests/external-search?q=${encodeURIComponent(clean)}&limit=5`
            );
            if (extRes.ok) {
              const extData = await extRes.json();
              const localTitles = new Set(localItems.map((l) => l.title.toLowerCase().trim()));
              const filteredExt = (extData.results || []).filter(
                (ext: any) => !ext.in_library && !localTitles.has(ext.title.toLowerCase().trim())
              );
              setExternalResults(filteredExt);
            } else {
              setExternalResults([]);
            }
          } catch {
            setExternalResults([]);
          }
        } else {
          setExternalResults([]);
        }

        if (!suppressPopupRef.current) {
          setIsOpen(true);
        }
      } catch {
        setResults([]);
        setExternalResults([]);
      } finally {
        setIsLoading(false);
      }
    }, 220);

    return () => clearTimeout(handler);
  }, [query]);

  // Click outside listener
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSelect = (item: SearchResultItem) => {
    const trackPayload = buildSearchTrackPayload(item);
    if (trackPayload) {
      fetch(`${API_URL}/search/track-click`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(trackPayload),
        keepalive: true,
      }).catch(() => {});
    }

    suppressOverlayHistoryBack();
    suppressPopupRef.current = true;
    inputRef.current?.blur();
    setIsOpen(false);
    setQuery("");
    onNavigate?.();
    onClose?.();

    router.push(getSearchResultHref(item));
  };

  const handleOpenRequest = (item: ExternalResultItem) => {
    setSelectedRequestItem({
      tmdb_id: item.tmdb_id,
      kinopoisk_id: item.kinopoisk_id,
      title: item.title,
      original_title: item.original_title,
      media_type: item.media_type,
      release_year: item.release_year,
      poster_url: item.poster_url,
      overview: item.overview,
      vote_average: item.vote_average,
    });
    setIsModalOpen(true);
  };

  const handleRequestSuccess = () => {
    if (selectedRequestItem) {
      const key = getExtKey(selectedRequestItem);
      setRequestedKeys((prev) => {
        const next = new Set(prev).add(key);
        try {
          localStorage.setItem("kinochi_requested_content_keys", JSON.stringify(Array.from(next)));
        } catch {}
        return next;
      });
      setExternalResults((prev) =>
        prev.map((it) => {
          if (getExtKey(it) === key) {
            return {
              ...it,
              request_count: Math.max(1, (it.request_count || 0) + 1),
              is_requested: true,
            };
          }
          return it;
        })
      );
    }
  };

  // Navigates strictly to full search page /search?q=...
  const handleFullSearch = (e?: React.MouseEvent | React.FormEvent) => {
    if (e) e.preventDefault();
    const cleanQ = query.trim();
    suppressOverlayHistoryBack();
    suppressPopupRef.current = true;
    setIsOpen(false);
    setIsKeyboardNavigating(false);
    inputRef.current?.blur();
    if (cleanQ) {
      setIsOpen(false);
      onNavigate?.();
      onClose?.();
      router.push(`/search?q=${encodeURIComponent(cleanQ)}`);
    }
  };

  const activeNavList = query.trim().length > 0 ? results : popularResults;

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    // Only select single item if user actively used keyboard arrow keys
    if (isKeyboardNavigating && selectedIndex >= 0 && selectedIndex < activeNavList.length) {
      handleSelect(activeNavList[selectedIndex]);
      return;
    }
    handleFullSearch(e);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isOpen) return;

    if (activeNavList.length > 0) {
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setIsKeyboardNavigating(true);
        setSelectedIndex((prev) => (prev < activeNavList.length - 1 ? prev + 1 : 0));
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        setIsKeyboardNavigating(true);
        setSelectedIndex((prev) => (prev > 0 ? prev - 1 : activeNavList.length - 1));
      }
    }
    if (e.key === "Escape") {
      setIsOpen(false);
      setIsKeyboardNavigating(false);
      onClose?.();
    }
  };

  const hasQuery = query.trim().length > 0;
  const hasAnyResults = results.length > 0 || externalResults.length > 0;
  const showPopularSection = !hasQuery && (popularResults.length > 0 || loadingPopular);

  return (
    <div ref={containerRef} className={`relative ${className}`}>
      <form onSubmit={handleSubmit} className="w-full relative">
        <div className="flex items-center w-full bg-slate-200/75 dark:bg-white/5 hover:bg-slate-200 dark:hover:bg-white/10 rounded-full px-3.5 py-1.5 xl:px-4 xl:py-2 border border-slate-300/80 dark:border-white/10 focus-within:border-[#E50914] dark:focus-within:border-primary-container focus-within:bg-white/95 dark:focus-within:bg-white/10 transition-all">
          <span
            className="material-symbols-outlined text-slate-500 dark:text-text-secondary mr-2 text-[18px] xl:text-[20px] shrink-0"
            style={{ fontVariationSettings: "'FILL' 0" }}
          >
            search
          </span>
          <input
            ref={inputRef}
            type="text"
            value={query}
            onMouseDown={() => {
              suppressPopupRef.current = false;
            }}
            onChange={(e) => {
              suppressPopupRef.current = false;
              setQuery(e.target.value);
              setSelectedIndex(-1);
              setIsKeyboardNavigating(false);
            }}
            onFocus={() => {
              if (suppressPopupRef.current) return;
              if (query.trim().length === 0) {
                loadPopularSearches();
                setIsOpen(true);
              } else if (hasAnyResults) {
                setIsOpen(true);
              }
            }}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            className={`search-pill-input bg-transparent border-none focus:ring-0 text-slate-900 dark:text-text-primary text-sm placeholder:text-slate-500 dark:placeholder:text-text-secondary outline-none w-full ${inputClassName}`}
          />
          {isLoading ? (
            <div className="w-4 h-4 border-2 border-primary-container border-t-transparent rounded-full animate-spin shrink-0 ml-1"></div>
          ) : query ? (
            <button
              type="button"
              onClick={() => {
                suppressPopupRef.current = false;
                setQuery("");
                setResults([]);
                setExternalResults([]);
                setSelectedIndex(-1);
                setIsKeyboardNavigating(false);
                loadPopularSearches();
                setIsOpen(true);
                inputRef.current?.focus();
              }}
              className="text-text-secondary hover:text-white transition-colors p-0.5"
            >
              <span className="material-symbols-outlined text-[16px]">close</span>
            </button>
          ) : null}
        </div>
      </form>

      {/* Live Dropdown Results Popover */}
      {isOpen && (hasQuery || showPopularSection) && (
        <div
          className={`bg-white/95 dark:bg-[#121318]/95 backdrop-blur-2xl border border-slate-200 dark:border-white/15 rounded-2xl shadow-2xl shadow-slate-900/15 dark:shadow-black/80 overflow-hidden transition-all flex flex-col ${
            isMobileBar
              ? "fixed left-2 right-2 top-[64px] max-h-[calc(100dvh-152px)] z-[70]"
              : isMobileDrawer
              ? "absolute left-0 right-0 mt-2 max-h-[60vh] w-full z-50"
              : "absolute left-0 right-0 mt-2 min-w-[340px] sm:min-w-[480px] max-h-[520px] z-50"
          }`}
        >
          {!hasQuery ? (
            <div className="overflow-y-auto p-1.5">
              <div className="px-3 py-1.5 text-[11px] font-bold uppercase tracking-wider text-slate-600 dark:text-text-secondary flex items-center justify-between">
                <span className="flex items-center gap-1.5">
                  <span className="material-symbols-outlined text-[15px] text-[#E50914]">
                    local_fire_department
                  </span>
                  <span>Eng ko&apos;p qidirilganlar</span>
                </span>
                {popularResults.length > 0 && (
                  <span className="text-[10px] text-[#D20A13] dark:text-[#E50914] font-bold">
                    TOP {popularResults.length}
                  </span>
                )}
              </div>

              {loadingPopular && popularResults.length === 0 ? (
                <div className="space-y-1.5 p-1.5">
                  {[...Array(4)].map((_, i) => (
                    <div key={i} className="h-14 rounded-xl bg-slate-200/70 dark:bg-white/5 animate-pulse" />
                  ))}
                </div>
              ) : (
                popularResults.map((item, idx) => {
                  const isSelected = isKeyboardNavigating && idx === selectedIndex;
                  const displayCode = getDisplaySearchCode(item);
                  return (
                    <button
                      key={`pop-${item.type}-${item.id}`}
                      type="button"
                      onClick={() => handleSelect(item)}
                      onMouseEnter={() => {
                        setIsKeyboardNavigating(false);
                        setSelectedIndex(idx);
                      }}
                      className={`w-full text-left flex items-center gap-3 p-2 rounded-xl transition-all cursor-pointer ${
                        isSelected
                          ? "bg-red-50 dark:bg-white/15 text-slate-900 dark:text-white"
                          : "hover:bg-slate-100 dark:hover:bg-white/10 text-slate-900 dark:text-text-primary"
                      }`}
                    >
                      <span
                        className={`w-5 text-center font-black text-xs shrink-0 ${
                          idx < 3 ? "text-[#D20A13] dark:text-[#E50914]" : "text-slate-400 dark:text-white/40"
                        }`}
                      >
                        {idx + 1}
                      </span>

                      <div className="w-10 h-14 rounded-lg bg-slate-200 dark:bg-surface-container-high overflow-hidden shrink-0 relative border border-slate-200 dark:border-white/10">
                        <SearchPoster item={item} />
                      </div>

                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-1.5 mb-0.5">
                          <span className="font-bold text-sm text-slate-900 dark:text-text-primary truncate">
                            {item.title}
                          </span>
                          {item.year && (
                            <span className="text-[11px] text-slate-500 dark:text-text-secondary shrink-0">
                              ({item.year})
                            </span>
                          )}
                        </div>

                        <div className="flex items-center gap-2 text-xs text-slate-600 dark:text-text-secondary">
                          <span
                            className={`px-1.5 py-0.5 rounded font-bold text-[10px] uppercase ${
                              item.type === "series"
                                ? "bg-sky-500/10 dark:bg-sky-500/20 text-sky-700 dark:text-sky-400"
                                : "bg-red-500/10 dark:bg-red-500/20 text-[#D20A13] dark:text-red-400"
                            }`}
                          >
                            {item.type === "series" ? "Serial" : "Kino"}
                          </span>

                          {item.imdb_rating && (
                            <span className="flex items-center gap-0.5 text-rating-gold font-bold text-[11px]">
                              <span
                                className="material-symbols-outlined text-[13px]"
                                style={{ fontVariationSettings: "'FILL' 1" }}
                              >
                                star
                              </span>
                              {Number(item.imdb_rating).toFixed(1)}
                            </span>
                          )}

                          {displayCode && (
                            <span className="font-mono text-[11px] text-slate-500 dark:text-white/50">
                              #{displayCode}
                            </span>
                          )}
                        </div>
                      </div>
                    </button>
                  );
                })
              )}
            </div>
          ) : hasAnyResults ? (
            <div className="overflow-y-auto divide-y divide-slate-200/70 dark:divide-white/5 p-1.5">
              {/* Section 1: Local Internal Results */}
              {results.length > 0 && (
                <div className="mb-2">
                  <div className="px-3 py-1.5 text-[11px] font-bold uppercase tracking-wider text-slate-500 dark:text-text-secondary flex items-center justify-between">
                    <span>Bazamizdagi natijalar</span>
                    <span className="text-[10px] text-emerald-600 dark:text-emerald-400 font-semibold">{results.length} ta mavjud</span>
                  </div>
                  {results.map((item, idx) => {
                    const isSelected = isKeyboardNavigating && idx === selectedIndex;
                    return (
                      <button
                        key={`${item.type}-${item.id}`}
                        type="button"
                        onClick={() => handleSelect(item)}
                        onMouseEnter={() => {
                          setIsKeyboardNavigating(false);
                          setSelectedIndex(idx);
                        }}
                        className={`w-full text-left flex items-center gap-3 p-2 rounded-xl transition-all cursor-pointer ${
                          isSelected
                            ? "bg-red-50 dark:bg-white/15 text-slate-900 dark:text-white"
                            : "hover:bg-slate-100 dark:hover:bg-white/10 text-slate-900 dark:text-text-primary"
                        }`}
                      >
                        {/* Poster Thumbnail */}
                        <div className="w-10 h-14 rounded-lg bg-slate-200 dark:bg-surface-container-high overflow-hidden shrink-0 relative border border-slate-200 dark:border-white/10">
                          <SearchPoster item={item} />
                        </div>

                        {/* Metadata */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-1.5 mb-0.5">
                            <span className="font-bold text-sm text-slate-900 dark:text-text-primary truncate">
                              {item.title}
                            </span>
                            {item.year && (
                              <span className="text-[11px] text-slate-500 dark:text-text-secondary shrink-0">
                                ({item.year})
                              </span>
                            )}
                          </div>

                          <div className="flex items-center gap-2 text-xs text-slate-600 dark:text-text-secondary">
                            {item.type === "movie" && (
                              <span className="px-1.5 py-0.5 rounded bg-red-500/10 dark:bg-red-500/20 text-[#D20A13] dark:text-red-400 font-bold text-[10px] uppercase">
                                Kino
                              </span>
                            )}
                            {item.type === "series" && (
                              <span className="px-1.5 py-0.5 rounded bg-sky-500/10 dark:bg-sky-500/20 text-sky-700 dark:text-sky-400 font-bold text-[10px] uppercase">
                                Serial
                              </span>
                            )}
                            {item.type === "collection" && (
                              <span className="px-1.5 py-0.5 rounded bg-red-500/10 dark:bg-[#E50914]/20 text-[#D20A13] dark:text-red-400 font-bold text-[10px] uppercase">
                                Xronologiya
                              </span>
                            )}

                            {item.imdb_rating && (
                              <span className="flex items-center gap-0.5 text-rating-gold font-bold text-[11px]">
                                <span
                                  className="material-symbols-outlined text-[13px]"
                                  style={{ fontVariationSettings: "'FILL' 1" }}
                                >
                                  star
                                </span>
                                {Number(item.imdb_rating).toFixed(1)}
                              </span>
                            )}

                            {item.code && (
                              <span className="font-mono text-[11px] text-slate-500 dark:text-white/50">
                                #{item.code}
                              </span>
                            )}

                            {item.extra && (
                              <span className="text-[10px] text-[#D20A13] dark:text-primary-container truncate">
                                {item.extra}
                              </span>
                            )}
                          </div>
                        </div>
                      </button>
                    );
                  })}
                </div>
              )}

              {/* Section 2: External TMDB Results (Bazada yo'q) */}
              {externalResults.length > 0 && (
                <div className="pt-1.5">
                  <div className="px-3 py-1.5 text-[11px] font-bold uppercase tracking-wider text-cyan-700 dark:text-cyan-400 flex items-center justify-between bg-cyan-500/10 rounded-xl mb-1.5 border border-cyan-500/25">
                    <span className="flex items-center gap-1.5">
                      <span className="material-symbols-outlined text-[15px]">travel_explore</span>
                      <span>TMDB Jahon katalogidan</span>
                    </span>
                    <span className="text-[10px] text-cyan-600 dark:text-cyan-300 font-normal">Bazada yo&apos;q</span>
                  </div>

                  {externalResults.map((ext) => {
                    const extKey = getExtKey(ext);
                    const isReq = ext.is_requested || requestedKeys.has(extKey);
                    const reqCount = isReq ? Math.max(1, ext.request_count || 1) : (ext.request_count || 0);

                    return (
                      <div
                        key={`ext-drop-${ext.tmdb_id || ext.kinopoisk_id || ext.title}`}
                        onClick={() => handleOpenRequest(ext)}
                        className="w-full flex items-center justify-between gap-3 p-2 rounded-xl hover:bg-slate-100 dark:hover:bg-white/10 transition-all cursor-pointer group"
                      >
                        <div className="flex items-center gap-3 min-w-0">
                          {/* Poster Thumbnail */}
                          <div className="w-10 h-14 rounded-lg bg-slate-200 dark:bg-surface-container-high overflow-hidden shrink-0 relative border border-slate-200 dark:border-white/10">
                            <ExternalPoster item={ext} />
                          </div>

                          {/* Info */}
                          <div className="min-w-0">
                            <div className="flex items-center gap-1.5 mb-0.5">
                              <h4 className="font-bold text-sm text-slate-900 dark:text-text-primary truncate group-hover:text-cyan-700 dark:group-hover:text-cyan-300 transition-colors">
                                {ext.title}
                              </h4>
                              {ext.release_year && (
                                <span className="text-[11px] text-slate-500 dark:text-text-secondary shrink-0">
                                  ({ext.release_year})
                                </span>
                              )}
                            </div>

                            <div className="flex items-center gap-2 text-xs text-slate-600 dark:text-text-secondary">
                              <span className="px-1.5 py-0.5 rounded bg-slate-100 dark:bg-white/10 text-slate-600 dark:text-white/70 font-bold text-[10px] uppercase">
                                {ext.media_type === "series" ? "Serial" : "Kino"}
                              </span>

                              {ext.vote_average && (
                                <span className="flex items-center gap-0.5 text-rating-gold font-bold text-[11px]">
                                  <span
                                    className="material-symbols-outlined text-[13px]"
                                    style={{ fontVariationSettings: "'FILL' 1" }}
                                  >
                                    star
                                  </span>
                                  {ext.vote_average.toFixed(1)}
                                </span>
                              )}

                              {reqCount > 0 && (
                                <span className="text-[11px] text-[#E50914] font-semibold">
                                  🔥 {reqCount} so&apos;rov
                                </span>
                              )}
                            </div>
                          </div>
                        </div>

                        {/* Action Button */}
                        <div className="shrink-0" onClick={(e) => e.stopPropagation()}>
                          {isReq ? (
                            <span className="px-2.5 py-1 text-[11px] font-bold rounded-lg bg-emerald-500/15 dark:bg-emerald-500/20 text-emerald-700 dark:text-emerald-400 border border-emerald-500/30 flex items-center gap-1">
                              <span className="material-symbols-outlined text-[13px]">check</span>
                              <span>So&apos;ralgan</span>
                            </span>
                          ) : (
                            <button
                              type="button"
                              onClick={() => handleOpenRequest(ext)}
                              className="px-2.5 py-1 text-[11px] font-bold rounded-lg bg-[#D20A13]/10 dark:bg-primary/20 hover:bg-[#D20A13] dark:hover:bg-primary text-[#D20A13] dark:text-primary hover:text-white border border-[#D20A13]/30 dark:border-primary/40 transition-all flex items-center gap-1 active:scale-95 shadow cursor-pointer"
                            >
                              <span className="material-symbols-outlined text-[14px]">add_circle</span>
                              <span>So&apos;rash</span>
                            </button>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}

              {/* View all button - ALWAYS goes to /search?q=... */}
              <div className="pt-2 pb-1 px-1 border-t border-slate-200 dark:border-white/10 mt-1 flex flex-col gap-1.5">
                <button
                  type="button"
                  onClick={handleFullSearch}
                  className="w-full py-2.5 px-3 text-center text-xs font-bold text-slate-900 dark:text-white bg-slate-100 hover:bg-[#D20A13] hover:text-white dark:bg-white/10 dark:hover:bg-[#E50914] border border-slate-200 dark:border-white/10 rounded-xl transition-all flex items-center justify-center gap-1.5 shadow-sm cursor-pointer"
                >
                  <span>&ldquo;{query}&rdquo; bo&apos;yicha to&apos;liq qidirish (barcha variantlar)</span>
                  <span className="material-symbols-outlined text-sm">arrow_forward</span>
                </button>
                <Link
                  href="/requests"
                  onClick={() => {
                    suppressOverlayHistoryBack();
                    suppressPopupRef.current = true;
                    setIsOpen(false);
                    onNavigate?.();
                  }}
                  className="w-full py-1.5 px-3 text-center text-xs font-medium text-slate-600 dark:text-text-secondary hover:text-[#D20A13] dark:hover:text-primary transition-colors flex items-center justify-center gap-1"
                >
                  <span className="material-symbols-outlined text-[14px]">format_list_bulleted</span>
                  <span>Barcha buyurtmalar ro&apos;yxati</span>
                </Link>
              </div>
            </div>
          ) : !isLoading && query.trim() ? (
            /* Case 3: Empty State (Neither in DB nor TMDB) */
            <div className="p-6 text-center text-slate-600 dark:text-text-secondary">
              <span className="material-symbols-outlined text-3xl opacity-40 mb-1">
                search_off
              </span>
              <p className="text-xs mb-3 text-slate-700 dark:text-white/80">
                &ldquo;{query}&rdquo; bo&apos;yicha hech qanday film yoki serial topilmadi
              </p>
              <div className="flex flex-col gap-2 max-w-[280px] mx-auto">
                <button
                  type="button"
                  onClick={() => {
                    suppressPopupRef.current = true;
                    setIsOpen(false);
                    setSelectedRequestItem({
                      title: query.trim(),
                      media_type: "movie",
                    });
                    setIsModalOpen(true);
                  }}
                  className="w-full py-2 px-3 rounded-xl bg-[#E50914] hover:bg-[#B80710] text-white font-bold text-xs active:scale-95 transition-all flex items-center justify-center gap-1.5 shadow-lg shadow-primary/30 cursor-pointer"
                >
                  <span className="material-symbols-outlined text-sm">add_circle</span>
                  <span>Shu kinoni qo&apos;shishni so&apos;rash</span>
                </button>
                <button
                  type="button"
                  onClick={handleFullSearch}
                  className="w-full py-1.5 px-3 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-white/5 dark:hover:bg-white/10 text-slate-700 dark:text-white/70 hover:text-slate-900 dark:hover:text-white text-xs font-medium transition-all cursor-pointer"
                >
                  To&apos;liq qidiruv sahifasiga o&apos;tish
                </button>
              </div>
            </div>
          ) : null}
        </div>
      )}

      {/* Direct Modal for requesting movies */}
      <RequestMovieModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        item={selectedRequestItem}
        onSuccess={handleRequestSuccess}
      />
    </div>
  );
}
