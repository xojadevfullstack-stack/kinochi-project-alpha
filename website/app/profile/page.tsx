"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth/AuthProvider";
import { fetchApi } from "@/lib/api";
import Link from "next/link";
import TelegramLoginWidget from "@/components/auth/TelegramLoginWidget";
import BackButton from "@/components/BackButton";
import ThemeToggle from "@/components/ThemeToggle";

interface HistoryProgress {
  id: string | number;
  title: string;
  poster_url?: string;
  currentTime: number;
  duration: number;
  updatedAt: number;
  href: string;
  isSeries?: boolean;
}

export default function ProfilePage() {
  const { status, user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState<"history" | "favorites" | "notifications" | "subscription">("history");
  const [historyItems, setHistoryItems] = useState<HistoryProgress[]>([]);
  const [notifications, setNotifications] = useState<any[]>([]);
  const [favorites, setFavorites] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // 1. Load saved playback history from localStorage
    try {
      const storedHistory = localStorage.getItem("kinochi_video_progress_list");
      if (storedHistory) {
        setHistoryItems(JSON.parse(storedHistory));
      } else {
        // Fallback demo/mock history items if empty so user immediately experiences the UX
        setHistoryItems([
          {
            id: 101,
            title: "Qashqirlar Makoni: Pistirma",
            currentTime: 2800,
            duration: 3600,
            updatedAt: Date.now() - 3600000,
            href: "/series/1",
            isSeries: true
          },
          {
            id: 102,
            title: "Interstellar (Yulduzlararo)",
            currentTime: 4500,
            duration: 9000,
            updatedAt: Date.now() - 86400000,
            href: "/movies",
            isSeries: false
          }
        ]);
      }
    } catch {}

    // 2. Fetch notifications/broadcasts
    const loadBroadcasts = async () => {
      try {
        const res: any = await fetchApi("/broadcasts/public?limit=6");
        if (res && Array.isArray(res.items)) {
          setNotifications(res.items);
        }
      } catch {
        setNotifications([
          { id: 1, title: "Xush kelibsiz!", message: "MediaPlus platformasiga xush kelibsiz. Eng so'nggi premyeralarni tomosha qiling.", created_at: "Bugun" },
          { id: 2, title: "Yangi serial qo'shildi", message: "Qashqirlar Makoni yangi qismlari yuklandi.", created_at: "Kecha" }
        ]);
      } finally {
        setLoading(false);
      }
    };

    // 3. Load favorites
    try {
      const savedFavs = localStorage.getItem("kinochi_favorites");
      if (savedFavs) {
        setFavorites(JSON.parse(savedFavs));
      }
    } catch {}

    loadBroadcasts();
  }, []);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const hrs = Math.floor(mins / 60);
    if (hrs > 0) {
      return `${hrs} soat ${mins % 60} daqiqa`;
    }
    return `${mins} daqiqa`;
  };

  return (
    <div className="min-h-screen pt-24 pb-28 xl:pb-16 px-4 md:px-8 bg-background-obsidian text-text-primary">
      <div className="max-w-5xl mx-auto space-y-6">
        
        {/* Top Bar with Back Button & Theme Toggle */}
        <div className="flex items-center justify-between">
          <BackButton />
          <div className="flex items-center gap-2">
            <ThemeToggle />
          </div>
        </div>

        {/* User Card Banner */}
        <div className="relative rounded-2xl bg-gradient-to-r from-surface-container via-surface-container-high to-surface-container border border-white/10 p-6 md:p-8 shadow-2xl overflow-hidden">
          <div className="absolute -top-16 -right-16 w-64 h-64 bg-primary-container/15 rounded-full blur-3xl pointer-events-none"></div>

          <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div className="flex items-center gap-4 sm:gap-5">
              {/* Avatar */}
              <div className="relative">
                <div className="w-16 h-16 sm:w-20 sm:h-20 rounded-2xl bg-gradient-to-tr from-primary-container to-rating-gold p-0.5 shadow-xl">
                  <div className="w-full h-full bg-background-obsidian rounded-2xl flex items-center justify-center text-xl sm:text-2xl font-black text-white font-headline-md">
                    {user?.first_name?.charAt(0) || "U"}
                  </div>
                </div>
                <span className="absolute -bottom-1 -right-1 w-5 h-5 bg-primary-container border-2 border-surface-container rounded-full flex items-center justify-center text-[10px]" title="VIP Obuna">
                  👑
                </span>
              </div>

              {/* User Details */}
              <div>
                <div className="flex items-center gap-2">
                  <h1 className="text-xl sm:text-2xl font-black text-text-primary font-headline-md tracking-tight">
                    {user ? `${user.first_name || ""} ${user.last_name || ""}`.trim() : "Mehmon Foydalanuvchi"}
                  </h1>
                  <span className="px-2 py-0.5 rounded-full bg-rating-gold/20 text-rating-gold border border-rating-gold/30 text-[10px] font-bold">
                    {status === "authenticated" ? "VIP STATUS" : "Oddiy"}
                  </span>
                </div>
                <p className="text-xs text-text-secondary mt-0.5">
                  {user?.username ? `@${user.username}` : `ID: #${user?.id || "mehmon"}`}
                </p>
                <div className="flex items-center gap-2 mt-2">
                  <span className="text-[11px] bg-white/5 border border-white/10 text-text-secondary px-2.5 py-0.5 rounded-md">
                    Obuna holati: <b className="text-rating-gold">{status === "authenticated" ? "Faol (Cheksiz)" : "Sinov rejimi"}</b>
                  </span>
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-2 sm:gap-3">
              {status === "authenticated" ? (
                <>
                  <Link
                    href="/achievements"
                    className="bg-primary-container hover:bg-inverse-primary text-white font-bold px-4 py-2.5 rounded-xl text-xs flex items-center gap-1.5 shadow-lg shadow-black/40 transition active:scale-95"
                  >
                    <span className="material-symbols-outlined text-[18px]">military_tech</span>
                    Yutuqlarim
                  </Link>
                  <button
                    onClick={() => logout()}
                    className="bg-white/5 hover:bg-red-500/20 text-text-secondary hover:text-red-400 border border-white/10 px-3.5 py-2.5 rounded-xl text-xs font-semibold transition active:scale-95 flex items-center gap-1"
                  >
                    <span className="material-symbols-outlined text-[18px]">logout</span>
                    Chiqish
                  </button>
                </>
              ) : (
                <div className="w-full sm:w-auto">
                  <TelegramLoginWidget />
                </div>
              )}
            </div>
          </div>
        </div>

        {/* UX Stats Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4">
          <div className="bg-surface-container border border-white/10 rounded-xl p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-primary-container/15 text-primary-container flex items-center justify-center shrink-0">
              <span className="material-symbols-outlined text-xl">play_circle</span>
            </div>
            <div>
              <div className="text-lg font-black text-white font-headline-md">{historyItems.length} ta</div>
              <div className="text-[11px] text-text-secondary">Ko'rilgan kinolar</div>
            </div>
          </div>

          <div className="bg-surface-container border border-white/10 rounded-xl p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-red-500/15 text-red-400 flex items-center justify-center shrink-0">
              <span className="material-symbols-outlined text-xl">favorite</span>
            </div>
            <div>
              <div className="text-lg font-black text-white font-headline-md">{favorites.length} ta</div>
              <div className="text-[11px] text-text-secondary">Sevimlilarim</div>
            </div>
          </div>

          <div className="bg-surface-container border border-white/10 rounded-xl p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-rating-gold/15 text-rating-gold flex items-center justify-center shrink-0">
              <span className="material-symbols-outlined text-xl">military_tech</span>
            </div>
            <div>
              <div className="text-lg font-black text-white font-headline-md">6 ta</div>
              <div className="text-[11px] text-text-secondary">Yutuqlar (Badjlar)</div>
            </div>
          </div>

          <div className="bg-surface-container border border-white/10 rounded-xl p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-sky-500/15 text-sky-400 flex items-center justify-center shrink-0">
              <span className="material-symbols-outlined text-xl">schedule</span>
            </div>
            <div>
              <div className="text-lg font-black text-white font-headline-md">84 soat</div>
              <div className="text-[11px] text-text-secondary">Tomosha vaqti</div>
            </div>
          </div>
        </div>

        {/* Profile Tabs & Content */}
        <div className="bg-surface-container border border-white/10 rounded-2xl overflow-hidden shadow-xl">
          {/* Tabs Navigation */}
          <div className="flex items-center border-b border-white/10 px-4 bg-surface-container-high overflow-x-auto text-xs font-bold hide-scrollbar">
            <button
              onClick={() => setActiveTab("history")}
              className={`py-3.5 px-4 flex items-center gap-1.5 whitespace-nowrap transition-colors border-b-2 ${
                activeTab === "history"
                  ? "border-primary-container text-primary-container font-extrabold"
                  : "border-transparent text-text-secondary hover:text-text-primary"
              }`}
            >
              <span className="material-symbols-outlined text-[18px]">history</span>
              Tomosha tarixi ({historyItems.length})
            </button>

            <button
              onClick={() => setActiveTab("favorites")}
              className={`py-3.5 px-4 flex items-center gap-1.5 whitespace-nowrap transition-colors border-b-2 ${
                activeTab === "favorites"
                  ? "border-primary-container text-primary-container font-extrabold"
                  : "border-transparent text-text-secondary hover:text-text-primary"
              }`}
            >
              <span className="material-symbols-outlined text-[18px]">favorite</span>
              Sevimlilar ({favorites.length})
            </button>

            <button
              onClick={() => setActiveTab("notifications")}
              className={`py-3.5 px-4 flex items-center gap-1.5 whitespace-nowrap transition-colors border-b-2 ${
                activeTab === "notifications"
                  ? "border-primary-container text-primary-container font-extrabold"
                  : "border-transparent text-text-secondary hover:text-text-primary"
              }`}
            >
              <span className="material-symbols-outlined text-[18px]">notifications</span>
              Habarlar
              {notifications.length > 0 && (
                <span className="px-1.5 py-0.2 bg-primary-container text-white text-[9px] rounded-full">
                  {notifications.length}
                </span>
              )}
            </button>

            <button
              onClick={() => setActiveTab("subscription")}
              className={`py-3.5 px-4 flex items-center gap-1.5 whitespace-nowrap transition-colors border-b-2 ${
                activeTab === "subscription"
                  ? "border-primary-container text-primary-container font-extrabold"
                  : "border-transparent text-text-secondary hover:text-text-primary"
              }`}
            >
              <span className="material-symbols-outlined text-[18px]">card_membership</span>
              Obuna & Sozlamalar
            </button>
          </div>

          {/* TAB 1: HISTORY (DAVOM ETTIRISH) */}
          {activeTab === "history" && (
            <div className="p-5 md:p-6 space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-xs font-bold text-text-secondary uppercase tracking-wider">
                  Oxirgi to'xtatilgan joyidan davom ettirish
                </h2>
                <Link href="/history" className="text-xs text-primary-container hover:underline font-bold">
                  Barcha tarix &rarr;
                </Link>
              </div>

              {historyItems.length === 0 ? (
                <div className="py-12 text-center text-text-secondary">
                  <span className="material-symbols-outlined text-4xl mb-2 opacity-30">movie</span>
                  <p className="text-sm">Hali hech qanday film tomosha qilinmagan.</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {historyItems.map((item, idx) => {
                    const percent = Math.min(100, Math.round((item.currentTime / (item.duration || 1)) * 100)) || 65;
                    return (
                      <div
                        key={idx}
                        className="p-3.5 bg-surface-container-high border border-white/5 hover:border-white/20 rounded-xl flex items-center justify-between gap-4 transition"
                      >
                        <div className="flex items-center gap-3.5 min-w-0">
                          <div className="w-12 h-14 bg-surface-container rounded-lg flex items-center justify-center text-zinc-600 shrink-0 border border-white/5">
                            <span className="material-symbols-outlined text-2xl text-primary-container">play_arrow</span>
                          </div>
                          <div className="min-w-0">
                            <h3 className="text-xs sm:text-sm font-bold text-text-primary truncate">
                              {item.title}
                            </h3>
                            <p className="text-[11px] text-text-secondary mt-0.5">
                              {formatTime(item.currentTime)} ko'rildi ({percent}%)
                            </p>
                            <div className="w-32 sm:w-48 h-1.5 bg-white/10 rounded-full mt-1.5 overflow-hidden">
                              <div className="h-full bg-primary-container rounded-full" style={{ width: `${percent}%` }}></div>
                            </div>
                          </div>
                        </div>

                        <Link
                          href={item.href || "/movies"}
                          className="shrink-0 bg-primary-container hover:bg-inverse-primary text-white font-bold px-3 py-1.5 rounded-lg text-xs flex items-center gap-1 shadow transition active:scale-95"
                        >
                          <span className="material-symbols-outlined text-sm icon-fill">play_arrow</span>
                          <span className="hidden sm:inline">Davom ettirish</span>
                        </Link>
                      </div>
                    );
                  })}
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
                <div className="py-12 text-center text-text-secondary">
                  <span className="material-symbols-outlined text-4xl mb-2 text-red-500/40">favorite</span>
                  <p className="text-sm">Sevimlilar ro'yxati hozircha bo'sh.</p>
                  <Link href="/catalog" className="inline-block mt-3 px-4 py-2 bg-white/5 hover:bg-white/10 text-xs font-bold text-white rounded-xl border border-white/10">
                    Katalogdan film topish
                  </Link>
                </div>
              ) : (
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
                  {favorites.map((fav, i) => (
                    <div key={i} className="bg-surface-container-high border border-white/5 rounded-xl p-2.5">
                      <div className="aspect-[2/3] bg-surface-container rounded-lg flex items-center justify-center text-zinc-600">
                        <span className="material-symbols-outlined text-3xl">movie</span>
                      </div>
                      <div className="mt-2 text-xs font-bold text-white truncate">{fav.title}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* TAB 3: NOTIFICATIONS */}
          {activeTab === "notifications" && (
            <div className="p-5 md:p-6 space-y-3">
              <div className="flex items-center justify-between">
                <h2 className="text-xs font-bold text-text-secondary uppercase tracking-wider">
                  Platforma xabarlari va yangiliklar
                </h2>
                <Link href="/notifications" className="text-xs text-primary-container hover:underline font-bold">
                  Barcha xabarlar &rarr;
                </Link>
              </div>

              {notifications.map((n, i) => (
                <div key={i} className="p-3.5 bg-surface-container-high border border-white/5 rounded-xl flex items-start gap-3">
                  <div className="w-8 h-8 rounded-lg bg-primary-container/15 text-primary-container flex items-center justify-center shrink-0 mt-0.5">
                    <span className="material-symbols-outlined text-base">notifications</span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <h4 className="text-xs font-bold text-text-primary">{n.title}</h4>
                      <span className="text-[10px] text-text-secondary">{n.created_at || "Yangi"}</span>
                    </div>
                    <p className="text-xs text-text-secondary mt-1 leading-relaxed">{n.message || n.text}</p>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* TAB 4: SUBSCRIPTION & SETTINGS */}
          {activeTab === "subscription" && (
            <div className="p-5 md:p-6 space-y-6">
              <div className="p-4 bg-surface-container-high border border-white/10 rounded-xl space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-bold text-white flex items-center gap-2">
                      <span className="material-symbols-outlined text-rating-gold">verified</span>
                      VIP Premium Tarif
                    </h3>
                    <p className="text-xs text-text-secondary mt-0.5">
                      Barcha kinolarni reklamasiz va to'liq 4K sifatda tomosha qilish
                    </p>
                  </div>
                  <span className="px-2.5 py-1 bg-primary-container text-white text-xs font-black rounded-lg">
                    FAOL
                  </span>
                </div>
                <div className="pt-2 border-t border-white/10 flex items-center justify-between text-xs text-text-secondary">
                  <span>Telegram Bot orqali boshqaruv:</span>
                  <a
                    href="https://t.me/kinochi_uz_bot"
                    target="_blank"
                    rel="noreferrer"
                    className="text-primary-container hover:underline font-bold flex items-center gap-1"
                  >
                    <span>@kinochi_uz_bot</span>
                    <span className="material-symbols-outlined text-xs">open_in_new</span>
                  </a>
                </div>
              </div>

              {/* Theme & Preferences */}
              <div className="p-4 bg-surface-container-high border border-white/10 rounded-xl flex items-center justify-between">
                <div>
                  <h4 className="text-xs font-bold text-white">Rejimni sozlash (Dark / Light)</h4>
                  <p className="text-[11px] text-text-secondary">Tungi yoki kunduzgi ranglar palitrasini tanlash</p>
                </div>
                <ThemeToggle />
              </div>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
