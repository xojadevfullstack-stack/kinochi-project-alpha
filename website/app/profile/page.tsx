"use client";

import { useEffect, useState, useCallback, Suspense } from "react";
import { useAuth } from "@/lib/auth/AuthProvider";
import { fetchApi } from "@/lib/api";
import { getHistory, HistoryItem } from "@/lib/api/history";
import Link from "next/link";
import Image from "next/image";
import { useSearchParams } from "next/navigation";
import TelegramLoginWidget from "@/components/auth/TelegramLoginWidget";
import BackButton from "@/components/BackButton";
import SubscribeButton from "@/components/SubscribeButton";

interface UnifiedHistoryItem {
  id: string | number;
  title: string;
  poster_url?: string | null;
  href: string;
  isSeries?: boolean;
  statusBadge: "in_progress" | "completed";
  lastWatchedAt?: string;
}

interface ProfileSubscriptionItem {
  id: number;
  title: string;
  poster_url?: string | null;
  type: "series" | "franchise";
  href: string;
  slug?: string;
  release_year?: number | null;
  imdb_rating?: number | null;
  item_count?: number;
  description?: string;
}

interface CollectionRecommendation {
  id: number;
  name: string;
  slug: string;
  description?: string | null;
  poster_url?: string | null;
  items_count?: number;
}

