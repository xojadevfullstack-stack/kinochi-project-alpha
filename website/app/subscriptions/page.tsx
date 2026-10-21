"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import Image from "next/image";
import BackButton from "@/components/BackButton";
import { fetchApi } from "@/lib/api";
import { useAuth } from "@/lib/auth/AuthProvider";
import TelegramLoginWidget from "@/components/auth/TelegramLoginWidget";
import SubscribeButton from "@/components/SubscribeButton";

interface SubscriptionItem {
  id: number;
  type: "franchise" | "series";
  title: string;
  poster_url?: string | null;
  banner_url?: string | null;
  slug?: string;
  itemCount?: number;
  description?: string;
  created_at?: string | null;
}

interface CollectionRecommendation {
  id: number;
  name: string;
  slug: string;
  description?: string | null;
  poster_url?: string | null;
  items_count?: number;
}

export default function SubscriptionsPage() {
  const { user, status } = useAuth();
  const [subscriptions, setSubscriptions] = useState<SubscriptionItem[]>([]);
  const [recommendations, setRecommendations] = useState<CollectionRecommendation[]>([]);
  const [activeTab, setActiveTab] = useState<"all" | "franchise" | "series">("all");
  const [loading, setLoading] = useState(true);
  const [unsubscribingId, setUnsubscribingId] = useState<number | null>(null);

  const loadSubscriptions = useCallback(async () => {
    if (status !== "authenticated") {
      setSubscriptions([]);
      setLoading(false);
      return;
    }

    try {
      const data = await fetchApi("/users/me/subscriptions");
      const mapped: SubscriptionItem[] = [];

      // 1. Series
      if (Array.isArray(data?.series)) {
        data.series.forEach((s: any) => {
          mapped.push({
            id: s.id,
            type: "series",
            title: s.title,
            poster_url: s.poster_url,
            slug: String(s.id),
            description: `${s.release_year ? s.release_year + ' • ' : ''}IMDb: ${s.imdb_rating || 'N/A'}`,
            created_at: s.created_at,
          });
        });
      }

      // 2. Collections
      if (Array.isArray(data?.collections)) {
        data.collections.forEach((c: any) => {
          mapped.push({
            id: c.id,
            type: "franchise",
            title: c.name,
            poster_url: c.poster_url,
            banner_url: c.banner_url,
            slug: c.slug,
            itemCount: c.item_count,
            description: c.description || "Franshiza xronologiyasi",
            created_at: c.created_at,
          });
        });
      }

      setSubscriptions(mapped);
    } catch (e) {
      console.warn("Failed to load user subscriptions:", e);
    } finally {
      setLoading(false);
    }
  }, [status]);

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
    loadSubscriptions();
    loadRecommendations();

    const handleSync = () => loadSubscriptions();
    window.addEventListener("subscription:change", handleSync);
    return () => window.removeEventListener("subscription:change", handleSync);
  }, [loadSubscriptions, loadRecommendations]);

  const handleUnsubscribe = async (item: SubscriptionItem) => {
    if (!user?.telegram_id) return;
    setUnsubscribingId(item.id);
    try {
      const endpoint =
        item.type === "series"
          ? `/series/${item.id}/subscribe`
          : `/collections/${item.id}/subscribe`;

      await fetchApi(endpoint, {
        method: "POST",
        body: JSON.stringify({ telegram_user_id: user.telegram_id }),
      });

      setSubscriptions((prev) => prev.filter((s) => !(s.id === item.id && s.type === item.type)));
      window.dispatchEvent(new Event("subscription:change"));
    } catch (err: any) {
      alert("Obunani bekor qilishda xatolik: " + err.message);
    } finally {
      setUnsubscribingId(null);
    }
  };

  const filtered = subscriptions.filter((sub) => {
    if (activeTab === "all") return true;
    return sub.type === activeTab;
  });

  const seriesCount = subscriptions.filter((s) => s.type === "series").length;
  const franchiseCount = subscriptions.filter((s) => s.type === "franchise").length;

  return (
    <div className="min-h-screen pt-20 sm:pt-24 pb-28 xl:pb-16 px-4 md:px-8 bg-background-obsidian text-text-primary">
      <div className="max-w-5xl mx-auto space-y-6">
        
        {/* Header Bar */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-white/10">
          <div className="flex items-center gap-3">
            <BackButton fallbackUrl="/" />
            <div>
              <h1 className="text-xl sm:text-2xl font-black text-text-primary font-headline-md tracking-tight flex items-center gap-2">
                <span className="material-symbols-outlined text-rating-gold text-2xl">loyalty</span>
                <span>Mening Obunalarim</span>
              </h1>
              <p className="text-xs text-text-secondary mt-0.5">
                Siz obuna bo'lgan seriallar, film olamlari va franshizalar yangilanishlari
              </p>
            </div>
          </div>

          {/* Type Filter Tabs */}
          <div className="flex items-center gap-1.5 bg-white/5 p-1 rounded-xl border border-white/10 self-start sm:self-auto">
            <button
              onClick={() => setActiveTab("all")}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                activeTab === "all"
                  ? "bg-white/15 text-white font-bold border border-white/20 shadow-sm"
                  : "text-text-secondary hover:text-white"
              }`}
            >
              Barchasi ({subscriptions.length})
            </button>
            <button
              onClick={() => setActiveTab("franchise")}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                activeTab === "franchise"
                  ? "bg-white/15 text-white font-bold border border-white/20 shadow-sm"
                  : "text-text-secondary hover:text-white"
              }`}
            >
              Franshizalar ({franchiseCount})
            </button>
            <button
              onClick={() => setActiveTab("series")}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                activeTab === "series"
                  ? "bg-white/15 text-white font-bold border border-white/20 shadow-sm"
                  : "text-text-secondary hover:text-white"
              }`}
            >
              Seriallar ({seriesCount})
            </button>
          </div>
        </div>

        {/* Guest Warning Banner if not authenticated */}
        {status !== "authenticated" && (
          <div className="bg-gradient-to-r from-red-950/40 via-surface-container-high/60 to-black/60 border border-white/10 rounded-2xl p-5 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-3 text-center sm:text-left">
              <div className="w-10 h-10 rounded-xl bg-red-600/20 text-red-400 flex items-center justify-center shrink-0 mx-auto sm:mx-0">
                <span className="material-symbols-outlined text-2xl">account_circle</span>
              </div>
              <div>
                <h3 className="text-sm font-bold text-white">Shaxsiy obunalaringizni ko'rish uchun kiring</h3>
                <p className="text-xs text-text-secondary">Telegram botingizdagi barcha faol obunalar bu yerda avtomatik sinxronlanadi.</p>
              </div>
            </div>
            <div className="shrink-0">
              <TelegramLoginWidget />
            </div>
          </div>
        )}

        {/* Subscribed Items Grid */}
        {loading ? (
          <div className="py-16 text-center text-text-secondary text-sm flex flex-col items-center gap-2">
            <span className="material-symbols-outlined animate-spin text-2xl text-rating-gold">sync</span>
            <span>Obunalar yuklanmoqda...</span>
          </div>
        ) : filtered.length > 0 ? (
          <div className="space-y-4">
            <div className="text-xs font-bold text-text-secondary uppercase tracking-wider flex items-center justify-between">
              <span>Faol obunalar ({filtered.length} ta)</span>
              <span className="text-[11px] text-text-secondary lowercase font-normal">
                Yangi qism chiqqanda Telegram botingizga xabar yuboriladi
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {filtered.map((item) => (
                <div
                  key={`${item.type}-${item.id}`}
                  className="bg-white/5 border border-white/10 rounded-2xl p-4 flex flex-col justify-between hover:border-white/20 transition-all group"
                >
                  <div className="flex items-start gap-3.5 mb-3">
                    <div className="w-16 h-22 rounded-xl bg-white/10 overflow-hidden relative shrink-0 border border-white/10">
                      {item.poster_url ? (
                        <Image
                          src={item.poster_url}
                          alt={item.title}
                          fill
                          unoptimized
                          className="object-cover group-hover:scale-105 transition-transform duration-300"
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center text-white/30">
                          <span className="material-symbols-outlined text-2xl">
                            {item.type === "series" ? "live_tv" : "movie"}
                          </span>
                        </div>
                      )}
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-1.5 mb-1">
                        <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded uppercase tracking-wider ${
                          item.type === "series"
                            ? "bg-purple-500/20 text-purple-300 border border-purple-500/30"
                            : "bg-primary-container/20 text-primary-container border border-primary-container/30"
                        }`}>
                          {item.type === "series" ? "Serial" : "Franshiza"}
                        </span>
                        <span className="inline-flex items-center gap-1 text-[10px] text-emerald-400 font-medium">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                          <span>Faol</span>
                        </span>
                      </div>
                      <h3 className="text-sm font-bold text-white line-clamp-1 mb-1">
                        {item.title}
                      </h3>
                      <p className="text-xs text-text-secondary line-clamp-2 leading-relaxed">
                        {item.description || "Yangi qismlar chiqarilganda bot xabar beradi."}
                      </p>
                    </div>
                  </div>

                  <div className="pt-3 border-t border-white/5 flex items-center justify-between">
                    <Link
                      href={item.type === "series" ? `/series/${item.id}` : `/collections/${item.slug}`}
                      className="text-xs font-bold text-text-secondary hover:text-white transition-colors flex items-center gap-1"
                    >
                      <span>Ko'rish</span>
                      <span className="material-symbols-outlined text-sm">chevron_right</span>
                    </Link>

                    <button
                      onClick={() => handleUnsubscribe(item)}
                      disabled={unsubscribingId === item.id}
                      className="text-xs text-red-400 hover:text-red-300 hover:bg-red-500/10 px-2.5 py-1 rounded-lg border border-red-500/20 transition cursor-pointer font-medium disabled:opacity-50"
                    >
                      {unsubscribingId === item.id ? "Bekor qilinmoqda..." : "Bekor qilish"}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="text-center py-12 bg-white/5 border border-white/10 rounded-2xl p-6">
            <span className="material-symbols-outlined text-4xl text-text-secondary mb-2">
              notifications_off
            </span>
            <h3 className="text-base font-bold text-white mb-1">
              Sizda hozircha obunalar mavjud emas
            </h3>
            <p className="text-xs text-text-secondary max-w-sm mx-auto mb-4">
              O'zingiz yoqtirgan franshiza yoki seriallarga obuna bo'lsangiz, yangi qismlar chiqqanda Telegram botingizga avtomatik xabar boradi.
            </p>
          </div>
        )}

        {/* Recommended Franchises / Series to Subscribe */}
        {recommendations.length > 0 && (
          <div className="pt-6 border-t border-white/10 space-y-4">
            <div className="text-xs font-bold text-text-secondary uppercase tracking-wider flex items-center justify-between">
              <span>Tavsiya etiladigan franshizalar</span>
              <Link href="/collections" className="text-xs text-text-secondary hover:text-white lowercase font-semibold">
                Barcha to'plamlar &rarr;
              </Link>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {recommendations.map((rec) => (
                <div
                  key={rec.id}
                  className="bg-white/5 border border-white/10 rounded-2xl p-4 flex flex-col justify-between hover:border-white/20 transition-all"
                >
                  <div className="flex items-start gap-3.5 mb-3">
                    <div className="w-16 h-22 rounded-xl bg-white/10 overflow-hidden relative shrink-0 border border-white/10">
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
                          <span className="material-symbols-outlined text-2xl">movie</span>
                        </div>
                      )}
                    </div>

                    <div className="flex-1 min-w-0">
                      <span className="text-[10px] text-text-secondary font-bold uppercase tracking-wider block mb-1">
                        {rec.items_count || 0} ta qism
                      </span>
                      <h3 className="text-sm font-bold text-white line-clamp-1 mb-1">
                        {rec.name}
                      </h3>
                      <p className="text-xs text-text-secondary line-clamp-2">
                        {rec.description || "Franshiza va filmlar xronologiyasi"}
                      </p>
                    </div>
                  </div>

                  <div className="pt-3 border-t border-white/5 flex items-center justify-between gap-2">
                    <Link
                      href={`/collections/${rec.slug}`}
                      className="text-xs font-bold text-text-secondary hover:text-white transition-colors flex items-center gap-1"
                    >
                      <span>Xronologiya</span>
                      <span className="material-symbols-outlined text-sm">arrow_forward</span>
                    </Link>

                    <SubscribeButton
                      targetType="collection"
                      targetId={rec.id}
                      title={rec.name}
                      className="px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer flex items-center gap-1 bg-red-600 hover:bg-red-700 text-white"
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
