"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth/AuthProvider";
import { getHistory, HistoryItem } from "@/lib/api/history";
import { fetchApi } from "@/lib/api";
import Link from "next/link";

interface NotificationItem {
  id: string;
  type: "personal" | "system" | "release";
  title: string;
  message: string;
  target_url?: string;
  created_at: string;
  is_read: boolean;
  icon: string;
}

export default function NotificationsPage() {
  const { status } = useAuth();
  const [activeTab, setActiveTab] = useState<"all" | "personal" | "system">("all");
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadNotifications() {
      setLoading(true);
      const list: NotificationItem[] = [];

      try {
        // 1. Fetch system broadcasts / announcements
        try {
          const bData = await fetchApi("/broadcasts?limit=5");
          if (bData && bData.items) {
            bData.items.forEach((b: any) => {
              list.push({
                id: `sys-${b.id}`,
                type: "system",
                title: "📢 Tizim Yangiligi",
                message: b.message_text,
                created_at: b.created_at || new Date().toISOString(),
                is_read: false,
                icon: "campaign",
              });
            });
          }
        } catch (err) {
          // If unauthenticated or no broadcasts, continue
        }

        // 2. Fetch personal watch history to generate tailored notifications
        if (status === "authenticated") {
          try {
            const hData = await getHistory(0, 10);
            const historyItems: HistoryItem[] = hData.items || [];

            // Personal alerts based on watched series/movies
            historyItems.forEach((h, idx) => {
              if (h.type === "movie" && h.movie) {
                list.push({
                  id: `rec-m-${h.movie.id}-${idx}`,
                  type: "personal",
                  title: `🎬 "${h.movie.title}" filmiga o'xshash premyeralar!`,
                  message: `Siz yaqinda ushbu filmni tomosha qildingiz. Xuddi shu janrdagi yangi saralangan kinolarni ko'rishni tavsiya qilamiz.`,
                  target_url: `/movie/${h.movie.code}`,
                  created_at: h.last_watched_at,
                  is_read: idx > 1,
                  icon: "movie",
                });
              } else if (h.type === "episode" && h.episode) {
                list.push({
                  id: `rec-e-${h.episode.id}-${idx}`,
                  type: "personal",
                  title: `📺 "${h.episode.series_title}" serialida yangi qismlar!`,
                  message: `Siz ${h.episode.season_number}-faslni ko'rmoqdasiz. Davom ettirish uchun bosing!`,
                  target_url: `/series/${h.episode.series_id}`,
                  created_at: h.last_watched_at,
                  is_read: false,
                  icon: "live_tv",
                });
              }
            });
          } catch (err) {
            console.error("Error loading personal alerts:", err);
          }
        }

        // 3. Fallback welcome notification if list is empty
        if (list.length === 0) {
          list.push({
            id: "sys-welcome",
            type: "system",
            title: "🎉 Kinochi platformasiga xush kelibsiz!",
            message: "Eng sara kinolar, seriallar, anime va doramalarni eng yuqori sifatda tomosha qiling.",
            target_url: "/",
            created_at: new Date().toISOString(),
            is_read: false,
            icon: "star",
          });
        }

        setNotifications(list);
      } finally {
        setLoading(false);
      }
    }

    loadNotifications();
  }, [status]);

  const markAllAsRead = () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
  };

  const filtered = notifications.filter((n) => {
    if (activeTab === "personal") return n.type === "personal";
    if (activeTab === "system") return n.type === "system";
    return true;
  });

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  return (
    <div className="min-h-screen bg-background-obsidian pt-24 pb-20">
      <div className="max-w-container-max mx-auto px-gutter">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
          <div>
            <h1 className="text-3xl md:text-4xl font-display-hero font-bold text-white flex items-center gap-3">
              <span className="material-symbols-outlined text-4xl text-primary-container">notifications</span>
              Bildirishnomalar
              {unreadCount > 0 && (
                <span className="text-xs bg-primary-container text-on-primary-container font-bold px-2.5 py-1 rounded-full">
                  {unreadCount} ta yangi
                </span>
              )}
            </h1>
            <p className="text-text-secondary mt-1">
              Siz yoqtirgan janrlar bo'yicha yangi kinolar va muhim e'lonlar
            </p>
          </div>

          {unreadCount > 0 && (
            <button
              onClick={markAllAsRead}
              className="text-xs text-primary-container hover:text-primary-container/80 font-semibold flex items-center gap-1 self-start sm:self-auto transition-colors"
            >
              <span className="material-symbols-outlined text-[16px]">done_all</span>
              Barchasini o'qilgan deb belgilash
            </button>
          )}
        </div>

        {/* Filter Tabs */}
        <div className="flex gap-2 border-b border-white/10 pb-4 mb-6 overflow-x-auto">
          <button
            onClick={() => setActiveTab("all")}
            className={`px-4 py-2 rounded-xl text-sm font-semibold transition-all ${
              activeTab === "all"
                ? "bg-primary-container text-on-primary-container"
                : "bg-surface-container/60 text-text-secondary hover:text-white"
            }`}
          >
            Barchasi ({notifications.length})
          </button>
          <button
            onClick={() => setActiveTab("personal")}
            className={`px-4 py-2 rounded-xl text-sm font-semibold transition-all flex items-center gap-1.5 ${
              activeTab === "personal"
                ? "bg-primary-container text-on-primary-container"
                : "bg-surface-container/60 text-text-secondary hover:text-white"
            }`}
          >
            <span className="material-symbols-outlined text-[16px]">person</span>
            Shaxsiy tavsiyalar ({notifications.filter((n) => n.type === "personal").length})
          </button>
          <button
            onClick={() => setActiveTab("system")}
            className={`px-4 py-2 rounded-xl text-sm font-semibold transition-all flex items-center gap-1.5 ${
              activeTab === "system"
                ? "bg-primary-container text-on-primary-container"
                : "bg-surface-container/60 text-text-secondary hover:text-white"
            }`}
          >
            <span className="material-symbols-outlined text-[16px]">campaign</span>
            Tizim yangiliklari ({notifications.filter((n) => n.type === "system").length})
          </button>
        </div>

        {/* Content */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-primary-container"></div>
          </div>
        ) : filtered.length === 0 ? (
          <div className="text-center py-20 bg-surface-container/20 rounded-3xl border border-white/5 p-8">
            <span className="material-symbols-outlined text-6xl text-text-secondary mb-3">notifications_off</span>
            <h3 className="text-lg font-bold text-white mb-1">Hozircha xabarlar yo'q</h3>
            <p className="text-sm text-text-secondary">
              Yangi filmlar va seriallar qo'shilganda shu yerda xabardor qilamiz.
            </p>
          </div>
        ) : (
          <div className="flex flex-col gap-3">
            {filtered.map((item) => (
              <div
                key={item.id}
                className={`rounded-2xl p-4 md:p-5 border transition-all flex items-start gap-4 ${
                  item.is_read
                    ? "bg-surface-container/30 border-white/5 opacity-75"
                    : "bg-surface-container/80 border-primary-container/30 shadow-lg shadow-primary-container/5"
                }`}
              >
                <div
                  className={`w-11 h-11 rounded-xl shrink-0 flex items-center justify-center ${
                    item.type === "personal"
                      ? "bg-primary-container/20 text-primary-container"
                      : "bg-amber-400/20 text-amber-400"
                  }`}
                >
                  <span className="material-symbols-outlined text-[24px]">{item.icon}</span>
                </div>

                <div className="flex-grow">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 mb-1">
                    <h4 className="font-bold text-base text-white">{item.title}</h4>
                    <span className="text-[11px] text-text-secondary shrink-0">
                      {new Date(item.created_at).toLocaleDateString("uz-UZ", {
                        day: "numeric",
                        month: "short",
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </span>
                  </div>
                  <p className="text-sm text-text-secondary leading-relaxed mb-3">{item.message}</p>

                  {item.target_url && (
                    <Link
                      href={item.target_url}
                      className="inline-flex items-center gap-1.5 text-xs font-semibold text-primary-container hover:text-primary-container/80 transition-colors"
                    >
                      <span>Tomosha qilish</span>
                      <span className="material-symbols-outlined text-[14px]">arrow_forward</span>
                    </Link>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
