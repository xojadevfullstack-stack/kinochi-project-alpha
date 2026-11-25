"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { fetchApi } from "@/lib/api";
import RequestsPanel from "@/components/RequestsPanel";
import {
  computeBarHeightPct,
  computeSourceShare,
  summarizeTmdbCoverage,
} from "@/lib/analyticsHelpers.mjs";

type MainTab = "overview" | "requests" | "tmdb";
type TmdbCategory =
  | "trending_week"
  | "trending_day"
  | "upcoming"
  | "now_playing"
  | "tv_on_the_air";

interface AnalyticsData {
  days: number;
  summary: {
    total_views: number;
    period_views: number;
    bot_views: number;
    web_views: number;
    stream_views: number;
    total_users: number;
    active_users_today: number;
    active_users_7d: number;
    active_users_30d: number;
    total_requests: number;
    pending_requests: number;
  };
  top_movies: Array<{
    id: number;
    title: string;
    code: string;
    short_code?: string | null;
    poster_url?: string | null;
    imdb_rating?: number | null;
    release_year?: number | null;
    total_views: number;
    period_views: number;
  }>;
  top_series: Array<{
    id: number;
    title: string;
    poster_url?: string | null;
    imdb_rating?: number | null;
    release_year?: number | null;
    status: string;
    total_views: number;
    period_views: number;
    subscribers_count: number;
  }>;
  daily_trend: Array<{
    date: string;
    bot: number;
    web: number;
    stream: number;
    total: number;
  }>;
}

interface TmdbInsightItem {
  tmdb_id: number;
  media_type: "movie" | "series";
  title: string;
  original_title?: string | null;
  release_date?: string | null;
  release_year?: number | null;
  poster_url?: string | null;
  overview?: string;
  vote_average: number;
  vote_count: number;
  popularity: number;
  in_library: boolean;
  library_id?: number | null;
  library_code?: string | null;
  is_requested: boolean;
  request_id?: number | null;
  request_votes: number;
  request_status?: string | null;
}

interface TmdbInsightsResponse {
  category: TmdbCategory;
  page: number;
  total_pages: number;
  total_results: number;
  items: TmdbInsightItem[];
}