function ProfileContent() {
  const searchParams = useSearchParams();
  const initialTab = (searchParams.get("tab") as any) || "history";

  const { status, user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState<"history" | "favorites" | "subscriptions" | "settings">(
    ["history", "favorites", "subscriptions", "settings"].includes(initialTab) ? initialTab : "history"
  );

  useEffect(() => {
    const tabParam = searchParams.get("tab");
    if (tabParam && ["history", "favorites", "subscriptions", "settings"].includes(tabParam)) {
      setActiveTab(tabParam as any);
    }
  }, [searchParams]);
  const [subFilter, setSubFilter] = useState<"all" | "series" | "franchise">("all");
  const [historyItems, setHistoryItems] = useState<UnifiedHistoryItem[]>([]);
  const [favorites, setFavorites] = useState<any[]>([]);
  const [userSubscriptions, setUserSubscriptions] = useState<ProfileSubscriptionItem[]>([]);
  const [recommendations, setRecommendations] = useState<CollectionRecommendation[]>([]);
  const [unsubscribingId, setUnsubscribingId] = useState<number | null>(null);

  // Load subscriptions from backend API
  const loadSubscriptions = useCallback(async () => {
    if (status !== "authenticated") {
      setUserSubscriptions([]);
      return;
    }
    try {
      const data = await fetchApi("/users/me/subscriptions");
      const list: ProfileSubscriptionItem[] = [];

      if (Array.isArray(data?.series)) {
        data.series.forEach((s: any) => {
          list.push({
            id: s.id,
            title: s.title,
            poster_url: s.poster_url,
            type: "series",
            href: `/series/${s.id}`,
            release_year: s.release_year,
            imdb_rating: s.imdb_rating,
            description: `${s.release_year ? s.release_year + '-yil • ' : ''}IMDb: ${s.imdb_rating || 'N/A'}`
          });
        });
      }

      if (Array.isArray(data?.collections)) {
        data.collections.forEach((c: any) => {
          list.push({
            id: c.id,
            title: c.name,
            slug: c.slug,
            poster_url: c.poster_url,
            type: "franchise",
            href: `/collections/${c.slug}`,
            item_count: c.item_count,
            description: `${c.item_count || 0} ta qism • Franshiza xronologiyasi`
          });
        });
      }

      setUserSubscriptions(list);
    } catch (e) {
      console.warn("Failed to load user subscriptions:", e);
    }
  }, [status]);

  // Load recommended collections
  const loadRecommendations = useCallback(async () => {
    try {
      const cols = await fetchApi("/collections?is_active=true");
      if (Array.isArray(cols)) {
        setRecommendations(cols.slice(0, 6));
      }
    } catch (e) {
      console.warn("Failed to load recommendations:", e);
    }
  }, []);

  useEffect(() => {
    // 1. Fetch real watch history
    if (status === "authenticated") {
      getHistory(0, 20)
        .then((res) => {
          const apiItems = res.items || [];
          if (apiItems.length > 0) {
            const mapped: UnifiedHistoryItem[] = apiItems.map((item: HistoryItem) => {
              const isSeries = item.type === "episode";
              const title = isSeries && item.episode
                ? `${item.episode.series_title} (${item.episode.display_code})`
                : item.movie?.title || "Noma'lum film";
              const poster = isSeries
                ? item.episode?.series_poster
                : item.movie?.poster_url;
              const href = isSeries && item.episode
                ? `/series/${item.episode.series_id}`
                : `/movie/${item.movie?.code || ""}`;

              return {
                id: item.id,
                title,
                poster_url: poster,
                href,
                isSeries,
                statusBadge: item.status,
                lastWatchedAt: item.last_watched_at
              };
            });
            setHistoryItems(mapped);
          }
        })
        .catch(() => {});
    }

    // 2. Load favorites from localStorage
    try {
      const savedFavs = localStorage.getItem("kinochi_favorites");
      if (savedFavs) {
        setFavorites(JSON.parse(savedFavs));
      }
    } catch {}

    // 3. Load subscriptions and recommendations
    loadSubscriptions();
    loadRecommendations();

    const handleSync = () => loadSubscriptions();
    window.addEventListener("subscription:change", handleSync);
    return () => window.removeEventListener("subscription:change", handleSync);
  }, [status, loadSubscriptions, loadRecommendations]);

  const handleUnsubscribe = async (sub: ProfileSubscriptionItem) => {
    if (!user?.telegram_id) return;
    setUnsubscribingId(sub.id);
    try {
      const endpoint = sub.type === "series"
        ? `/series/${sub.id}/subscribe`
        : `/collections/${sub.id}/subscribe`;

      await fetchApi(endpoint, {
        method: "POST",
        body: JSON.stringify({ telegram_user_id: user.telegram_id })
      });

      setUserSubscriptions(prev => prev.filter(x => !(x.id === sub.id && x.type === sub.type)));
      window.dispatchEvent(new Event("subscription:change"));
    } catch (e: any) {
      alert("Obunani bekor qilishda xatolik: " + e.message);
    } finally {
      setUnsubscribingId(null);
    }
  };

  const filteredSubscriptions = userSubscriptions.filter((sub) => {
    if (subFilter === "all") return true;
    return sub.type === subFilter;
  });

  const seriesCount = userSubscriptions.filter(s => s.type === "series").length;
  const franchiseCount = userSubscriptions.filter(s => s.type === "franchise").length;

  return (
    <div className="min-h-screen pt-20 sm:pt-24 pb-28 xl:pb-16 px-4 md:px-8 bg-background-obsidian text-text-primary">
      <div className="max-w-5xl mx-auto space-y-6">
        
        {/* Top Bar with Back Button */}
        <div className="flex items-center justify-between">
          <BackButton fallbackUrl="/" />
        </div>

        {/* User Card Banner */}
        <div className="relative rounded-2xl bg-white/5 border border-white/10 p-6 md:p-8 shadow-xl overflow-hidden">
          <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div className="flex items-center gap-4 sm:gap-5">
              <div className="relative">
                <div className="w-16 h-16 sm:w-20 sm:h-20 rounded-2xl bg-white/10 border border-white/15 flex items-center justify-center text-white text-2xl sm:text-3xl font-black shadow-inner">
                  {status === "authenticated" && user?.first_name ? user.first_name.charAt(0) : "U"}
                </div>
              </div>

              <div>
                <h1 className="text-xl sm:text-2xl font-black text-white font-headline-md tracking-tight">
                  {status === "authenticated" && user ? `${user.first_name} ${user.last_name || ""}` : "Mehmon foydalanuvchi"}
                </h1>
                <p className="text-xs text-text-secondary mt-0.5 font-mono">
                  {status === "authenticated" && user?.username ? `@${user.username}` : (user?.id ? `ID: ${user.id}` : "Tizimga kiring")}
                </p>

                <div className="flex items-center gap-2 mt-3">
                  <span className="px-2.5 py-0.5 rounded-full bg-white/10 text-rating-gold text-[11px] font-bold border border-white/10 flex items-center gap-1">
                    <span className="material-symbols-outlined text-[14px]">verified</span>
                    <span>{status === "authenticated" ? "Faol profil" : "Mehmon"}</span>
                  </span>
                  <span className="text-[11px] text-text-secondary">
                    {historyItems.length} ta ko'rilgan
                  </span>
                </div>
              </div>
            </div>

            {/* Quick Action / Login */}
            <div className="flex flex-wrap items-center gap-3">
              {status === "authenticated" ? (
                <button
                  onClick={() => logout()}
                  className="bg-white/10 hover:bg-white/15 text-text-secondary hover:text-white font-semibold px-4 py-2.5 rounded-xl text-xs flex items-center gap-1.5 border border-white/10 transition active:scale-95 cursor-pointer"
                >
                  <span className="material-symbols-outlined text-base">logout</span>
                  <span>Chiqish</span>
                </button>
              ) : (
                <div className="p-2 bg-white/5 rounded-xl border border-white/10">
                  <TelegramLoginWidget />
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Gamified Summary Cards */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4">
          <button
            onClick={() => setActiveTab("history")}
            className="p-4 bg-white/5 hover:bg-white/10 border border-white/10 rounded-2xl flex items-center gap-3.5 transition text-left cursor-pointer"
          >
            <div className="w-10 h-10 rounded-lg bg-white/10 text-sky-400 flex items-center justify-center shrink-0">
              <span className="material-symbols-outlined text-xl">history</span>
            </div>
            <div>
              <div className="text-lg font-black text-white">{historyItems.length}</div>
              <div className="text-[11px] text-text-secondary">Ko'rilgan filmlar</div>
            </div>
          </button>

          <button
            onClick={() => setActiveTab("favorites")}
            className="p-4 bg-white/5 hover:bg-white/10 border border-white/10 rounded-2xl flex items-center gap-3.5 transition text-left cursor-pointer"
          >
            <div className="w-10 h-10 rounded-lg bg-white/10 text-red-400 flex items-center justify-center shrink-0">
              <span className="material-symbols-outlined text-xl">favorite</span>
            </div>
            <div>
              <div className="text-lg font-black text-white">{favorites.length}</div>
              <div className="text-[11px] text-text-secondary">Sevimlilar</div>
            </div>
          </button>

          <button
            onClick={() => setActiveTab("subscriptions")}
            className="p-4 bg-white/5 hover:bg-white/10 border border-white/10 rounded-2xl flex items-center gap-3.5 transition text-left cursor-pointer"
          >
            <div className="w-10 h-10 rounded-lg bg-white/10 text-rating-gold flex items-center justify-center shrink-0">
              <span className="material-symbols-outlined text-xl">loyalty</span>
            </div>
            <div>
              <div className="text-lg font-black text-white">{userSubscriptions.length}</div>
              <div className="text-[11px] text-text-secondary">Obunalar</div>
            </div>
          </button>

          <div className="p-4 bg-white/5 border border-white/10 rounded-2xl flex items-center gap-3.5">
            <div className="w-10 h-10 rounded-lg bg-white/10 text-emerald-400 flex items-center justify-center shrink-0">
              <span className="material-symbols-outlined text-xl">verified</span>
            </div>
            <div>
              <div className="text-lg font-black text-white">{status === "authenticated" ? "VIP" : "Oddiy"}</div>
              <div className="text-[11px] text-text-secondary">Tarif holati</div>
            </div>
          </div>
        </div>

        {/* Profile Tabs Navigation */}
        <div className="bg-white/5 border border-white/10 rounded-2xl overflow-hidden shadow-xl">
          <div className="flex items-center gap-1 p-2 border-b border-white/10 overflow-x-auto hide-scrollbar">
            <button
              onClick={() => setActiveTab("history")}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold transition cursor-pointer whitespace-nowrap ${
                activeTab === "history"
                  ? "bg-white/15 text-white border border-white/20 shadow-sm"
                  : "text-text-secondary hover:text-white"
              }`}
            >
              <span className="material-symbols-outlined text-[18px]">history</span>
              Tomosha tarixi ({historyItems.length})
            </button>

            <button
              onClick={() => setActiveTab("favorites")}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold transition cursor-pointer whitespace-nowrap ${
                activeTab === "favorites"
                  ? "bg-white/15 text-white border border-white/20 shadow-sm"
                  : "text-text-secondary hover:text-white"
              }`}
            >
              <span className="material-symbols-outlined text-[18px]">favorite</span>
              Sevimlilar ({favorites.length})
            </button>

            <button
              onClick={() => setActiveTab("subscriptions")}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold transition cursor-pointer whitespace-nowrap ${
                activeTab === "subscriptions"
                  ? "bg-white/15 text-white border border-white/20 shadow-sm"
                  : "text-text-secondary hover:text-white"
              }`}
            >
              <span className="material-symbols-outlined text-[18px]">loyalty</span>
              Obunalar ({userSubscriptions.length})
            </button>

            <button
              onClick={() => setActiveTab("settings")}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold transition cursor-pointer whitespace-nowrap ${
                activeTab === "settings"
                  ? "bg-white/15 text-white border border-white/20 shadow-sm"
                  : "text-text-secondary hover:text-white"
              }`}
            >
              <span className="material-symbols-outlined text-[18px]">settings</span>
              Sozlamalar
            </button>
          </div>

          {/* TAB 1: WATCH HISTORY */}
          {activeTab === "history" && (
            <div className="p-5 md:p-6 space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-xs font-bold text-text-secondary uppercase tracking-wider">
                  Ko'rilgan filmlar va davom ettirish
                </h2>
                <Link href="/history" className="text-xs text-text-secondary hover:text-white font-semibold transition-colors">
                  Barcha tarix &rarr;
                </Link>
              </div>

              {historyItems.length === 0 ? (
                <div className="py-12 text-center bg-white/5 border border-white/10 rounded-2xl p-6">
                  <span className="material-symbols-outlined text-4xl text-text-secondary mb-2">history</span>
                  <h3 className="text-base font-bold text-white mb-1">Tomosha tarixi bo'sh</h3>
                  <p className="text-xs text-text-secondary max-w-sm mx-auto mb-4">
                    Siz hali hech qanday film yoki serialni tomosha qilmadingiz. Sevimli filmlaringizni katalogdan toping.
                  </p>
                  <Link href="/catalog" className="inline-flex items-center gap-2 px-4 py-2 bg-white/10 hover:bg-white/15 text-xs font-bold text-white rounded-xl border border-white/10 transition">
                    <span>Katalogdan film topish</span>
                    <span className="material-symbols-outlined text-sm">arrow_forward</span>
                  </Link>
                </div>
              ) : (
                <div className="space-y-2.5">
                  {historyItems.map((item) => (
                    <div
                      key={item.id}
                      className="p-3.5 bg-white/5 border border-white/10 rounded-xl flex items-center justify-between gap-4 hover:border-white/20 transition group"
                    >
                      <div className="flex items-center gap-3.5 min-w-0">
                        <div className="w-12 h-16 rounded-lg bg-white/10 overflow-hidden relative shrink-0">
                          {item.poster_url ? (
                            <Image
                              src={item.poster_url}
                              alt={item.title}
                              fill
                              unoptimized
                              className="object-cover"
                            />
                          ) : (
                            <div className="w-full h-full flex items-center justify-center text-white/30">
                              <span className="material-symbols-outlined text-lg">movie</span>
                            </div>
                          )}
                        </div>

                        <div className="min-w-0">
                          <h4 className="text-xs font-bold text-white group-hover:text-white truncate mb-1">
                            {item.title}
                          </h4>
                          <div className="flex items-center gap-2">
                            <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                              item.statusBadge === "completed"
                                ? "bg-emerald-500/20 text-emerald-400"
                                : "bg-rating-gold/20 text-rating-gold"
                            }`}>
                              {item.statusBadge === "completed" ? "Tugallangan" : "Ko'rilmoqda"}
                            </span>
                            {item.isSeries && (
                              <span className="text-[10px] text-text-secondary">Serial</span>
                            )}
                          </div>
                        </div>
                      </div>

                      <Link
                        href={item.href || "/movies"}
                        className="shrink-0 bg-white/15 hover:bg-white/25 text-white font-bold px-3 py-1.5 rounded-lg text-xs flex items-center gap-1.5 border border-white/20 transition active:scale-95"
                      >
                        <span className="material-symbols-outlined text-sm">play_arrow</span>
                        <span className="hidden sm:inline">Tomosha qilish</span>
                      </Link>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* TAB 2: FAVORITES */}
          {activeTab === "favorites" && (
            <div className="p-5 md:p-6 space-y-4">
              <h2 className="text-xs font-bold text-text-secondary uppercase tracking-wider">
                Saqlab qo'yilgan filmlar va seriallar
              </h2>
              {favorites.length === 0 ? (
                <div className="py-12 text-center bg-white/5 border border-white/10 rounded-2xl p-6">
                  <span className="material-symbols-outlined text-4xl text-text-secondary mb-2">favorite</span>
                  <h3 className="text-base font-bold text-white mb-1">Sevimlilar ro'yxati bo'sh</h3>
                  <p className="text-xs text-text-secondary max-w-sm mx-auto mb-4">
                    O'zingizga yoqqan kinolarni "+ Sevimlilarga" tugmasi orqali saqlab qo'yishingiz mumkin.
                  </p>
                  <Link href="/catalog" className="inline-flex items-center gap-2 px-4 py-2 bg-white/10 hover:bg-white/15 text-xs font-bold text-white rounded-xl border border-white/10 transition">
                    <span>Katalogga o'tish</span>
                    <span className="material-symbols-outlined text-sm">arrow_forward</span>
                  </Link>
                </div>
              ) : (
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  {favorites.map((fav, idx) => (
                    <Link
                      key={idx}
                      href={fav.href || "/movies"}
                      className="p-3 bg-white/5 border border-white/10 rounded-xl hover:border-white/20 transition group"
                    >
                      <h4 className="text-xs font-bold text-white group-hover:text-white truncate">{fav.title}</h4>
                    </Link>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* TAB 3: COMPLETE SUBSCRIPTIONS MANAGEMENT (DIRECTLY IN PROFILE) */}
          {activeTab === "subscriptions" && (
            <div className="p-5 md:p-6 space-y-6">
              {/* Header + Sub-filter pills */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-white/10 pb-4">
                <div>
                  <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                    <span className="material-symbols-outlined text-rating-gold text-lg">loyalty</span>
                    <span>Kuzatilayotgan Franshizalar va Seriallar ({userSubscriptions.length})</span>
                  </h2>
                  <p className="text-xs text-text-secondary mt-0.5">
                    Yangi qism chiqarilganda Telegram botingizga poster va video havolasi bilan xabar yuboriladi.
                  </p>
                </div>

                {/* Sub-filter tabs */}
                <div className="flex items-center gap-1 bg-white/5 p-1 rounded-xl border border-white/10 self-start sm:self-auto">
                  <button
                    onClick={() => setSubFilter("all")}
                    className={`px-3 py-1 rounded-lg text-xs font-bold transition cursor-pointer ${
                      subFilter === "all"
                        ? "bg-white/15 text-white border border-white/20"
                        : "text-text-secondary hover:text-white"
                    }`}
                  >
                    Barchasi ({userSubscriptions.length})
                  </button>
                  <button
                    onClick={() => setSubFilter("series")}
                    className={`px-3 py-1 rounded-lg text-xs font-bold transition cursor-pointer ${
                      subFilter === "series"
                        ? "bg-white/15 text-white border border-white/20"
                        : "text-text-secondary hover:text-white"
                    }`}
                  >
                    Seriallar ({seriesCount})
                  </button>
                  <button
                    onClick={() => setSubFilter("franchise")}
                    className={`px-3 py-1 rounded-lg text-xs font-bold transition cursor-pointer ${
                      subFilter === "franchise"
                        ? "bg-white/15 text-white border border-white/20"
                        : "text-text-secondary hover:text-white"
                    }`}
                  >
                    Franshizalar ({franchiseCount})
                  </button>
                </div>
              </div>

              {/* Active Subscriptions List */}
              {status !== "authenticated" ? (
                <div className="py-8 text-center bg-white/5 border border-white/10 rounded-2xl p-6 space-y-3">
                  <span className="material-symbols-outlined text-4xl text-rating-gold">account_circle</span>
                  <h3 className="text-base font-bold text-white">Obunalarni boshqarish uchun kiring</h3>
                  <p className="text-xs text-text-secondary max-w-sm mx-auto">
                    Telegram orqali tizimga kirsangiz, barcha obunalaringiz bu yerda ko'rinadi va boshqariladi.
                  </p>
                  <div className="flex justify-center pt-2">
                    <TelegramLoginWidget />
                  </div>
                </div>
              ) : filteredSubscriptions.length === 0 ? (
                <div className="py-10 text-center bg-white/5 border border-white/10 rounded-2xl p-6">
                  <span className="material-symbols-outlined text-4xl text-text-secondary mb-2">notifications_off</span>
                  <h3 className="text-base font-bold text-white mb-1">
                    {subFilter === "all" ? "Faol obunalar mavjud emas" : `${subFilter === "series" ? "Serial" : "Franshiza"} obunalari yo'q`}
                  </h3>
                  <p className="text-xs text-text-secondary max-w-sm mx-auto mb-4">
                    Quyidagi tavsiya etiladigan to'plamlar yoki seriallarga bir bosishda obuna bo'lishingiz mumkin.
                  </p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {filteredSubscriptions.map((sub) => (
                    <div
                      key={`${sub.type}-${sub.id}`}
                      className="p-4 bg-white/5 border border-white/10 rounded-2xl flex flex-col justify-between hover:border-white/20 transition group"
                    >
                      <div className="flex items-start gap-3.5 mb-3">
                        <div className="w-16 h-22 rounded-xl bg-white/10 overflow-hidden relative shrink-0 border border-white/10">
                          {sub.poster_url ? (
                            <Image
                              src={sub.poster_url}
                              alt={sub.title}
                              fill
                              unoptimized
                              className="object-cover group-hover:scale-105 transition-transform duration-300"
                            />
                          ) : (
                            <div className="w-full h-full flex items-center justify-center text-white/30">
                              <span className="material-symbols-outlined text-2xl">
                                {sub.type === "series" ? "live_tv" : "movie"}
                              </span>
                            </div>
                          )}
                        </div>

                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-1.5 mb-1">
                            <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded uppercase tracking-wider ${
                              sub.type === "series"
                                ? "bg-purple-500/20 text-purple-300 border border-purple-500/30"
                                : "bg-primary-container/20 text-primary-container border border-primary-container/30"
                            }`}>
                              {sub.type === "series" ? "Serial" : "Franshiza"}
                            </span>
                            <span className="inline-flex items-center gap-1 text-[10px] text-emerald-400 font-medium">
                              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                              <span>Faol obuna</span>
                            </span>
                          </div>

                          <h3 className="text-sm font-bold text-white line-clamp-1 mb-1">
                            {sub.title}
                          </h3>
                          <p className="text-xs text-text-secondary line-clamp-2">
                            {sub.description}
                          </p>
                        </div>
                      </div>

                      {/* Card Action Buttons: Qismlarga o'tish (NO 404!) & Obunani bekor qilish */}
                      <div className="pt-3 border-t border-white/10 flex items-center justify-between gap-2">
                        <Link
                          href={sub.href}
                          className="bg-primary-container hover:bg-inverse-primary text-white font-bold px-3.5 py-1.5 rounded-xl text-xs flex items-center gap-1.5 transition active:scale-95 shadow-sm"
                        >
                          <span className="material-symbols-outlined text-sm">play_arrow</span>
                          <span>Qismlarni ko'rish</span>
                        </Link>

                        <button
                          onClick={() => handleUnsubscribe(sub)}
                          disabled={unsubscribingId === sub.id}
                          className="text-xs text-red-400 hover:text-red-300 hover:bg-red-500/10 px-3 py-1.5 rounded-xl border border-red-500/20 transition cursor-pointer font-medium disabled:opacity-50 flex items-center gap-1"
                        >
                          <span className="material-symbols-outlined text-sm">notifications_off</span>
                          <span>{unsubscribingId === sub.id ? "Bekor qilinmoqda..." : "Bekor qilish"}</span>
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Recommended Franchises directly in the profile tab */}
              {recommendations.length > 0 && (
                <div className="pt-6 border-t border-white/10 space-y-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-xs font-bold text-text-secondary uppercase tracking-wider">
                        Tavsiya etiladigan franshizalar
                      </h3>
                      <p className="text-[11px] text-text-secondary">Yangi qismlarni o'tkazib yubormaslik uchun obuna bo'ling</p>
                    </div>
                    <Link href="/collections" className="text-xs text-text-secondary hover:text-white font-semibold">
                      Barchasi &rarr;
                    </Link>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                    {recommendations.map((rec) => (
                      <div
                        key={rec.id}
                        className="p-3.5 bg-white/5 border border-white/10 rounded-xl flex flex-col justify-between hover:border-white/20 transition"
                      >
                        <div className="flex items-start gap-3 mb-2.5">
                          <div className="w-12 h-16 rounded-lg bg-white/10 overflow-hidden relative shrink-0 border border-white/10">
                            {rec.poster_url ? (
                              <Image
                                src={rec.poster_url}
                                alt={rec.name}
                                fill
                                unoptimized
                                className="object-cover"
                              />
                            ) : (
                              <div className="w-full h-full flex items-center justify-center text-white/30">
                                <span className="material-symbols-outlined text-lg">movie</span>
                              </div>
                            )}
                          </div>
                          <div className="min-w-0 flex-1">
                            <span className="text-[10px] text-text-secondary font-bold uppercase tracking-wider block">
                              {rec.items_count || 0} ta qism
                            </span>
                            <h4 className="text-xs font-bold text-white truncate mb-0.5">{rec.name}</h4>
                            <p className="text-[11px] text-text-secondary line-clamp-1">{rec.description || "Franshiza xronologiyasi"}</p>
                          </div>
                        </div>

                        <div className="pt-2.5 border-t border-white/5 flex items-center justify-between gap-2">
                          <Link
                            href={`/collections/${rec.slug}`}
                            className="text-[11px] text-text-secondary hover:text-white transition font-semibold"
                          >
                            Xronologiya &rarr;
                          </Link>

                          <SubscribeButton
                            targetType="collection"
                            targetId={rec.id}
                            title={rec.name}
                            className="px-2.5 py-1 rounded-lg text-[11px] font-bold transition-all cursor-pointer flex items-center gap-1 bg-red-600 hover:bg-red-700 text-white"
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* TAB 4: SETTINGS */}
          {activeTab === "settings" && (
            <div className="p-5 md:p-6 space-y-4">
              <h2 className="text-xs font-bold text-text-secondary uppercase tracking-wider">
                Profil sozlamalari
              </h2>
              <div className="p-4 bg-white/5 border border-white/10 rounded-xl flex items-center justify-between">
                <div>
                  <div className="text-xs font-bold text-white">Bildirishnomalar</div>
                  <div className="text-[11px] text-text-secondary">Yangi kinolar va seriallar haqida xabar olish</div>
                </div>
                <span className="text-xs text-emerald-400 font-bold">Yoqilgan</span>
              </div>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}

export default function ProfilePage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen pt-24 text-center text-text-secondary">
        <span className="material-symbols-outlined animate-spin text-2xl text-primary">sync</span>
      </div>
    }>
      <ProfileContent />
    </Suspense>
  );
}
