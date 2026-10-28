"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth/AuthProvider";
import { getHistory, HistoryItem } from "@/lib/api/history";
import { fetchApi } from "@/lib/api";
import MovieCard from "@/components/catalog/MovieCard";
import { CatalogItem } from "@/lib/api/catalog";

export interface ContinueItem {
  id: string | number;
  code?: string;
  title: string;
  poster_url: string | null;
  is_series: boolean;
  release_year?: number | null;
  imdb_rating?: number | null;
  genres?: string | null;
  progress?: number;
  last_watched_at?: string;
  is_18_plus?: boolean;
}

export default function ContinueWatchingSection() {
  const { status } = useAuth();
  const [items, setItems] = useState<ContinueItem[]>([]);
  const [loading, setLoading] = useState(true);

  const loadItems = useCallback(async () => {
    const combinedItems: ContinueItem[] = [];

    // 1. Authenticated user history
    if (status === "authenticated") {
      try {
        const historyData = await getHistory(0, 10);
        if (historyData?.items && Array.isArray(historyData.items)) {
          const authItems: ContinueItem[] = historyData.items.map((h: HistoryItem) => {
            if (h.type === "episode" && h.episode) {
              return {
                id: h.episode.series_id || h.id,
                code: h.episode.code,
                title: `${h.episode.series_title} (${h.episode.display_code})`,
                poster_url: h.episode.series_poster,
                is_series: true,
                release_year: h.episode.release_year || null,
                imdb_rating: h.episode.imdb_rating || null,
                genres: h.episode.genres || null,
                progress: h.status === "completed" ? 100 : 55,
                last_watched_at: h.last_watched_at,
              };
            }
            return {
              id: h.movie?.id || h.id,
              code: h.movie?.code,
              title: h.movie?.title || "Noma'lum film",
              poster_url: h.movie?.poster_url || null,
              is_series: false,
              release_year: h.movie?.release_year || null,
              imdb_rating: h.movie?.imdb_rating || null,
              genres: h.movie?.genres || null,
              progress: h.status === "completed" ? 100 : 65,
              last_watched_at: h.last_watched_at,
            };
          });
          combinedItems.push(...authItems);
        }
      } catch (err) {
        console.error("Failed to fetch authenticated watch history:", err);
      }
    }

    // 2. Local storage guest history
    if (typeof window !== "undefined") {
      try {
        const raw = localStorage.getItem("mediaplus_continue_watching");
        if (raw) {
          const localParsed = JSON.parse(raw);
          if (Array.isArray(localParsed)) {
            const guestItems: ContinueItem[] = localParsed
              .filter((item: any) => {
                const idStr = String(item.id || item.code || "");
                return idStr && !idStr.startsWith("http") && idStr !== "unknown" && idStr !== "0";
              })
              .map((item: any) => {
                const seriesId = item.seriesId || item.series_id;
                const rawId = item.id || item.code;
                const resolvedId = (item.is_series && seriesId && String(seriesId) !== "0")
                  ? seriesId
                  : (rawId && String(rawId) !== "0" ? rawId : item.code);
                return {
                  id: resolvedId,
                  code: item.code && !String(item.code).startsWith("http") ? String(item.code) : undefined,
                  title: item.title || "Noma'lum film",
                  poster_url: item.poster_url || null,
                  is_series: !!item.is_series,
                  release_year: item.release_year || null,
                  imdb_rating: item.imdb_rating || null,
                  genres: item.genres || null,
                  progress: item.progress || 60,
                  last_watched_at: item.last_watched_at,
                  is_18_plus: !!item.is_18_plus,
                };
              });

            // Merge avoiding duplicates by id or code
            for (const gItem of guestItems) {
              const alreadyExists = combinedItems.some(
                (c) =>
                  String(c.id) === String(gItem.id) ||
                  (c.code && gItem.code && String(c.code) === String(gItem.code))
              );
              if (!alreadyExists) {
                combinedItems.push(gItem);
              }
            }
          }
        }
      } catch (err) {
        console.error("Failed to parse local continue watching items:", err);
      }
    }

    const sliced = combinedItems.slice(0, 10);
    setItems(sliced);
    setLoading(false);

    // Asynchronously enrich missing year & rating (e.g. for legacy items)
    const needsEnrich = sliced.some((x) => !x.release_year || !x.imdb_rating || !x.genres || x.genres === "Serial" || x.genres === "Kino");
    if (needsEnrich) {
      try {
        const enriched = await Promise.all(
          sliced.map(async (it) => {
            if (it.release_year && it.imdb_rating && it.genres && it.genres !== "Serial" && it.genres !== "Kino") {
              return it;
            }
            try {
              let data: any = null;
              if (it.is_series) {
                const targetKey = it.id || it.code;
                try {
                  data = await fetchApi(`/series/${targetKey}`);
                } catch {
                  if (it.code) {
                    try {
                      data = await fetchApi(`/series/code/${it.code}`);
                    } catch {}
                  }
                }
                if (!data && (it.code || it.id)) {
                  try {
                    const epDetail = await fetchApi(`/series/episodes/code/${it.code || it.id}`);
                    if (epDetail?.series_id) {
                      data = await fetchApi(`/series/${epDetail.series_id}`);
                    }
                  } catch {}
                }
              } else {
                try {
                  data = await fetchApi(`/movies/${it.code || it.id}`);
                } catch {}
              }

              if (data) {
                const resolvedYear = data.release_year || it.release_year || null;
                const resolvedRating = data.imdb_rating || data.tmdb_rating || it.imdb_rating || null;
                const resolvedGenre = (data.categories?.[0]?.name || (typeof data.genres === "string" ? data.genres.split(",")[0].trim() : null)) || it.genres;
                const resolvedSeriesId = (it.is_series && data.id) ? data.id : it.id;

                try {
                  const raw = localStorage.getItem("mediaplus_continue_watching");
                  if (raw) {
                    const list = JSON.parse(raw);
                    if (Array.isArray(list)) {
                      const updatedList = list.map((localItem: any) => {
                        const isMatch = String(localItem.id) === String(it.id) || (localItem.code && String(localItem.code) === String(it.code));
                        if (isMatch) {
                          return {
                            ...localItem,
                            id: resolvedSeriesId,
                            seriesId: it.is_series ? resolvedSeriesId : localItem.seriesId,
                            release_year: resolvedYear,
                            imdb_rating: resolvedRating,
                            genres: resolvedGenre,
                          };
                        }
                        return localItem;
                      });
                      localStorage.setItem("mediaplus_continue_watching", JSON.stringify(updatedList));
                    }
                  }
                } catch (e) {}

                return {
                  ...it,
                  id: resolvedSeriesId,
                  release_year: resolvedYear,
                  imdb_rating: resolvedRating,
                  genres: resolvedGenre,
                  poster_url: it.poster_url || data.poster_url,
                };
              }
            } catch {
              // fallback
            }
            return it;
          })
        );
        setItems(enriched);
      } catch (e) {}
    }
  }, [status]);

  useEffect(() => {
    loadItems();

    const handleUpdate = () => {
      loadItems();
    };

    window.addEventListener("mediaplus_continue_watching_updated", handleUpdate);
    return () => {
      window.removeEventListener("mediaplus_continue_watching_updated", handleUpdate);
    };
  }, [loadItems]);

  return (
    <section className="max-w-container-max mx-auto px-gutter mb-12 sm:mb-16 mt-6 relative z-20">
      <div className="flex items-center justify-between mb-4">
        <h2 className="font-headline-md text-lg sm:text-xl md:text-2xl text-text-primary flex items-center gap-2 font-bold">
          <span className="w-1 h-6 bg-primary rounded-full block" />
          <span>Ko'rishni davom ettirish</span>
        </h2>
        {items.length > 0 && (
          <Link
            href="/profile?tab=history"
            className="text-text-secondary hover:text-white text-xs sm:text-sm font-semibold transition-colors flex items-center gap-1 group"
          >
            <span>Barchasi (Tarix)</span>
            <span className="material-symbols-outlined text-[16px] group-hover:translate-x-0.5 transition-transform">
              arrow_forward
            </span>
          </Link>
        )}
      </div>

      {loading ? (
        <div className="flex gap-3 sm:gap-4 overflow-x-auto pb-4 pt-1">
          {[1, 2, 3, 4].map((i) => (
            <div
              key={i}
              className="w-[140px] sm:w-[170px] md:w-[200px] shrink-0 aspect-[2/3] rounded-xl bg-white/5 animate-pulse"
            />
          ))}
        </div>
      ) : items.length === 0 ? (
        /* Empty State Card */
        <div className="p-6 sm:p-8 rounded-2xl bg-white/[0.03] border border-white/10 backdrop-blur-md flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-4 text-center sm:text-left">
            <div className="w-12 h-12 rounded-xl bg-rating-gold/10 border border-rating-gold/20 flex items-center justify-center text-rating-gold shrink-0">
              <span className="material-symbols-outlined text-2xl">history</span>
            </div>
            <div>
              <h3 className="text-sm sm:text-base font-bold text-white mb-1">
                Davom ettirish uchun filmlar yo'q
              </h3>
              <p className="text-xs text-text-secondary max-w-md">
                Biror kino yoki serialni tomosha qilishni boshlang, u avtomatik ravishda ushbu ro'yxatda paydo bo'ladi.
              </p>
            </div>
          </div>
          <Link
            href="/catalog"
            className="h-10 px-4 rounded-xl bg-white/10 hover:bg-white/15 text-white font-semibold text-xs sm:text-sm border border-white/15 flex items-center gap-2 transition-all hover:scale-[1.02] active:scale-95 shrink-0"
          >
            <span className="material-symbols-outlined text-[18px]">movie</span>
            <span>Katalogni ochish</span>
          </Link>
        </div>
      ) : (
        /* Scrollable List of In-Progress Cards */
        <div className="flex gap-3 sm:gap-4 overflow-x-auto snap-x hide-scrollbar pb-4 pt-1">
          {items.map((item) => {
            const cleanCode = item.code && !String(item.code).startsWith("http") && String(item.code) !== "0" ? String(item.code) : "";
            const cleanId = item.id && !String(item.id).startsWith("http") && String(item.id) !== "0" ? String(item.id) : "";
            const target = cleanId || cleanCode;
            if (!target || target === "unknown" || target === "0") return null;

            const targetHref = item.is_series ? `/series/${target}` : `/movie/${cleanCode || target}`;
            const numericId = typeof item.id === "number" && item.id > 0 ? item.id : (Number(cleanId) || Number(cleanCode) || 0);

            const catalogItem: CatalogItem = {
              id: numericId,
              code: cleanCode || (isNaN(Number(target)) ? target : undefined),
              title: item.title,
              poster_url: item.poster_url,
              is_series: item.is_series,
              genres: item.genres || (item.is_series ? "Serial" : "Kino"),
              release_year: item.release_year || null,
              imdb_rating: item.imdb_rating ?? null,
              tmdb_rating: null,
            };

            return (
              <div
                key={`cw-${item.id}-${item.code || ""}`}
                className="w-[140px] sm:w-[170px] md:w-[200px] shrink-0 snap-start"
              >
                <MovieCard item={catalogItem} statusBadge="in_progress" href={targetHref} />
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}
