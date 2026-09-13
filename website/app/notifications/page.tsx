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
        // Read persisted read notification IDs from localStorage
        let readIds = new Set<string>();
        try {
          const saved = localStorage.getItem("kinochi_read_notification_ids");
          if (saved) {
            readIds = new Set(JSON.parse(saved));
          }
        } catch (e) {
          console.error("Failed to load read notifications from localStorage:", e);
        }

        // 1. Fetch system broadcasts / announcements
        try {
          const bData = await fetchApi("/broadcasts?limit=5");
          if (bData && bData.items) {
            bData.items.forEach((b: any) => {
              const id = `sys-${b.id}`;
              list.push({
                id,
                type: "system",
                title: "Tizim Yangiligi",
                message: b.message_text,
                created_at: b.created_at || new Date().toISOString(),
                is_read: readIds.has(id),
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
            const hData = await getHistory(0, 15);
            const historyItems: HistoryItem[] = hData.items || [];

            // Deduplicate: only generate 1 notification per unique movie and 1 per unique series!
            const seenMovies = new Set<number>();
            const seenSeries = new Set<number>();

            for (const h of historyItems) {
              if (h.type === "movie" && h.movie) {
                if (!seenMovies.has(h.movie.id)) {
                  seenMovies.add(h.movie.id);
                  const id = `rec-m-${h.movie.id}`;
                  list.push({
                    id,
                    type: "personal",
                    title: `"${h.movie.title}" filmiga o'xshash tavsiyalar`,
                    message: `Siz yaqinda ushbu filmni ko'rdingiz. Sizga yoqishi mumkin bo'lgan shunga o'xshash saralangan kinolarni ko'rishni tavsiya qilamiz.`,
                    target_url: `/movie/${h.movie.code}`,
                    created_at: h.last_watched_at,
                    is_read: readIds.has(id),
                    icon: "movie",
                  });
                }
              } else if (h.type === "episode" && h.episode) {
                const sId = h.episode.series_id;
                if (sId && !seenSeries.has(sId)) {
                  seenSeries.add(sId);
                  const id = `rec-s-${sId}`;
                  list.push({
                    id,
                    type: "personal",
                    title: `"${h.episode.series_title}" serialini davom ettirish`,
                    message: `Siz ${h.episode.season_number}-fasl, ${h.episode.episode_number}-qismni tomosha qildingiz. Serialni davom ettirish uchun bosing!`,
                    target_url: `/series/${sId}`,
                    created_at: h.last_watched_at,
                    is_read: readIds.has(id),
                    icon: "live_tv",
                  });
                }
              }
            }
          } catch (err) {
            console.error("Error loading personal alerts:", err);
          }
        }

        // 3. Fallback welcome notification if list is empty
        if (list.length === 0) {
          const id = "sys-welcome";
          list.push({
            id,
            type: "system",
            title: "Kinochi platformasiga xush kelibsiz!",
            message: "Eng sara kinolar, seriallar, anime va doramalarni eng yuqori sifatda tomosha qiling.",
            target_url: "/",
            created_at: new Date().toISOString(),
            is_read: readIds.has(id),
            icon: "star",
          });
        }

        setNotifications(list);

        // Synchronize unread status with localStorage
        const hasUnread = list.some((n) => !n.is_read);
        try {
          localStorage.setItem("kinochi_has_unread", hasUnread ? "true" : "false");
          window.dispatchEvent(new Event("kinochi_notifications_updated"));
        } catch (e) {}
      } finally {
        setLoading(false);
      }
    }

    loadNotifications();
  }, [status]);

  const markAllAsRead = () => {
    setNotifications((prev) => {
      const updated = prev.map((n) => ({ ...n, is_read: true }));
      try {
        const allIds = updated.map((n) => n.id);
        localStorage.setItem("kinochi_read_notification_ids", JSON.stringify(allIds));
        localStorage.setItem("kinochi_has_unread", "false");
        window.dispatchEvent(new Event("kinochi_notifications_updated"));
      } catch (err) {
        console.error("Failed to save read notifications:", err);
      }
      return updated;
    });
  };

  const markItemAsRead = (id: string) => {
    setNotifications((prev) => {
      const updated = prev.map((n) => (n.id === id ? { ...n, is_read: true } : n));
      try {
        const saved: string[] = JSON.parse(localStorage.getItem("kinochi_read_notification_ids") || "[]");
        if (!saved.includes(id)) {
          saved.push(id);
          localStorage.setItem("kinochi_read_notification_ids", JSON.stringify(saved));
        }
        const hasUnread = updated.some((n) => !n.is_read);
        localStorage.setItem("kinochi_has_unread", hasUnread ? "true" : "false");
        window.dispatchEvent(new Event("kinochi_notifications_updated"));
      } catch (err) {
        console.error("Failed to mark notification as read:", err);
      }
      return updated;
    });
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
            <h1 className="text-2xl sm:text-3xl md:text-4xl font-display-hero font-bold text-white flex items-center gap-3">
              <span className="material-symbols-outlined text-3xl sm:text-4xl text-white/90">notifications</span>
              <span>Bildirishnomalar</span>
              {unreadCount > 0 && (
                <span className="inline-flex items-center gap-1.5 text-xs bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 font-bold px-3 py-1 rounded-full">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                  <span>{unreadCount} ta yangi</span>
                </span>
              )}
            </h1>
            <p className="text-text-secondary text-sm mt-1">
              Siz yoqtirgan janrlar bo'yicha yangi kinolar va muhim e'lonlar
            </p>
          </div>

          {unreadCount > 0 && (
            <button
              onClick={markAllAsRead}
              className="text-xs text-text-secondary hover:text-white font-medium flex items-center gap-1.5 py-2 px-3.5 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 transition-all self-start sm:self-auto cursor-pointer"
            >
              <span className="material-symbols-outlined text-[16px]">done_all</span>
              <span>Barchasini o'qilgan deb belgilash</span>
            </button>
          )}
        </div>

        {/* Filter Tabs */}
        <div className="flex gap-2 pb-4 mb-6 overflow-x-auto hide-scrollbar">
          <button
            onClick={() => setActiveTab("all")}
            className={`px-4 sm:px-5 py-2.5 rounded-xl text-xs sm:text-sm font-semibold transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5 active:scale-95 shrink-0 flex items-center gap-2 border cursor-pointer ${
              activeTab === "all"
                ? "bg-white/20 text-white border-white/30 shadow-lg shadow-black/20 font-bold backdrop-blur-md"
                : "bg-white/5 border-white/10 text-text-secondary hover:text-text-primary hover:bg-white/10"
            }`}
          >
            <span>Barchasi ({notifications.length})</span>
          </button>
          <button
            onClick={() => setActiveTab("personal")}
            className={`px-4 sm:px-5 py-2.5 rounded-xl text-xs sm:text-sm font-semibold transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5 active:scale-95 shrink-0 flex items-center gap-2 border cursor-pointer ${
              activeTab === "personal"
                ? "bg-white/20 text-white border-white/30 shadow-lg shadow-black/20 font-bold backdrop-blur-md"
                : "bg-white/5 border-white/10 text-text-secondary hover:text-text-primary hover:bg-white/10"
            }`}
          >
            <span className="material-symbols-outlined text-[18px] text-sky-400">person</span>
            <span>Shaxsiy tavsiyalar ({notifications.filter((n) => n.type === "personal").length})</span>
          </button>
          <button
            onClick={() => setActiveTab("system")}
            className={`px-4 sm:px-5 py-2.5 rounded-xl text-xs sm:text-sm font-semibold transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5 active:scale-95 shrink-0 flex items-center gap-2 border cursor-pointer ${
              activeTab === "system"
                ? "bg-white/20 text-white border-white/30 shadow-lg shadow-black/20 font-bold backdrop-blur-md"
                : "bg-white/5 border-white/10 text-text-secondary hover:text-text-primary hover:bg-white/10"
            }`}
          >
            <span className="material-symbols-outlined text-[18px] text-amber-400">campaign</span>
            <span>Tizim yangiliklari ({notifications.filter((n) => n.type === "system").length})</span>
          </button>
        </div>

        {/* Content */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-white/40"></div>
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
                onClick={() => markItemAsRead(item.id)}
                className={`rounded-2xl p-4 md:p-5 border transition-all duration-200 flex items-start gap-4 cursor-pointer hover:scale-[1.005] ${
                  item.is_read
                    ? "bg-white/[0.02] border-white/5 opacity-75 hover:opacity-100 hover:border-white/15"
                    : "bg-white/[0.06] border-white/20 shadow-xl shadow-black/25 hover:border-white/30"
                }`}
              >
                <div
                  className={`w-11 h-11 rounded-xl shrink-0 flex items-center justify-center border ${
                    item.type === "personal"
                      ? "bg-sky-500/15 border-sky-500/25 text-sky-400"
                      : "bg-amber-400/15 border-amber-400/25 text-amber-400"
                  }`}
                >
                  <span className="material-symbols-outlined text-[24px]">{item.icon}</span>
                </div>

                <div className="flex-grow min-w-0">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 mb-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <h4 className="font-bold text-base text-white">{item.title}</h4>
                      {!item.is_read && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/15 border border-emerald-500/30 text-emerald-400">
                          Yangi
                        </span>
                      )}
                    </div>
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
                      onClick={() => markItemAsRead(item.id)}
                      className="inline-flex items-center gap-1.5 text-xs font-semibold text-text-primary hover:text-white bg-white/10 hover:bg-white/15 border border-white/10 hover:border-white/25 px-3 py-1.5 rounded-xl transition-all"
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
