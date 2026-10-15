"use client";

import { useState, useEffect } from "react";
import { fetchApi } from "@/lib/api";

interface Defect {
  field?: string;
  code?: string;
  message?: string;
}

interface RejectedItem {
  id: number;
  media_type: string;
  source: string;
  source_key: string;
  title: string;
  payload: Record<string, any>;
  defects: Defect[];
  media_id: number | null;
  attempts: number;
  status: "rejected" | "resolved" | "blacklisted" | string;
  created_at: string;
  updated_at: string;
}

export default function RejectedPage() {
  const [items, setItems] = useState<RejectedItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [searchTerm, setSearchTerm] = useState("");
  const [page, setPage] = useState(0);
  const limit = 20;

  // Selected item for detail modal
  const [selectedItem, setSelectedItem] = useState<RejectedItem | null>(null);
  const [actionLoading, setActionLoading] = useState<number | null>(null);
  const [notification, setNotification] = useState<{ message: string; type: "success" | "error" } | null>(null);

  const showNotification = (message: string, type: "success" | "error" = "success") => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 4000);
  };

  const fetchRejectedItems = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      params.append("skip", (page * limit).toString());
      params.append("limit", limit.toString());
      if (statusFilter) {
        params.append("status", statusFilter);
      }

      const res = await fetchApi(`/rejected?${params.toString()}`);
      setItems(res.items || []);
      setTotal(res.total || 0);
    } catch (err: any) {
      console.error("Error fetching rejected items:", err);
      showNotification(err.message || "Rad etilgan kontentlarni yuklashda xatolik", "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRejectedItems();
  }, [page, statusFilter]);

  const handleRetry = async (item: RejectedItem) => {
    if (!confirm(`"${item.title}" elementini qayta urinish holatiga o'tkazmoqchimisiz?`)) {
      return;
    }
    try {
      setActionLoading(item.id);
      await fetchApi(`/rejected/${item.id}/retry`, { method: "POST" });
      showNotification(`"${item.title}" qayta urinish uchun tayyorlandi.`);
      fetchRejectedItems();
      if (selectedItem?.id === item.id) {
        setSelectedItem(null);
      }
    } catch (err: any) {
      showNotification(err.message || "Qayta urinishda xatolik yuz berdi", "error");
    } finally {
      setActionLoading(null);
    }
  };

  const handleBlacklist = async (item: RejectedItem) => {
    if (!confirm(`"${item.title}" ni butunlay qora ro'yxatga kiritmoqchimisiz?`)) {
      return;
    }
    try {
      setActionLoading(item.id);
      await fetchApi(`/rejected/${item.id}/blacklist`, { method: "POST" });
      showNotification(`"${item.title}" qora ro'yxatga kiritildi.`);
      fetchRejectedItems();
      if (selectedItem?.id === item.id) {
        setSelectedItem(null);
      }
    } catch (err: any) {
      showNotification(err.message || "Qora ro'yxatga olishda xatolik", "error");
    } finally {
      setActionLoading(null);
    }
  };

  const filteredItems = items.filter((item) => {
    if (!searchTerm.trim()) return true;
    const term = searchTerm.toLowerCase();
    return (
      item.title.toLowerCase().includes(term) ||
      item.source.toLowerCase().includes(term) ||
      item.source_key.toLowerCase().includes(term)
    );
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "rejected":
        return <span className="px-2.5 py-1 text-xs rounded-full bg-rose-500/20 text-rose-400 border border-rose-500/30 font-medium">Rad etilgan</span>;
      case "resolved":
        return <span className="px-2.5 py-1 text-xs rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 font-medium">Hal qilingan</span>;
      case "blacklisted":
        return <span className="px-2.5 py-1 text-xs rounded-full bg-slate-500/20 text-slate-400 border border-slate-500/30 font-medium">Qora ro'yxatda</span>;
      default:
        return <span className="px-2.5 py-1 text-xs rounded-full bg-amber-500/20 text-amber-400 border border-amber-500/30 font-medium">{status}</span>;
    }
  };

  const getMediaTypeBadge = (mediaType: string) => {
    const isMovie = mediaType === "movie";
    const isSeries = mediaType === "series";
    return (
      <span
        className={`px-2 py-0.5 text-[11px] rounded uppercase tracking-wider font-semibold ${
          isMovie
            ? "bg-blue-500/20 text-blue-400 border border-blue-500/30"
            : isSeries
            ? "bg-purple-500/20 text-purple-400 border border-purple-500/30"
            : "bg-amber-500/20 text-amber-400 border border-amber-500/30"
        }`}
      >
        {mediaType}
      </span>
    );
  };

  return (
    <div className="p-6 sm:p-8 space-y-6">
      {/* Toast Notification */}
      {notification && (
        <div
          className={`fixed top-5 right-5 z-50 px-4 py-3 rounded-xl shadow-lg border backdrop-blur-md flex items-center gap-3 transition-all ${
            notification.type === "success"
              ? "bg-emerald-950/80 border-emerald-500/30 text-emerald-300"
              : "bg-rose-950/80 border-rose-500/30 text-rose-300"
          }`}
        >
          <span className="material-symbols-outlined text-xl">
            {notification.type === "success" ? "check_circle" : "error"}
          </span>
          <span className="text-sm font-medium">{notification.message}</span>
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <span className="material-symbols-outlined text-rose-400 text-3xl">rule_folder</span>
            <h1 className="text-2xl sm:text-3xl font-bold text-white">Rad Etilgan Kontentlar</h1>
          </div>
          <p className="text-sm text-text-secondary mt-1">
            Admission Gate tekshiruvidan o'tmagan yoki nuqsonli bo'lgan kontentlar ro'yxati (Jami: {total})
          </p>
        </div>

        <button
          onClick={fetchRejectedItems}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 text-text-primary text-sm font-medium transition-all"
        >
          <span className={`material-symbols-outlined text-lg ${loading ? "animate-spin" : ""}`}>refresh</span>
          Yangilash
        </button>
      </div>

      {/* Filter Tabs & Search */}
      <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4">
        <div className="flex items-center gap-1.5 p-1 bg-surface-container-high/40 rounded-xl border border-white/5 overflow-x-auto">
          {[
            { label: "Barchasi", value: "" },
            { label: "Rad etilgan", value: "rejected" },
            { label: "Hal qilingan", value: "resolved" },
            { label: "Qora ro'yxat", value: "blacklisted" },
          ].map((tab) => (
            <button
              key={tab.value}
              onClick={() => {
                setStatusFilter(tab.value);
                setPage(0);
              }}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all whitespace-nowrap ${
                statusFilter === tab.value
                  ? "bg-primary-container text-background-obsidian font-bold shadow"
                  : "text-text-secondary hover:text-white hover:bg-white/5"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div className="relative min-w-[280px]">
          <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-text-secondary text-lg">
            search
          </span>
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Nomi yoki manbasi bo'yicha qidiruv..."
            className="w-full pl-9 pr-4 py-2 bg-surface-container-high/40 border border-white/10 rounded-xl text-sm text-white placeholder-text-secondary focus:outline-none focus:border-primary-container transition-colors"
          />
        </div>
      </div>

      {/* Content Table */}
      <div className="bg-surface-container-lowest/60 border border-white/5 rounded-2xl overflow-hidden shadow-xl">
        {loading ? (
          <div className="p-12 text-center text-text-secondary">
            <span className="material-symbols-outlined text-4xl animate-spin text-primary-container mb-3">progress_activity</span>
            <p>Rad etilgan kontentlar yuklanmoqda...</p>
          </div>
        ) : filteredItems.length === 0 ? (
          <div className="p-12 text-center text-text-secondary">
            <span className="material-symbols-outlined text-4xl text-text-secondary/50 mb-3">task_alt</span>
            <p className="font-medium text-white">Hech qanday rad etilgan kontent topilmadi</p>
            <p className="text-xs text-text-secondary mt-1">Barcha kontentlar Admission Gate filtrlari talablariga muvofiq.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-white/5 text-[11px] uppercase tracking-wider text-text-secondary bg-white/[0.02]">
                  <th className="py-3 px-4 font-semibold">ID</th>
                  <th className="py-3 px-4 font-semibold">Turi</th>
                  <th className="py-3 px-4 font-semibold">Sarlavha & Manba</th>
                  <th className="py-3 px-4 font-semibold">Nuqsonlar (Defects)</th>
                  <th className="py-3 px-4 font-semibold text-center">Urinishlar</th>
                  <th className="py-3 px-4 font-semibold">Holati</th>
                  <th className="py-3 px-4 font-semibold text-right">Amallar</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 text-sm">
                {filteredItems.map((item) => (
                  <tr key={item.id} className="hover:bg-white/[0.02] transition-colors">
                    <td className="py-3.5 px-4 font-mono text-xs text-text-secondary">#{item.id}</td>
                    <td className="py-3.5 px-4">{getMediaTypeBadge(item.media_type)}</td>
                    <td className="py-3.5 px-4">
                      <div className="font-semibold text-white">{item.title}</div>
                      <div className="text-xs text-text-secondary flex items-center gap-2 mt-0.5">
                        <span className="px-1.5 py-0.5 rounded bg-white/5 font-mono">{item.source}</span>
                        <span className="truncate max-w-[200px]" title={item.source_key}>
                          {item.source_key}
                        </span>
                      </div>
                    </td>
                    <td className="py-3.5 px-4 max-w-xs">
                      <div className="flex flex-wrap gap-1.5">
                        {(item.defects || []).slice(0, 3).map((d, i) => (
                          <span
                            key={i}
                            title={d.message || d.code}
                            className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] bg-rose-500/10 text-rose-300 border border-rose-500/20"
                          >
                            <span className="font-mono">{d.field || d.code}</span>
                          </span>
                        ))}
                        {(item.defects || []).length > 3 && (
                          <span className="px-1.5 py-0.5 rounded text-[10px] bg-white/5 text-text-secondary">
                            +{(item.defects || []).length - 3}
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="py-3.5 px-4 text-center font-mono text-xs text-text-secondary">
                      {item.attempts}
                    </td>
                    <td className="py-3.5 px-4">{getStatusBadge(item.status)}</td>
                    <td className="py-3.5 px-4 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <button
                          onClick={() => setSelectedItem(item)}
                          className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-text-secondary hover:text-white transition-colors"
                          title="Tafsilotlarni ko'rish"
                        >
                          <span className="material-symbols-outlined text-lg">info</span>
                        </button>

                        {item.status !== "resolved" && (
                          <button
                            onClick={() => handleRetry(item)}
                            disabled={actionLoading === item.id}
                            className="p-1.5 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 transition-colors"
                            title="Qayta urinish (Retry)"
                          >
                            <span className="material-symbols-outlined text-lg">replay</span>
                          </button>
                        )}

                        {item.status !== "blacklisted" && (
                          <button
                            onClick={() => handleBlacklist(item)}
                            disabled={actionLoading === item.id}
                            className="p-1.5 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 transition-colors"
                            title="Qora ro'yxatga olish (Blacklist)"
                          >
                            <span className="material-symbols-outlined text-lg">block</span>
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination footer */}
        {total > limit && (
          <div className="p-4 border-t border-white/5 flex items-center justify-between text-xs text-text-secondary">
            <span>
              Ko'rsatilmoqda: {page * limit + 1} - {Math.min((page + 1) * limit, total)} / Jami: {total}
            </span>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage((p) => Math.max(0, p - 1))}
                disabled={page === 0}
                className="px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 disabled:opacity-40 disabled:hover:bg-white/5 transition-all"
              >
                Oldingi
              </button>
              <button
                onClick={() => setPage((p) => p + 1)}
                disabled={(page + 1) * limit >= total}
                className="px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 disabled:opacity-40 disabled:hover:bg-white/5 transition-all"
              >
                Keyingi
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Detail Modal */}
      {selectedItem && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-surface-container-low border border-white/10 rounded-2xl max-w-2xl w-full p-6 space-y-5 max-h-[90vh] overflow-y-auto">
            <div className="flex items-start justify-between gap-4 border-b border-white/10 pb-4">
              <div>
                <div className="flex items-center gap-2">
                  {getMediaTypeBadge(selectedItem.media_type)}
                  <h2 className="text-xl font-bold text-white">{selectedItem.title}</h2>
                </div>
                <p className="text-xs text-text-secondary mt-1">
                  ID: #{selectedItem.id} | Manba: {selectedItem.source} ({selectedItem.source_key})
                </p>
              </div>
              <button
                onClick={() => setSelectedItem(null)}
                className="p-1 rounded-lg hover:bg-white/10 text-text-secondary hover:text-white transition-colors"
              >
                <span className="material-symbols-outlined text-xl">close</span>
              </button>
            </div>

            {/* Defects Details */}
            <div className="space-y-2">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-rose-400">
                Aniqlangan nuqsonlar ({selectedItem.defects?.length || 0}):
              </h3>
              <div className="space-y-2">
                {(selectedItem.defects || []).map((defect, i) => (
                  <div
                    key={i}
                    className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-xs space-y-1"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-rose-300 font-mono">
                        {defect.field || "field"} : {defect.code || "defect"}
                      </span>
                    </div>
                    <p className="text-text-primary">{defect.message || "Batafsil xabar berilmagan."}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Raw Payload Preview */}
            <div className="space-y-2">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-text-secondary">
                Saqlangan parametrlar (Payload):
              </h3>
              <pre className="p-3 bg-surface-container-lowest border border-white/5 rounded-xl text-xs font-mono text-emerald-400 overflow-x-auto max-h-48">
                {JSON.stringify(selectedItem.payload, null, 2)}
              </pre>
            </div>

            {/* Modal Actions */}
            <div className="flex items-center justify-end gap-3 pt-3 border-t border-white/10">
              <button
                onClick={() => setSelectedItem(null)}
                className="px-4 py-2 rounded-xl bg-white/5 hover:bg-white/10 text-text-secondary hover:text-white text-xs font-medium transition-colors"
              >
                Yopish
              </button>
              {selectedItem.status !== "resolved" && (
                <button
                  onClick={() => handleRetry(selectedItem)}
                  className="px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-black font-semibold text-xs transition-colors flex items-center gap-1.5"
                >
                  <span className="material-symbols-outlined text-base">replay</span>
                  Qayta urinish
                </button>
              )}
              {selectedItem.status !== "blacklisted" && (
                <button
                  onClick={() => handleBlacklist(selectedItem)}
                  className="px-4 py-2 rounded-xl bg-rose-500 hover:bg-rose-600 text-white font-semibold text-xs transition-colors flex items-center gap-1.5"
                >
                  <span className="material-symbols-outlined text-base">block</span>
                  Qora ro'yxatga olish
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
