"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth/AuthProvider";
import { fetchApi } from "@/lib/api";
import { getHistory, HistoryItem } from "@/lib/api/history";
import Link from "next/link";
import TelegramLoginWidget from "@/components/auth/TelegramLoginWidget";
import BackButton from "@/components/BackButton";

interface UnifiedHistoryItem {
  id: string | number;
  title: string;
  poster_url?: string | null;
  href: string;
  isSeries?: boolean;
  statusBadge: "in_progress" | "completed";
  lastWatchedAt?: string;
}

export default function ProfilePage() {
  const { status, user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState<"history" | "favorites" | "subscriptions" | "settings">("history");
  const [historyItems, setHistoryItems] = useState<UnifiedHistoryItem[]>([]);
  const [notifications, setNotifications] = useState<any[]>([]);
  const [favorites, setFavorites] = useState<any[]>([]);
  const [userSubscriptions, setUserSubscriptions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // 1. Fetch real watch history from API when authenticated
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
          } else {
            // Check localStorage fallback
            try {
              const storedHistory = localStorage.getItem("kinochi_video_progress_list");
              if (storedHistory) {
                setHistoryItems(JSON.parse(storedHistory));
              }
            } catch {}
          }
        })
        .catch(() => {
          try {
            const storedHistory = localStorage.getItem("kinochi_video_progress_list");
            if (storedHistory) {
              setHistoryItems(JSON.parse(storedHistory));
            }
          } catch {}
        });
    } else {
      // LocalStorage for guest / unauthenticated
      try {
        const storedHistory = localStorage.getItem("kinochi_video_progress_list");
        if (storedHistory) {
          setHistoryItems(JSON.parse(storedHistory));
        }
      } catch {}
    }

    // 2. Fetch notifications/broadcasts
    const loadBroadcasts = async () => {
      try {
        const res: any = await fetchApi("/broadcasts/public?limit=6");
        if (res && Array.isArray(res.items)) {
          setNotifications(res.items);
        }
      } catch {
        setNotifications([]);
      } finally {
        setLoading(false);
      }
    };

    // 3. Load favorites and followed subscriptions
    try {
      const savedFavs = localStorage.getItem("kinochi_favorites");
      if (savedFavs) {
        setFavorites(JSON.parse(savedFavs));
      }
      const savedSubs = localStorage.getItem("kinochi_user_subscriptions");
      if (savedSubs) {
        setUserSubscriptions(JSON.parse(savedSubs));
      }
    } catch {}

    loadBroadcasts();
  }, [status]);

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

        {/* Gamified Watch Summary Cards */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4">
          <div className="p-4 bg-white/5 border border-white/10 rounded-2xl flex items-center gap-3.5">
            <div className="w-10 h-10 rounded-lg bg-white/10 text-sky-400 flex items-center justify-center shrink-0">
              <span className="material-symbols-outlined text-xl">history</span>
            </div>
            <div>
              <div className="text-lg font-black text-white">{historyItems.length}</div>
              <div className="text-[11px] text-text-secondary">Ko'rilgan filmlar</div>
            </div>
          </div>

          <div className="p-4 bg-white/5 border border-white/10 rounded-2xl flex items-center gap-3.5">
            <div className="w-10 h-10 rounded-lg bg-white/10 text-red-400 flex items-center justify-center shrink-0">
              <span className="material-symbols-outlined text-xl">favorite</span>
            </div>
            <div>
              <div className="text-lg font-black text-white">{favorites.length}</div>
              <div className="text-[11px] text-text-secondary">Sevimlilar</div>
            </div>
          </div>

          <div className="p-4 bg-white/5 border border-white/10 rounded-2xl flex items-center gap-3.5">
            <div className="w-10 h-10 rounded-lg bg-white/10 text-rating-gold flex items-center justify-center shrink-0">
              <span className="material-symbols-outlined text-xl">loyalty</span>
            </div>
            <div>
              <div className="text-lg font-black text-white">{userSubscriptions.length}</div>
              <div className="text-[11px] text-text-secondary">Obunalar</div>
            </div>
          </div>

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

          {/* TAB 1: REAL WATCH HISTORY */}
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
                <div className="space-y-3">
                  {historyItems.map((item, idx) => (
                    <div
                      key={idx}
                      className="p-3.5 bg-white/5 border border-white/10 hover:border-white/20 rounded-xl flex items-center justify-between gap-4 transition"
                    >
                      <div className="flex items-center gap-3.5 min-w-0">
                        <div className="w-12 h-16 bg-white/10 rounded-lg overflow-hidden shrink-0 border border-white/10 relative flex items-center justify-center text-white/30">
                          {item.poster_url ? (
                            <img
                              src={item.poster_url}
                              alt={item.title}
                              className="w-full h-full object-cover"
                            />
                          ) : (
                            <span className="material-symbols-outlined text-2xl">movie</span>
                          )}
                        </div>
                        <div className="min-w-0">
                          <h3 className="text-xs sm:text-sm font-bold text-white truncate">
                            {item.title}
                          </h3>
                          <div className="flex items-center gap-2 mt-1">
                            <span className="text-[10px] px-2 py-0.5 rounded bg-white/10 text-rating-gold font-bold uppercase">
                              {item.statusBadge === "in_progress" ? "Davom etmoqda" : "Ko'rilgan"}
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

          {/* TAB 3: USER SUBSCRIPTIONS (Followed content) */}
          {activeTab === "subscriptions" && (
            <div className="p-5 md:p-6 space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-xs font-bold text-text-secondary uppercase tracking-wider">
                  Kuzatilayotgan franshizalar va seriallar
                </h2>
                <Link href="/subscriptions" className="text-xs text-text-secondary hover:text-white font-semibold transition-colors">
                  To'liq obunalar sahifasi &rarr;
                </Link>
              </div>

              {userSubscriptions.length === 0 ? (
                <div className="py-12 text-center bg-white/5 border border-white/10 rounded-2xl p-6">
                  <span className="material-symbols-outlined text-4xl text-text-secondary mb-2">loyalty</span>
                  <h3 className="text-base font-bold text-white mb-1">Obunalar mavjud emas</h3>
                  <p className="text-xs text-text-secondary max-w-sm mx-auto mb-4">
                    O'zingiz yoqtirgan franshizalarga obuna bo'lsangiz, yangi qismlar chiqqanda xabardor bo'lasiz.
                  </p>
                  <Link href="/subscriptions" className="inline-flex items-center gap-2 px-4 py-2 bg-white/10 hover:bg-white/15 text-xs font-bold text-white rounded-xl border border-white/10 transition">
                    <span>Franshizalarni ko'rish</span>
                    <span className="material-symbols-outlined text-sm">arrow_forward</span>
                  </Link>
                </div>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {userSubscriptions.map((sub, idx) => (
                    <div key={idx} className="p-4 bg-white/5 border border-white/10 rounded-xl flex items-center justify-between">
                      <div>
                        <h4 className="text-xs font-bold text-white">{sub.title}</h4>
                        <span className="text-[10px] text-text-secondary">{sub.itemCount || 10} ta qism</span>
                      </div>
                      <Link href={sub.slug ? `/collections/${sub.slug}` : "/collections"} className="text-xs text-text-secondary hover:text-white font-semibold">
                        Qismlar &rarr;
                      </Link>
                    </div>
                  ))}
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
