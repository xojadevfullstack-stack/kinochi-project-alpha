"use client";

import React, { useState, useEffect, useRef } from "react";
import Image from "next/image";
import { useRouter } from "next/navigation";

interface SearchResultItem {
  id: number;
  title: string;
  original_title?: string | null;
  code: string;
  year?: number | null;
  poster_url?: string | null;
  imdb_rating?: number | null;
  type: "movie" | "series" | "collection";
  extra?: string | null;
}

interface LiveSearchProps {
  placeholder?: string;
  className?: string;
  inputClassName?: string;
  onNavigate?: () => void;
  isMobileDrawer?: boolean;
}

export default function LiveSearch({
  placeholder = "Kino, serial yoki #kod qidirish...",
  className = "",
  inputClassName = "",
  onNavigate,
  isMobileDrawer = false,
}: LiveSearchProps) {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResultItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState<number>(-1);
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

  // Debounced live fetch
  useEffect(() => {
    const clean = query.trim();
    if (clean.length < 1) {
      setResults([]);
      setIsLoading(false);
      setIsOpen(false);
      return;
    }

    setIsLoading(true);
    const handler = setTimeout(async () => {
      try {
        const res = await fetch(`${API_URL}/search/live?q=${encodeURIComponent(clean)}&limit=8`);
        if (res.ok) {
          const data = await res.json();
          setResults(data.results || []);
          setIsOpen(true);
        } else {
          setResults([]);
        }
      } catch (err) {
        setResults([]);
      } finally {
        setIsLoading(false);
      }
    }, 220);

    return () => clearTimeout(handler);
  }, [query, API_URL]);

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
    setIsOpen(false);
    setQuery("");
    onNavigate?.();

    if (item.type === "movie") {
      router.push(`/movie/${item.code}`);
    } else if (item.type === "series") {
      const serialId = item.code?.replace("s_", "") || item.id;
      router.push(`/series/${serialId}`);
    } else if (item.type === "collection") {
      router.push(`/collections/${item.code}`);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedIndex >= 0 && selectedIndex < results.length) {
      handleSelect(results[selectedIndex]);
      return;
    }
    if (query.trim()) {
      setIsOpen(false);
      onNavigate?.();
      router.push(`/search?q=${encodeURIComponent(query.trim())}`);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isOpen || results.length === 0) return;

    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelectedIndex((prev) => (prev < results.length - 1 ? prev + 1 : 0));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedIndex((prev) => (prev > 0 ? prev - 1 : results.length - 1));
    } else if (e.key === "Escape") {
      setIsOpen(false);
    }
  };

  return (
    <div ref={containerRef} className={`relative ${className}`}>
      <form onSubmit={handleSubmit} className="w-full relative">
        <div className="flex items-center w-full bg-white/5 hover:bg-white/10 rounded-full px-3.5 py-1.5 xl:px-4 xl:py-2 border border-white/10 focus-within:border-primary-container focus-within:bg-white/10 transition-all">
          <span
            className="material-symbols-outlined text-text-secondary mr-2 text-[18px] xl:text-[20px] shrink-0"
            style={{ fontVariationSettings: "'FILL' 0" }}
          >
            search
          </span>
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setSelectedIndex(-1);
            }}
            onFocus={() => {
              if (results.length > 0) setIsOpen(true);
            }}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            className={`bg-transparent border-none focus:ring-0 text-text-primary text-sm placeholder:text-text-secondary outline-none w-full ${inputClassName}`}
          />
          {isLoading ? (
            <div className="w-4 h-4 border-2 border-primary-container border-t-transparent rounded-full animate-spin shrink-0 ml-1"></div>
          ) : query ? (
            <button
              type="button"
              onClick={() => {
                setQuery("");
                setResults([]);
                setIsOpen(false);
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
      {isOpen && (
        <div
          className={`absolute left-0 right-0 mt-2 bg-background-obsidian/95 backdrop-blur-2xl border border-white/15 rounded-2xl shadow-2xl shadow-black/80 overflow-hidden z-50 transition-all ${
            isMobileDrawer ? "max-h-[60vh] w-full" : "min-w-[320px] max-w-[420px] max-h-[460px]"
          } flex flex-col`}
        >
          {results.length > 0 ? (
            <div className="overflow-y-auto divide-y divide-white/5 p-1.5">
              <div className="px-3 py-1.5 text-[11px] font-bold uppercase tracking-wider text-text-secondary flex items-center justify-between">
                <span>Jonli natijalar</span>
                <span className="text-[10px] text-white/40">Tezkor tanlov</span>
              </div>
              {results.map((item, idx) => {
                const isSelected = idx === selectedIndex;
                return (
                  <button
                    key={`${item.type}-${item.id}`}
                    type="button"
                    onClick={() => handleSelect(item)}
                    onMouseEnter={() => setSelectedIndex(idx)}
                    className={`w-full text-left flex items-center gap-3 p-2 rounded-xl transition-all ${
                      isSelected
                        ? "bg-white/15 text-white"
                        : "hover:bg-white/10 text-text-primary"
                    }`}
                  >
                    {/* Poster Thumbnail */}
                    <div className="w-10 h-14 rounded-lg bg-surface-container-high overflow-hidden shrink-0 relative border border-white/10">
                      {item.poster_url ? (
                        <Image
                          src={item.poster_url}
                          alt={item.title}
                          fill
                          sizes="40px"
                          className="object-cover"
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center text-white/30 text-xs">
                          <span className="material-symbols-outlined text-lg">
                            {item.type === "movie"
                              ? "movie"
                              : item.type === "series"
                              ? "live_tv"
                              : "auto_awesome_motion"}
                          </span>
                        </div>
                      )}
                    </div>

                    {/* Metadata */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-1.5 mb-0.5">
                        <span className="font-bold text-sm text-text-primary truncate">
                          {item.title}
                        </span>
                        {item.year && (
                          <span className="text-[11px] text-text-secondary shrink-0">
                            ({item.year})
                          </span>
                        )}
                      </div>

                      <div className="flex items-center gap-2 text-xs text-text-secondary">
                        {item.type === "movie" && (
                          <span className="px-1.5 py-0.5 rounded bg-red-500/20 text-red-400 font-bold text-[10px] uppercase">
                            Kino
                          </span>
                        )}
                        {item.type === "series" && (
                          <span className="px-1.5 py-0.5 rounded bg-sky-500/20 text-sky-400 font-bold text-[10px] uppercase">
                            Serial
                          </span>
                        )}
                        {item.type === "collection" && (
                          <span className="px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-400 font-bold text-[10px] uppercase">
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
                          <span className="font-mono text-[11px] text-white/50">
                            #{item.code}
                          </span>
                        )}

                        {item.extra && (
                          <span className="text-[10px] text-primary-container truncate">
                            {item.extra}
                          </span>
                        )}
                      </div>
                    </div>
                  </button>
                );
              })}

              {/* View all button */}
              <div className="pt-1.5 pb-0.5 px-1">
                <button
                  type="button"
                  onClick={handleSubmit}
                  className="w-full py-2 px-3 text-center text-xs font-bold text-primary-container hover:text-white bg-primary-container/10 hover:bg-primary-container/20 rounded-xl transition-all flex items-center justify-center gap-1.5"
                >
                  <span>"{query}" bo'yicha to'liq qidirish</span>
                  <span className="material-symbols-outlined text-sm">arrow_forward</span>
                </button>
              </div>
            </div>
          ) : !isLoading && query.trim() ? (
            <div className="p-6 text-center text-text-secondary">
              <span className="material-symbols-outlined text-3xl opacity-40 mb-1">
                search_off
              </span>
              <p className="text-xs">Hech qanday film yoki serial topilmadi</p>
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
}
