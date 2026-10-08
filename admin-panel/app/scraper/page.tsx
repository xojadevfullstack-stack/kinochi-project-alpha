"use client";

import { useEffect, useState, useRef, useTransition } from "react";
import { fetchApi } from "@/lib/api";

interface ProgressData {
  current: number;
  total: number;
  percentage: number;
}

interface LogEntry {
  timestamp: string;
  message: string;
  level: "info" | "success" | "warning" | "error";
}

interface ScraperStatus {
  is_running: boolean;
  task_type: string;
  current_action: string;
  current_item: { title?: string; code?: string } | null;
  progress?: ProgressData;
  started_at: string | null;
  elapsed_seconds: number;
  logs?: LogEntry[];
  stats?: {
    total: number;
    pending: number;
    completed: number;
    already_exists: number;
    failed: number;
    in_progress: number;
  };
}

interface QueueItem {
  id: string;
  source: string;
  title: string;
  original_title?: string | null;
  year?: number | null;
  media_type: string;
  url: string;
  poster_url?: string | null;
  status: "pending" | "in_progress" | "completed" | "failed" | "already_exists" | "needs_review";
  episodes_count?: number | null;
  downloaded_episodes: number;
  error_message?: string | null;
}

export default function ScraperPage() {
  // ── Status State ──────────────────────────────────────────
  const [status, setStatus] = useState<ScraperStatus | null>(null);
  const [isPolling, setIsPolling] = useState(true);
  const [autoScrollLogs, setAutoScrollLogs] = useState(true);
  const [statusError, setStatusError] = useState<string | null>(null);
  const terminalLogsBoxRef = useRef<HTMLDivElement>(null);

  // ── Queue State ───────────────────────────────────────────
  const [queueItems, setQueueItems] = useState<QueueItem[]>([]);
  const [queueTotal, setQueueTotal] = useState(0);
  const [queuePage, setQueuePage] = useState(1);
  const [queueTotalPages, setQueueTotalPages] = useState(1);
  const [statusFilter, setStatusFilter] = useState("all");
  const [sourceFilter, setSourceFilter] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [loadingQueue, setLoadingQueue] = useState(false);

  // ── Action / Form States ──────────────────────────────────
  const [parseSource, setParseSource] = useState("uzmovi");
  const [parsePages, setParsePages] = useState(3);
  const [downloadTarget, setDownloadTarget] = useState("uzmovi");
  const [downloadLimit, setDownloadLimit] = useState(5);
  const [downloadCodes, setDownloadCodes] = useState("");
  const [downloadMediaType, setDownloadMediaType] = useState("all");

  const [actionLoading, setActionLoading] = useState(false);
  const [actionMsg, setActionMsg] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [activeTab, setActiveTab] = useState<"grabber" | "parser" | "search" | "moderation" | "tools">("grabber");

  // ── Site Search States ────────────────────────────────────
  const [siteSearchQuery, setSiteSearchQuery] = useState("");
  const [siteSearchSource, setSiteSearchSource] = useState<"all" | "uzmovi" | "asilmedia">("all");
  const [siteSearchResults, setSiteSearchResults] = useState<any[]>([]);
  const [searchingSite, setSearchingSite] = useState(false);
  const [searchHasSearched, setSearchHasSearched] = useState(false);
  const [quickActionLoading, setQuickActionLoading] = useState<string | null>(null);

  // ── Moderation & Manual Edit States ───────────────────────
  const [reviewItems, setReviewItems] = useState<{ db_movies: any[]; queue_items: any[] }>({
    db_movies: [],
    queue_items: [],
  });
  const [loadingReview, setLoadingReview] = useState(false);
  const [editingItem, setEditingItem] = useState<{
    isDb: boolean;
    id: string | number;
    title: string;
    original_title?: string;
    release_year?: number;
    poster_url?: string;
    trailer_url?: string;
    description?: string;
    genres?: string;
    code?: string;
    imdb_rating?: number;
    tmdb_id?: number;
    media_type?: string;
  } | null>(null);
  const [tmdbSearchQuery, setTmdbSearchQuery] = useState("");
  const [tmdbResults, setTmdbResults] = useState<any[]>([]);
  const [searchingTmdb, setSearchingTmdb] = useState(false);
  const [savingEdit, setSavingEdit] = useState(false);

  // Trackers to prevent stale async responses
  const queueReqId = useRef(0);
  const statusInFlight = useRef(false);
  const wasRunning = useRef(false);

  // ── Fetch Status ──────────────────────────────────────────
  const fetchStatus = async () => {
    if (statusInFlight.current) return;
    statusInFlight.current = true;
    try {
      const data = await fetchApi("/scraper/status");
      setStatus(data);
      setStatusError(null);
    } catch (err: any) {
      // Do not spam loud error if it's transient
      console.warn("Status fetch warning:", err?.message);
      setStatusError(err?.message || "Statusni olib bo'lmadi");
    } finally {
      statusInFlight.current = false;
    }
  };

  // ── Fetch Queue Items ─────────────────────────────────────
  const fetchQueue = async (page = queuePage) => {
    const reqId = ++queueReqId.current;
    setLoadingQueue(true);
    try {
      const queryParams = new URLSearchParams({
        page: page.toString(),
        page_size: "15",
        status: statusFilter,
        source: sourceFilter,
      });
      if (searchQuery.trim()) {
        queryParams.append("search", searchQuery.trim());
      }
      const data = await fetchApi(`/scraper/queue?${queryParams.toString()}`);
      if (reqId !== queueReqId.current) return;

      if ((data.items || []).length === 0 && page > 1 && data.total_pages < page) {
        fetchQueue(Math.max(1, data.total_pages));
        return;
      }
      setQueueItems(data.items || []);
      setQueueTotal(data.total || 0);
      setQueuePage(data.page || 1);
      setQueueTotalPages(data.total_pages || 1);
    } catch (err: any) {
      if (reqId === queueReqId.current) {
        console.error("Queue fetch error:", err);
      }
    } finally {
      if (reqId === queueReqId.current) {
        setLoadingQueue(false);
      }
    }
  };

  // Initial load
  useEffect(() => {
    fetchStatus();
    fetchQueue(1);
    fetchIncomplete();
  }, []);

  // ── Fetch Incomplete / Review Items ───────────────────────
  const fetchIncomplete = async () => {
    setLoadingReview(true);
    try {
      const data = await fetchApi("/scraper/incomplete-movies");
      setReviewItems(data || { db_movies: [], queue_items: [] });
    } catch (err: any) {
      console.warn("fetchIncomplete error:", err);
    } finally {
      setLoadingReview(false);
    }
  };

  const openEditModal = (item: any) => {
    setEditingItem(item);
    setTmdbSearchQuery(item.title && item.title !== "Kino" && item.title !== "Film" ? item.title : "");
    setTmdbResults([]);
  };

  const handleSearchTmdb = async () => {
    if (!tmdbSearchQuery.trim()) return;
    setSearchingTmdb(true);
    try {
      const results = await fetchApi(`/content-lookup/search?q=${encodeURIComponent(tmdbSearchQuery.trim())}`);
      setTmdbResults(Array.isArray(results) ? results : []);
    } catch (err: any) {
      setActionMsg({ type: "error", text: "TMDb qidiruv xatosi: " + (err?.message || "") });
    } finally {
      setSearchingTmdb(false);
    }
  };

  const handleSelectTmdbMovie = (m: any) => {
    if (!editingItem) return;
    setEditingItem({
      ...editingItem,
      title: m.title || m.name || editingItem.title,
      original_title: m.original_title || m.original_name || "",
      release_year: m.release_year || (m.release_date ? parseInt(m.release_date.slice(0, 4), 10) : editingItem.release_year),
      poster_url: m.poster_url || (m.poster_path ? `https://image.tmdb.org/t/p/w500${m.poster_path}` : editingItem.poster_url),
      description: m.overview || editingItem.description || "",
      genres: m.genres ? (Array.isArray(m.genres) ? m.genres.join(", ") : m.genres) : editingItem.genres,
      imdb_rating: m.vote_average || editingItem.imdb_rating,
      tmdb_id: m.id || m.tmdb_id,
    });
    setTmdbResults([]);
  };

  const handleSaveEdit = async (grabImmediately = false) => {
    if (!editingItem) return;
    setSavingEdit(true);
    try {
      if (editingItem.isDb) {
        await fetchApi(`/scraper/db-movies/${editingItem.id}/fix`, {
          method: "POST",
          body: JSON.stringify({
            title: editingItem.title,
            original_title: editingItem.original_title,
            release_year: editingItem.release_year,
            description: editingItem.description,
            poster_url: editingItem.poster_url,
            trailer_url: editingItem.trailer_url,
            genres: editingItem.genres,
            imdb_rating: editingItem.imdb_rating,
            tmdb_id: editingItem.tmdb_id,
          }),
        });
        setActionMsg({ type: "success", text: `Film #${editingItem.id} bazada yangilandi!` });
      } else {
        await fetchApi(`/scraper/queue/${editingItem.id}`, {
          method: "PUT",
          body: JSON.stringify({
            title: editingItem.title,
            year: editingItem.release_year,
            poster_url: editingItem.poster_url,
            original_title: editingItem.original_title,
            media_type: editingItem.media_type || "movie",
            status: "pending",
          }),
        });
        setActionMsg({ type: "success", text: `${editingItem.title} navbatda yangilandi!` });
        if (grabImmediately) {
          await handleGrabSingleItem(String(editingItem.id), editingItem.title);
        }
      }
      setEditingItem(null);
      fetchIncomplete();
      fetchQueue();
    } catch (err: any) {
      setActionMsg({ type: "error", text: "Saqlashda xatolik: " + (err?.message || "") });
    } finally {
      setSavingEdit(false);
    }
  };

  const handleDeleteDbMovie = async (movieId: number) => {
    if (!confirm("Haqiqatan ham ushbu filmni bazadan butunlay o'chirmoqchimisiz?")) return;
    try {
      await fetchApi(`/scraper/db-movies/${movieId}`, { method: "DELETE" });
      setActionMsg({ type: "success", text: `Film #${movieId} bazadan o'chirildi.` });
      fetchIncomplete();
    } catch (err: any) {
      setActionMsg({ type: "error", text: "O'chirishda xatolik: " + (err?.message || "") });
    }
  };

  // Status Polling (2 seconds)
  useEffect(() => {
    if (!isPolling) return;
    const interval = setInterval(fetchStatus, 2000);
    return () => clearInterval(interval);
  }, [isPolling]);

  // Queue Polling while process is running (every 4 seconds)
  useEffect(() => {
    if (!status?.is_running) return;
    const qInterval = setInterval(() => fetchQueue(queuePage), 4000);
    return () => clearInterval(qInterval);
  }, [status?.is_running, queuePage, statusFilter, sourceFilter, searchQuery]);

  // Refresh queue when job completes
  useEffect(() => {
    const running = !!status?.is_running;
    if (wasRunning.current && !running) {
      fetchQueue(queuePage);
    }
    wasRunning.current = running;
  }, [status?.is_running]);

  // Search Debounce (350ms)
  useEffect(() => {
    const timer = setTimeout(() => {
      fetchQueue(1);
    }, 350);
    return () => clearTimeout(timer);
  }, [searchQuery, statusFilter, sourceFilter]);

  // Terminal Auto-scroll (Without jumping entire window)
  useEffect(() => {
    if (autoScrollLogs && terminalLogsBoxRef.current) {
      terminalLogsBoxRef.current.scrollTop = terminalLogsBoxRef.current.scrollHeight;
    }
  }, [status?.logs, autoScrollLogs]);

  // Format elapsed time (MM:SS)
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  };

  const showToast = (type: "success" | "error", text: string) => {
    setActionMsg({ type, text });
    setTimeout(() => setActionMsg(null), 4500);
  };

  // ── Site Search Handlers ──────────────────────────────────
  const handleSiteSearch = async () => {
    if (!siteSearchQuery.trim() || siteSearchQuery.trim().length < 2) return;
    setSearchingSite(true);
    setSearchHasSearched(true);
    try {
      const data = await fetchApi(`/scraper/search-site?q=${encodeURIComponent(siteSearchQuery.trim())}&source=${siteSearchSource}`);
      setSiteSearchResults(data?.results || []);
    } catch (err: any) {
      showToast("error", "Saytdan qidiruv xatosi: " + (err?.message || ""));
    } finally {
      setSearchingSite(false);
    }
  };

  const handleAddToQueue = async (item: any) => {
    setQuickActionLoading(item.id);
    try {
      const res = await fetchApi("/scraper/queue-add", {
        method: "POST",
        body: JSON.stringify(item),
      });
      showToast("success", res.message || "Navbatga qo'shildi!");
      setSiteSearchResults((prev) =>
        prev.map((it) => (it.id === item.id ? { ...it, queue_status: it.is_duplicate ? "already_exists" : "pending" } : it))
      );
      fetchQueue(1);
    } catch (err: any) {
      showToast("error", "Navbatga qo'shishda xatolik: " + (err?.message || ""));
    } finally {
      setQuickActionLoading(null);
    }
  };

  const handleQuickGrab = async (item: any) => {
    setQuickActionLoading(item.id);
    try {
      const res = await fetchApi("/scraper/quick-grab", {
        method: "POST",
        body: JSON.stringify(item),
      });
      showToast("success", res.message || "Yuklash boshlandi!");
      fetchStatus();
      fetchQueue(1);
    } catch (err: any) {
      showToast("error", "Yuklashni boshlashda xatolik: " + (err?.message || ""));
    } finally {
      setQuickActionLoading(null);
    }
  };

  // ── Handlers ──────────────────────────────────────────────
  const handleStartParse = async () => {
    setActionLoading(true);
    try {
      const res = await fetchApi("/scraper/start-parse", {
        method: "POST",
        body: JSON.stringify({
          source: parseSource,
          pages: Math.max(1, Number(parsePages) || 1),
        }),
      });
      showToast("success", res.message || "Katalog yig'ish boshlandi!");
      fetchStatus();
    } catch (e: any) {
      showToast("error", e.message || "Xatolik yuz berdi");
    } finally {
      setActionLoading(false);
    }
  };

  const handleStartDownload = async () => {
    setActionLoading(true);
    try {
      const res = await fetchApi("/scraper/start-download", {
        method: "POST",
        body: JSON.stringify({
          target: downloadTarget,
          limit: Math.max(1, Number(downloadLimit) || 1),
          codes: downloadCodes.trim() || null,
          media_type: downloadMediaType,
        }),
      });
      showToast("success", res.message || "Yuklab olish jarayoni boshlandi!");
      fetchStatus();
    } catch (e: any) {
      showToast("error", e.message || "Xatolik yuz berdi");
    } finally {
      setActionLoading(false);
    }
  };

  const handleGrabSingleItem = async (itemId: string, itemTitle: string) => {
    if (status?.is_running) {
      showToast("error", "Boshqa jarayon allaqachon ishlayapti. Avval uni kuting yoki to'xtating.");
      return;
    }
    try {
      const res = await fetchApi(`/scraper/queue/${itemId}/grab-now`, { method: "POST" });
      showToast("success", res.message || `'${itemTitle}' yuklash boshlandi!`);
      fetchStatus();
    } catch (e: any) {
      showToast("error", e.message || "Yuklab bo'lmadi");
    }
  };

  const handleCleanDuplicates = async () => {
    if (!confirm("Navbatdagi barcha filmlar bazadagi dublikatlarga tekshirilsinmi?")) return;
    setActionLoading(true);
    try {
      const res = await fetchApi("/scraper/clean-duplicates", { method: "POST" });
      showToast("success", res.message || "Dublikatlarni tekshirish boshlandi!");
      fetchStatus();
    } catch (e: any) {
      showToast("error", e.message || "Xatolik yuz berdi");
    } finally {
      setActionLoading(false);
    }
  };

  const handleStopProcess = async () => {
    if (!confirm("Rostdan ham faol jarayonni to'xtatmoqchimisiz?")) return;
    try {
      const res = await fetchApi("/scraper/stop", { method: "POST" });
      showToast("success", res.message || "To'xtatish signali yuborildi");
      fetchStatus();
    } catch (e: any) {
      showToast("error", e.message || "To'xtatib bo'lmadi");
    }
  };

  const handleClearLogs = async () => {
    try {
      await fetchApi("/scraper/clear-logs", { method: "POST" });
      fetchStatus();
    } catch (e) {}
  };

  const handleRetryItem = async (id: string) => {
    try {
      await fetchApi(`/scraper/queue/${id}/retry`, { method: "POST" });
      showToast("success", "Element qayta navbatga qo'yildi");
      fetchQueue(queuePage);
      fetchStatus();
    } catch (e: any) {
      showToast("error", e.message || "Xatolik yuz berdi");
    }
  };

  const handleDeleteItem = async (id: string) => {
    if (!confirm(`Ushbu element navbatdan o'chirilsinmi? (${id})`)) return;
    try {
      await fetchApi(`/scraper/queue/${id}`, { method: "DELETE" });
      showToast("success", "Element navbatdan o'chirildi");
      fetchQueue(queuePage);
      fetchStatus();
    } catch (e: any) {
      showToast("error", e.message || "O'chirib bo'lmadi");
    }
  };

  const handleRetryAllFailed = async () => {
    if (!confirm("Barcha xatolikka uchragan elementlar qayta navbatga qo'yilsinmi?")) return;
    try {
      const res = await fetchApi("/scraper/queue/retry-all-failed", { method: "POST" });
      showToast("success", res.message || "Xatoliklar qayta tiklandi");
      fetchQueue(1);
      fetchStatus();
    } catch (e: any) {
      showToast("error", e.message || "Xatolik yuz berdi");
    }
  };

  const handleClearByStatus = async (st: string) => {
    if (!confirm(`Barcha '${st}' statusidagi elementlar navbatdan o'chirilsinmi?`)) return;
    try {
      const res = await fetchApi("/scraper/queue/clear-by-status", {
        method: "POST",
        body: JSON.stringify({ status: st }),
      });
      showToast("success", res.message || "Tozalandi");
      fetchQueue(1);
      fetchStatus();
    } catch (e: any) {
      showToast("error", e.message || "Tozalashda xatolik");
    }
  };

  const stats = status?.stats || {
    total: queueTotal || 0,
    pending: 0,
    completed: 0,
    already_exists: 0,
    failed: 0,
    in_progress: 0,
  };

  const isRunning = Boolean(status?.is_running);
  const currentPercentage = Math.min(100, Math.max(0, status?.progress?.percentage ?? 0));

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto space-y-6">
      {/* Toast Alert */}
      {actionMsg && (
        <div
          className={`fixed top-5 right-5 z-50 px-4 py-3 rounded-xl shadow-2xl flex items-center gap-3 text-sm font-medium transition-all ${
            actionMsg.type === "success"
              ? "bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 backdrop-blur-md"
              : "bg-red-500/20 border border-red-500/40 text-red-300 backdrop-blur-md"
          }`}
        >
          <span className="material-symbols-outlined text-xl">
            {actionMsg.type === "success" ? "check_circle" : "error"}
          </span>
          <span>{actionMsg.text}</span>
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/5 pb-5">
        <div>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-primary-container/20 border border-primary-container/30 flex items-center justify-center text-primary-container">
              <span className="material-symbols-outlined text-2xl">smart_toy</span>
            </div>
            <div>
              <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-white flex items-center gap-3">
                Parser & Grabber Markazi
                {isRunning ? (
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 animate-pulse">
                    <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
                    Jarayonda
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-zinc-800 text-zinc-400 border border-zinc-700">
                    <span className="w-2 h-2 rounded-full bg-zinc-500"></span>
                    Kutishda
                  </span>
                )}
              </h1>
              <p className="text-xs sm:text-sm text-text-secondary mt-0.5">
                Katalog yig'ish, Telegram botlardan videolarni yuklash va to'liq jonli monitoring
              </p>
            </div>
          </div>
        </div>

        {/* Polling & Manual Refresh */}
        <div className="flex items-center gap-2 self-start sm:self-auto">
          <button
            onClick={() => setIsPolling(!isPolling)}
            className={`px-3 py-2 rounded-xl text-xs font-medium border transition-all flex items-center gap-2 ${
              isPolling
                ? "bg-white/5 border-white/10 text-emerald-400 hover:bg-white/10"
                : "bg-white/5 border-white/10 text-zinc-400 hover:bg-white/10"
            }`}
            title={isPolling ? "Avto-yangilanishni to'xtatish" : "Avto-yangilanishni yoqish"}
          >
            <span className={`material-symbols-outlined text-sm ${isPolling ? "animate-spin" : ""}`}>sync</span>
            <span>{isPolling ? "Jonli Kuzatuv (2s)" : "Kuzatuv To'xtatilgan"}</span>
          </button>

          <button
            onClick={() => {
              fetchStatus();
              fetchQueue();
            }}
            className="p-2 rounded-xl bg-white/5 border border-white/10 text-white hover:bg-white/10 active:scale-95 transition-all"
            title="Yangilash"
          >
            <span className="material-symbols-outlined text-lg">refresh</span>
          </button>
        </div>
      </div>

      {/* ── 1. REAL-TIME MISSION CONTROL ───────────────────────────── */}
      <div className="bg-surface-container-lowest/80 border border-white/10 rounded-2xl p-5 sm:p-6 backdrop-blur-md relative overflow-hidden shadow-2xl">
        <div className="absolute top-0 right-0 w-80 h-80 bg-primary-container/10 rounded-full blur-3xl pointer-events-none -z-0" />

        <div className="relative z-10 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <span
                className={`p-2.5 rounded-xl flex items-center justify-center ${
                  isRunning
                    ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                    : "bg-white/5 text-zinc-400 border border-white/10"
                }`}
              >
                <span className={`material-symbols-outlined text-2xl ${isRunning ? "animate-spin" : ""}`}>
                  {isRunning ? "hourglass_top" : "check_circle"}
                </span>
              </span>
              <div>
                <span className="text-[11px] font-semibold tracking-wider uppercase text-text-secondary">
                  Jarayon Holati
                </span>
                <h3 className="text-base sm:text-lg font-bold text-white flex items-center gap-2">
                  {isRunning ? (
                    <>
                      <span className="capitalize">{status?.task_type || "Jarayon"}</span> vazifasi bajarilmoqda
                    </>
                  ) : (
                    "Tizim hozir kutish rejimida"
                  )}
                </h3>
              </div>
            </div>

            {/* Time & Stop Button */}
            <div className="flex items-center gap-3">
              {isRunning && status?.elapsed_seconds !== undefined && (
                <div className="px-3 py-1.5 rounded-lg bg-black/40 border border-white/5 text-xs text-zinc-300 font-mono flex items-center gap-2">
                  <span className="material-symbols-outlined text-sm text-zinc-400">timer</span>
                  <span>{formatTime(status.elapsed_seconds)}</span>
                </div>
              )}

              {isRunning && (
                <button
                  onClick={handleStopProcess}
                  className="px-4 py-2 rounded-xl bg-red-500/20 border border-red-500/40 hover:bg-red-500/30 active:scale-95 text-red-300 text-xs font-bold tracking-wider uppercase transition-all flex items-center gap-1.5 shadow-lg shadow-red-500/10"
                >
                  <span className="material-symbols-outlined text-sm">stop_circle</span>
                  To'xtatish
                </button>
              )}
            </div>
          </div>

          {/* Current Action / What is it doing right now ("Nia qivoti") */}
          <div className="bg-black/40 border border-white/10 rounded-xl p-4 space-y-3">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <span
                  className={`w-2 h-2 rounded-full ${
                    isRunning ? "bg-emerald-400 animate-ping" : "bg-zinc-500"
                  }`}
                ></span>
                <span className="text-xs text-text-secondary uppercase tracking-wider font-semibold">
                  Ayni damda bajarilayotgan amal:
                </span>
              </div>
              {status?.current_item?.title && (
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-primary-container/20 border border-primary-container/40 text-white truncate max-w-[280px]">
                  <span className="material-symbols-outlined text-xs text-primary-container">movie</span>
                  {status.current_item.title}
                </span>
              )}
              {status?.current_item?.code && (
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono font-bold bg-amber-500/20 border border-amber-500/40 text-amber-300">
                  Kod: #{status.current_item.code}
                </span>
              )}
            </div>

            <div className="text-sm sm:text-base font-semibold text-zinc-100 flex items-center gap-2.5 overflow-hidden">
              <span className="material-symbols-outlined text-primary-container shrink-0 text-xl">
                {isRunning ? "arrow_forward" : "task_alt"}
              </span>
              <p className="truncate">
                {status?.current_action || "Hozirda hech qanday fon vazifasi bajarilmayapti."}
              </p>
            </div>

            {/* Progress Bar ("Qanchalik tugatdan") */}
            <div className="space-y-1.5 pt-1">
              <div className="flex justify-between items-center text-xs">
                <span className="text-text-secondary">
                  Jarayon bajarilishi:{" "}
                  {isRunning && (status?.progress?.total ?? 0) > 0 ? (
                    <strong className="text-white">
                      {status?.progress?.current ?? 0} / {status?.progress?.total ?? 0} ta
                    </strong>
                  ) : isRunning ? (
                    <span className="text-zinc-400">Davom etmoqda...</span>
                  ) : (
                    <span className="text-zinc-500">Tayyor</span>
                  )}
                </span>
                <span className="font-mono font-bold text-primary-container">
                  {isRunning ? `${currentPercentage}%` : "100%"}
                </span>
              </div>
              <div className="w-full h-3 bg-white/5 border border-white/10 rounded-full overflow-hidden p-0.5">
                <div
                  className="h-full bg-gradient-to-r from-red-600 via-primary-container to-amber-500 rounded-full transition-all duration-500 relative"
                  style={{ width: `${isRunning ? currentPercentage : 0}%` }}
                >
                  {isRunning && <div className="absolute inset-0 bg-white/20 animate-pulse rounded-full" />}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── 2. METRICS OVERVIEW (6 CARDS) ──────────────────────────── */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 sm:gap-4">
        {/* Total */}
        <div className="bg-surface-container-lowest/60 border border-white/5 p-4 rounded-xl flex flex-col justify-between hover:border-white/10 transition-colors">
          <div className="flex items-center justify-between text-text-secondary">
            <span className="text-xs font-semibold uppercase tracking-wider">Jami Navbat</span>
            <span className="material-symbols-outlined text-lg">format_list_bulleted</span>
          </div>
          <div className="mt-2 text-2xl font-bold text-white">{stats.total}</div>
        </div>

        {/* Pending */}
        <div className="bg-surface-container-lowest/60 border border-amber-500/20 p-4 rounded-xl flex flex-col justify-between hover:border-amber-500/40 transition-colors">
          <div className="flex items-center justify-between text-amber-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Kutilmoqda</span>
            <span className="material-symbols-outlined text-lg">pending_actions</span>
          </div>
          <div className="mt-2 text-2xl font-bold text-amber-300">{stats.pending}</div>
        </div>

        {/* Completed */}
        <div className="bg-surface-container-lowest/60 border border-emerald-500/20 p-4 rounded-xl flex flex-col justify-between hover:border-emerald-500/40 transition-colors">
          <div className="flex items-center justify-between text-emerald-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Bajarildi</span>
            <span className="material-symbols-outlined text-lg">check_circle</span>
          </div>
          <div className="mt-2 text-2xl font-bold text-emerald-300">{stats.completed}</div>
        </div>

        {/* Already exists */}
        <div className="bg-surface-container-lowest/60 border border-sky-500/20 p-4 rounded-xl flex flex-col justify-between hover:border-sky-500/40 transition-colors">
          <div className="flex items-center justify-between text-sky-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Bazada Bor</span>
            <span className="material-symbols-outlined text-lg">dataset_linked</span>
          </div>
          <div className="mt-2 text-2xl font-bold text-sky-300">{stats.already_exists}</div>
        </div>

        {/* Failed */}
        <div className="bg-surface-container-lowest/60 border border-red-500/20 p-4 rounded-xl flex flex-col justify-between hover:border-red-500/40 transition-colors">
          <div className="flex items-center justify-between text-red-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Xatolik</span>
            <span className="material-symbols-outlined text-lg">error</span>
          </div>
          <div className="mt-2 text-2xl font-bold text-red-400">{stats.failed}</div>
        </div>

        {/* In progress */}
        <div className="bg-surface-container-lowest/60 border border-primary-container/20 p-4 rounded-xl flex flex-col justify-between hover:border-primary-container/40 transition-colors">
          <div className="flex items-center justify-between text-primary-container">
            <span className="text-xs font-semibold uppercase tracking-wider">Yuklanmoqda</span>
            <span className="material-symbols-outlined text-lg">autorenew</span>
          </div>
          <div className="mt-2 text-2xl font-bold text-primary-container">{stats.in_progress}</div>
        </div>
      </div>

      {/* ── 3. ACTIONS & LIVE CONSOLE TERMINAL ──────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Control Panel (5 cols) */}
        <div className="lg:col-span-5 bg-surface-container-lowest/60 border border-white/10 rounded-2xl p-5 flex flex-col space-y-4">
          <div className="flex items-center justify-between border-b border-white/5 pb-3">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <span className="material-symbols-outlined text-primary-container">tune</span>
              Boshqaruv Paneli
            </h2>
            <div className="flex bg-white/5 p-1 rounded-xl border border-white/10 text-xs">
              <button
                onClick={() => setActiveTab("grabber")}
                className={`px-3 py-1 rounded-lg transition-all font-medium ${
                  activeTab === "grabber" ? "bg-primary-container text-white shadow" : "text-zinc-400 hover:text-white"
                }`}
              >
                Grabber
              </button>
              <button
                onClick={() => setActiveTab("parser")}
                className={`px-3 py-1 rounded-lg transition-all font-medium ${
                  activeTab === "parser" ? "bg-primary-container text-white shadow" : "text-zinc-400 hover:text-white"
                }`}
              >
                Parser
              </button>
              <button
                onClick={() => setActiveTab("search")}
                className={`px-3 py-1 rounded-lg transition-all font-medium flex items-center gap-1 ${
                  activeTab === "search" ? "bg-primary-container text-white shadow" : "text-zinc-400 hover:text-white"
                }`}
              >
                <span className="material-symbols-outlined text-xs">search</span>
                <span>Qidiruv</span>
              </button>
              <button
                onClick={() => {
                  setActiveTab("moderation");
                  fetchIncomplete();
                }}
                className={`px-3 py-1 rounded-lg transition-all font-medium flex items-center gap-1.5 ${
                  activeTab === "moderation"
                    ? "bg-amber-500 text-black font-bold shadow"
                    : "text-amber-400 hover:text-amber-300"
                }`}
              >
                <span>Moderatsiya</span>
                {reviewItems.db_movies.length + reviewItems.queue_items.length > 0 && (
                  <span className="px-1.5 py-0.2 rounded-full bg-red-500 text-white text-[10px] font-bold">
                    {reviewItems.db_movies.length + reviewItems.queue_items.length}
                  </span>
                )}
              </button>
              <button
                onClick={() => setActiveTab("tools")}
                className={`px-3 py-1 rounded-lg transition-all font-medium ${
                  activeTab === "tools" ? "bg-primary-container text-white shadow" : "text-zinc-400 hover:text-white"
                }`}
              >
                Servis
              </button>
            </div>
          </div>

          {/* TAB 1: GRABBER */}
          {activeTab === "grabber" && (
            <div className="space-y-4 flex-1 flex flex-col justify-between">
              <div className="space-y-3">
                <p className="text-xs text-text-secondary">
                  Telegram botlaridan videolarni qidirish, yuklash, kanalga joylash va saytga ulash.
                </p>

                {/* Target Bot */}
                <div>
                  <label className="block text-xs font-semibold text-text-secondary mb-1">Maqsadli Bot Manbasi</label>
                  <select
                    value={downloadTarget}
                    onChange={(e) => setDownloadTarget(e.target.value)}
                    className="w-full bg-black/40 border border-white/10 rounded-xl px-3 py-2.5 text-sm text-white focus:outline-none focus:border-primary-container"
                  >
                    <option value="uzmovi">Uzmovi (@UzmovieTV_Bot)</option>
                    <option value="asilmedia">Asilmedia (@asilmediabot)</option>
                  </select>
                </div>

                {/* Limit & Media Type */}
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-semibold text-text-secondary mb-1">Miqdori (Limit)</label>
                    <input
                      type="number"
                      min={1}
                      max={100}
                      value={downloadLimit}
                      onChange={(e) => setDownloadLimit(Math.max(1, parseInt(e.target.value, 10) || 1))}
                      className="w-full bg-black/40 border border-white/10 rounded-xl px-3 py-2.5 text-sm text-white focus:outline-none focus:border-primary-container"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-text-secondary mb-1">Media Turi</label>
                    <select
                      value={downloadMediaType}
                      onChange={(e) => setDownloadMediaType(e.target.value)}
                      className="w-full bg-black/40 border border-white/10 rounded-xl px-3 py-2.5 text-sm text-white focus:outline-none focus:border-primary-container"
                    >
                      <option value="all">Hammasi</option>
                      <option value="movie">Faqat Kinolar</option>
                      <option value="series">Faqat Seriallar</option>
                    </select>
                  </div>
                </div>

                {/* Specific Codes (Optional) */}
                <div>
                  <label className="block text-xs font-semibold text-text-secondary mb-1">
                    Aniq Film Kodi (Ixtiyoriy)
                  </label>
                  <input
                    type="text"
                    placeholder="Masalan: 15 yoki 1-5 yoki 10,12,18"
                    value={downloadCodes}
                    onChange={(e) => setDownloadCodes(e.target.value)}
                    className="w-full bg-black/40 border border-white/10 rounded-xl px-3 py-2.5 text-sm text-white placeholder-zinc-500 focus:outline-none focus:border-primary-container"
                  />
                  <span className="text-[10px] text-zinc-400 mt-0.5 block">
                    Agar kod yozilsa, navbat o'rniga aynan shu kodlar yuklanadi.
                  </span>
                </div>
              </div>

              <button
                disabled={actionLoading || isRunning}
                onClick={handleStartDownload}
                className={`w-full py-3 rounded-xl font-bold text-xs uppercase tracking-wider flex items-center justify-center gap-2 transition-all shadow-lg ${
                  actionLoading || isRunning
                    ? "bg-zinc-800 text-zinc-500 cursor-not-allowed"
                    : "bg-primary-container hover:bg-primary-container/90 text-white active:scale-95 shadow-red-600/20"
                }`}
              >
                <span className="material-symbols-outlined text-lg">download</span>
                {isRunning ? "Jarayon Bajarilmoqda..." : "Yuklashni Boshlash (Grab)"}
              </button>
            </div>
          )}

          {/* TAB 2: PARSER */}
          {activeTab === "parser" && (
            <div className="space-y-4 flex-1 flex flex-col justify-between">
              <div className="space-y-3">
                <p className="text-xs text-text-secondary">
                  Saytlar katalogidan eng so'nggi kinolarni parallel ravishda yig'ish va navbatga qo'shish.
                </p>

                {/* Source Selection */}
                <div>
                  <label className="block text-xs font-semibold text-text-secondary mb-1">Sayt Manbasi</label>
                  <select
                    value={parseSource}
                    onChange={(e) => setParseSource(e.target.value)}
                    className="w-full bg-black/40 border border-white/10 rounded-xl px-3 py-2.5 text-sm text-white focus:outline-none focus:border-primary-container"
                  >
                    <option value="uzmovi">Uzmovi (uzmovi.net / tarjima-kinolar)</option>
                    <option value="asilmedia">Asilmedia (asilmedia.org)</option>
                  </select>
                </div>

                {/* Pages count */}
                <div>
                  <label className="block text-xs font-semibold text-text-secondary mb-1">
                    Yig'iladigan Sahifalar Soni
                  </label>
                  <input
                    type="number"
                    min={1}
                    max={20}
                    value={parsePages}
                    onChange={(e) => setParsePages(Math.max(1, parseInt(e.target.value, 10) || 1))}
                    className="w-full bg-black/40 border border-white/10 rounded-xl px-3 py-2.5 text-sm text-white focus:outline-none focus:border-primary-container"
                  />
                  <span className="text-[10px] text-zinc-400 mt-0.5 block">
                    Har bir sahifada ~10-15 ta film bo'ladi. Dublikatlardan tozalangan holda saqlanadi.
                  </span>
                </div>
              </div>

              <button
                disabled={actionLoading || isRunning}
                onClick={handleStartParse}
                className={`w-full py-3 rounded-xl font-bold text-xs uppercase tracking-wider flex items-center justify-center gap-2 transition-all shadow-lg ${
                  actionLoading || isRunning
                    ? "bg-zinc-800 text-zinc-500 cursor-not-allowed"
                    : "bg-blue-600 hover:bg-blue-500 text-white active:scale-95 shadow-blue-600/20"
                }`}
              >
                <span className="material-symbols-outlined text-lg">travel_explore</span>
                {isRunning ? "Jarayon Bajarilmoqda..." : "Katalog Yig'ishni Boshlash (Parse)"}
              </button>
            </div>
          )}

          {/* TAB: SEARCH SITES */}
          {activeTab === "search" && (
            <div className="space-y-3 flex-1 flex flex-col">
              <div>
                <p className="text-xs text-text-secondary">
                  Uzmovi va Asilmedia saytlaridan to'g'ridan-to'g'ri qidirish, dublikatni tekshirish va bir klikda yuklash.
                </p>
              </div>

              {/* Source pills */}
              <div className="flex gap-1.5 p-1 bg-black/40 rounded-xl border border-white/10">
                {([
                  { id: "all", label: "Barchasi" },
                  { id: "uzmovi", label: "Uzmovi" },
                  { id: "asilmedia", label: "Asilmedia" },
                ] as const).map((s) => (
                  <button
                    key={s.id}
                    type="button"
                    onClick={() => setSiteSearchSource(s.id)}
                    className={`flex-1 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                      siteSearchSource === s.id
                        ? "bg-primary-container text-white shadow"
                        : "text-zinc-400 hover:text-white"
                    }`}
                  >
                    {s.label}
                  </button>
                ))}
              </div>

              {/* Search input bar */}
              <div className="flex gap-2">
                <div className="relative flex-1">
                  <span className="material-symbols-outlined absolute left-3 top-2.5 text-zinc-400 text-base pointer-events-none">
                    search
                  </span>
                  <input
                    type="text"
                    placeholder="Kino yoki serial nomi..."
                    value={siteSearchQuery}
                    onChange={(e) => setSiteSearchQuery(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleSiteSearch()}
                    className="w-full bg-black/40 border border-white/10 rounded-xl pl-9 pr-8 py-2 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-primary-container"
                  />
                  {siteSearchQuery && (
                    <button
                      onClick={() => setSiteSearchQuery("")}
                      className="absolute right-2.5 top-2 text-zinc-400 hover:text-white"
                    >
                      <span className="material-symbols-outlined text-sm">close</span>
                    </button>
                  )}
                </div>
                <button
                  type="button"
                  disabled={searchingSite || !siteSearchQuery.trim()}
                  onClick={handleSiteSearch}
                  className="px-3.5 py-2 rounded-xl bg-primary-container hover:bg-primary-container/80 text-white font-semibold text-xs transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1.5 shrink-0 shadow-lg shadow-primary-container/20"
                >
                  {searchingSite ? (
                    <span className="material-symbols-outlined text-base animate-spin">progress_activity</span>
                  ) : (
                    <span className="material-symbols-outlined text-base">search</span>
                  )}
                  <span>Qidirish</span>
                </button>
              </div>

              {/* Results Container */}
              <div className="flex-1 flex flex-col min-h-[300px] max-h-[360px] overflow-hidden rounded-xl border border-white/5 bg-black/20 p-2">
                {searchingSite ? (
                  <div className="flex-1 flex flex-col items-center justify-center text-zinc-400 gap-2 py-8">
                    <span className="material-symbols-outlined text-3xl animate-spin text-primary-container">
                      hourglass_top
                    </span>
                    <span className="text-xs">Saytlardan qidirilmoqda...</span>
                  </div>
                ) : !searchHasSearched ? (
                  <div className="flex-1 flex flex-col items-center justify-center text-zinc-500 gap-2 py-8 text-center px-4">
                    <span className="material-symbols-outlined text-3xl text-zinc-600">manage_search</span>
                    <span className="text-xs">Qidirish uchun kino yoki serial nomini kiriting va qidiring</span>
                  </div>
                ) : siteSearchResults.length === 0 ? (
                  <div className="flex-1 flex flex-col items-center justify-center text-zinc-500 gap-2 py-8 text-center px-4">
                    <span className="material-symbols-outlined text-3xl text-zinc-600">sentiment_dissatisfied</span>
                    <span className="text-xs">Hech qanday natija topilmadi</span>
                    <span className="text-[10px] text-zinc-600">Qidiruv so'zini qisqartirib yoki boshqacha yozib ko'ring</span>
                  </div>
                ) : (
                  <div className="flex-1 overflow-y-auto space-y-2 pr-1 custom-scrollbar">
                    <div className="text-[11px] text-zinc-400 px-1 py-0.5 flex justify-between items-center">
                      <span>Topildi: <b className="text-white">{siteSearchResults.length}</b> ta</span>
                      <span className="text-[10px] text-zinc-500">Bazada bor/yo'qligi tekshirildi</span>
                    </div>

                    {siteSearchResults.map((item) => {
                      const isItemLoading = quickActionLoading === item.id;
                      const isDup = item.is_duplicate;
                      const inQueue = !!item.queue_status && item.queue_status !== "not_found";

                      return (
                        <div
                          key={item.id}
                          className={`p-2.5 rounded-xl border transition-all flex flex-col gap-2 ${
                            isDup
                              ? "bg-amber-950/20 border-amber-500/20 hover:border-amber-500/40"
                              : "bg-white/[0.03] border-white/10 hover:border-white/20"
                          }`}
                        >
                          <div className="flex items-start gap-2.5">
                            {/* Poster */}
                            <div className="w-11 h-14 rounded-lg bg-black/40 overflow-hidden flex-shrink-0 border border-white/5 relative">
                              {item.poster || item.poster_url ? (
                                <img
                                  src={item.poster || item.poster_url}
                                  alt={item.title}
                                  className="w-full h-full object-cover"
                                  onError={(e: any) => {
                                    e.target.style.display = "none";
                                  }}
                                />
                              ) : (
                                <div className="w-full h-full flex items-center justify-center text-zinc-600">
                                  <span className="material-symbols-outlined text-sm">movie</span>
                                </div>
                              )}
                            </div>

                            {/* Details */}
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-1.5 flex-wrap">
                                <span
                                  className={`px-1.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                                    item.source === "uzmovi"
                                      ? "bg-blue-500/20 text-blue-400 border border-blue-500/30"
                                      : "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                                  }`}
                                >
                                  {item.source} #{item.code}
                                </span>

                                {item.year && (
                                  <span className="text-[10px] text-zinc-400 bg-white/5 px-1 rounded">
                                    {item.year}
                                  </span>
                                )}

                                {isDup ? (
                                  <span
                                    className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/30"
                                    title={item.duplicate_reason || item.db_reason || "Bazada mavjud"}
                                  >
                                    Bazada bor
                                  </span>
                                ) : (
                                  <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                                    Yangi
                                  </span>
                                )}

                                {inQueue && (
                                  <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-purple-500/20 text-purple-300 border border-purple-500/30">
                                    Navbatda: {item.queue_status}
                                  </span>
                                )}
                              </div>

                              <a
                                href={item.url}
                                target="_blank"
                                rel="noreferrer"
                                className="font-semibold text-xs text-white hover:text-primary-container truncate block mt-1"
                                title={item.title}
                              >
                                {item.title}
                              </a>

                              {isDup && (item.duplicate_reason || item.db_reason) && (
                                <p className="text-[10px] text-amber-400/80 truncate mt-0.5">
                                  {item.duplicate_reason || item.db_reason}
                                </p>
                              )}
                            </div>
                          </div>

                          {/* Quick Action Buttons */}
                          <div className="flex items-center gap-2 pt-1 border-t border-white/5">
                            <button
                              type="button"
                              disabled={isItemLoading || inQueue}
                              onClick={() => handleAddToQueue(item)}
                              className={`flex-1 py-1 px-2 rounded-lg text-[11px] font-semibold flex items-center justify-center gap-1 transition-all ${
                                inQueue
                                  ? "bg-zinc-800 text-zinc-500 cursor-not-allowed"
                                  : "bg-white/5 hover:bg-white/10 text-zinc-200 border border-white/10 active:scale-95"
                              }`}
                            >
                              <span className="material-symbols-outlined text-xs">playlist_add</span>
                              <span>{inQueue ? "Navbatda bor" : "+ Navbatga"}</span>
                            </button>

                            <button
                              type="button"
                              disabled={isItemLoading || isRunning}
                              onClick={() => handleQuickGrab(item)}
                              className={`flex-1 py-1 px-2 rounded-lg text-[11px] font-semibold flex items-center justify-center gap-1 transition-all ${
                                isRunning
                                  ? "bg-zinc-800 text-zinc-500 cursor-not-allowed"
                                  : "bg-emerald-600 hover:bg-emerald-500 text-white active:scale-95 shadow-sm shadow-emerald-600/30"
                              }`}
                              title={isRunning ? "Hozir boshqa jarayon ishlamoqda" : "Darhol yuklab olish"}
                            >
                              {isItemLoading ? (
                                <span className="material-symbols-outlined text-xs animate-spin">
                                  progress_activity
                                </span>
                              ) : (
                                <span className="material-symbols-outlined text-xs">bolt</span>
                              )}
                              <span>⚡ Grab (Yuklash)</span>
                            </button>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 3: TOOLS */}
          {activeTab === "tools" && (
            <div className="space-y-3 flex-1 flex flex-col justify-between">
              <div className="space-y-2.5">
                <p className="text-xs text-text-secondary mb-2">
                  Navbatni tozalash, xatolarni tiklash va dublikatlarni qayta tekshirish amallari.
                </p>

                {/* Clean Duplicates */}
                <button
                  disabled={actionLoading || isRunning}
                  onClick={handleCleanDuplicates}
                  className="w-full p-3 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 active:scale-95 text-left text-xs transition-all flex items-center justify-between"
                >
                  <div className="flex items-center gap-2.5">
                    <span className="material-symbols-outlined text-sky-400 text-lg">find_replace</span>
                    <div>
                      <div className="font-bold text-white">Dublikatlarni tozalash</div>
                      <div className="text-[11px] text-zinc-400">Navbatni bazadagi kinolar bilan qayta solishtiradi</div>
                    </div>
                  </div>
                  <span className="material-symbols-outlined text-sm text-zinc-400">chevron_right</span>
                </button>

                {/* Retry All Failed */}
                <button
                  disabled={actionLoading || isRunning}
                  onClick={handleRetryAllFailed}
                  className="w-full p-3 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 active:scale-95 text-left text-xs transition-all flex items-center justify-between"
                >
                  <div className="flex items-center gap-2.5">
                    <span className="material-symbols-outlined text-amber-400 text-lg">replay</span>
                    <div>
                      <div className="font-bold text-white">Xatolarni qayta navbatga qo'yish</div>
                      <div className="text-[11px] text-zinc-400">Barcha failed elementlarni pending holatiga qaytaradi</div>
                    </div>
                  </div>
                  <span className="material-symbols-outlined text-sm text-zinc-400">chevron_right</span>
                </button>

                {/* Clear Completed */}
                <button
                  disabled={actionLoading || isRunning}
                  onClick={() => handleClearByStatus("completed")}
                  className="w-full p-3 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 active:scale-95 text-left text-xs transition-all flex items-center justify-between"
                >
                  <div className="flex items-center gap-2.5">
                    <span className="material-symbols-outlined text-emerald-400 text-lg">mop</span>
                    <div>
                      <div className="font-bold text-white">Bajarilganlarni tozalash</div>
                      <div className="text-[11px] text-zinc-400">Yuklab bo'lingan elementlarni ro'yxatdan o'chiradi</div>
                    </div>
                  </div>
                  <span className="material-symbols-outlined text-sm text-zinc-400">chevron_right</span>
                </button>

                {/* Clear Already Exists */}
                <button
                  disabled={actionLoading || isRunning}
                  onClick={() => handleClearByStatus("already_exists")}
                  className="w-full p-3 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 active:scale-95 text-left text-xs transition-all flex items-center justify-between"
                >
                  <div className="flex items-center gap-2.5">
                    <span className="material-symbols-outlined text-zinc-400 text-lg">delete_sweep</span>
                    <div>
                      <div className="font-bold text-white">Bazada borlarni tozalash</div>
                      <div className="text-[11px] text-zinc-400">Bazada allaqachon mavjud bo'lganlarni olib tashlaydi</div>
                    </div>
                  </div>
                  <span className="material-symbols-outlined text-sm text-zinc-400">chevron_right</span>
                </button>
              </div>
            </div>
          )}

          {/* TAB 4: MODERATSIYA / CHALA KINOLAR */}
          {activeTab === "moderation" && (
            <div className="space-y-3 flex-1 flex flex-col justify-between overflow-y-auto max-h-[340px] pr-1">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <p className="text-xs text-text-secondary">
                    Nomi noaniq (&quot;Kino&quot;) yoki tavsifi to&apos;liq bo&apos;lmagan filmlar nazorati:
                  </p>
                  <button
                    onClick={fetchIncomplete}
                    disabled={loadingReview}
                    className="p-1 rounded-lg hover:bg-white/10 text-zinc-400 hover:text-white"
                    title="Yangilash"
                  >
                    <span className={`material-symbols-outlined text-sm ${loadingReview ? "animate-spin" : ""}`}>
                      refresh
                    </span>
                  </button>
                </div>

                {reviewItems.db_movies.length === 0 && reviewItems.queue_items.length === 0 ? (
                  <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-center">
                    <span className="material-symbols-outlined text-2xl text-emerald-400 mb-1">verified</span>
                    <p className="text-xs font-semibold text-emerald-300">Barcha kinolar tekshirilgan!</p>
                    <p className="text-[11px] text-zinc-400 mt-0.5">
                      Hozirda moderatsiya talab qiluvchi chala kinolar mavjud emas.
                    </p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {/* Database Incomplete Movies */}
                    {reviewItems.db_movies.map((m) => (
                      <div
                        key={`db-${m.id}`}
                        className="p-3 rounded-xl bg-red-500/10 border border-red-500/30 flex items-center justify-between gap-3"
                      >
                        <div className="flex items-center gap-2.5 min-w-0">
                          {m.poster_url ? (
                            <img
                              src={m.poster_url}
                              alt=""
                              className="w-9 h-12 rounded object-cover border border-white/10 shrink-0"
                              onError={(e) => {
                                e.currentTarget.style.display = "none";
                              }}
                            />
                          ) : (
                            <div className="w-9 h-12 rounded bg-black/40 border border-white/10 flex items-center justify-center shrink-0 text-zinc-500">
                              <span className="material-symbols-outlined text-base">movie</span>
                            </div>
                          )}
                          <div className="min-w-0">
                            <div className="flex items-center gap-1.5">
                              <span className="font-bold text-white text-xs truncate">{m.title}</span>
                              <span className="px-1.5 py-0.5 rounded text-[9px] bg-red-500/30 text-red-200 uppercase font-mono">
                                BAZADA #{m.id}
                              </span>
                            </div>
                            <p className="text-[10px] text-amber-300 truncate mt-0.5">
                              ⚠️ Kodi: {m.code} | Yili: {m.release_year || "Yo'q"} | Tavsif:{" "}
                              {m.description ? m.description.slice(0, 30) + "..." : "Mavjud emas"}
                            </p>
                          </div>
                        </div>

                        <div className="flex items-center gap-1 shrink-0">
                          <button
                            onClick={() =>
                              openEditModal({
                                isDb: true,
                                id: m.id,
                                title: m.title,
                                original_title: m.original_title || "",
                                release_year: m.release_year,
                                description: m.description || "",
                                poster_url: m.poster_url || "",
                                genres: m.genres || "",
                                code: m.code,
                                imdb_rating: m.imdb_rating,
                                tmdb_id: m.tmdb_id,
                              })
                            }
                            className="p-1.5 rounded-lg bg-amber-500/20 hover:bg-amber-500/40 text-amber-300 text-xs font-semibold flex items-center gap-1"
                            title="TMDb orqali to'g'rilash"
                          >
                            <span className="material-symbols-outlined text-sm">edit</span>
                            To&apos;g&apos;rilash
                          </button>
                          <button
                            onClick={() => handleDeleteDbMovie(m.id)}
                            className="p-1.5 rounded-lg bg-red-500/20 hover:bg-red-500/40 text-red-300 text-xs"
                            title="Bazadan o'chirish"
                          >
                            <span className="material-symbols-outlined text-sm">delete</span>
                          </button>
                        </div>
                      </div>
                    ))}

                    {/* Queue Needs Review Items */}
                    {reviewItems.queue_items.map((q) => (
                      <div
                        key={`q-${q.id}`}
                        className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-between gap-3"
                      >
                        <div className="flex items-center gap-2.5 min-w-0">
                          {q.poster_url ? (
                            <img
                              src={q.poster_url}
                              alt=""
                              className="w-9 h-12 rounded object-cover border border-white/10 shrink-0"
                              onError={(e) => {
                                e.currentTarget.style.display = "none";
                              }}
                            />
                          ) : (
                            <div className="w-9 h-12 rounded bg-black/40 border border-white/10 flex items-center justify-center shrink-0 text-zinc-500">
                              <span className="material-symbols-outlined text-base">movie</span>
                            </div>
                          )}
                          <div className="min-w-0">
                            <div className="flex items-center gap-1.5">
                              <span className="font-bold text-white text-xs truncate">{q.title}</span>
                              <span className="px-1.5 py-0.5 rounded text-[9px] bg-amber-500/30 text-amber-200 uppercase font-mono">
                                NAVBATDA
                              </span>
                            </div>
                            <p className="text-[10px] text-zinc-400 truncate mt-0.5">
                              {q.error_message || "⚠️ Nomi yoki tavsifi noaniq"}
                            </p>
                          </div>
                        </div>

                        <div className="flex items-center gap-1 shrink-0">
                          <button
                            onClick={() =>
                              openEditModal({
                                isDb: false,
                                id: q.id,
                                title: q.title,
                                original_title: q.original_title || "",
                                release_year: q.year,
                                poster_url: q.poster_url || "",
                                media_type: q.media_type,
                                code: q.id,
                              })
                            }
                            className="p-1.5 rounded-lg bg-amber-500/20 hover:bg-amber-500/40 text-amber-300 text-xs font-semibold flex items-center gap-1"
                            title="Tahrirlash va TMDb dan qidirish"
                          >
                            <span className="material-symbols-outlined text-sm">edit</span>
                            To&apos;g&apos;rilash
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Right: Live Terminal Logs (7 cols) */}
        <div className="lg:col-span-7 bg-[#0b0f19] border border-white/10 rounded-2xl flex flex-col overflow-hidden shadow-2xl h-[420px]">
          {/* Terminal Top Bar */}
          <div className="bg-[#111726] px-4 py-2.5 border-b border-white/5 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-red-500/80 inline-block"></span>
              <span className="w-3 h-3 rounded-full bg-amber-500/80 inline-block"></span>
              <span className="w-3 h-3 rounded-full bg-emerald-500/80 inline-block"></span>
              <span className="ml-2 text-xs font-mono font-semibold text-zinc-300 flex items-center gap-1.5">
                <span className="material-symbols-outlined text-sm text-primary-container">terminal</span>
                Jonli Konsol Loglari (Live Terminal)
              </span>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => setAutoScrollLogs(!autoScrollLogs)}
                className={`px-2 py-1 rounded text-[11px] font-mono border transition-all ${
                  autoScrollLogs
                    ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
                    : "bg-white/5 border-white/10 text-zinc-400"
                }`}
                title="Loglar kelganda oxiriga avtomatik tushish"
              >
                Auto-scroll: {autoScrollLogs ? "ON" : "OFF"}
              </button>
              <button
                onClick={handleClearLogs}
                className="p-1 rounded text-zinc-400 hover:text-white hover:bg-white/10 transition-colors"
                title="Loglarni tozalash"
              >
                <span className="material-symbols-outlined text-base">clear_all</span>
              </button>
            </div>
          </div>

          {/* Terminal Logs Content */}
          <div
            ref={terminalLogsBoxRef}
            className="flex-1 p-3 sm:p-4 font-mono text-xs overflow-y-auto space-y-1 select-text scroll-smooth"
          >
            {status?.logs && status.logs.length > 0 ? (
              status.logs.map((log, i) => {
                let color = "text-zinc-300";
                if (log.level === "error") color = "text-red-400 font-semibold";
                else if (log.level === "warning") color = "text-amber-300";
                else if (log.level === "success") color = "text-emerald-400 font-semibold";

                return (
                  <div key={i} className="leading-relaxed break-all flex items-start gap-2 hover:bg-white/5 px-1 rounded">
                    <span className="text-zinc-500 shrink-0 select-none">[{log.timestamp}]</span>
                    <span className={color}>{log.message}</span>
                  </div>
                );
              })
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-zinc-600 gap-2">
                <span className="material-symbols-outlined text-3xl">developer_board</span>
                <span>Hozircha loglar mavjud emas. Jarayon boshlanganda barcha loglar jonli ko'rinadi.</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ── 4. QUEUE EXPLORER TABLE ────────────────────────────────── */}
      <div className="bg-surface-container-lowest/60 border border-white/10 rounded-2xl p-5 space-y-4">
        {/* Header & Search */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-white/5 pb-4">
          <div>
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <span className="material-symbols-outlined text-primary-container">view_list</span>
              Navbatdagi Filmlar va Seriallar ({queueTotal} ta)
            </h2>
            <p className="text-xs text-text-secondary mt-0.5">
              Yuklanishi kutilayotgan, bajarilgan yoki dublikat deb topilgan barcha elementlar
            </p>
          </div>

          {/* Search Box */}
          <div className="flex items-center gap-2">
            <div className="relative">
              <span className="material-symbols-outlined absolute left-3 top-2.5 text-zinc-500 text-lg">search</span>
              <input
                type="text"
                placeholder="Qidiruv (nomi, kodi)..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9 pr-8 py-2 bg-black/40 border border-white/10 rounded-xl text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-primary-container w-64"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery("")}
                  className="absolute right-2.5 top-2.5 text-zinc-400 hover:text-white"
                  title="Qidiruvni tozalash"
                >
                  <span className="material-symbols-outlined text-base">close</span>
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Filter Tabs */}
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap items-center gap-1.5">
            {[
              { id: "all", label: `Barchasi (${stats.total})` },
              { id: "pending", label: `Kutilmoqda (${stats.pending})` },
              { id: "in_progress", label: `Jarayonda (${stats.in_progress})` },
              { id: "needs_review", label: "⚠️ Moderatsiya" },
              { id: "completed", label: `Bajarildi (${stats.completed})` },
              { id: "already_exists", label: `Bazada Bor (${stats.already_exists})` },
              { id: "failed", label: `Xatolik (${stats.failed})` },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setStatusFilter(tab.id)}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all ${
                  statusFilter === tab.id
                    ? "bg-primary-container text-white shadow"
                    : "bg-white/5 border border-white/5 text-zinc-400 hover:text-white hover:bg-white/10"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Source Filter */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-text-secondary">Manba:</span>
            <select
              value={sourceFilter}
              onChange={(e) => setSourceFilter(e.target.value)}
              className="bg-black/40 border border-white/10 rounded-lg px-2.5 py-1 text-xs text-white focus:outline-none"
            >
              <option value="all">Barchasi</option>
              <option value="uzmovi">Uzmovi</option>
              <option value="asilmedia">Asilmedia</option>
            </select>
          </div>
        </div>

        {/* Table */}
        <div className="overflow-x-auto rounded-xl border border-white/5">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-white/5 text-text-secondary uppercase text-[10px] tracking-wider border-b border-white/5">
                <th className="py-3 px-4">Film / Serial</th>
                <th className="py-3 px-4">Turi</th>
                <th className="py-3 px-4">Yili</th>
                <th className="py-3 px-4">Manba</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Izoh / Sabab</th>
                <th className="py-3 px-4 text-right">Amallar</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {loadingQueue ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-zinc-400">
                    <span className="material-symbols-outlined text-2xl animate-spin">sync</span>
                    <p className="mt-1">Yuklanmoqda...</p>
                  </td>
                </tr>
              ) : queueItems.length > 0 ? (
                queueItems.map((item) => {
                  let badgeClass = "bg-zinc-800 text-zinc-300 border-zinc-700";
                  let statusText: string = item.status;

                  if (item.status === "completed") {
                    badgeClass = "bg-emerald-500/20 text-emerald-300 border-emerald-500/30";
                    statusText = "Bajarildi";
                  } else if (item.status === "in_progress") {
                    badgeClass = "bg-primary-container/20 text-primary-container border-primary-container/30 animate-pulse";
                    statusText = "Yuklanmoqda";
                  } else if (item.status === "failed") {
                    badgeClass = "bg-red-500/20 text-red-300 border-red-500/30";
                    statusText = "Xatolik";
                  } else if (item.status === "already_exists") {
                    badgeClass = "bg-sky-500/20 text-sky-300 border-sky-500/30";
                    statusText = "Bazada Bor";
                  } else if (item.status === "needs_review") {
                    badgeClass = "bg-amber-500/20 text-amber-300 border-amber-500/40 font-bold";
                    statusText = "⚠️ Moderatsiya";
                  } else if (item.status === "pending") {
                    badgeClass = "bg-amber-500/20 text-amber-300 border-amber-500/30";
                    statusText = "Kutilmoqda";
                  }

                  return (
                    <tr key={item.id} className="hover:bg-white/[0.02] transition-colors">
                      {/* Title & Poster */}
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-3">
                          {item.poster_url ? (
                            <img
                              src={item.poster_url}
                              alt={item.title}
                              onError={(e) => {
                                e.currentTarget.style.display = "none";
                              }}
                              className="w-10 h-14 object-cover rounded-md border border-white/10 shrink-0"
                            />
                          ) : (
                            <div className="w-10 h-14 rounded-md bg-white/5 border border-white/10 flex items-center justify-center text-zinc-500 shrink-0">
                              <span className="material-symbols-outlined text-lg">movie</span>
                            </div>
                          )}
                          <div className="min-w-0">
                            <p className="font-bold text-white truncate max-w-xs sm:max-w-md">{item.title}</p>
                            {item.original_title && (
                              <p className="text-[11px] text-zinc-400 truncate max-w-xs">{item.original_title}</p>
                            )}
                            <span className="text-[10px] text-zinc-500 font-mono">ID: {item.id}</span>
                          </div>
                        </div>
                      </td>

                      {/* Media type */}
                      <td className="py-3 px-4 whitespace-nowrap">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                            item.media_type === "series"
                              ? "bg-purple-500/20 text-purple-300 border border-purple-500/30"
                              : "bg-blue-500/20 text-blue-300 border border-blue-500/30"
                          }`}
                        >
                          {item.media_type === "series" ? "Serial" : "Kino"}
                        </span>
                        {item.media_type === "series" && item.episodes_count && (
                          <div className="text-[10px] text-zinc-400 mt-1">
                            {item.downloaded_episodes || 0} / {item.episodes_count} qism
                          </div>
                        )}
                      </td>

                      {/* Year */}
                      <td className="py-3 px-4 whitespace-nowrap font-mono text-zinc-300">
                        {item.year || "-"}
                      </td>

                      {/* Source */}
                      <td className="py-3 px-4 whitespace-nowrap">
                        <a
                          href={item.url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-xs text-sky-400 hover:underline flex items-center gap-1 capitalize"
                        >
                          {item.source}
                          <span className="material-symbols-outlined text-[13px]">open_in_new</span>
                        </a>
                      </td>

                      {/* Status */}
                      <td className="py-3 px-4 whitespace-nowrap">
                        <span className={`px-2.5 py-1 rounded-full text-[11px] font-semibold border ${badgeClass}`}>
                          {statusText}
                        </span>
                      </td>

                      {/* Error / Reason */}
                      <td className="py-3 px-4 max-w-xs truncate">
                        {item.error_message ? (
                          <span
                            className={`text-[11px] ${
                              item.status === "failed" ? "text-red-400 font-medium" : "text-zinc-400"
                            }`}
                            title={item.error_message}
                          >
                            {item.error_message}
                          </span>
                        ) : (
                          <span className="text-zinc-600">-</span>
                        )}
                      </td>

                      {/* Actions */}
                      <td className="py-3 px-4 text-right whitespace-nowrap">
                        <div className="flex items-center justify-end gap-1.5">
                          {/* Direct Grab Button */}
                          <button
                            disabled={isRunning}
                            onClick={() => handleGrabSingleItem(item.id, item.title)}
                            className="p-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 hover:bg-emerald-500/30 hover:text-emerald-200 text-emerald-400 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
                            title="Aynan ushbu kinoni hozir yuklash"
                          >
                            <span className="material-symbols-outlined text-base">play_arrow</span>
                          </button>

                          {/* Edit / Moderation Button */}
                          <button
                            onClick={() =>
                              openEditModal({
                                isDb: false,
                                id: item.id,
                                title: item.title,
                                original_title: item.original_title || "",
                                release_year: item.year || undefined,
                                poster_url: item.poster_url || "",
                                media_type: item.media_type,
                                code: item.id,
                              })
                            }
                            className="p-1.5 rounded-lg bg-blue-500/10 border border-blue-500/20 hover:bg-blue-500/30 hover:text-blue-200 text-blue-400 transition-all"
                            title="TMDb orqali ma'lumotlarini to'g'rilash"
                          >
                            <span className="material-symbols-outlined text-base">edit</span>
                          </button>

                          {item.status !== "pending" && (
                            <button
                              onClick={() => handleRetryItem(item.id)}
                              className="p-1.5 rounded-lg bg-white/5 border border-white/10 hover:bg-amber-500/20 hover:border-amber-500/40 hover:text-amber-300 text-zinc-400 transition-all"
                              title="Qayta kutilayotgan holatga o'tkazish"
                            >
                              <span className="material-symbols-outlined text-base">replay</span>
                            </button>
                          )}

                          <button
                            onClick={() => handleDeleteItem(item.id)}
                            className="p-1.5 rounded-lg bg-white/5 border border-white/10 hover:bg-red-500/20 hover:border-red-500/40 hover:text-red-400 text-zinc-400 transition-all"
                            title="O'chirish"
                          >
                            <span className="material-symbols-outlined text-base">delete</span>
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-zinc-500">
                    <span className="material-symbols-outlined text-3xl mb-1">inbox</span>
                    <p>Hech qanday element topilmadi.</p>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Footer */}
        {queueTotalPages > 1 && (
          <div className="flex items-center justify-between pt-2 border-t border-white/5">
            <span className="text-xs text-text-secondary">
              Sahifa: <strong className="text-white">{queuePage}</strong> / {queueTotalPages}
            </span>
            <div className="flex items-center gap-1.5">
              <button
                disabled={queuePage <= 1}
                onClick={() => fetchQueue(queuePage - 1)}
                className="px-3 py-1.5 rounded-lg bg-white/5 border border-white/10 text-xs text-white disabled:opacity-40 disabled:cursor-not-allowed hover:bg-white/10 transition-all"
              >
                Oldingi
              </button>
              <button
                disabled={queuePage >= queueTotalPages}
                onClick={() => fetchQueue(queuePage + 1)}
                className="px-3 py-1.5 rounded-lg bg-white/5 border border-white/10 text-xs text-white disabled:opacity-40 disabled:cursor-not-allowed hover:bg-white/10 transition-all"
              >
                Keyingi
              </button>
            </div>
          </div>
        )}
      </div>

      {/* ── MODAL: MANUAL EDIT & TMDB SEARCH ── */}
      {editingItem && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#121316] border border-white/10 rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto p-6 space-y-5 shadow-2xl">
            {/* Modal Header */}
            <div className="flex items-center justify-between border-b border-white/10 pb-3">
              <div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <span className="material-symbols-outlined text-amber-400">tune</span>
                  Film Ma&apos;lumotlarini To&apos;g&apos;rilash (Moderatsiya)
                </h3>
                <p className="text-xs text-text-secondary mt-0.5">
                  {editingItem.isDb ? `Bazada mavjud film: ID #${editingItem.id}` : `Navbatdagi element: ${editingItem.id}`}
                </p>
              </div>
              <button
                onClick={() => setEditingItem(null)}
                className="p-1.5 rounded-xl hover:bg-white/10 text-zinc-400 hover:text-white"
              >
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>

            {/* TMDb Live Search */}
            <div className="p-4 rounded-xl bg-white/5 border border-white/10 space-y-3">
              <label className="block text-xs font-bold text-amber-300">
                🔍 TMDb dan to&apos;g&apos;ri film nomini qidirish
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder="Masalan: Substansiya yoki The Substance"
                  value={tmdbSearchQuery}
                  onChange={(e) => setTmdbSearchQuery(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") handleSearchTmdb();
                  }}
                  className="flex-1 bg-black/40 border border-white/10 rounded-xl px-3 py-2 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-amber-400"
                />
                <button
                  type="button"
                  onClick={handleSearchTmdb}
                  disabled={searchingTmdb || !tmdbSearchQuery.trim()}
                  className="px-4 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 disabled:opacity-40 text-black text-xs font-bold transition-all flex items-center gap-1.5"
                >
                  {searchingTmdb ? (
                    <span className="material-symbols-outlined text-sm animate-spin">progress_activity</span>
                  ) : (
                    <span className="material-symbols-outlined text-sm">search</span>
                  )}
                  Qidirish
                </button>
              </div>

              {/* TMDb Search Results Dropdown/List */}
              {tmdbResults.length > 0 && (
                <div className="space-y-2 max-h-56 overflow-y-auto pr-1 pt-2 border-t border-white/10">
                  <span className="text-[10px] text-zinc-400 uppercase font-bold tracking-wider">
                    Mos kelgan natijalar (Tanlash uchun bosing):
                  </span>
                  {tmdbResults.map((res: any) => (
                    <div
                      key={res.id}
                      onClick={() => handleSelectTmdbMovie(res)}
                      className="p-2.5 rounded-xl bg-white/5 hover:bg-amber-500/10 border border-white/5 hover:border-amber-500/30 cursor-pointer flex items-center gap-3 transition-all"
                    >
                      {res.poster_path ? (
                        <img
                          src={`https://image.tmdb.org/t/p/w200${res.poster_path}`}
                          alt=""
                          className="w-8 h-12 object-cover rounded shrink-0 border border-white/10"
                        />
                      ) : (
                        <div className="w-8 h-12 rounded bg-zinc-800 flex items-center justify-center shrink-0 text-zinc-500">
                          <span className="material-symbols-outlined text-sm">image</span>
                        </div>
                      )}
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-bold text-white truncate">{res.title || res.name}</span>
                          <span className="text-[11px] text-zinc-400 font-mono">
                            ({res.release_date?.slice(0, 4) || res.first_air_date?.slice(0, 4) || "Noma'lum"})
                          </span>
                        </div>
                        <p className="text-[11px] text-zinc-400 line-clamp-1 mt-0.5">
                          {res.overview || "Tavsif mavjud emas"}
                        </p>
                      </div>
                      <span className="text-xs font-bold text-amber-400 bg-amber-500/10 px-2 py-1 rounded border border-amber-500/20 shrink-0">
                        Tanlash
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Form Fields */}
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-text-secondary mb-1">
                    Film Nomi (O&apos;zbekcha)
                  </label>
                  <input
                    type="text"
                    value={editingItem.title}
                    onChange={(e) => setEditingItem({ ...editingItem, title: e.target.value })}
                    className="w-full bg-black/40 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-amber-400"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-text-secondary mb-1">
                    Asl Nomi (Original Title)
                  </label>
                  <input
                    type="text"
                    value={editingItem.original_title || ""}
                    onChange={(e) => setEditingItem({ ...editingItem, original_title: e.target.value })}
                    className="w-full bg-black/40 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-amber-400"
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-text-secondary mb-1">Yili</label>
                  <input
                    type="number"
                    value={editingItem.release_year || ""}
                    onChange={(e) =>
                      setEditingItem({
                        ...editingItem,
                        release_year: parseInt(e.target.value, 10) || undefined,
                      })
                    }
                    className="w-full bg-black/40 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-amber-400"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-text-secondary mb-1">Janrlari</label>
                  <input
                    type="text"
                    placeholder="Jangari, Drama"
                    value={editingItem.genres || ""}
                    onChange={(e) => setEditingItem({ ...editingItem, genres: e.target.value })}
                    className="w-full bg-black/40 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-amber-400"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-text-secondary mb-1">IMDb Reyting</label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    max="10"
                    value={editingItem.imdb_rating || ""}
                    onChange={(e) =>
                      setEditingItem({
                        ...editingItem,
                        imdb_rating: parseFloat(e.target.value) || undefined,
                      })
                    }
                    className="w-full bg-black/40 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-amber-400"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-text-secondary mb-1">Poster URL</label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={editingItem.poster_url || ""}
                    onChange={(e) => setEditingItem({ ...editingItem, poster_url: e.target.value })}
                    className="flex-1 bg-black/40 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-amber-400"
                  />
                  {editingItem.poster_url && (
                    <img
                      src={editingItem.poster_url}
                      alt=""
                      className="w-8 h-10 object-cover rounded border border-white/10 shrink-0"
                      onError={(e) => {
                        e.currentTarget.style.display = "none";
                      }}
                    />
                  )}
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-text-secondary mb-1">Film Tavsifi (Overview)</label>
                <textarea
                  rows={3}
                  value={editingItem.description || ""}
                  onChange={(e) => setEditingItem({ ...editingItem, description: e.target.value })}
                  className="w-full bg-black/40 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-amber-400"
                />
              </div>
            </div>

            {/* Modal Actions */}
            <div className="flex items-center justify-end gap-2 border-t border-white/10 pt-4">
              <button
                type="button"
                onClick={() => setEditingItem(null)}
                className="px-4 py-2 rounded-xl bg-white/5 border border-white/10 text-xs font-semibold text-zinc-400 hover:text-white"
              >
                Bekor qilish
              </button>

              {!editingItem.isDb && (
                <button
                  type="button"
                  disabled={savingEdit || !editingItem.title.trim()}
                  onClick={() => handleSaveEdit(true)}
                  className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 text-white text-xs font-bold transition-all flex items-center gap-1.5"
                >
                  <span className="material-symbols-outlined text-sm">play_arrow</span>
                  Saqlash va Darhol Yuklash
                </button>
              )}

              <button
                type="button"
                disabled={savingEdit || !editingItem.title.trim()}
                onClick={() => handleSaveEdit(false)}
                className="px-5 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 disabled:opacity-40 text-black text-xs font-bold transition-all flex items-center gap-1.5 shadow-lg shadow-amber-500/20"
              >
                {savingEdit ? (
                  <span className="material-symbols-outlined text-sm animate-spin">progress_activity</span>
                ) : (
                  <span className="material-symbols-outlined text-sm">check</span>
                )}
                {editingItem.isDb ? "Bazada Saqlash va Yangilash" : "Navbatda Saqlash"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
