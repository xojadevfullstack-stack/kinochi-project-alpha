"use client";

import { useEffect, useState, useRef } from "react";
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
  progress: ProgressData;
  started_at: string | null;
  elapsed_seconds: number;
  logs: LogEntry[];
  stats: {
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
  status: "pending" | "in_progress" | "completed" | "failed" | "already_exists";
  episodes_count?: number | null;
  downloaded_episodes: number;
  error_message?: string | null;
}

export default function ScraperPage() {
  // Real-time Status state
  const [status, setStatus] = useState<ScraperStatus | null>(null);
  const [isPolling, setIsPolling] = useState(true);
  const [autoScrollLogs, setAutoScrollLogs] = useState(true);
  const terminalEndRef = useRef<HTMLDivElement>(null);

  // Queue state
  const [queueItems, setQueueItems] = useState<QueueItem[]>([]);
  const [queueTotal, setQueueTotal] = useState(0);
  const [queuePage, setQueuePage] = useState(1);
  const [queueTotalPages, setQueueTotalPages] = useState(1);
  const [statusFilter, setStatusFilter] = useState("all");
  const [sourceFilter, setSourceFilter] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [loadingQueue, setLoadingQueue] = useState(false);

  // Forms state
  const [parseSource, setParseSource] = useState("uzmovi");
  const [parsePages, setParsePages] = useState(3);
  const [downloadTarget, setDownloadTarget] = useState("uzmovi");
  const [downloadLimit, setDownloadLimit] = useState(5);
  const [downloadCodes, setDownloadCodes] = useState("");
  const [downloadMediaType, setDownloadMediaType] = useState("all");

  // Action busy states
  const [actionLoading, setActionLoading] = useState(false);
  const [actionMsg, setActionMsg] = useState<{ type: "success" | "error"; text: string } | null>(null);

  // Active Control Tab
  const [activeTab, setActiveTab] = useState<"grabber" | "parser" | "tools">("grabber");

  const [statusError, setStatusError] = useState<string | null>(null);
  const queueReqId = useRef(0);
  const statusInFlight = useRef(false);
  const wasRunning = useRef(false);

  // ── Fetch Status periodically ────────────────────────────
  const fetchStatus = async () => {
    if (statusInFlight.current) return; // never stack requests on a slow backend
    statusInFlight.current = true;
    try {
      const data = await fetchApi("/scraper/status");
      setStatus(data);
      setStatusError(null);
    } catch (err: any) {
      setStatusError(err?.message || "Statusni olib bo'lmadi");
    } finally {
      statusInFlight.current = false;
    }
  };

  // ── Fetch Queue Items ────────────────────────────────────
  const fetchQueue = async (page = queuePage) => {
    const reqId = ++queueReqId.current; // only the latest request may update the UI
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

      // Page vanished (e.g. last item on it was deleted) -> go back one page
      if ((data.items || []).length === 0 && page > 1 && data.total_pages < page) {
        fetchQueue(Math.max(1, data.total_pages));
        return;
      }
      setQueueItems(data.items || []);
      setQueueTotal(data.total || 0);
      setQueuePage(data.page || 1);
      setQueueTotalPages(data.total_pages || 1);
    } catch (err: any) {
      if (reqId === queueReqId.current) console.error("Queue fetch error:", err);
    } finally {
      if (reqId === queueReqId.current) setLoadingQueue(false);
    }
  };

  // Initial load
  useEffect(() => {
    fetchStatus();
  }, []);

  // Status polling (2s) — only toggles the interval, doesn't reload the queue
  useEffect(() => {
    if (!isPolling) return;
    const interval = setInterval(fetchStatus, 2000);
    return () => clearInterval(interval);
  }, [isPolling]);

  // Refresh queue while a job is running (every 4s)
  useEffect(() => {
    if (!status?.is_running) return;
    const qInterval = setInterval(() => fetchQueue(queuePage), 4000);
    return () => clearInterval(qInterval);
  }, [status?.is_running, queuePage, statusFilter, sourceFilter, searchQuery]);

  // One final queue refresh the moment a job finishes
  useEffect(() => {
    const running = !!status?.is_running;
    if (wasRunning.current && !running) fetchQueue(queuePage);
    wasRunning.current = running;
  }, [status?.is_running]);

  // Filters change (also covers the initial queue load)
  useEffect(() => {
    fetchQueue(1);
  }, [statusFilter, sourceFilter]);

  // Auto-scroll terminal
  useEffect(() => {
    if (autoScrollLogs && terminalEndRef.current) {
      terminalEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [status?.logs, autoScrollLogs]);

  // Format elapsed time
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  };

  // ── Handlers ─────────────────────────────────────────────
  const showToast = (type: "success" | "error", text: string) => {
    setActionMsg({ type, text });
    setTimeout(() => setActionMsg(null), 5000);
  };

  const handleStartParse = async () => {
    setActionLoading(true);
    try {
      const res = await fetchApi("/scraper/start-parse", {
        method: "POST",
        body: JSON.stringify({
          source: parseSource,
          pages: Number(parsePages),
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
          limit: Number(downloadLimit),
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
      showToast("success", `${id} qayta navbatga qo'yildi`);
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
      showToast("success", `${id} navbatdan o'chirildi`);
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
    if (!confirm(`Barcha '${st}' statusidagi elementlar navbatdan butunlay o'chirilsinmi?`)) return;
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
    total: 0,
    pending: 0,
    completed: 0,
    already_exists: 0,
    failed: 0,
    in_progress: 0,
  };

  const isRunning = status?.is_running ?? false;

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto space-y-6">
      {/* Toast Notification */}
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

      {/* Page Header */}
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
                Saytlardan avtomatlashtirilgan katalog yig'ish, Telegram botlardan videolarni grab qilish va jarayon monitoringi
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
            title={isPolling ? "Avtomatik yangilanishni to'xtatish" : "Avtomatik yangilanishni yoqish"}
          >
            <span className={`material-symbols-outlined text-sm ${isPolling ? "animate-spin" : ""}`}>sync</span>
            <span>{isPolling ? "Avto-yangilanish: Faol (2s)" : "Avto-yangilanish: To'xtatilgan"}</span>
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

      {statusError && (
        <div className="bg-red-500/10 border border-red-500/30 text-red-300 rounded-xl px-4 py-3 text-sm flex items-start gap-3">
          <span className="material-symbols-outlined text-xl shrink-0">warning</span>
          <div>
            <p className="font-semibold">Scraper holatini olib bo'lmadi</p>
            <p className="text-xs text-red-300/80 mt-0.5">{statusError}</p>
          </div>
        </div>
      )}

      {/* ── 1. ACTIVE PROCESS MONITOR (KATTA VIZUAL PANEL) ─────────── */}
      <div className="bg-surface-container-lowest/80 border border-white/10 rounded-2xl p-5 sm:p-6 backdrop-blur-md relative overflow-hidden shadow-2xl">
        <div className="absolute top-0 right-0 w-80 h-80 bg-primary-container/10 rounded-full blur-3xl pointer-events-none -z-0" />

        <div className="relative z-10 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <span className={`p-2.5 rounded-xl flex items-center justify-center ${
                isRunning ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30" : "bg-white/5 text-zinc-400 border border-white/10"
              }`}>
                <span className={`material-symbols-outlined text-2xl ${isRunning ? "animate-pulse" : ""}`}>
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
                      <span className="capitalize">{status?.task_type}</span> vazifasi bajarilmoqda
                    </>
                  ) : (
                    "Tizim hozir kutish rejimida"
                  )}
                </h3>
              </div>
            </div>

            {/* Time and Stop Button */}
            <div className="flex items-center gap-3">
              {status?.started_at && (
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
                <span className="w-2 h-2 rounded-full bg-primary-container animate-ping"></span>
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
              <p className="truncate">{status?.current_action || "Hozirda hech qanday fon vazifasi bajarilmayapti."}</p>
            </div>

            {/* Progress Bar ("Qanchalik tugatdan") */}
            <div className="space-y-1.5 pt-1">
              <div className="flex justify-between items-center text-xs">
                <span className="text-text-secondary">
                  Jarayon bajarilishi:{" "}
                  <strong className="text-white">
                    {status?.progress.current ?? 0} / {status?.progress.total ?? 0}
                  </strong>
                </span>
                <span className="font-mono font-bold text-primary-container">
                  {status?.progress.percentage ?? 0}%
                </span>
              </div>
              <div className="w-full h-3 bg-white/5 border border-white/10 rounded-full overflow-hidden p-0.5">
                <div
                  className="h-full bg-gradient-to-r from-red-600 via-primary-container to-amber-500 rounded-full transition-all duration-500 relative"
                  style={{ width: `${Math.min(100, Math.max(0, status?.progress.percentage ?? 0))}%` }}
                >
                  <div className="absolute inset-0 bg-white/20 animate-pulse rounded-full" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── 2. STATISTICAL METRICS OVERVIEW (6 KARTALAR) ───────────── */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 sm:gap-4">
        {/* Total */}
        <div className="bg-surface-container-lowest/60 border border-white/5 p-4 rounded-xl flex flex-col justify-between">
          <div className="flex items-center justify-between text-text-secondary">
            <span className="text-xs font-semibold uppercase tracking-wider">Jami Navbat</span>
            <span className="material-symbols-outlined text-lg">format_list_bulleted</span>
          </div>
          <div className="mt-2 text-2xl font-bold text-white">{stats.total}</div>
        </div>

        {/* Pending */}
        <div className="bg-surface-container-lowest/60 border border-amber-500/20 p-4 rounded-xl flex flex-col justify-between">
          <div className="flex items-center justify-between text-amber-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Kutilmoqda</span>
            <span className="material-symbols-outlined text-lg">pending_actions</span>
          </div>
          <div className="mt-2 text-2xl font-bold text-amber-300">{stats.pending}</div>
        </div>

        {/* Completed */}
        <div className="bg-surface-container-lowest/60 border border-emerald-500/20 p-4 rounded-xl flex flex-col justify-between">
          <div className="flex items-center justify-between text-emerald-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Bajarildi</span>
            <span className="material-symbols-outlined text-lg">check_circle</span>
          </div>
          <div className="mt-2 text-2xl font-bold text-emerald-300">{stats.completed}</div>
        </div>

        {/* Already exists */}
        <div className="bg-surface-container-lowest/60 border border-sky-500/20 p-4 rounded-xl flex flex-col justify-between">
          <div className="flex items-center justify-between text-sky-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Bazada Bor</span>
            <span className="material-symbols-outlined text-lg">dataset_linked</span>
          </div>
          <div className="mt-2 text-2xl font-bold text-sky-300">{stats.already_exists}</div>
        </div>

        {/* Failed */}
        <div className="bg-surface-container-lowest/60 border border-red-500/20 p-4 rounded-xl flex flex-col justify-between">
          <div className="flex items-center justify-between text-red-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Xatolik</span>
            <span className="material-symbols-outlined text-lg">error</span>
          </div>
          <div className="mt-2 text-2xl font-bold text-red-400">{stats.failed}</div>
        </div>

        {/* In progress */}
        <div className="bg-surface-container-lowest/60 border border-primary-container/20 p-4 rounded-xl flex flex-col justify-between">
          <div className="flex items-center justify-between text-primary-container">
            <span className="text-xs font-semibold uppercase tracking-wider">Yuklanmoqda</span>
            <span className="material-symbols-outlined text-lg">autorenew</span>
          </div>
          <div className="mt-2 text-2xl font-bold text-primary-container">{stats.in_progress}</div>
        </div>
      </div>

      {/* ── 3. ACTIONS & LIVE LOGS (IKKI USTUNLI ZONA) ─────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Control Panel (5 columns) */}
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
                onClick={() => setActiveTab("tools")}
                className={`px-3 py-1 rounded-lg transition-all font-medium ${
                  activeTab === "tools" ? "bg-primary-container text-white shadow" : "text-zinc-400 hover:text-white"
                }`}
              >
                Servis
              </button>
            </div>
          </div>

          {/* TAB 1: GRABBER (TELEGRAM BOTDAN YUKLASH) */}
          {activeTab === "grabber" && (
            <div className="space-y-4 flex-1 flex flex-col justify-between">
              <div className="space-y-3">
                <p className="text-xs text-text-secondary">
                  Telegram botlaridan videolarni avtomatik qidirish, yuklab olish, kanalga joylash va saytga ulash.
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
                      onChange={(e) => setDownloadLimit(Number(e.target.value))}
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

          {/* TAB 2: PARSER (SAYTDAN KATALOG YIG'ISH) */}
          {activeTab === "parser" && (
            <div className="space-y-4 flex-1 flex flex-col justify-between">
              <div className="space-y-3">
                <p className="text-xs text-text-secondary">
                  Saytlar katalogidan eng so'nggi film va seriallar ro'yxatini parallel ravishda yig'ish va navbatga qo'shish.
                </p>

                {/* Source Selection */}
                <div>
                  <label className="block text-xs font-semibold text-text-secondary mb-1">Sayt Manbasi</label>
                  <select
                    value={parseSource}
                    onChange={(e) => setParseSource(e.target.value)}
                    className="w-full bg-black/40 border border-white/10 rounded-xl px-3 py-2.5 text-sm text-white focus:outline-none focus:border-primary-container"
                  >
                    <option value="uzmovi">Uzmovi (uzmovi.com / tarjima-kinolar)</option>
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
                    onChange={(e) => setParsePages(Number(e.target.value))}
                    className="w-full bg-black/40 border border-white/10 rounded-xl px-3 py-2.5 text-sm text-white focus:outline-none focus:border-primary-container"
                  />
                  <span className="text-[10px] text-zinc-400 mt-0.5 block">
                    Har bir sahifada ~10-15 ta film bo'ladi. Barchasi parallel va dublikatlardan tozalangan holda qo'shiladi.
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

          {/* TAB 3: TOOLS & MAINTENANCE */}
          {activeTab === "tools" && (
            <div className="space-y-3 flex-1 flex flex-col justify-between">
              <div className="space-y-2.5">
                <p className="text-xs text-text-secondary mb-2">
                  Navbatni optimallashtirish, xatolarni tozalash va dublikatlarni qayta tekshirish amallari.
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
                      <div className="text-[11px] text-zinc-400">Navbatni bazadagi kinolar bilan qayta tekshiradi</div>
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
                      <div className="text-[11px] text-zinc-400">Barcha failed elementlarni pending holatiga o'tkazadi</div>
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
                      <div className="text-[11px] text-zinc-400">Yuklab olingan elementlarni ro'yxatdan o'chiradi</div>
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
                      <div className="text-[11px] text-zinc-400">Bazada allaqachon mavjud bo'lganlarni navbatdan olib tashlaydi</div>
                    </div>
                  </div>
                  <span className="material-symbols-outlined text-sm text-zinc-400">chevron_right</span>
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Right: Live Terminal Logs (7 columns) */}
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
                title="Skrollni doimo pastga ushlab turish"
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

          {/* Terminal Content */}
          <div className="flex-1 p-3 sm:p-4 font-mono text-xs overflow-y-auto space-y-1 select-text">
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
            <div ref={terminalEndRef} />
          </div>
        </div>
      </div>

      {/* ── 4. QUEUE TABLE EXPLORER (NAVBAT RO'YXATI VA FILTRLAR) ───── */}
      <div className="bg-surface-container-lowest/60 border border-white/10 rounded-2xl p-5 space-y-4">
        {/* Header & Controls */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-white/5 pb-4">
          <div>
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <span className="material-symbols-outlined text-primary-container">view_list</span>
              Navbatdagi Filmlar va Seriallar ({queueTotal} ta)
            </h2>
            <p className="text-xs text-text-secondary mt-0.5">
              Yuklanishi kutilayotgan, bajarilgan yoki tekshiruvdan o'tgan barcha elementlar
            </p>
          </div>

          {/* Search Input */}
          <div className="flex items-center gap-2">
            <div className="relative">
              <span className="material-symbols-outlined absolute left-3 top-2.5 text-zinc-500 text-lg">search</span>
              <input
                type="text"
                placeholder="Qidiruv (nomi, kodi)..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") fetchQueue(1);
                }}
                className="pl-9 pr-3 py-2 bg-black/40 border border-white/10 rounded-xl text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-primary-container w-60"
              />
            </div>
            <button
              onClick={() => fetchQueue(1)}
              className="px-3 py-2 rounded-xl bg-white/5 border border-white/10 text-white hover:bg-white/10 text-xs font-semibold"
            >
              Qidirish
            </button>
          </div>
        </div>

        {/* Filters Tabs */}
        <div className="flex flex-wrap items-center justify-between gap-3">
          {/* Status filter buttons */}
          <div className="flex flex-wrap items-center gap-1.5">
            {[
              { id: "all", label: "Barchasi" },
              { id: "pending", label: `Kutilmoqda (${stats.pending})` },
              { id: "in_progress", label: `Jarayonda (${stats.in_progress})` },
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

          {/* Source filter dropdown */}
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

        {/* Table Container */}
        <div className="overflow-x-auto rounded-xl border border-white/5">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-white/5 text-text-secondary uppercase text-[10px] tracking-wider border-b border-white/5">
                <th className="py-3 px-4">Film / Serial</th>
                <th className="py-3 px-4">Turi</th>
                <th className="py-3 px-4">Yili</th>
                <th className="py-3 px-4">Manba</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Izoh / Xatolik</th>
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
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                          item.media_type === "series" ? "bg-purple-500/20 text-purple-300 border border-purple-500/30" : "bg-blue-500/20 text-blue-300 border border-blue-500/30"
                        }`}>
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

                      {/* Error / note */}
                      <td className="py-3 px-4 max-w-xs truncate">
                        {item.error_message ? (
                          <span className={`text-[11px] ${item.status === 'failed' ? 'text-red-400' : 'text-zinc-400'}`}>
                            {item.error_message}
                          </span>
                        ) : (
                          <span className="text-zinc-600">-</span>
                        )}
                      </td>

                      {/* Actions */}
                      <td className="py-3 px-4 text-right whitespace-nowrap">
                        <div className="flex items-center justify-end gap-1.5">
                          {item.status !== "pending" && (
                            <button
                              onClick={() => handleRetryItem(item.id)}
                              className="p-1.5 rounded-lg bg-white/5 border border-white/10 hover:bg-amber-500/20 hover:border-amber-500/40 hover:text-amber-300 text-zinc-400 transition-all"
                              title="Qayta navbatga qo'yish"
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
    </div>
  );
}
