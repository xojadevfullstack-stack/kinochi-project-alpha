"use client";

import { useEffect, useState, useMemo } from "react";
import { useAuth } from "@/lib/auth/AuthProvider";
import { fetchApi } from "@/lib/api";
import Link from "next/link";
import TelegramLoginWidget from "@/components/auth/TelegramLoginWidget";

interface Achievement {
  code: string;
  title: string;
  earned_at?: string;
}

const ALL_ACHIEVEMENTS = [
  {
    code: "first_blood",
    title: "Tomoshalarni boshlaganingiz bilan!",
    desc: "1 ta film yoki qismni to'liq tomosha qiling",
    icon: "play_circle",
  },
  {
    code: "ten_movies",
    title: "Kino ixlosmandi",
    desc: "10 ta film yoki qismni to'liq tomosha qiling",
    icon: "movie",
  },
  {
    code: "hundred_club",
    title: "Yuzlar klubi a'zosi",
    desc: "100 ta film yoki qismni to'liq tomosha qiling",
    icon: "stars",
  },
  {
    code: "anime_fan",
    title: "Anime ishqibozi",
    desc: "5 ta anime filmini to'liq tomosha qiling",
    icon: "animation",
  },
  {
    code: "genre_explorer",
    title: "Kashfiyotchi",
    desc: "5 xil janrdagi filmlarni tomosha qiling",
    icon: "explore",
  },
  {
    code: "night_owl",
    title: "Tungi boyqush",
    desc: "Tungi 00:00 dan 04:00 oralig'ida film tomosha qiling",
    icon: "bedtime",
  },
  {
    code: "marathoner",
    title: "Marafonchi",
    desc: "Bir kun ichida 3+ film tomosha qiling",
    icon: "bolt",
  },
  {
    code: "series_finisher",
    title: "Serial yakunlovchi",
    desc: "Serialning barcha qismlarini to'liq tomosha qiling",
    icon: "done_all",
  },
];

function formatAchievementDate(dateStr?: string): string {
  if (!dateStr) return "";
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return "";
  const months = [
    "yanvar", "fevral", "mart", "aprel", "may", "iyun",
    "iyul", "avgust", "sentabr", "oktabr", "noyabr", "dekabr"
  ];
  return `${d.getDate()}-${months[d.getMonth()]}, ${d.getFullYear()}`;
}

function getUserRank(unlocked: number, total: number) {
  if (unlocked === 0) {
    return { title: "Yangi Tomoshabin", desc: "Kinolar ko'rishni boshlang va medallarni to'plang", icon: "explore" };
  }
  if (unlocked <= 2) {
    return { title: "Havaskor Tomoshabin", desc: "Dastlabki yutuqlarga muvaffaqiyatli erishildi", icon: "military_tech" };
  }
  if (unlocked <= 5) {
    return { title: "Kino Ixlosmandi", desc: "Platformada faol va sara filmlar shinavandasi", icon: "stars" };
  }
  if (unlocked < total) {
    return { title: "Kino Eksperti", desc: "Barcha asosiy janr va seriallarni zabt etgan", icon: "workspace_premium" };
  }
  return { title: "MediaPlus Afsonasi", desc: "Barcha yutuqlarni 100% ochgan mutlaq chempion!", icon: "hotel_class" };
}

