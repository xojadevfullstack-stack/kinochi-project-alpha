"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import Image from "next/image";
import BackButton from "@/components/BackButton";
import { fetchApi } from "@/lib/api";

interface SubscriptionItem {
  id: string | number;
  type: "franchise" | "series" | "movie";
  title: string;
  poster_url?: string | null;
  banner_url?: string | null;
  slug?: string;
  itemCount?: number;
  description?: string;
  subscribedAt: number;
}

const POPULAR_RECOMMENDATIONS = [
  {
    id: "marvel-cinematic-universe",
    type: "franchise" as const,
    title: "Marvel Kinematografiya Olami",
    slug: "marvel",
    poster_url: "https://image.tmdb.org/t/p/w500/yF1eOkaYvwiORauRCPWznV9xVvi.jpg",
    itemCount: 33,
    description: "Temir odam, Qasoskorlar va Marvel olamining barcha qismlari xronologik tartibda.",
    subscribedAt: Date.now()
  },
  {
    id: "harry-potter-wizarding-world",
    type: "franchise" as const,
    title: "Garri Potter va Sehrgarlar Olami",
    slug: "garri-potter",
    poster_url: "https://image.tmdb.org/t/p/w500/wuMc08IPKEatf9rnMNXvIDxqP4W.jpg",
    itemCount: 11,
    description: "Xogvarts sehrgarlari, Fantastik maxluqlar va sehrli olam sarguzashtlari.",
    subscribedAt: Date.now()
  },
  {
    id: "fast-furious-saga",
    type: "franchise" as const,
    title: "Forsaj Xronologiyasi",
    slug: "forsaj",
    poster_url: "https://image.tmdb.org/t/p/w500/fiVW06jE7z9YnO4trhaMEdclSiC.jpg",
    itemCount: 11,
    description: "Tezlik va oila qadriyatlari. Dominik Toretto va uning jamoasi poygalari.",
    subscribedAt: Date.now()
  }
];

