"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import Image from "next/image";
import BackButton from "@/components/BackButton";
import SubscribeButton from "@/components/SubscribeButton";
import { useAuth } from "@/lib/auth/AuthProvider";
import { fetchApi } from "@/lib/api";

interface SubscribedSeries {
  id: number;
  title: string;
  poster_url?: string | null;
  imdb_rating?: number | null;
  release_year?: number | null;
  type: string;
}

interface SubscribedCollection {
  id: number;
  name: string;
  slug: string;
  description?: string | null;
  poster_url?: string | null;
  banner_url?: string | null;
  item_count?: number;
  type: string;
}

export default function SubscriptionsPage() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<"all" | "series" | "collections">("all");
  const [seriesList, setSeriesList] = useState<SubscribedSeries[]>([]);
  const [collectionsList, setCollectionsList] = useState<SubscribedCollection[]>([]);
  const [loading, setLoading] = useState(true);

  const loadSubscriptions = useCallback(async () => {
    setLoading(true);
    try {
      if (user?.telegram_id) {
        const data = await fetchApi("/users/me/subscriptions");
        setSeriesList(data?.series || []);
        setCollectionsList(data?.collections || []);
      } else {
        // Fallback for guest users from localStorage
        const raw = localStorage.getItem("mediaplus_guest_subscriptions");
        if (raw) {
          const parsed = JSON.parse(raw);
          setSeriesList(parsed?.series || []);
          setCollectionsList(parsed?.collections || []);
        } else {
          setSeriesList([]);
          setCollectionsList([]);
        }
      }
    } catch (err) {
      // Graceful fallback
      setSeriesList([]);
      setCollectionsList([]);
    } finally {
      setLoading(false);
    }
  }, [user?.telegram_id]);

  useEffect(() => {
    loadSubscriptions();

    const handleSync = () => loadSubscriptions();
    window.addEventListener("subscription:change", handleSync);
    return () => {
      window.removeEventListener("subscription:change", handleSync);
    };
  }, [loadSubscriptions]);

  const totalCount = seriesList.length + collectionsList.length;

  return (
    <div className="min-h-screen pt-24 pb-20 px-4 sm:px-6 max-w-container-max mx-auto text-text-primary">
      {/* 1. Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 sm:mb-8 pb-4 border-b border-white/10">
        <div className="flex items-center gap-3">
          <BackButton fallbackUrl="/" />
          <div>
            <div className="flex items-center gap-2">
              <span className="px-2 py-0.5 rounded-full bg-rating-gold/15 text-rating-gold text-[10px] sm:text-xs font-bold tracking-wider uppercase border border-rating-gold/30">
                Mening Obunalarim
              </span>
              <span className="text-text-secondary text-xs">Kuzatuv ro&apos;yxati</span>
            </div>
            <h1 className="text-xl sm:text-3xl font-extrabold text-white tracking-tight mt-0.5">
              Obunalar
            </h1>
          </div>
        </div>

        {/* Filter Tabs */}
        <div className="flex items-center gap-1.5 bg-white/5 border border-white/10 p-1 rounded-xl self-start sm:self-auto">
          <button
            onClick={() => setActiveTab("all")}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              activeTab === "all"
                ? "bg-white/15 text-white shadow-sm"
                : "text-text-secondary hover:text-white"
            }`}
          >
            Barchasi ({totalCount})
          </button>
          <button
            onClick={() => setActiveTab("series")}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              activeTab === "series"
                ? "bg-white/15 text-white shadow-sm"
                : "text-text-secondary hover:text-white"
            }`}
          >
            Seriallar ({seriesList.length})
          </button>
          <button
            onClick={() => setActiveTab("collections")}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              activeTab === "collections"
                ? "bg-white/15 text-white shadow-sm"
                : "text-text-secondary hover:text-white"
            }`}
          >
            To&apos;plamlar ({collectionsList.length})
          </button>
        </div>
      </div>

      {/* Guest notice if not logged in */}
      {!user && (
        <div className="mb-6 p-4 rounded-2xl bg-white/[0.03] border border-white/5 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <span className="material-symbols-outlined text-rating-gold text-2xl">info</span>
            <p className="text-xs sm:text-sm text-text-secondary">
              Telegram orqali tizimga kirsangiz, obuna bo&apos;lgan kino va seriallaringiz yangi qismlari chiqqanda Telegram orqali darhol xabarnoma olasiz!
            </p>
          </div>
          <Link
            href="/profile"
            className="px-4 py-2 rounded-xl bg-primary-container text-white text-xs font-bold whitespace-nowrap hover:bg-inverse-primary transition-all self-start sm:self-auto"
          >
            Kirish
          </Link>
        </div>
      )}

      {/* Loading State */}
      {loading ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="aspect-[2/3] rounded-2xl bg-white/5 animate-pulse" />
          ))}
        </div>
      ) : totalCount === 0 ? (
        /* Empty State */
        <div className="rounded-3xl bg-white/[0.02] border border-white/5 p-12 sm:p-16 text-center flex flex-col items-center justify-center max-w-xl mx-auto my-8">
          <div className="w-16 h-16 rounded-2xl bg-white/5 flex items-center justify-center mb-4 text-white/40">
            <span className="material-symbols-outlined text-3xl">bookmark_border</span>
          </div>
          <h2 className="text-lg sm:text-xl font-bold text-white mb-2">
            Hozircha obunalar yo&apos;q
          </h2>
          <p className="text-xs sm:text-sm text-text-secondary max-w-md leading-relaxed mb-6">
            O&apos;zingizga yoqqan serial yoki film franshizasi sahifasiga kirib &quot;Obuna bo&apos;lish&quot; tugmasini bosing. Yangi qismlar chiqqanda xabardor bo&apos;lasiz!
          </p>
          <Link
            href="/catalog"
            className="px-6 py-3 rounded-xl bg-white/10 hover:bg-white/15 border border-white/15 text-white text-xs sm:text-sm font-bold transition-all hover:scale-[1.02] active:scale-95"
          >
            Katalogga o&apos;tish
          </Link>
        </div>
      ) : (
        /* Subscriptions Grid */
        <div className="space-y-8">
          {/* 1. Series Section */}
          {(activeTab === "all" || activeTab === "series") && seriesList.length > 0 && (
            <div>
              <h2 className="text-base sm:text-lg font-bold text-white mb-4 flex items-center gap-2">
                <span className="w-1.5 h-4 bg-primary-container rounded-full block"></span>
                Kuzatilayotgan Seriallar ({seriesList.length})
              </h2>
              <div className="grid grid-cols-2 xs:grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 gap-3 sm:gap-4">
                {seriesList.map((series) => (
                  <div
                    key={`series-${series.id}`}
                    className="group relative flex flex-col rounded-2xl overflow-hidden bg-surface-container-low border border-white/5 hover:border-primary-container/40 transition-all duration-300"
                  >
                    <Link href={`/series/${series.id}`} className="block relative aspect-[2/3] w-full bg-surface-container-high overflow-hidden">
                      {series.poster_url ? (
                        <Image
                          src={series.poster_url}
                          alt={series.title}
                          fill
                          sizes="(max-width: 640px) 50vw, 20vw"
                          className="object-cover group-hover:scale-105 transition-transform duration-500"
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center text-white/30 text-xs">
                          Rasm yo&apos;q
                        </div>
                      )}
                      {series.imdb_rating && (
                        <div className="absolute top-2 left-2 bg-black/70 backdrop-blur-md px-2 py-0.5 rounded-lg border border-white/10 text-[10px] font-bold text-white flex items-center gap-1">
                          <span className="text-rating-gold">★</span>
                          <span>{series.imdb_rating}</span>
                        </div>
                      )}
                    </Link>

                    <div className="p-2.5 sm:p-3 flex flex-col flex-1 justify-between gap-2">
                      <div>
                        <Link href={`/series/${series.id}`}>
                          <h3 className="font-semibold text-xs sm:text-sm text-white group-hover:text-primary-container transition-colors line-clamp-1">
                            {series.title}
                          </h3>
                        </Link>
                        {series.release_year && (
                          <span className="text-[10px] text-text-secondary">
                            {series.release_year} • Serial
                          </span>
                        )}
                      </div>

                      <div className="pt-2 border-t border-white/5 flex items-center justify-between">
                        <span className="text-[10px] text-emerald-400 flex items-center gap-1">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                          Obunada
                        </span>
                        <SubscribeButton
                          targetType="series"
                          targetId={series.id}
                          title={series.title}
                          showIconOnly={true}
                          className="!p-1 !h-7 !w-7"
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 2. Collections / Franchises Section */}
          {(activeTab === "all" || activeTab === "collections") && collectionsList.length > 0 && (
            <div>
              <h2 className="text-base sm:text-lg font-bold text-white mb-4 flex items-center gap-2">
                <span className="w-1.5 h-4 bg-primary-container rounded-full block"></span>
                Kuzatilayotgan To&apos;plamlar va Franshizalar ({collectionsList.length})
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {collectionsList.map((col) => (
                  <div
                    key={`col-${col.id}`}
                    className="group relative flex items-center gap-4 p-3.5 rounded-2xl bg-surface-container-low border border-white/5 hover:border-primary-container/40 transition-all duration-300"
                  >
                    <Link
                      href={`/collections/${col.slug}`}
                      className="relative w-20 h-28 shrink-0 rounded-xl overflow-hidden bg-surface-container-high"
                    >
                      {col.poster_url || col.banner_url ? (
                        <Image
                          src={col.poster_url || col.banner_url || ""}
                          alt={col.name}
                          fill
                          sizes="80px"
                          className="object-cover group-hover:scale-105 transition-transform duration-500"
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center text-white/30 text-xs">
                          Rasm yo&apos;q
                        </div>
                      )}
                    </Link>

                    <div className="flex-1 flex flex-col justify-between h-full py-1">
                      <div>
                        <Link href={`/collections/${col.slug}`}>
                          <h3 className="font-bold text-sm text-white group-hover:text-primary-container transition-colors line-clamp-1 mb-1">
                            {col.name}
                          </h3>
                        </Link>
                        {col.description && (
                          <p className="text-xs text-text-secondary line-clamp-2 leading-relaxed mb-2">
                            {col.description}
                          </p>
                        )}
                        {col.item_count !== undefined && (
                          <span className="text-[11px] text-white/60 font-medium">
                            {col.item_count} ta film
                          </span>
                        )}
                      </div>

                      <div className="flex items-center justify-between pt-2 border-t border-white/5 mt-auto">
                        <Link
                          href={`/collections/${col.slug}`}
                          className="text-xs text-primary-container hover:underline font-semibold"
                        >
                          To&apos;plamni ko&apos;rish &rarr;
                        </Link>
                        <SubscribeButton
                          targetType="collection"
                          targetId={col.id}
                          title={col.name}
                          showIconOnly={true}
                          className="!p-1 !h-7 !w-7"
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
