"use client";

import { useEffect, useState } from "react";
import { fetchApi } from "@/lib/api";

type ReportItem = {
  id: number;
  media_type: "movie" | "series";
  movie_id?: number | null;
  series_id?: number | null;
  episode_id?: number | null;
  issue_type: string;
  description?: string | null;
  file_url?: string | null;
  file_type?: string | null;
  status: "pending" | "resolved" | "rejected";
  ip_address?: string | null;
  created_at?: string | null;
  media_title?: string | null;
  media_code_or_id?: string | null;
};

const ISSUE_LABELS: Record<string, { label: string; color: string }> = {
  poster_xato: { label: "🖼 Poster noto'g'ri", color: "bg-blue-500/20 text-blue-300 border-blue-500/30" },
  dublikat: { label: "👥 Dublikat", color: "bg-purple-500/20 text-purple-300 border-purple-500/30" },
  video_xato: { label: "🎞 Video noto'g'ri", color: "bg-rose-500/20 text-rose-300 border-rose-500/30" },
  ovoz_xato: { label: "🔇 Ovozda muammo", color: "bg-amber-500/20 text-amber-300 border-amber-500/30" },
  malumot_xato: { label: "📝 Ma'lumot xato", color: "bg-sky-500/20 text-sky-300 border-sky-500/30" },
  treyler_xato: { label: "🍿 Treyler ishlamayapti", color: "bg-orange-500/20 text-orange-300 border-orange-500/30" },
  boshqa: { label: "✍️ Boshqa xatolik", color: "bg-gray-500/20 text-gray-300 border-gray-500/30" },
};