export default function SubscriptionsPage() {
  const [subscriptions, setSubscriptions] = useState<SubscriptionItem[]>([]);
  const [activeTab, setActiveTab] = useState<"all" | "franchise" | "series">("all");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    try {
      const stored = localStorage.getItem("kinochi_user_subscriptions");
      if (stored) {
        setSubscriptions(JSON.parse(stored));
      } else {
        // Default with 1-2 demo active subscriptions if empty, so user immediately sees how it works
        setSubscriptions([POPULAR_RECOMMENDATIONS[0]]);
        localStorage.setItem("kinochi_user_subscriptions", JSON.stringify([POPULAR_RECOMMENDATIONS[0]]));
      }
    } catch {}
    setLoading(false);
  }, []);

  const handleToggleSub = (item: SubscriptionItem) => {
    setSubscriptions((prev) => {
      const exists = prev.some((sub) => String(sub.id) === String(item.id));
      let next: SubscriptionItem[];
      if (exists) {
        next = prev.filter((sub) => String(sub.id) !== String(item.id));
      } else {
        next = [...prev, { ...item, subscribedAt: Date.now() }];
      }
      try {
        localStorage.setItem("kinochi_user_subscriptions", JSON.stringify(next));
      } catch {}
      return next;
    });
  };

  const isSubscribed = (id: string | number) => {
    return subscriptions.some((sub) => String(sub.id) === String(id));
  };

  const filtered = subscriptions.filter((sub) => {
    if (activeTab === "all") return true;
    return sub.type === activeTab;
  });

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
              Franshizalar
            </button>
            <button
              onClick={() => setActiveTab("series")}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                activeTab === "series"
                  ? "bg-white/15 text-white font-bold border border-white/20 shadow-sm"
                  : "text-text-secondary hover:text-white"
              }`}
            >
              Seriallar
            </button>
          </div>
        </div>

        {/* Subscribed Items Grid */}
        {filtered.length > 0 ? (
          <div className="space-y-4">
            <div className="text-xs font-bold text-text-secondary uppercase tracking-wider flex items-center justify-between">
              <span>Faol obunalar ({filtered.length} ta)</span>
              <span className="text-[11px] text-text-secondary lowercase font-normal">
                Yangi qism chiqqanda bildirishnoma yuboriladi
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {filtered.map((item) => (
                <div
                  key={item.id}
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
                          <span className="material-symbols-outlined text-2xl">movie</span>
                        </div>
                      )}
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="inline-flex items-center gap-1 text-[10px] text-rating-gold font-bold uppercase tracking-wider mb-1">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                        <span>Kuzatilmoqda</span>
                      </div>
                      <h3 className="text-sm font-bold text-white line-clamp-1 mb-1">
                        {item.title}
                      </h3>
                      <p className="text-xs text-text-secondary line-clamp-2 leading-relaxed">
                        {item.description || "Ushbu to'plamga obuna bo'lingan."}
                      </p>
                    </div>
                  </div>

                  <div className="pt-3 border-t border-white/5 flex items-center justify-between">
                    <Link
                      href={item.slug ? `/collections/${item.slug}` : `/collections`}
                      className="text-xs font-bold text-text-secondary hover:text-white transition-colors flex items-center gap-1"
                    >
                      <span>Qismlarni ko'rish</span>
                      <span className="material-symbols-outlined text-sm">chevron_right</span>
                    </Link>

                    <button
                      onClick={() => handleToggleSub(item)}
                      className="text-xs text-red-400 hover:text-red-300 hover:bg-red-500/10 px-2.5 py-1 rounded-lg border border-red-500/20 transition cursor-pointer font-medium"
                    >
                      Bekor qilish
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
              O'zingiz yoqtirgan franshiza yoki seriallarga obuna bo'lsangiz, yangi qismlar chiqqanda xabardor bo'lasiz.
            </p>
          </div>
        )}

        {/* Recommended Franchises / Series to Subscribe */}
        <div className="pt-6 border-t border-white/10 space-y-4">
          <div className="text-xs font-bold text-text-secondary uppercase tracking-wider flex items-center justify-between">
            <span>Tavsiya etiladigan franshizalar</span>
            <Link href="/collections" className="text-xs text-text-secondary hover:text-white lowercase font-semibold">
              Barcha to'plamlar &rarr;
            </Link>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {POPULAR_RECOMMENDATIONS.map((rec) => {
              const subbed = isSubscribed(rec.id);
              return (
                <div
                  key={rec.id}
                  className="bg-white/5 border border-white/10 rounded-2xl p-4 flex flex-col justify-between hover:border-white/20 transition-all"
                >
                  <div className="flex items-start gap-3.5 mb-3">
                    <div className="w-16 h-22 rounded-xl bg-white/10 overflow-hidden relative shrink-0 border border-white/10">
                      <Image
                        src={rec.poster_url}
                        alt={rec.title}
                        fill
                        unoptimized
                        className="object-cover"
                      />
                    </div>

                    <div className="flex-1 min-w-0">
                      <span className="text-[10px] text-text-secondary font-bold uppercase tracking-wider block mb-1">
                        {rec.itemCount} ta qism
                      </span>
                      <h3 className="text-sm font-bold text-white line-clamp-1 mb-1">
                        {rec.title}
                      </h3>
                      <p className="text-xs text-text-secondary line-clamp-2">
                        {rec.description}
                      </p>
                    </div>
                  </div>

                  <div className="pt-3 border-t border-white/5 flex items-center justify-between">
                    <Link
                      href={`/collections/${rec.slug}`}
                      className="text-xs font-bold text-text-secondary hover:text-white transition-colors flex items-center gap-1"
                    >
                      <span>Xronologiya</span>
                      <span className="material-symbols-outlined text-sm">arrow_forward</span>
                    </Link>

                    <button
                      onClick={() => handleToggleSub(rec)}
                      className={`text-xs px-3 py-1.5 rounded-lg border font-bold transition-all cursor-pointer flex items-center gap-1 ${
                        subbed
                          ? "bg-white/15 text-white border-white/25"
                          : "bg-primary-container hover:bg-inverse-primary text-white border-primary-container shadow-sm"
                      }`}
                    >
                      <span className="material-symbols-outlined text-sm">
                        {subbed ? "check" : "add"}
                      </span>
                      <span>{subbed ? "Obuna bo'lingan" : "Obuna bo'lish"}</span>
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

      </div>
    </div>
  );
}
