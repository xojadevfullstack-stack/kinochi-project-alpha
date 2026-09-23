"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { fetchApi } from "@/lib/api";

interface RecentItem {
  id: number;
  title: string;
  type: "kino" | "serial";
  status: string;
  poster_url: string | null;
  created_at: string;
}

interface DashboardStats {
  total_users: number;
  new_users_today: number;
  total_movies: number;
  total_series: number;
  recent_items: RecentItem[];
}

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadStats = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchApi("/statistics/dashboard");
      setStats(data);
    } catch (err: any) {
      setError(err.message || "Statistikalarni yuklab bo'lmadi");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStats();
  }, []);

  const formatDate = (dateStr: string) => {
    try {
      return new Date(dateStr).toLocaleDateString("uz-UZ", {
        day: "numeric",
        month: "short",
        year: "numeric",
      });
    } catch {
      return dateStr;
    }
  };

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto text-text-primary">
      {/* Header */}
      <header className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 mb-6 sm:mb-8">
        <div>
          <h2 className="font-display text-2xl sm:text-4xl font-black text-text-primary tracking-tighter">
            Umumiy ko'rsatkichlar
          </h2>
          <p className="font-sans text-sm sm:text-base text-text-secondary mt-1">
            Xush kelibsiz, Boshqaruvchi. Real vaqtdagi tizim holati.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={loadStats}
            disabled={loading}
            title="Yangilash"
            className="glass-panel p-2 sm:px-3 sm:py-2 rounded-full flex items-center gap-1.5 text-text-secondary hover:text-text-primary hover:bg-white/10 transition-colors text-xs sm:text-sm"
          >
            <span className={`material-symbols-outlined text-[18px] ${loading ? "animate-spin" : ""}`}>
              refresh
            </span>
            <span className="hidden sm:inline font-sans">Yangilash</span>
          </button>
          <div className="glass-panel px-3.5 py-1.5 sm:px-4 sm:py-2 rounded-full flex items-center gap-2 text-text-secondary text-xs sm:text-sm">
            <span className="material-symbols-outlined text-[18px] sm:text-[20px]">
              calendar_today
            </span>
            <span className="font-sans">
              {new Date().toLocaleDateString("uz-UZ", {
                month: "short",
                day: "numeric",
                year: "numeric",
              })}
            </span>
          </div>
        </div>
      </header>

      {/* Error notification if any */}
      {error && (
        <div className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="material-symbols-outlined text-xl">error</span>
            <span className="text-sm font-sans">{error}</span>
          </div>
          <button
            onClick={loadStats}
            className="text-xs uppercase tracking-wider font-bold underline hover:text-red-300"
          >
            Qayta urinish
          </button>
        </div>
      )}

      {/* Metrics Grid */}
      <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6 mb-6 sm:mb-8">
        {/* Metric 1: Users */}
        <div className="metric-card p-5 sm:p-6 rounded-2xl flex flex-col justify-between">
          <div className="flex justify-between items-start mb-4">
            <div className="w-12 h-12 rounded-xl bg-surface-container-highest flex items-center justify-center text-primary-container">
              <span
                className="material-symbols-outlined"
                style={{ fontVariationSettings: "'FILL' 1" }}
              >
                group
              </span>
            </div>
            {loading ? (
              <div className="w-16 h-6 bg-white/5 rounded-full animate-pulse" />
            ) : stats && stats.new_users_today > 0 ? (
              <span className="text-[#0072d7] flex items-center gap-1 font-sans text-xs uppercase tracking-widest font-bold bg-[#0072d7]/10 px-2.5 py-1 rounded-full">
                <span className="material-symbols-outlined text-[14px]">trending_up</span>
                +{stats.new_users_today} bugun
              </span>
            ) : (
              <span className="text-text-secondary flex items-center font-sans text-xs uppercase tracking-widest font-bold bg-white/5 px-2.5 py-1 rounded-full">
                Faol
              </span>
            )}
          </div>
          <div>
            <p className="font-sans text-xs uppercase tracking-widest font-bold text-text-secondary mb-1">
              Jami Foydalanuvchilar
            </p>
            {loading ? (
              <div className="w-24 h-9 bg-white/10 rounded-lg animate-pulse" />
            ) : (
              <h3 className="font-display text-2xl sm:text-3xl font-bold text-text-primary">
                {stats ? stats.total_users.toLocaleString() : "0"}
              </h3>
            )}
          </div>
        </div>

        {/* Metric 2: Movies */}
        <div className="metric-card p-5 sm:p-6 rounded-2xl flex flex-col justify-between">
          <div className="flex justify-between items-start mb-4">
            <div className="w-12 h-12 rounded-xl bg-surface-container-highest flex items-center justify-center text-primary-container">
              <span
                className="material-symbols-outlined"
                style={{ fontVariationSettings: "'FILL' 1" }}
              >
                movie
              </span>
            </div>
            <Link
              href="/movies"
              className="text-[#0072d7] hover:underline flex items-center gap-1 font-sans text-xs uppercase tracking-widest font-bold bg-[#0072d7]/10 px-2.5 py-1 rounded-full transition-colors"
            >
              Boshqarish
              <span className="material-symbols-outlined text-[14px]">arrow_forward</span>
            </Link>
          </div>
          <div>
            <p className="font-sans text-xs uppercase tracking-widest font-bold text-text-secondary mb-1">
              Jami Kinolar
            </p>
            {loading ? (
              <div className="w-24 h-9 bg-white/10 rounded-lg animate-pulse" />
            ) : (
              <h3 className="font-display text-2xl sm:text-3xl font-bold text-text-primary">
                {stats ? stats.total_movies.toLocaleString() : "0"}
              </h3>
            )}
          </div>
        </div>

        {/* Metric 3: Series */}
        <div className="metric-card p-5 sm:p-6 rounded-2xl flex flex-col justify-between sm:col-span-2 lg:col-span-1">
          <div className="flex justify-between items-start mb-4">
            <div className="w-12 h-12 rounded-xl bg-surface-container-highest flex items-center justify-center text-primary-container">
              <span
                className="material-symbols-outlined"
                style={{ fontVariationSettings: "'FILL' 1" }}
              >
                tv
              </span>
            </div>
            <Link
              href="/series"
              className="text-[#F5C518] hover:underline flex items-center gap-1 font-sans text-xs uppercase tracking-widest font-bold bg-[#F5C518]/10 px-2.5 py-1 rounded-full transition-colors"
            >
              Boshqarish
              <span className="material-symbols-outlined text-[14px]">arrow_forward</span>
            </Link>
          </div>
          <div>
            <p className="font-sans text-xs uppercase tracking-widest font-bold text-text-secondary mb-1">
              Jami Seriallar
            </p>
            {loading ? (
              <div className="w-24 h-9 bg-white/10 rounded-lg animate-pulse" />
            ) : (
              <h3 className="font-display text-2xl sm:text-3xl font-bold text-text-primary">
                {stats ? stats.total_series.toLocaleString() : "0"}
              </h3>
            )}
          </div>
        </div>
      </section>

      {/* Data Table Section */}
      <section className="glass-panel rounded-2xl overflow-hidden shadow-2xl">
        <div className="p-4 sm:p-6 border-b border-white/5 flex justify-between items-center bg-[#1a0908]/80">
          <div>
            <h3 className="font-display text-lg sm:text-xl font-bold text-text-primary">
              So'nggi qo'shilganlar
            </h3>
            <p className="text-xs text-text-secondary mt-0.5">
              Eng so'nggi qo'shilgan kino va seriallar ro'yxati
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Link
              href="/movies"
              className="text-text-secondary hover:text-primary-container transition-colors font-sans text-xs uppercase tracking-widest font-bold flex items-center gap-1"
            >
              Kinolar <span className="material-symbols-outlined text-[16px]">arrow_forward</span>
            </Link>
            <span className="text-white/20">•</span>
            <Link
              href="/series"
              className="text-text-secondary hover:text-primary-container transition-colors font-sans text-xs uppercase tracking-widest font-bold flex items-center gap-1"
            >
              Seriallar <span className="material-symbols-outlined text-[16px]">arrow_forward</span>
            </Link>
          </div>
        </div>

        <div className="overflow-x-auto custom-scrollbar">
          <table className="w-full text-left border-collapse min-w-[600px]">
            <thead>
              <tr className="bg-[#1a0908]/50 border-b border-white/10">
                <th className="p-3.5 sm:p-4 font-sans text-xs uppercase tracking-widest text-text-secondary font-medium">
                  Nomi
                </th>
                <th className="p-3.5 sm:p-4 font-sans text-xs uppercase tracking-widest text-text-secondary font-medium">
                  Turi
                </th>
                <th className="p-3.5 sm:p-4 font-sans text-xs uppercase tracking-widest text-text-secondary font-medium">
                  Holati
                </th>
                <th className="p-3.5 sm:p-4 font-sans text-xs uppercase tracking-widest text-text-secondary font-medium">
                  Qo'shilgan sana
                </th>
                <th className="p-3.5 sm:p-4 font-sans text-xs uppercase tracking-widest text-text-secondary font-medium text-right">
                  Amal
                </th>
              </tr>
            </thead>
            <tbody className="font-sans text-sm sm:text-base divide-y divide-white/5">
              {loading ? (
                // Loading skeleton rows
                [...Array(4)].map((_, i) => (
                  <tr key={i} className="animate-pulse">
                    <td className="p-3.5 sm:p-4">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-14 bg-white/5 rounded shrink-0" />
                        <div className="w-36 h-4 bg-white/10 rounded" />
                      </div>
                    </td>
                    <td className="p-3.5 sm:p-4">
                      <div className="w-16 h-4 bg-white/5 rounded" />
                    </td>
                    <td className="p-3.5 sm:p-4">
                      <div className="w-14 h-5 bg-white/5 rounded-full" />
                    </td>
                    <td className="p-3.5 sm:p-4">
                      <div className="w-24 h-4 bg-white/5 rounded" />
                    </td>
                    <td className="p-3.5 sm:p-4 text-right">
                      <div className="w-8 h-8 bg-white/5 rounded-full ml-auto" />
                    </td>
                  </tr>
                ))
              ) : !stats || stats.recent_items.length === 0 ? (
                // Empty state
                <tr>
                  <td colSpan={5} className="p-8 text-center text-text-secondary">
                    <div className="flex flex-col items-center justify-center gap-2">
                      <span className="material-symbols-outlined text-4xl text-white/20">
                        movie_filter
                      </span>
                      <p className="font-medium text-text-primary">
                        Hozircha kontent mavjud emas
                      </p>
                      <p className="text-xs text-text-secondary">
                        Kino yoki serial qo'shish uchun tegishli bo'limga o'ting.
                      </p>
                      <div className="flex gap-2 mt-3">
                        <Link
                          href="/movies"
                          className="px-3.5 py-1.5 bg-primary-container text-white text-xs rounded-xl font-bold hover:bg-opacity-90 transition-opacity"
                        >
                          + Kino qo'shish
                        </Link>
                        <Link
                          href="/series"
                          className="px-3.5 py-1.5 bg-surface-container-highest text-white text-xs rounded-xl font-bold hover:bg-white/10 transition-colors"
                        >
                          + Serial qo'shish
                        </Link>
                      </div>
                    </div>
                  </td>
                </tr>
              ) : (
                // Real data rows
                stats.recent_items.map((item) => (
                  <tr key={`${item.type}-${item.id}`} className="data-table-row">
                    <td className="p-3.5 sm:p-4">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-14 bg-surface-container-highest rounded overflow-hidden relative shrink-0 border border-white/10">
                          {item.poster_url ? (
                            <img
                              src={item.poster_url}
                              alt={item.title}
                              className="w-full h-full object-cover"
                              onError={(e) => {
                                // fallback to icon if image fails to load
                                (e.target as HTMLElement).style.display = "none";
                              }}
                            />
                          ) : (
                            <div className="w-full h-full flex items-center justify-center text-text-secondary">
                              <span className="material-symbols-outlined text-xl opacity-60">
                                {item.type === "kino" ? "movie" : "tv"}
                              </span>
                            </div>
                          )}
                        </div>
                        <span className="text-text-primary font-medium line-clamp-1">
                          {item.title}
                        </span>
                      </div>
                    </td>
                    <td className="p-3.5 sm:p-4 text-text-secondary text-sm">
                      {item.type === "kino" ? (
                        <span className="inline-flex items-center gap-1.5 font-medium text-primary-container">
                          <span className="material-symbols-outlined text-[16px]">movie</span>
                          Kino
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1.5 font-medium text-[#F5C518]">
                          <span className="material-symbols-outlined text-[16px]">tv</span>
                          Serial
                        </span>
                      )}
                    </td>
                    <td className="p-3.5 sm:p-4">
                      <span
                        className={`px-2.5 py-1 rounded-full text-xs uppercase tracking-widest font-bold ${
                          item.status === "Faol"
                            ? "bg-[#0072d7]/20 text-[#0072d7]"
                            : item.status === "Jarayonda"
                            ? "bg-[#F5C518]/20 text-[#F5C518]"
                            : "bg-emerald-500/20 text-emerald-400"
                        }`}
                      >
                        {item.status}
                      </span>
                    </td>
                    <td className="p-3.5 sm:p-4 text-text-secondary text-sm">
                      {formatDate(item.created_at)}
                    </td>
                    <td className="p-3.5 sm:p-4 text-right">
                      <Link
                        href={item.type === "kino" ? "/movies" : "/series"}
                        className="inline-flex items-center gap-1 text-text-secondary hover:text-text-primary p-2 rounded-xl hover:bg-white/10 transition-colors text-xs font-medium"
                        title="Tahrirlash / Ko'rish"
                      >
                        <span className="material-symbols-outlined text-[18px]">open_in_new</span>
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
