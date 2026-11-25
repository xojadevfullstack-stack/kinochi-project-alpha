"use client";

import { useEffect, useState } from "react";
import { fetchApi } from "@/lib/api";

export type ContentRequestItem = {
  id: number;
  title: string;
  original_title?: string | null;
  media_type: "movie" | "series";
  release_year?: number | null;
  poster_url?: string | null;
  overview?: string | null;
  tmdb_id?: number | null;
  kinopoisk_id?: number | null;
  preferred_language: string;
  vote_count: number;
  status: "pending" | "in_review" | "completed" | "rejected";
  created_at: string;
  admin_notes?: string | null;
  user_contact?: string | null;
};

type ExternalResult = {
  tmdb_id?: number | null;
  kinopoisk_id?: number | null;
  title: string;
  original_title?: string | null;
  media_type: "movie" | "series";
  release_year?: number | null;
  poster_url?: string | null;
  overview?: string | null;
  vote_average?: number | null;
  in_library: boolean;
  library_code?: string | null;
  request_count: number;
  is_requested: boolean;
};

interface RequestsPanelProps {
  compactHeader?: boolean;
  onChanged?: () => void;
}

export default function RequestsPanel({
  compactHeader = false,
  onChanged,
}: RequestsPanelProps) {
  const [requests, setRequests] = useState<ContentRequestItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [feedback, setFeedback] = useState<{ type: "ok" | "err"; text: string } | null>(null);

  // External TMDb / Kinopoisk search to add request directly
  const [extQuery, setExtQuery] = useState("");
  const [extSearching, setExtSearching] = useState(false);
  const [extResults, setExtResults] = useState<ExternalResult[] | null>(null);
  const [addingTmdbKey, setAddingTmdbKey] = useState<string | null>(null);

  // Bridge Modal state
  const [bridgeModalOpen, setBridgeModalOpen] = useState(false);
  const [activeRequest, setActiveRequest] = useState<ContentRequestItem | null>(null);
  const [linkedContentCode, setLinkedContentCode] = useState("");
  const [adminNote, setAdminNote] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    loadRequests();
  }, [statusFilter]);

  const loadRequests = async () => {
    setLoading(true);
    try {
      const url = `/content-requests?limit=100&sort=votes${
        statusFilter && statusFilter !== "all" ? `&status=${statusFilter}` : "&status=all"
      }`;
      const data = await fetchApi(url);
      setRequests(data?.items || []);
      setTotal(data?.total ?? (data?.items || []).length);
    } catch (e: any) {
      setFeedback({ type: "err", text: e?.message || "So'rovlarni yuklashda xato" });
    } finally {
      setLoading(false);
    }
  };

  const handleExternalSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    const q = extQuery.trim();
    if (!q) return;
    setExtSearching(true);
    setFeedback(null);
    try {
      const data = await fetchApi(
        `/content-requests/external-search?q=${encodeURIComponent(q)}&limit=12`
      );
      setExtResults(data?.results || []);
    } catch (err: any) {
      setFeedback({ type: "err", text: err?.message || "TMDb qidiruvda xatolik" });
    } finally {
      setExtSearching(false);
    }
  };

  const handleCreateFromExternal = async (item: ExternalResult) => {
    const key = `${item.media_type}:${item.tmdb_id || item.kinopoisk_id || item.title}`;
    setAddingTmdbKey(key);
    setFeedback(null);
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
          kinopoisk_id: item.kinopoisk_id,
          preferred_language: "uz",
        }),
      });
      setFeedback({ type: "ok", text: `"${item.title}" buyurtmalar ro'yxatiga qo'shildi.` });
      setExtResults((prev) =>
        prev
          ? prev.map((r) =>
              r.tmdb_id === item.tmdb_id && r.title === item.title
                ? { ...r, is_requested: true, request_count: (r.request_count || 0) + 1 }
                : r
            )
          : prev
      );
      await loadRequests();
      onChanged?.();
    } catch (err: any) {
      setFeedback({ type: "err", text: err?.message || "Buyurtma yaratishda xatolik" });
    } finally {
      setAddingTmdbKey(null);
    }
  };

  const handleUpdateStatus = async (
    id: number,
    status: "pending" | "in_review" | "completed" | "rejected"
  ) => {
    setFeedback(null);
    try {
      await fetchApi(`/content-requests/${id}`, {
        method: "PATCH",
        body: JSON.stringify({ status }),
      });
      await loadRequests();
      onChanged?.();
    } catch (e: any) {
      setFeedback({ type: "err", text: "Holatni o'zgartirishda xato: " + e.message });
    }
  };

  const handleOpenBridge = (req: ContentRequestItem) => {
    setActiveRequest(req);
    setLinkedContentCode(
      req.admin_notes?.includes("Yuklandi: ")
        ? req.admin_notes.split("Yuklandi: ")[1]
        : ""
    );
    setAdminNote(req.admin_notes || "");
    setBridgeModalOpen(true);
  };

  const handleSaveBridge = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeRequest) return;
    setSubmitting(true);
    setFeedback(null);
    try {
      await fetchApi(`/content-requests/${activeRequest.id}`, {
        method: "PATCH",
        body: JSON.stringify({
          status: "completed",
          linked_content_code: linkedContentCode.trim(),
          admin_notes: adminNote.trim(),
        }),
      });
      setBridgeModalOpen(false);
      setActiveRequest(null);
      await loadRequests();
      onChanged?.();
    } catch (e: any) {
      setFeedback({ type: "err", text: "Ko'prikni saqlashda xato: " + e.message });
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Haqiqatan ham bu so'rovni o'chirmoqchimisiz?")) return;
    setFeedback(null);
    try {
      await fetchApi(`/content-requests/${id}`, { method: "DELETE" });
      await loadRequests();
      onChanged?.();
    } catch (e: any) {
      setFeedback({ type: "err", text: "O'chirishda xato: " + e.message });
    }
  };

  const filteredRequests = requests.filter((r) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      r.title.toLowerCase().includes(q) ||
      (r.original_title && r.original_title.toLowerCase().includes(q)) ||
      (r.tmdb_id && String(r.tmdb_id).includes(q)) ||
      (r.admin_notes && r.admin_notes.toLowerCase().includes(q))
    );
  });

  const pendingCount = requests.filter((r) => r.status === "pending").length;
  const inReviewCount = requests.filter((r) => r.status === "in_review").length;
  const completedCount = requests.filter((r) => r.status === "completed").length;

  return (
    <div className="space-y-5">
      {/* Header */}
      {!compactHeader && (
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight flex items-center gap-3">
              <span className="material-symbols-outlined text-[#E50914] text-3xl">add_to_queue</span>
              <span>Kino va Serial So'rovlari (Buyurtmalar)</span>
            </h1>
            <p className="text-sm text-zinc-400 mt-1">
              Foydalanuvchilar qidirib topa olmagan va TMDb orqali qo'shilgan buyurtmalar ro'yxati.
            </p>
          </div>
          <button
            onClick={loadRequests}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/10 hover:bg-[#E50914] text-white text-xs font-semibold transition"
          >
            <span className="material-symbols-outlined text-[17px]">refresh</span>
            <span>Yangilash</span>
          </button>
        </div>
      )}

      {feedback && (
        <div
          className={`p-3 rounded-xl text-xs font-medium flex items-center justify-between border ${
            feedback.type === "ok"
              ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-300"
              : "bg-red-500/10 border-red-500/30 text-red-300"
          }`}
        >
          <span>{feedback.text}</span>
          <button onClick={() => setFeedback(null)} className="opacity-70 hover:opacity-100">
            ✕
          </button>
        </div>
      )}

      {/* TMDb / Kinopoisk Quick Request Search */}
      <div className="bg-[#12141a] border border-white/10 rounded-2xl p-4 space-y-3">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2 text-sm font-bold text-white">
            <span className="material-symbols-outlined text-[#E50914] text-xl">travel_explore</span>
            <span>TMDb & Kinopoisk dan qidirib buyurtma yaratish</span>
          </div>
          {extResults !== null && (
            <button
              onClick={() => setExtResults(null)}
              className="text-xs text-zinc-400 hover:text-white"
            >
              Natijalarni yopish
            </button>
          )}
        </div>

        <form onSubmit={handleExternalSearch} className="flex gap-2">
          <input
            type="text"
            value={extQuery}
            onChange={(e) => setExtQuery(e.target.value)}
            placeholder="Kino yoki serial nomi (masalan: Avatar 3, Dune, Severance)..."
            className="flex-1 px-3.5 py-2 rounded-xl bg-white/5 border border-white/10 text-xs sm:text-sm text-white focus:outline-none focus:border-[#E50914]"
          />
          <button
            type="submit"
            disabled={extSearching || !extQuery.trim()}
            className="px-4 py-2 rounded-xl bg-[#E50914] hover:bg-[#b80710] disabled:opacity-50 text-white text-xs font-bold transition whitespace-nowrap"
          >
            {extSearching ? "Qidirilmoqda..." : "TMDb Qidirish"}
          </button>
        </form>

        {extResults !== null && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 pt-1">
            {extResults.length === 0 ? (
              <div className="col-span-full text-xs text-zinc-500 py-3 text-center">
                Hech narsa topilmadi.
              </div>
            ) : (
              extResults.map((item, idx) => {
                const key = `${item.media_type}:${item.tmdb_id || item.kinopoisk_id || item.title}`;
                return (
                  <div
                    key={`${key}-${idx}`}
                    className="flex gap-3 p-3 rounded-xl bg-white/[0.03] border border-white/10"
                  >
                    <div className="w-12 h-16 rounded-lg overflow-hidden bg-zinc-800 shrink-0">
                      {item.poster_url ? (
                        <img
                          src={item.poster_url}
                          alt={item.title}
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center text-zinc-600">
                          <span className="material-symbols-outlined text-lg">movie</span>
                        </div>
                      )}
                    </div>
                    <div className="min-w-0 flex-1 flex flex-col justify-between">
                      <div>
                        <div className="text-xs font-bold text-white truncate">{item.title}</div>
                        <div className="flex items-center gap-2 text-[11px] text-zinc-400 mt-0.5">
                          <span>{item.media_type === "series" ? "Serial" : "Kino"}</span>
                          {item.release_year && <span>• {item.release_year}</span>}
                          {item.vote_average ? (
                            <span className="text-[#F5C518] font-bold">★ {item.vote_average}</span>
                          ) : null}
                        </div>
                      </div>
                      <div className="pt-2">
                        {item.in_library ? (
                          <span className="inline-block px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-400 text-[11px] font-semibold">
                            Saytda bor {item.library_code ? `(#${item.library_code})` : ""}
                          </span>
                        ) : item.is_requested ? (
                          <button
                            onClick={() => handleCreateFromExternal(item)}
                            disabled={addingTmdbKey === key}
                            className="px-2.5 py-1 rounded-lg bg-white/10 hover:bg-[#E50914] text-white text-[11px] font-semibold transition"
                          >
                            +1 Ovoz ({item.request_count})
                          </button>
                        ) : (
                          <button
                            onClick={() => handleCreateFromExternal(item)}
                            disabled={addingTmdbKey === key}
                            className="px-2.5 py-1 rounded-lg bg-[#E50914] hover:bg-[#b80710] text-white text-[11px] font-bold transition"
                          >
                            {addingTmdbKey === key ? "Qo'shilmoqda..." : "+ Buyurtmaga qo'shish"}
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        )}
      </div>

      {/* Stats Counter Bar */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4">
        <div className="bg-[#12141a] border border-white/10 rounded-2xl p-4">
          <div className="text-xs text-zinc-400 font-medium">Jami so'rovlar</div>
          <div className="text-2xl font-black text-white mt-1">{total} ta</div>
        </div>
        <div className="bg-[#12141a] border border-white/10 rounded-2xl p-4">
          <div className="text-xs text-zinc-300 font-medium">Kutilmoqda</div>
          <div className="text-2xl font-black text-[#E50914] mt-1">{pendingCount} ta</div>
        </div>
        <div className="bg-[#12141a] border border-white/10 rounded-2xl p-4">
          <div className="text-xs text-blue-400 font-medium">Jarayonda</div>
          <div className="text-2xl font-black text-blue-400 mt-1">{inReviewCount} ta</div>
        </div>
        <div className="bg-[#12141a] border border-white/10 rounded-2xl p-4">
          <div className="text-xs text-emerald-400 font-medium">Bajarildi (Yuklangan)</div>
          <div className="text-2xl font-black text-emerald-400 mt-1">{completedCount} ta</div>
        </div>
      </div>

      {/* Filters and Search Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 bg-[#111318] border border-white/10 rounded-2xl p-3 sm:p-4">
        <div className="flex items-center gap-1.5 overflow-x-auto hide-scrollbar">
          {[
            { id: "all", label: "Barchasi" },
            { id: "pending", label: "Kutilmoqda" },
            { id: "in_review", label: "Jarayonda" },
            { id: "completed", label: "Bajarildi" },
            { id: "rejected", label: "Rad etildi" },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setStatusFilter(tab.id)}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold transition whitespace-nowrap ${
                statusFilter === tab.id
                  ? "bg-[#E50914] text-white shadow-md shadow-[#E50914]/25"
                  : "bg-white/5 hover:bg-white/10 text-zinc-400 hover:text-white"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <div className="relative flex-1 sm:w-64">
            <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400 text-lg">
              search
            </span>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Nomi yoki TMDb ID..."
              className="w-full pl-9 pr-3 py-1.5 rounded-xl bg-white/5 border border-white/10 text-xs text-white focus:outline-none focus:border-[#E50914]"
            />
          </div>
          <button
            onClick={loadRequests}
            title="Yangilash"
            className="p-1.5 rounded-xl bg-white/5 hover:bg-[#E50914] text-zinc-300 hover:text-white transition"
          >
            <span className={`material-symbols-outlined text-[18px] ${loading ? "animate-spin" : ""}`}>
              refresh
            </span>
          </button>
        </div>
      </div>

      {/* Requests List */}
      <div className="bg-[#111318] border border-white/10 rounded-2xl overflow-hidden shadow-xl">
        {loading ? (
          <div className="p-12 text-center text-zinc-400 text-sm">Yuklanmoqda...</div>
        ) : filteredRequests.length === 0 ? (
          <div className="p-12 text-center text-zinc-500 text-sm">
            Ushbu filtr bo'yicha hech qanday so'rov topilmadi.
          </div>
        ) : (
          <div className="divide-y divide-white/5">
            {filteredRequests.map((req) => {
              const statusConfig = {
                pending: {
                  label: "Kutilmoqda",
                  bg: "bg-[#E50914]/15 text-[#ff6b73] border-[#E50914]/30",
                },
                in_review: {
                  label: "Jarayonda",
                  bg: "bg-blue-500/15 text-blue-400 border-blue-500/30",
                },
                completed: {
                  label: "Bajarildi",
                  bg: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
                },
                rejected: {
                  label: "Rad etildi",
                  bg: "bg-zinc-500/15 text-zinc-400 border-zinc-500/30",
                },
              }[req.status] || {
                label: req.status,
                bg: "bg-white/10 text-white border-white/20",
              };

              return (
                <div
                  key={req.id}
                  className="p-4 sm:p-5 flex flex-col md:flex-row md:items-center justify-between gap-4 hover:bg-white/[0.02] transition"
                >
                  <div className="flex items-start gap-4">
                    <div className="w-14 h-20 bg-zinc-800 rounded-lg overflow-hidden shrink-0 border border-white/10 flex items-center justify-center">
                      {req.poster_url ? (
                        <img
                          src={req.poster_url}
                          alt={req.title}
                          className="w-full h-full object-cover"
                          onError={(e) => {
                            (e.target as HTMLElement).style.display = "none";
                          }}
                        />
                      ) : (
                        <span className="material-symbols-outlined text-zinc-600">movie</span>
                      )}
                    </div>

                    <div className="space-y-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-bold text-white text-base">{req.title}</span>
                        {req.release_year && (
                          <span className="text-xs text-zinc-400">({req.release_year})</span>
                        )}
                        <span className="px-2 py-0.5 rounded text-[11px] font-bold uppercase bg-white/10 text-zinc-300">
                          {req.media_type === "series" ? "Serial" : "Kino"}
                        </span>
                        <span className={`px-2 py-0.5 rounded text-[11px] font-semibold border ${statusConfig.bg}`}>
                          {statusConfig.label}
                        </span>
                      </div>

                      {req.original_title && req.original_title !== req.title && (
                        <p className="text-xs text-zinc-400 italic">{req.original_title}</p>
                      )}

                      <div className="flex flex-wrap items-center gap-3 text-xs text-zinc-400 pt-1">
                        <span className="flex items-center gap-1 font-semibold text-emerald-400">
                          <span className="material-symbols-outlined text-[15px]">how_to_vote</span>
                          <span>{req.vote_count} ta ovoz</span>
                        </span>
                        {req.preferred_language && (
                          <span className="uppercase text-[11px] px-1.5 py-0.5 rounded bg-white/5 border border-white/10">
                            Til: {req.preferred_language}
                          </span>
                        )}
                        {req.tmdb_id && <span className="text-zinc-500">TMDb: #{req.tmdb_id}</span>}
                        {req.user_contact && (
                          <span className="text-zinc-400">Aloqa: {req.user_contact}</span>
                        )}
                      </div>

                      {req.admin_notes && (
                        <div className="pt-1.5 flex items-center gap-2 text-xs">
                          <span className="material-symbols-outlined text-[16px] text-[#E50914]">
                            link
                          </span>
                          <span className="text-zinc-300 font-medium bg-[#E50914]/10 border border-[#E50914]/20 px-2.5 py-1 rounded-lg">
                            {req.admin_notes}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="flex flex-wrap items-center gap-2 shrink-0">
                    <button
                      onClick={() => handleOpenBridge(req)}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-[#E50914] hover:bg-[#b80710] text-white font-bold text-xs shadow-md transition"
                      title="Yuklangan film/serial bilan ko'prik qilib ulash"
                    >
                      <span className="material-symbols-outlined text-[16px]">link</span>
                      <span>Ko'prik ulash</span>
                    </button>

                    {req.status === "pending" && (
                      <button
                        onClick={() => handleUpdateStatus(req.id, "in_review")}
                        className="px-2.5 py-1.5 rounded-xl bg-blue-500/20 hover:bg-blue-500/30 text-blue-300 text-xs font-semibold transition"
                      >
                        Jarayonga
                      </button>
                    )}

                    {req.status !== "rejected" && (
                      <button
                        onClick={() => handleUpdateStatus(req.id, "rejected")}
                        className="px-2.5 py-1.5 rounded-xl bg-white/5 hover:bg-white/10 text-zinc-400 hover:text-red-400 text-xs font-semibold transition"
                      >
                        Rad etish
                      </button>
                    )}

                    <button
                      onClick={() => handleDelete(req.id)}
                      className="p-1.5 rounded-xl text-zinc-500 hover:text-red-400 hover:bg-white/5 transition"
                      title="O'chirish"
                    >
                      <span className="material-symbols-outlined text-[18px]">delete</span>
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* KO'PRIK (BRIDGE) MODAL */}
      {bridgeModalOpen && activeRequest && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
          <div className="bg-[#161820] border border-white/15 rounded-2xl w-full max-w-lg p-6 shadow-2xl space-y-5">
            <div className="flex items-center justify-between pb-3 border-b border-white/10">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-[#E50914] text-2xl">link</span>
                <h3 className="font-bold text-white text-lg">Ko'prik qilib ulash</h3>
              </div>
              <button
                onClick={() => setBridgeModalOpen(false)}
                className="text-zinc-400 hover:text-white transition"
              >
                ✕
              </button>
            </div>

            <div className="p-3 bg-white/5 rounded-xl space-y-1">
              <div className="text-xs text-zinc-400 font-medium">So'ralgan kontent:</div>
              <div className="font-bold text-white text-sm">
                {activeRequest.title}{" "}
                {activeRequest.release_year ? `(${activeRequest.release_year})` : ""}
              </div>
              <div className="text-xs text-emerald-400">
                {activeRequest.vote_count} ta foydalanuvchi so'ragan
              </div>
            </div>

            <form onSubmit={handleSaveBridge} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-zinc-300 mb-1.5">
                  Yuklangan Film/Serial Kodi yoki URL manzili:
                </label>
                <input
                  type="text"
                  required
                  value={linkedContentCode}
                  onChange={(e) => setLinkedContentCode(e.target.value)}
                  placeholder="Masalan: 3955, /movie/3955 yoki /series/1005"
                  className="w-full px-3.5 py-2.5 rounded-xl bg-white/5 border border-white/15 text-white text-sm focus:outline-none focus:border-[#E50914]"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-zinc-300 mb-1.5">
                  Qo'shimcha admin izohi (ixtiyoriy):
                </label>
                <textarea
                  rows={2}
                  value={adminNote}
                  onChange={(e) => setAdminNote(e.target.value)}
                  placeholder="Masalan: O'zbek tilida sifatli dublyaj bilan yuklandi..."
                  className="w-full px-3.5 py-2 rounded-xl bg-white/5 border border-white/15 text-white text-sm focus:outline-none focus:border-[#E50914]"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setBridgeModalOpen(false)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-zinc-400 hover:text-white transition"
                >
                  Bekor qilish
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-5 py-2.5 rounded-xl bg-[#E50914] hover:bg-[#b80710] text-white font-bold text-xs shadow-lg transition flex items-center gap-2"
                >
                  <span className="material-symbols-outlined text-[17px]">check_circle</span>
                  <span>{submitting ? "Saqlanmoqda..." : "Ulash va Bajarildi qilish"}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
