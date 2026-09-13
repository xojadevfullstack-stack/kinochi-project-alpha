"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth/AuthProvider";
import { fetchApi } from "@/lib/api";
import Link from "next/link";

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

export default function AchievementsPage() {
  const { status, loginDirect } = useAuth();
  const [unlocked, setUnlocked] = useState<Record<string, Achievement>>({});

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
  const progressPercent = Math.round((unlockedCount / ALL_ACHIEVEMENTS.length) * 100);

  return (
    <div className="min-h-screen bg-background-obsidian pt-24 sm:pt-28 pb-24">
      <div className="max-w-container-max mx-auto px-gutter">
        {/* Back Link */}
        <div className="mb-4 sm:mb-6">
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-xs sm:text-sm text-text-secondary hover:text-white transition-colors bg-white/5 hover:bg-white/10 px-3.5 py-1.5 rounded-xl border border-white/10"
          >
            <span className="material-symbols-outlined text-[18px]">arrow_back</span>
            <span>Bosh sahifa</span>
          </Link>
        </div>

        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
          <div>
            <h1 className="text-2xl sm:text-3xl md:text-4xl font-display-hero font-bold text-white flex items-center gap-3">
              <span className="material-symbols-outlined text-3xl sm:text-4xl text-amber-400">emoji_events</span>
              Yutuqlar
            </h1>
            <p className="text-text-secondary text-xs sm:text-sm mt-1">
              Kinolar va seriallar tomosha qilib erishgan unvonlaringiz
            </p>
          </div>

          {/* Progress summary */}
          <div className="bg-surface-container/60 border border-white/10 rounded-2xl p-4 min-w-[240px]">
            <div className="flex justify-between items-center mb-2">
              <span className="text-xs text-text-secondary font-medium">
                {status === "authenticated" ? "Bajarildi" : "Umumiy yutuqlar"}
              </span>
              <span className="text-sm font-bold text-amber-400">
                {status === "authenticated" 
                  ? `${unlockedCount} / ${ALL_ACHIEVEMENTS.length} (${progressPercent}%)`
                  : `0 / ${ALL_ACHIEVEMENTS.length}`}
              </span>
            </div>
            <div className="w-full bg-white/10 rounded-full h-2 overflow-hidden">
              <div
                className="bg-gradient-to-r from-amber-400 to-primary-container h-2 rounded-full transition-all duration-500"
                style={{ width: `${status === "authenticated" ? progressPercent : 0}%` }}
              ></div>
            </div>
          </div>
        </div>

        {/* Unauthenticated Login Callout Banner */}
        {status === "unauthenticated" && (
          <div className="mb-8 p-5 sm:p-6 rounded-2xl bg-white/[0.04] border border-white/10 backdrop-blur-xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 shadow-xl">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-2xl bg-amber-400/10 border border-amber-400/20 flex items-center justify-center text-amber-400 shrink-0">
                <span className="material-symbols-outlined text-2xl">lock_open</span>
              </div>
              <div>
                <h3 className="font-bold text-white text-base">Yutuqlaringizni saqlab boring</h3>
                <p className="text-xs sm:text-sm text-text-secondary mt-0.5">
                  Medallarni ochish va faolligingizni ko'rish uchun profilingizga kiring.
                </p>
              </div>
            </div>
            {loginDirect && (
              <button
                onClick={() => loginDirect({ telegram_id: 1990156236, first_name: "XOJA" })}
                className="w-full sm:w-auto px-5 py-2.5 bg-primary-container hover:bg-primary-container/90 text-white font-bold rounded-xl text-sm transition-all flex items-center justify-center gap-2 shadow-lg shadow-primary-container/20 shrink-0 cursor-pointer"
              >
                <span className="material-symbols-outlined text-lg">bolt</span>
                <span>Tezkor Kirish</span>
              </button>
            )}
          </div>
        )}

        {/* Grid of Achievements */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
          {ALL_ACHIEVEMENTS.map((item) => {
            const isUnlocked = !!unlocked[item.code];
            const earnedDate = unlocked[item.code]?.earned_at;

            return (
              <div
                key={item.code}
                className={`relative rounded-2xl p-5 border transition-all duration-300 flex flex-col justify-between ${
                  isUnlocked
                    ? "bg-surface-container/80 border-amber-400/30 shadow-lg shadow-amber-400/5 hover:border-amber-400/60"
                    : "bg-surface-container/20 border-white/5 opacity-60"
                }`}
              >
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <div
                      className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                        isUnlocked
                          ? "bg-amber-400/20 text-amber-400"
                          : "bg-white/5 text-text-secondary"
                      }`}
                    >
                      <span className="material-symbols-outlined text-[28px]">{item.icon}</span>
                    </div>

                    {isUnlocked ? (
                      <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-400 bg-emerald-400/10 px-2 py-0.5 rounded-full">
                        <span className="material-symbols-outlined text-[14px]">check</span>
                        Ochilgan
                      </span>
                    ) : (
                      <span className="material-symbols-outlined text-text-secondary text-[20px]">
                        lock
                      </span>
                    )}
                  </div>

                  <h3 className={`font-bold text-base mb-1 ${isUnlocked ? "text-white" : "text-text-secondary"}`}>
                    {item.title}
                  </h3>
                  <p className="text-xs text-text-secondary leading-relaxed">{item.desc}</p>
                </div>

                {isUnlocked && earnedDate && (
                  <div className="mt-4 pt-3 border-t border-white/5 text-[11px] text-text-secondary flex items-center gap-1">
                    <span className="material-symbols-outlined text-[14px]">calendar_today</span>
                    {new Date(earnedDate).toLocaleDateString("uz-UZ", {
                      day: "numeric",
                      month: "short",
                      year: "numeric",
                    })}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