export default function AchievementsPage() {
  const { status } = useAuth();
  const [unlocked, setUnlocked] = useState<Record<string, Achievement>>({});
  const [filter, setFilter] = useState<"all" | "unlocked" | "locked">("all");

  useEffect(() => {
    if (status === "authenticated") {
      fetchApi("/users/me/achievements")
        .then((res) => {
          const map: Record<string, Achievement> = {};
          (res.items || []).forEach((item: Achievement) => {
            map[item.code] = item;
          });
          setUnlocked(map);
        })
        .catch((err) => {
          console.error("Failed to load achievements:", err);
        });
    }
  }, [status]);

  const unlockedCount = Object.keys(unlocked).length;
  const lockedCount = ALL_ACHIEVEMENTS.length - unlockedCount;
  const progressPercent = Math.round((unlockedCount / ALL_ACHIEVEMENTS.length) * 100);
  const rank = getUserRank(unlockedCount, ALL_ACHIEVEMENTS.length);

  const filteredAchievements = useMemo(() => {
    if (filter === "unlocked") {
      return ALL_ACHIEVEMENTS.filter((item) => !!unlocked[item.code]);
    }
    if (filter === "locked") {
      return ALL_ACHIEVEMENTS.filter((item) => !unlocked[item.code]);
    }
    return ALL_ACHIEVEMENTS;
  }, [filter, unlocked]);

  return (
    <div className="min-h-screen bg-background-obsidian pt-24 sm:pt-28 pb-28">
      <div className="max-w-container-max mx-auto px-gutter">
        {/* Navigation Breadcrumb / Back Button */}
        <div className="mb-4 sm:mb-6">
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-xs sm:text-sm text-text-secondary hover:text-white transition-colors bg-white/[0.04] hover:bg-white/[0.08] px-3.5 py-1.5 rounded-xl border border-white/10"
          >
            <span className="material-symbols-outlined text-[18px]">arrow_back</span>
            <span>Bosh sahifaga</span>
          </Link>
        </div>

        {/* Hero Banner & Stats Card */}
        <div className="relative rounded-3xl p-6 sm:p-8 bg-white/[0.03] backdrop-blur-2xl border border-white/10 mb-8 shadow-2xl overflow-hidden">
          {/* Subtle Ambient Gold Glow */}
          <div className="absolute -top-24 -right-24 w-80 h-80 bg-amber-500/10 rounded-full blur-3xl pointer-events-none" />
          <div className="absolute -bottom-24 -left-24 w-80 h-80 bg-primary-container/10 rounded-full blur-3xl pointer-events-none" />

          <div className="relative z-10">
            {/* Top row: Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 pb-6 border-b border-white/10">
              <div className="flex items-start sm:items-center gap-4">
                <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-amber-400/20 to-amber-500/5 border border-amber-400/30 flex items-center justify-center text-amber-400 shrink-0">
                  <span className="material-symbols-outlined text-[32px]">emoji_events</span>
                </div>
                <div>
                  <h1 className="text-2xl sm:text-3xl font-display-hero font-extrabold text-white tracking-tight">
                    Yutuqlar va Medallar
                  </h1>
                  <p className="text-text-secondary text-xs sm:text-sm mt-1">
                    Kinolar va seriallar tomosha qilib qo'lga kiritilgan shaxsiy unvonlaringiz
                  </p>
                </div>
              </div>

              {/* Quick Badge */}
              <div className="flex items-center gap-2 self-start md:self-auto">
                <div className="px-4 py-2 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-md flex items-center gap-2.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-amber-400 animate-pulse" />
                  <span className="text-xs font-semibold text-text-secondary">
                    Status: <strong className="text-white font-bold">{rank.title}</strong>
                  </span>
                </div>
              </div>
            </div>

            {/* Metrics Row (3 Columns) */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 sm:gap-6 pt-6">
              {/* Metric 1: User Rank */}
              <div className="p-4 rounded-2xl bg-white/[0.02] border border-white/5 flex items-center gap-3.5">
                <div className="w-11 h-11 rounded-xl bg-amber-400/10 border border-amber-400/20 flex items-center justify-center text-amber-400 shrink-0">
                  <span className="material-symbols-outlined text-[24px]">{rank.icon}</span>
                </div>
                <div className="overflow-hidden">
                  <div className="text-xs text-text-secondary font-medium">Darajangiz</div>
                  <div className="text-base font-bold text-white truncate mt-0.5">{rank.title}</div>
                </div>
              </div>

              {/* Metric 2: Count */}
              <div className="p-4 rounded-2xl bg-white/[0.02] border border-white/5 flex items-center gap-3.5">
                <div className="w-11 h-11 rounded-xl bg-emerald-400/10 border border-emerald-400/20 flex items-center justify-center text-emerald-400 shrink-0">
                  <span className="material-symbols-outlined text-[24px]">verified</span>
                </div>
                <div>
                  <div className="text-xs text-text-secondary font-medium">Ochilgan medallar</div>
                  <div className="text-base font-bold text-white mt-0.5">
                    {unlockedCount} / {ALL_ACHIEVEMENTS.length}
                    <span className="text-xs text-text-secondary font-normal ml-2">
                      ({lockedCount} ta qoldi)
                    </span>
                  </div>
                </div>
              </div>

              {/* Metric 3: Progress Percentage with Bar */}
              <div className="p-4 rounded-2xl bg-white/[0.02] border border-white/5 flex flex-col justify-center">
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-xs text-text-secondary font-medium">Umumiy natija</span>
                  <span className="text-sm font-bold text-amber-400">{progressPercent}%</span>
                </div>
                <div className="w-full bg-white/10 rounded-full h-2 overflow-hidden">
                  <div
                    className="bg-gradient-to-r from-amber-400 to-amber-500 h-full rounded-full transition-all duration-700"
                    style={{ width: `${progressPercent}%` }}
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Unauthenticated Login Callout Banner */}
        {status === "unauthenticated" && (
          <div className="mb-8 p-5 sm:p-6 rounded-3xl bg-white/[0.03] border border-white/10 backdrop-blur-xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 shadow-xl">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-2xl bg-amber-400/10 border border-amber-400/20 flex items-center justify-center text-amber-400 shrink-0">
                <span className="material-symbols-outlined text-2xl">lock_open</span>
              </div>
              <div>
                <h3 className="font-bold text-white text-base">Yutuqlaringizni saqlab boring</h3>
                <p className="text-xs sm:text-sm text-text-secondary mt-0.5">
                  Tomosha qilgan kinolaringiz hisoblanishi va medallarni ochish uchun profilingizga kiring.
                </p>
              </div>
            </div>
            <div className="w-full sm:w-auto shrink-0">
              <TelegramLoginWidget />
            </div>
          </div>
        )}

        {/* Segmented Filter Tabs */}
        <div className="flex items-center justify-between flex-wrap gap-4 mb-6 sm:mb-8">
          <div className="flex items-center gap-1.5 p-1.5 bg-white/[0.04] backdrop-blur-xl border border-white/10 rounded-2xl">
            <button
              onClick={() => setFilter("all")}
              className={`px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold transition-all cursor-pointer ${
                filter === "all"
                  ? "bg-white/15 text-white shadow-md border border-white/10"
                  : "text-text-secondary hover:text-white hover:bg-white/5"
              }`}
            >
              Barchasi ({ALL_ACHIEVEMENTS.length})
            </button>
            <button
              onClick={() => setFilter("unlocked")}
              className={`px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold transition-all cursor-pointer flex items-center gap-1.5 ${
                filter === "unlocked"
                  ? "bg-amber-400/20 text-amber-400 shadow-md border border-amber-400/30"
                  : "text-text-secondary hover:text-white hover:bg-white/5"
              }`}
            >
              <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
              Ochilganlar ({unlockedCount})
            </button>
            <button
              onClick={() => setFilter("locked")}
              className={`px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold transition-all cursor-pointer flex items-center gap-1.5 ${
                filter === "locked"
                  ? "bg-white/15 text-white shadow-md border border-white/10"
                  : "text-text-secondary hover:text-white hover:bg-white/5"
              }`}
            >
              <span className="w-1.5 h-1.5 rounded-full bg-zinc-500" />
              Qulflanganlar ({lockedCount})
            </button>
          </div>

          <div className="text-xs text-text-secondary font-medium hidden sm:block">
            Ko'rsatilmoqda: <strong className="text-white">{filteredAchievements.length} ta yutuq</strong>
          </div>
        </div>

        {/* Achievements Grid */}
        {filteredAchievements.length === 0 ? (
          <div className="text-center py-16 px-4 bg-white/[0.02] border border-white/10 rounded-3xl backdrop-blur-xl">
            <div className="w-16 h-16 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center mx-auto mb-4 text-text-secondary">
              <span className="material-symbols-outlined text-3xl">emoji_events</span>
            </div>
            <h3 className="text-lg font-bold text-white mb-1">Hech qanday yutuq topilmadi</h3>
            <p className="text-sm text-text-secondary max-w-sm mx-auto mb-6">
              {filter === "unlocked"
                ? "Siz hali birorta medalni ochmadingiz. Kinolar tomosha qiling va dastlabki medalga ega bo'ling!"
                : "Barcha yutuqlar muvaffaqiyatli ochilgan!"}
            </p>
            <button
              onClick={() => setFilter("all")}
              className="px-5 py-2 rounded-xl bg-white/10 hover:bg-white/20 text-white text-xs font-semibold transition-all cursor-pointer"
            >
              Barcha yutuqlarni ko'rish
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 sm:gap-5">
            {filteredAchievements.map((item) => {
              const isUnlocked = !!unlocked[item.code];
              const earnedDate = unlocked[item.code]?.earned_at;

              return (
                <div
                  key={item.code}
                  className={`relative rounded-3xl p-5 sm:p-6 backdrop-blur-xl transition-all duration-300 flex flex-col justify-between group ${
                    isUnlocked
                      ? "bg-white/[0.035] border border-amber-400/25 hover:border-amber-400/50 hover:bg-white/[0.06] shadow-lg shadow-black/40"
                      : "bg-white/[0.02] border border-white/10 hover:border-white/20 hover:bg-white/[0.04] opacity-75 hover:opacity-100 shadow-sm"
                  }`}
                >
                  <div>
                    {/* Top row: Badge icon + Status Chip */}
                    <div className="flex items-center justify-between mb-5">
                      <div
                        className={`w-13 h-13 rounded-2xl flex items-center justify-center transition-transform group-hover:scale-105 duration-300 ${
                          isUnlocked
                            ? "bg-gradient-to-br from-amber-400/20 via-amber-500/10 to-transparent border border-amber-400/30 text-amber-400 shadow-[0_0_20px_rgba(251,191,36,0.15)]"
                            : "bg-white/5 border border-white/10 text-zinc-500"
                        }`}
                      >
                        <span className="material-symbols-outlined text-[28px]">{item.icon}</span>
                      </div>

                      {isUnlocked ? (
                        <span className="inline-flex items-center gap-1.5 text-[11px] font-bold text-emerald-400 bg-emerald-400/10 border border-emerald-400/20 px-2.5 py-1 rounded-full">
                          <span className="material-symbols-outlined text-[14px]">verified</span>
                          Ochilgan
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-zinc-400 bg-white/5 border border-white/10 px-2.5 py-1 rounded-full">
                          <span className="material-symbols-outlined text-[13px]">lock</span>
                          Qulflangan
                        </span>
                      )}
                    </div>

                    {/* Title & Description */}
                    <h3 className={`font-bold text-base sm:text-lg mb-1.5 transition-colors ${
                      isUnlocked ? "text-white group-hover:text-amber-300" : "text-zinc-300"
                    }`}>
                      {item.title}
                    </h3>
                    <p className="text-xs sm:text-sm text-text-secondary leading-relaxed">
                      {item.desc}
                    </p>
                  </div>

                  {/* Card Footer: Earned Date or Unlock Hint */}
                  <div className={`mt-5 pt-3.5 border-t text-xs flex items-center justify-between ${
                    isUnlocked ? "border-white/10 text-text-secondary" : "border-white/5 text-zinc-500"
                  }`}>
                    {isUnlocked && earnedDate ? (
                      <>
                        <div className="flex items-center gap-1.5 text-text-secondary font-medium">
                          <span className="material-symbols-outlined text-[16px] text-amber-400/80">calendar_today</span>
                          <span>{formatAchievementDate(earnedDate)}</span>
                        </div>
                        <span className="material-symbols-outlined text-emerald-400 text-[18px]">check_circle</span>
                      </>
                    ) : (
                      <div className="flex items-center gap-1.5 text-zinc-500">
                        <span className="material-symbols-outlined text-[15px]">info</span>
                        <span>Tomosha qilib oching</span>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