export default function AnalyticsPage() {
  const [activeTab, setActiveTab] = useState<MainTab>("overview");
  const [days, setDays] = useState<number>(7);
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [loadingAnalytics, setLoadingAnalytics] = useState(true);
  const [analyticsError, setAnalyticsError] = useState<string | null>(null);

  // TMDb Insights state
  const [tmdbCategory, setTmdbCategory] = useState<TmdbCategory>("trending_week");
  const [tmdbPage, setTmdbPage] = useState(1);
  const [tmdbData, setTmdbData] = useState<TmdbInsightsResponse | null>(null);
  const [loadingTmdb, setLoadingTmdb] = useState(false);
  const [tmdbError, setTmdbError] = useState<string | null>(null);
  const [requestingKey, setRequestingKey] = useState<string | null>(null);
  const [tmdbToast, setTmdbToast] = useState<string | null>(null);

  const loadAnalytics = async (targetDays: number = days) => {
    setLoadingAnalytics(true);
    setAnalyticsError(null);
    try {
      const data = await fetchApi(`/statistics/analytics?days=${targetDays}`);
      setAnalytics(data);
    } catch (err: any) {
      setAnalyticsError(err?.message || "Analitika ma'lumotlarini yuklab bo'lmadi");
    } finally {
      setLoadingAnalytics(false);
    }
  };

  const loadTmdbInsights = async (
    category: TmdbCategory = tmdbCategory,
    page: number = tmdbPage
  ) => {
    setLoadingTmdb(true);
    setTmdbError(null);
    try {
      const data = await fetchApi(
        `/statistics/tmdb-insights?category=${category}&page=${page}`
      );
      setTmdbData(data);
    } catch (err: any) {
      setTmdbError(err?.message || "TMDb ma'lumotlarini yuklab bo'lmadi");
    } finally {
      setLoadingTmdb(false);
    }
  };

  useEffect(() => {
    loadAnalytics(days);
  }, [days]);

  useEffect(() => {
    if (activeTab === "tmdb") {
      loadTmdbInsights(tmdbCategory, tmdbPage);
    }
  }, [activeTab, tmdbCategory, tmdbPage]);

  const handleRequestFromTmdb = async (item: TmdbInsightItem) => {
    const key = `${item.media_type}:${item.tmdb_id}`;
    setRequestingKey(key);
    setTmdbToast(null);
    try {
      await fetchApi("/content-requests", {
        method: "POST",
        body: JSON.stringify({
          title: item.title,
          original_title: item.original_title,
          media_type: item.media_type,
          release_year: item.release_year,
          poster_url: item.poster_url,
          overview: item.overview,
          tmdb_id: item.tmdb_id,
          preferred_language: "uz",
        }),
      });
      setTmdbToast(`"${item.title}" buyurtmalar ro'yxatiga qo'shildi.`);
      setTmdbData((prev) =>
        prev
          ? {
              ...prev,
              items: prev.items.map((x) =>
                x.tmdb_id === item.tmdb_id && x.media_type === item.media_type
                  ? {
                      ...x,
                      is_requested: true,
                      request_votes: (x.request_votes || 0) + 1,
                    }
                  : x
              ),
            }
          : prev
      );
      loadAnalytics(days);
    } catch (err: any) {
      setTmdbError(err?.message || "Buyurtma qo'shishda xatolik");
    } finally {
      setRequestingKey(null);
    }
  };

  const summary = analytics?.summary;
  const sourceShare = computeSourceShare(
    summary?.bot_views ?? 0,
    summary?.web_views ?? 0,
    summary?.stream_views ?? 0
  );
  const maxTrend = Math.max(
    ...(analytics?.daily_trend || []).map((d) => d.total),
    0
  );
  const tmdbCoverage = summarizeTmdbCoverage(tmdbData?.items || []);

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto text-text-primary space-y-6">
      {/* Header */}
      <header className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="font-display text-2xl sm:text-4xl font-black text-text-primary tracking-tight flex items-center gap-3">
            <span className="material-symbols-outlined text-[#E50914] text-3xl sm:text-4xl">
              analytics
            </span>
            <span>Real Analitika & TMDb Markazi</span>
          </h1>
          <p className="text-sm text-text-secondary mt-1">
            Haqiqiy ko'rilishlar (Bot & Sayt), TOP kontent, foydalanuvchi buyurtmalari va TMDb premyera statistikasi.
          </p>
        </div>

        {/* Main Section Tabs */}
        <div className="flex items-center gap-1.5 bg-[#12141a] border border-white/10 p-1.5 rounded-2xl overflow-x-auto">
          {[
            { id: "overview" as const, label: "Real Statistika", icon: "bar_chart" },
            {
              id: "requests" as const,
              label: `Buyurtmalar (${summary?.pending_requests ?? 0})`,
              icon: "add_to_queue",
            },
            { id: "tmdb" as const, label: "TMDb Yangiliklar", icon: "travel_explore" },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold transition whitespace-nowrap ${
                activeTab === tab.id
                  ? "bg-[#E50914] text-white shadow-lg shadow-[#E50914]/25"
                  : "text-zinc-400 hover:text-white hover:bg-white/5"
              }`}
            >
              <span className="material-symbols-outlined text-[16px]">{tab.icon}</span>
              <span>{tab.label}</span>
            </button>
          ))}
        </div>
      </header>

      {/* TAB 1: REAL ANALYTICS OVERVIEW */}
      {activeTab === "overview" && (
        <div className="space-y-6">
          {/* Period Filter & Refresh */}
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-1.5 bg-[#12141a] border border-white/10 p-1 rounded-xl">
              {[
                { val: 1, label: "Bugun" },
                { val: 7, label: "7 kun" },
                { val: 30, label: "30 kun" },
                { val: 0, label: "Barchasi" },
              ].map((p) => (
                <button
                  key={p.val}
                  onClick={() => setDays(p.val)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-bold transition ${
                    days === p.val
                      ? "bg-[#E50914] text-white"
                      : "text-zinc-400 hover:text-white hover:bg-white/5"
                  }`}
                >
                  {p.label}
                </button>
              ))}
            </div>

            <button
              onClick={() => loadAnalytics(days)}
              disabled={loadingAnalytics}
              className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-white/5 hover:bg-[#E50914] border border-white/10 text-xs font-semibold text-white transition"
            >
              <span
                className={`material-symbols-outlined text-[16px] ${
                  loadingAnalytics ? "animate-spin" : ""
                }`}
              >
                refresh
              </span>
              <span>Yangilash</span>
            </button>
          </div>

          {analyticsError && (
            <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-sm flex items-center justify-between">
              <span>{analyticsError}</span>
              <button
                onClick={() => loadAnalytics(days)}
                className="text-xs font-bold underline"
              >
                Qayta urinish
              </button>
            </div>
          )}

          {/* KPI Cards */}
          <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="metric-card p-5 rounded-2xl border border-white/10 bg-[#12141a]">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs uppercase tracking-wider font-bold text-zinc-400">
                  Davr Ko'rishlari
                </span>
                <span className="material-symbols-outlined text-[#E50914]">visibility</span>
              </div>
              <div className="text-3xl font-black text-white">
                {loadingAnalytics ? "…" : (summary?.period_views ?? 0).toLocaleString()}
              </div>
              <div className="text-xs text-zinc-400 mt-1">
                Jami tarixda: {(summary?.total_views ?? 0).toLocaleString()} ta
              </div>
            </div>

            <div className="metric-card p-5 rounded-2xl border border-white/10 bg-[#12141a]">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs uppercase tracking-wider font-bold text-zinc-400">
                  Bot vs Sayt
                </span>
                <span className="material-symbols-outlined text-blue-400">devices</span>
              </div>
              <div className="flex items-baseline gap-2 text-lg font-extrabold text-white">
                <span>Bot: {(summary?.bot_views ?? 0).toLocaleString()}</span>
                <span className="text-zinc-500">/</span>
                <span className="text-emerald-400">
                  Sayt: {((summary?.web_views ?? 0) + (summary?.stream_views ?? 0)).toLocaleString()}
                </span>
              </div>
              <div className="w-full h-2 rounded-full bg-white/10 overflow-hidden flex mt-3">
                <div
                  className="bg-[#E50914] h-full"
                  style={{ width: `${sourceShare.botPct}%` }}
                  title={`Bot: ${sourceShare.botPct}%`}
                />
                <div
                  className="bg-emerald-500 h-full"
                  style={{ width: `${sourceShare.webPct + sourceShare.streamPct}%` }}
                  title={`Sayt/Stream: ${sourceShare.webPct + sourceShare.streamPct}%`}
                />
              </div>
            </div>

            <div className="metric-card p-5 rounded-2xl border border-white/10 bg-[#12141a]">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs uppercase tracking-wider font-bold text-zinc-400">
                  Faol Foydalanuvchilar
                </span>
                <span className="material-symbols-outlined text-emerald-400">group</span>
              </div>
              <div className="text-3xl font-black text-white">
                {loadingAnalytics ? "…" : (summary?.active_users_7d ?? 0).toLocaleString()}
                <span className="text-xs font-normal text-zinc-400 ml-1.5">7 kun</span>
              </div>
              <div className="text-xs text-zinc-400 mt-1">
                Bugun: {summary?.active_users_today ?? 0} • 30 kun: {summary?.active_users_30d ?? 0}
              </div>
            </div>

            <button
              onClick={() => setActiveTab("requests")}
              className="text-left metric-card p-5 rounded-2xl border border-white/10 bg-[#12141a] hover:border-[#E50914]/60 transition"
            >
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs uppercase tracking-wider font-bold text-zinc-400">
                  Buyurtmalar
                </span>
                <span className="material-symbols-outlined text-[#E50914]">add_to_queue</span>
              </div>
              <div className="text-3xl font-black text-white">
                {loadingAnalytics ? "…" : (summary?.pending_requests ?? 0).toLocaleString()}
                <span className="text-xs font-normal text-zinc-400 ml-1.5">kutilmoqda</span>
              </div>
              <div className="text-xs text-[#E50914] font-semibold mt-1">
                Jami {summary?.total_requests ?? 0} ta so'rov → Ko'rish
              </div>
            </button>
          </section>

          {/* Daily Views Bar Chart */}
          <section className="rounded-2xl border border-white/10 bg-[#12141a] p-5">
            <div className="flex flex-wrap items-center justify-between gap-2 mb-4">
              <div>
                <h2 className="text-base font-bold text-white">Kunlik Ko'rishlar Dinamikasi</h2>
                <p className="text-xs text-zinc-400">
                  Qizil — Telegram Bot • Yashil — Sayt & Stream
                </p>
              </div>
              <div className="text-xs text-zinc-400">
                Maksimum kun: <strong className="text-white">{maxTrend}</strong>
              </div>
            </div>

            <div className="flex items-end gap-1.5 sm:gap-2 h-40 pt-4">
              {(analytics?.daily_trend || []).map((d) => {
                const webTotal = d.web + d.stream;
                const totalPct = computeBarHeightPct(d.total, maxTrend);
                const botPartPct =
                  d.total > 0 ? Math.round((d.bot / d.total) * 100) : 0;
                return (
                  <div
                    key={d.date}
                    className="flex-1 flex flex-col items-center gap-1.5 h-full justify-end group"
                    title={`${d.date}: Jami ${d.total} (Bot: ${d.bot}, Sayt: ${webTotal})`}
                  >
                    <div className="text-[10px] text-zinc-400 opacity-0 group-hover:opacity-100 transition">
                      {d.total}
                    </div>
                    <div
                      className="w-full max-w-[28px] rounded-t-md bg-white/5 overflow-hidden flex flex-col justify-end transition-all"
                      style={{ height: `${totalPct || 2}%` }}
                    >
                      {d.total > 0 ? (
                        <>
                          <div
                            className="w-full bg-emerald-500/85"
                            style={{ height: `${100 - botPartPct}%` }}
                          />
                          <div
                            className="w-full bg-[#E50914]"
                            style={{ height: `${botPartPct}%` }}
                          />
                        </>
                      ) : (
                        <div className="w-full h-full bg-white/5" />
                      )}
                    </div>
                    <span className="text-[10px] text-zinc-500 truncate max-w-full">
                      {d.date.slice(5)}
                    </span>
                  </div>
                );
              })}
            </div>
          </section>

          {/* TOP 10 MOVIES & TOP 10 SERIES */}
          <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* TOP 10 Movies */}
            <div className="rounded-2xl border border-white/10 bg-[#12141a] overflow-hidden">
              <div className="p-4 sm:p-5 border-b border-white/10 flex items-center justify-between">
                <div>
                  <h2 className="font-bold text-white text-base flex items-center gap-2">
                    <span className="material-symbols-outlined text-[#E50914]">local_fire_department</span>
                    <span>Eng ko'p ko'rilgan TOP 10 Kino</span>
                  </h2>
                  <p className="text-xs text-zinc-400 mt-0.5">
                    Tanlangan davr bo'yicha real ko'rishlar reytingi
                  </p>
                </div>
                <Link href="/movies" className="text-xs text-[#E50914] font-bold hover:underline">
                  Kinolar →
                </Link>
              </div>

              <div className="divide-y divide-white/5">
                {!analytics || analytics.top_movies.length === 0 ? (
                  <div className="p-8 text-center text-xs text-zinc-500">
                    Ushbu davrda hali ko'rishlar qayd etilmagan.
                  </div>
                ) : (
                  analytics.top_movies.map((m, idx) => (
                    <div
                      key={m.id}
                      className="p-3.5 sm:px-5 flex items-center justify-between gap-3 hover:bg-white/[0.02]"
                    >
                      <div className="flex items-center gap-3 min-w-0">
                        <span
                          className={`w-6 text-center font-black text-sm shrink-0 ${
                            idx < 3 ? "text-[#E50914]" : "text-zinc-500"
                          }`}
                        >
                          #{idx + 1}
                        </span>
                        <div className="w-10 h-14 rounded bg-zinc-800 overflow-hidden shrink-0 border border-white/10">
                          {m.poster_url ? (
                            <img
                              src={m.poster_url}
                              alt={m.title}
                              className="w-full h-full object-cover"
                            />
                          ) : null}
                        </div>
                        <div className="min-w-0">
                          <div className="text-sm font-bold text-white truncate">{m.title}</div>
                          <div className="flex items-center gap-2 text-xs text-zinc-400">
                            <span>#{m.short_code || m.code}</span>
                            {m.release_year && <span>• {m.release_year}</span>}
                            {m.imdb_rating ? (
                              <span className="text-[#F5C518] font-bold">★ {m.imdb_rating}</span>
                            ) : null}
                          </div>
                        </div>
                      </div>
                      <div className="text-right shrink-0">
                        <div className="text-sm font-black text-white">
                          {m.period_views.toLocaleString()}
                        </div>
                        <div className="text-[11px] text-zinc-500">
                          Jami: {m.total_views.toLocaleString()}
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* TOP 10 Series */}
            <div className="rounded-2xl border border-white/10 bg-[#12141a] overflow-hidden">
              <div className="p-4 sm:p-5 border-b border-white/10 flex items-center justify-between">
                <div>
                  <h2 className="font-bold text-white text-base flex items-center gap-2">
                    <span className="material-symbols-outlined text-[#E50914]">live_tv</span>
                    <span>Eng ko'p ko'rilgan TOP 10 Serial</span>
                  </h2>
                  <p className="text-xs text-zinc-400 mt-0.5">
                    Ko'rishlar va obunachilar soni bilan
                  </p>
                </div>
                <Link href="/series" className="text-xs text-[#E50914] font-bold hover:underline">
                  Seriallar →
                </Link>
              </div>

              <div className="divide-y divide-white/5">
                {!analytics || analytics.top_series.length === 0 ? (
                  <div className="p-8 text-center text-xs text-zinc-500">
                    Ushbu davrda serial ko'rishlari hali qayd etilmagan.
                  </div>
                ) : (
                  analytics.top_series.map((s, idx) => (
                    <div
                      key={s.id}
                      className="p-3.5 sm:px-5 flex items-center justify-between gap-3 hover:bg-white/[0.02]"
                    >
                      <div className="flex items-center gap-3 min-w-0">
                        <span
                          className={`w-6 text-center font-black text-sm shrink-0 ${
                            idx < 3 ? "text-[#E50914]" : "text-zinc-500"
                          }`}
                        >
                          #{idx + 1}
                        </span>
                        <div className="w-10 h-14 rounded bg-zinc-800 overflow-hidden shrink-0 border border-white/10">
                          {s.poster_url ? (
                            <img
                              src={s.poster_url}
                              alt={s.title}
                              className="w-full h-full object-cover"
                            />
                          ) : null}
                        </div>
                        <div className="min-w-0">
                          <div className="text-sm font-bold text-white truncate">{s.title}</div>
                          <div className="flex items-center gap-2 text-xs text-zinc-400">
                            <span>{s.subscribers_count} obunachi</span>
                            {s.release_year && <span>• {s.release_year}</span>}
                            {s.imdb_rating ? (
                              <span className="text-[#F5C518] font-bold">★ {s.imdb_rating}</span>
                            ) : null}
                          </div>
                        </div>
                      </div>
                      <div className="text-right shrink-0">
                        <div className="text-sm font-black text-white">
                          {s.period_views.toLocaleString()}
                        </div>
                        <div className="text-[11px] text-zinc-500">
                          Jami: {s.total_views.toLocaleString()}
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </section>
        </div>
      )}

      {/* TAB 2: REQUESTS / ORDERS */}
      {activeTab === "requests" && (
        <RequestsPanel compactHeader onChanged={() => loadAnalytics(days)} />
      )}

      {/* TAB 3: TMDB NEWS, UPCOMING PREMIERES & COVERAGE */}
      {activeTab === "tmdb" && (
        <div className="space-y-5">
          {/* TMDb Sub-tabs & Coverage summary */}
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3 bg-[#12141a] border border-white/10 rounded-2xl p-3 sm:p-4">
            <div className="flex items-center gap-1.5 overflow-x-auto hide-scrollbar">
              {[
                { id: "trending_week" as const, label: "Hafta Trendlari" },
                { id: "trending_day" as const, label: "Bugun Trendda" },
                { id: "upcoming" as const, label: "Kutilayotgan Premyeralar" },
                { id: "now_playing" as const, label: "Hozir Kinoteatrlarda" },
                { id: "tv_on_the_air" as const, label: "Yangi Seriallar" },
              ].map((cat) => (
                <button
                  key={cat.id}
                  onClick={() => {
                    setTmdbCategory(cat.id);
                    setTmdbPage(1);
                  }}
                  className={`px-3 py-1.5 rounded-xl text-xs font-bold transition whitespace-nowrap ${
                    tmdbCategory === cat.id
                      ? "bg-[#E50914] text-white shadow-md shadow-[#E50914]/25"
                      : "bg-white/5 hover:bg-white/10 text-zinc-400 hover:text-white"
                  }`}
                >
                  {cat.label}
                </button>
              ))}
            </div>

            <div className="flex flex-wrap items-center gap-2 text-xs">
              <span className="px-2.5 py-1 rounded-lg bg-emerald-500/15 text-emerald-400 font-semibold">
                Saytda bor: {tmdbCoverage.inLibrary}
              </span>
              <span className="px-2.5 py-1 rounded-lg bg-blue-500/15 text-blue-400 font-semibold">
                Buyurtmada: {tmdbCoverage.requested}
              </span>
              <span className="px-2.5 py-1 rounded-lg bg-[#E50914]/15 text-[#ff7077] font-semibold">
                Saytda yo'q: {tmdbCoverage.missing}
              </span>
              <button
                onClick={() => loadTmdbInsights(tmdbCategory, tmdbPage)}
                disabled={loadingTmdb}
                className="p-1.5 rounded-lg bg-white/5 hover:bg-[#E50914] text-white transition"
                title="Yangilash"
              >
                <span
                  className={`material-symbols-outlined text-[16px] ${
                    loadingTmdb ? "animate-spin" : ""
                  }`}
                >
                  refresh
                </span>
              </button>
            </div>
          </div>

          {tmdbToast && (
            <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs flex items-center justify-between">
              <span>{tmdbToast}</span>
              <button onClick={() => setTmdbToast(null)}>✕</button>
            </div>
          )}

          {tmdbError && (
            <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-sm">
              {tmdbError}
            </div>
          )}

          {loadingTmdb ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {[...Array(6)].map((_, i) => (
                <div
                  key={i}
                  className="h-44 rounded-2xl bg-white/5 animate-pulse border border-white/10"
                />
              ))}
            </div>
          ) : !tmdbData || tmdbData.items.length === 0 ? (
            <div className="p-12 text-center text-zinc-500 rounded-2xl border border-white/10 bg-[#12141a] text-sm">
              TMDb dan natijalar topilmadi (TMDB_API_KEY sozlanganligini tekshiring).
            </div>
          ) : (
            <>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {tmdbData.items.map((item) => {
                  const key = `${item.media_type}:${item.tmdb_id}`;
                  return (
                    <div
                      key={key}
                      className="rounded-2xl border border-white/10 bg-[#12141a] p-4 flex gap-3.5 hover:border-white/20 transition"
                    >
                      <div className="w-20 h-28 rounded-xl overflow-hidden bg-zinc-800 shrink-0 border border-white/10">
                        {item.poster_url ? (
                          <img
                            src={item.poster_url}
                            alt={item.title}
                            className="w-full h-full object-cover"
                          />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center text-zinc-600">
                            <span className="material-symbols-outlined">movie</span>
                          </div>
                        )}
                      </div>

                      <div className="min-w-0 flex-1 flex flex-col justify-between">
                        <div>
                          <div className="flex items-start justify-between gap-2">
                            <h3 className="text-sm font-bold text-white line-clamp-2">
                              {item.title}
                            </h3>
                            <span className="text-[10px] font-bold uppercase px-1.5 py-0.5 rounded bg-white/10 text-zinc-300 shrink-0">
                              {item.media_type === "series" ? "Serial" : "Kino"}
                            </span>
                          </div>

                          <div className="flex flex-wrap items-center gap-2 text-xs text-zinc-400 mt-1">
                            {item.release_date && <span>{item.release_date}</span>}
                            {item.vote_average > 0 && (
                              <span className="text-[#F5C518] font-bold">
                                ★ {item.vote_average}
                              </span>
                            )}
                            <span className="text-zinc-500">
                              Pop: {Math.round(item.popularity)}
                            </span>
                          </div>

                          {item.overview && (
                            <p className="text-[11px] text-zinc-500 line-clamp-2 mt-1.5">
                              {item.overview}
                            </p>
                          )}
                        </div>

                        <div className="pt-2.5 flex flex-wrap items-center gap-2">
                          {item.in_library ? (
                            <span className="px-2.5 py-1 rounded-lg bg-emerald-500/15 text-emerald-400 text-[11px] font-bold">
                              Saytda bor #{item.library_code}
                            </span>
                          ) : item.is_requested ? (
                            <span className="px-2.5 py-1 rounded-lg bg-blue-500/15 text-blue-400 text-[11px] font-bold">
                              Buyurtmada ({item.request_votes} ovoz)
                            </span>
                          ) : (
                            <button
                              onClick={() => handleRequestFromTmdb(item)}
                              disabled={requestingKey === key}
                              className="px-3 py-1.5 rounded-lg bg-[#E50914] hover:bg-[#b80710] disabled:opacity-50 text-white text-[11px] font-bold transition"
                            >
                              {requestingKey === key
                                ? "Qo'shilmoqda..."
                                : "+ Buyurtmaga qo'shish"}
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Pagination */}
              <div className="flex items-center justify-center gap-2 pt-2">
                <button
                  onClick={() => setTmdbPage((p) => Math.max(1, p - 1))}
                  disabled={tmdbPage <= 1}
                  className="px-3 py-1.5 rounded-xl bg-white/5 hover:bg-[#E50914] disabled:opacity-40 text-xs font-bold text-white transition"
                >
                  ← Oldingi
                </button>
                <span className="text-xs text-zinc-400">
                  Sahifa {tmdbData.page} / {tmdbData.total_pages}
                </span>
                <button
                  onClick={() =>
                    setTmdbPage((p) => Math.min(tmdbData.total_pages || 1, p + 1))
                  }
                  disabled={tmdbPage >= (tmdbData.total_pages || 1)}
                  className="px-3 py-1.5 rounded-xl bg-white/5 hover:bg-[#E50914] disabled:opacity-40 text-xs font-bold text-white transition"
                >
                  Keyingi →
                </button>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