export default function ReportsPage() {
  const [reports, setReports] = useState<ReportItem[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [pendingCount, setPendingCount] = useState<number>(0);
  const [activeTab, setActiveTab] = useState<string>("all"); // all | pending | resolved | rejected
  const [loading, setLoading] = useState<boolean>(true);
  const [actionLoading, setActionLoading] = useState<number | null>(null);

  // Media preview modal state
  const [previewMedia, setPreviewMedia] = useState<{ url: string; type: "image" | "video"; title: string } | null>(null);

  const loadReports = async (status?: string) => {
    setLoading(true);
    try {
      const endpoint = status && status !== "all" ? `/reports?status=${status}&limit=100` : `/reports?limit=100`;
      const res = await fetchApi(endpoint);
      setReports(res.items || []);
      setTotal(res.total || 0);
      setPendingCount(res.pending_count || 0);
    } catch (e) {
      console.error("Shikoyatlarni yuklashda xatolik:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReports(activeTab);
  }, [activeTab]);

  const handleStatusChange = async (id: number, newStatus: "resolved" | "rejected" | "pending") => {
    setActionLoading(id);
    try {
      await fetchApi(`/reports/${id}`, {
        method: "PATCH",
        body: JSON.stringify({ status: newStatus }),
      });
      setReports((prev) =>
        prev.map((r) => (r.id === id ? { ...r, status: newStatus } : r))
      );
      if (newStatus !== "pending") {
        setPendingCount((c) => Math.max(0, c - 1));
      }
    } catch (e: any) {
      alert("Statusni o'zgartirishda xatolik: " + (e.message || ""));
    } finally {
      setActionLoading(null);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Haqiqatan ham bu shikoyatni o'chirmoqchimisiz?")) return;
    setActionLoading(id);
    try {
      await fetchApi(`/reports/${id}`, {
        method: "DELETE",
      });
      setReports((prev) => prev.filter((r) => r.id !== id));
      setTotal((t) => Math.max(0, t - 1));
    } catch (e: any) {
      alert("O'chirishda xatolik: " + (e.message || ""));
    } finally {
      setActionLoading(null);
    }
  };

  const API_STATIC_BASE = process.env.NEXT_PUBLIC_API_URL?.replace(/\/api\/v1\/?$/, "") || "http://localhost:8000";

  return (
    <div className="p-4 sm:p-6 lg:p-8 space-y-6 max-w-7xl mx-auto">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <span className="material-symbols-outlined text-3xl text-amber-400">
              report_problem
            </span>
            <h1 className="text-2xl sm:text-3xl font-bold font-display tracking-tight text-white">
              Shikoyatlar va Xatoliklar
            </h1>
          </div>
          <p className="text-xs sm:text-sm text-text-secondary mt-1">
            Foydalanuvchilar tomonidan saytdan yuborilgan xatolik xabarlari, skrinshot va videolar.
          </p>
        </div>

        <button
          onClick={() => loadReports(activeTab)}
          className="px-4 py-2 bg-white/5 hover:bg-white/10 active:scale-95 border border-white/10 rounded-xl text-xs sm:text-sm font-medium transition-all flex items-center gap-2"
        >
          <span className="material-symbols-outlined text-base">refresh</span>
          <span>Yangilash</span>
        </button>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4">
        <div className="metric-card rounded-2xl p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between text-text-secondary mb-2">
            <span className="text-xs uppercase font-bold tracking-wider">Jami arizalar</span>
            <span className="material-symbols-outlined text-lg">receipt_long</span>
          </div>
          <div className="text-2xl sm:text-3xl font-black text-white">{total}</div>
        </div>

        <div className="metric-card rounded-2xl p-4 flex flex-col justify-between border-amber-500/20 bg-amber-950/20">
          <div className="flex items-center justify-between text-amber-400 mb-2">
            <span className="text-xs uppercase font-bold tracking-wider">Kutilmoqda</span>
            <span className="material-symbols-outlined text-lg">pending_actions</span>
          </div>
          <div className="text-2xl sm:text-3xl font-black text-amber-300">{pendingCount}</div>
        </div>

        <div className="metric-card rounded-2xl p-4 flex flex-col justify-between border-emerald-500/20 bg-emerald-950/20">
          <div className="flex items-center justify-between text-emerald-400 mb-2">
            <span className="text-xs uppercase font-bold tracking-wider">Hal qilindi</span>
            <span className="material-symbols-outlined text-lg">check_circle</span>
          </div>
          <div className="text-2xl sm:text-3xl font-black text-emerald-300">
            {reports.filter((r) => r.status === "resolved").length}
          </div>
        </div>

        <div className="metric-card rounded-2xl p-4 flex flex-col justify-between border-red-500/20 bg-red-950/20">
          <div className="flex items-center justify-between text-red-400 mb-2">
            <span className="text-xs uppercase font-bold tracking-wider">Rad etildi</span>
            <span className="material-symbols-outlined text-lg">cancel</span>
          </div>
          <div className="text-2xl sm:text-3xl font-black text-red-300">
            {reports.filter((r) => r.status === "rejected").length}
          </div>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 border-b border-white/10 pb-2 overflow-x-auto custom-scrollbar">
        {[
          { id: "all", label: "Hammasi", count: total },
          { id: "pending", label: "Kutilmoqda", count: pendingCount },
          { id: "resolved", label: "Hal qilingan" },
          { id: "rejected", label: "Rad etilgan" },
        ].map((tab) => {
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold transition-all whitespace-nowrap flex items-center gap-2 ${
                isActive
                  ? "bg-primary-container text-white shadow-lg shadow-primary-container/20"
                  : "bg-surface-container-lowest text-text-secondary hover:text-white hover:bg-white/5"
              }`}
            >
              <span>{tab.label}</span>
              {tab.count !== undefined && (
                <span
                  className={`text-[11px] px-1.5 py-0.2 rounded-full font-bold ${
                    isActive ? "bg-white/20 text-white" : "bg-white/10 text-text-secondary"
                  }`}
                >
                  {tab.count}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Reports Table / List */}
      <div className="glass-panel rounded-2xl overflow-hidden border border-white/10 shadow-xl">
        {loading ? (
          <div className="py-20 text-center flex flex-col items-center justify-center gap-3">
            <span className="animate-spin material-symbols-outlined text-3xl text-primary-container">
              progress_activity
            </span>
            <p className="text-sm text-text-secondary">Shikoyatlar yuklanmoqda...</p>
          </div>
        ) : reports.length === 0 ? (
          <div className="py-20 text-center flex flex-col items-center justify-center gap-3">
            <span className="material-symbols-outlined text-5xl text-text-secondary/40">
              verified
            </span>
            <p className="text-base font-semibold text-white">Hech qanday shikoyat topilmadi</p>
            <p className="text-xs text-text-secondary">
              Tanlangan filtr bo&apos;yicha yangi xabarlar mavjud emas.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto custom-scrollbar">
            <table className="w-full text-left text-xs sm:text-sm">
              <thead className="bg-surface-container-lowest/80 text-text-secondary font-medium uppercase text-[11px] tracking-wider border-b border-white/10">
                <tr>
                  <th className="py-3 px-4">ID</th>
                  <th className="py-3 px-4">Media</th>
                  <th className="py-3 px-4">Muammo turi</th>
                  <th className="py-3 px-4">User izohi</th>
                  <th className="py-3 px-4">Fayl</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Vaqt</th>
                  <th className="py-3 px-4 text-right">Amallar</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {reports.map((report) => {
                  const issueMeta = ISSUE_LABELS[report.issue_type] || {
                    label: report.issue_type,
                    color: "bg-white/10 text-white border-white/20",
                  };

                  const fullFileUrl = report.file_url?.startsWith("http")
                    ? report.file_url
                    : `${API_STATIC_BASE}${report.file_url}`;

                  return (
                    <tr key={report.id} className="data-table-row">
                      <td className="py-3 px-4 font-mono text-text-secondary font-bold">
                        #{report.id}
                      </td>

                      {/* Media Link */}
                      <td className="py-3 px-4">
                        <div className="font-semibold text-white truncate max-w-[160px] sm:max-w-[220px]">
                          {report.media_title || "Noma'lum"}
                        </div>
                        <div className="flex items-center gap-2 mt-0.5">
                          <span className="text-[10px] uppercase font-bold px-1.5 py-0.2 rounded bg-white/5 text-text-secondary border border-white/10">
                            {report.media_type === "movie" ? "Kino" : "Serial"}
                          </span>
                          {report.media_code_or_id && (
                            <a
                              href={
                                report.media_type === "movie"
                                  ? `https://kinochi.uz/movie/${report.media_code_or_id}`
                                  : `https://kinochi.uz/series/${report.media_code_or_id}`
                              }
                              target="_blank"
                              rel="noreferrer"
                              className="text-[11px] text-primary-container hover:underline flex items-center gap-0.5"
                            >
                              <span>Saytda ko&apos;rish</span>
                              <span className="material-symbols-outlined text-[11px]">open_in_new</span>
                            </a>
                          )}
                        </div>
                      </td>

                      {/* Issue Type Chip */}
                      <td className="py-3 px-4">
                        <span
                          className={`inline-block px-2.5 py-1 rounded-lg text-xs font-semibold border ${issueMeta.color}`}
                        >
                          {issueMeta.label}
                        </span>
                      </td>

                      {/* Description */}
                      <td className="py-3 px-4 max-w-[200px] sm:max-w-[280px]">
                        <p className="text-text-primary text-xs leading-relaxed line-clamp-2">
                          {report.description || <span className="text-text-secondary/40 italic">Izoh yo&apos;q</span>}
                        </p>
                      </td>

                      {/* Attached File Preview */}
                      <td className="py-3 px-4">
                        {report.file_url ? (
                          report.file_type === "image" ? (
                            <button
                              type="button"
                              onClick={() =>
                                setPreviewMedia({
                                  url: fullFileUrl,
                                  type: "image",
                                  title: report.media_title || "Skrinshot",
                                })
                              }
                              className="relative group rounded-lg overflow-hidden border border-white/10 hover:border-amber-400/50 transition-all block"
                              title="Rasmni kattalashtirish"
                            >
                              <img
                                src={fullFileUrl}
                                alt="Skrinshot"
                                className="w-12 h-12 object-cover group-hover:scale-105 transition-transform"
                              />
                              <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 flex items-center justify-center transition-opacity">
                                <span className="material-symbols-outlined text-white text-sm">zoom_in</span>
                              </div>
                            </button>
                          ) : (
                            <button
                              type="button"
                              onClick={() =>
                                setPreviewMedia({
                                  url: fullFileUrl,
                                  type: "video",
                                  title: report.media_title || "Video",
                                })
                              }
                              className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-amber-500/15 border border-amber-500/30 text-amber-300 hover:bg-amber-500/25 transition-all text-xs font-semibold"
                              title="Videoni ko'rish"
                            >
                              <span className="material-symbols-outlined text-base">play_circle</span>
                              <span>Video</span>
                            </button>
                          )
                        ) : (
                          <span className="text-text-secondary/40 text-xs italic">—</span>
                        )}
                      </td>

                      {/* Status */}
                      <td className="py-3 px-4">
                        {report.status === "pending" && (
                          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold bg-amber-500/15 text-amber-300 border border-amber-500/30">
                            <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse"></span>
                            Kutilmoqda
                          </span>
                        )}
                        {report.status === "resolved" && (
                          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
                            <span className="material-symbols-outlined text-[13px]">check</span>
                            Hal qilindi
                          </span>
                        )}
                        {report.status === "rejected" && (
                          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold bg-red-500/15 text-red-300 border border-red-500/30">
                            <span className="material-symbols-outlined text-[13px]">close</span>
                            Rad etildi
                          </span>
                        )}
                      </td>

                      {/* Created At */}
                      <td className="py-3 px-4 text-xs text-text-secondary whitespace-nowrap">
                        {report.created_at ? new Date(report.created_at).toLocaleString("uz-UZ", {
                          month: "short",
                          day: "numeric",
                          hour: "2-digit",
                          minute: "2-digit",
                        }) : "—"}
                      </td>

                      {/* Actions */}
                      <td className="py-3 px-4 text-right whitespace-nowrap">
                        <div className="flex items-center justify-end gap-1.5">
                          {report.status !== "resolved" && (
                            <button
                              disabled={actionLoading === report.id}
                              onClick={() => handleStatusChange(report.id, "resolved")}
                              className="p-1.5 bg-emerald-500/15 hover:bg-emerald-500/25 text-emerald-400 border border-emerald-500/30 rounded-lg transition-all active:scale-95 disabled:opacity-50"
                              title="Hal qilindi deb belgilash"
                            >
                              <span className="material-symbols-outlined text-base">check</span>
                            </button>
                          )}

                          {report.status !== "rejected" && (
                            <button
                              disabled={actionLoading === report.id}
                              onClick={() => handleStatusChange(report.id, "rejected")}
                              className="p-1.5 bg-amber-500/15 hover:bg-amber-500/25 text-amber-400 border border-amber-500/30 rounded-lg transition-all active:scale-95 disabled:opacity-50"
                              title="Rad etish"
                            >
                              <span className="material-symbols-outlined text-base">close</span>
                            </button>
                          )}

                          <button
                            disabled={actionLoading === report.id}
                            onClick={() => handleDelete(report.id)}
                            className="p-1.5 bg-red-500/15 hover:bg-red-500/25 text-red-400 border border-red-500/30 rounded-lg transition-all active:scale-95 disabled:opacity-50"
                            title="O'chirish"
                          >
                            <span className="material-symbols-outlined text-base">delete</span>
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Media Preview Modal */}
      {previewMedia && (
        <div
          onClick={() => setPreviewMedia(null)}
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/90 backdrop-blur-md animate-in fade-in duration-200"
        >
          <div
            onClick={(e) => e.stopPropagation()}
            className="relative max-w-4xl max-h-[90vh] bg-surface-container-high border border-white/10 rounded-2xl overflow-hidden shadow-2xl flex flex-col"
          >
            <div className="p-3 border-b border-white/10 flex items-center justify-between bg-surface-container-lowest">
              <span className="text-xs font-semibold text-white truncate">{previewMedia.title}</span>
              <button
                type="button"
                onClick={() => setPreviewMedia(null)}
                className="p-1 text-text-secondary hover:text-white rounded"
              >
                <span className="material-symbols-outlined text-lg">close</span>
              </button>
            </div>

            <div className="p-2 flex items-center justify-center bg-black">
              {previewMedia.type === "image" ? (
                <img
                  src={previewMedia.url}
                  alt={previewMedia.title}
                  className="max-h-[80vh] w-auto object-contain rounded"
                />
              ) : (
                <video
                  src={previewMedia.url}
                  controls
                  autoPlay
                  className="max-h-[80vh] max-w-full rounded"
                />
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
