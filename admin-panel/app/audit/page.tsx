"use client";

import { useEffect, useState, useRef } from "react";
import { fetchApi } from "@/lib/api";
import VideoUploadModal from "@/components/VideoUploadModal";
import Link from "next/link";

type IssueBadge = {
  code: string;
  label: string;
  severity: "danger" | "warning" | "info";
};

type AuditItem = {
  id: number;
  content_type: "movie" | "series";
  title: string;
  original_title?: string | null;
  code?: string | null;
  poster_url?: string | null;
  trailer_url?: string | null;
  description?: string | null;
  genres?: string | null;
  release_year?: number | null;
  imdb_rating?: number | null;
  tmdb_id?: number | null;
  source_id?: number | null;
  source_topic_id?: number | null;
  categories: { id: number; name: string }[];
  has_video: boolean;
  has_poster: boolean;
  has_description: boolean;
  has_genres: boolean;
  has_categories: boolean;
  has_trailer: boolean;
  has_tmdb: boolean;
  has_source: boolean;
  issues: IssueBadge[];
  issues_count: number;
};

type AuditStatsSection = {
  total: number;
  missing_video: number;
  missing_poster: number;
  missing_description: number;
  missing_genres: number;
  missing_categories: number;
  missing_trailer: number;
  missing_tmdb: number;
  missing_source: number;
  has_any_issue: number;
  healthy_count: number;
  health_score: number;
};

type AuditStats = {
  movies: AuditStatsSection;
  series: AuditStatsSection;
  overall_health_score: number;
  total_content: number;
  total_issues_content: number;
};

type Category = { id: number; name: string };

const ISSUE_FILTERS = [
  { id: "all_issues", label: "Barcha kamchiliklar", icon: "warning", color: "text-amber-400 border-amber-500/30 bg-amber-500/10" },
  { id: "missing_video", label: "Videosi yo'q", icon: "videocam_off", color: "text-rose-400 border-rose-500/30 bg-rose-500/10" },
  { id: "missing_poster", label: "Posteri yo'q / xato", icon: "broken_image", color: "text-red-400 border-red-500/30 bg-red-500/10" },
  { id: "missing_description", label: "Tasnifi yo'q / qisqa", icon: "description", color: "text-amber-300 border-amber-500/30 bg-amber-500/10" },
  { id: "missing_categories", label: "Kategoriya yo'q", icon: "category", color: "text-purple-400 border-purple-500/30 bg-purple-500/10" },
  { id: "missing_genres", label: "Janrlari yo'q", icon: "theater_comedy", color: "text-pink-400 border-pink-500/30 bg-pink-500/10" },
  { id: "missing_trailer", label: "Treyler yo'q", icon: "movie", color: "text-sky-400 border-sky-500/30 bg-sky-500/10" },
  { id: "missing_tmdb", label: "TMDb ulanmagan", icon: "sync_problem", color: "text-blue-400 border-blue-500/30 bg-blue-500/10" },
  { id: "missing_source", label: "Manba / Topic yo'q", icon: "forum", color: "text-emerald-400 border-emerald-500/30 bg-emerald-500/10" },
  { id: "healthy", label: "100% To'liq (Sog'lom)", icon: "check_circle", color: "text-emerald-400 border-emerald-500/30 bg-emerald-500/10" },
];

export default function AuditPage() {
  const [stats, setStats] = useState<AuditStats | null>(null);
  const [contentType, setContentType] = useState<"movie" | "series">("movie");
  const [issueType, setIssueType] = useState<string>("all_issues");
  const [searchQuery, setSearchQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  
  const [items, setItems] = useState<AuditItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [statsLoading, setStatsLoading] = useState(true);
  
  const [categories, setCategories] = useState<Category[]>([]);
  const [toast, setToast] = useState<{ message: string; type: "success" | "error" } | null>(null);

  // Quick edit modal
  const [editingItem, setEditingItem] = useState<AuditItem | null>(null);
  const [editForm, setEditForm] = useState({
    title: "",
    original_title: "",
    description: "",
    poster_url: "",
    trailer_url: "",
    genres: "",
    release_year: 0,
    imdb_rating: 0,
    tmdb_id: 0,
    category_ids: [] as number[],
  });
  const [savingEdit, setSavingEdit] = useState(false);

  // Auto-fix loading
  const [autoFixingId, setAutoFixingId] = useState<number | null>(null);

  // Video Upload Modal for Movies
  const [videoModalOpen, setVideoModalOpen] = useState(false);
  const [videoMovieId, setVideoMovieId] = useState<number | null>(null);

  // Delete Confirmation
  const [deletingItem, setDeletingItem] = useState<AuditItem | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const PAGE_SIZE = 50;

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(searchQuery.trim());
    }, 350);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Load stats and categories on mount
  useEffect(() => {
    loadStats();
    loadCategories();
  }, []);

  // Reload items when content type, issue filter, or search changes
  useEffect(() => {
    loadItems(true);
  }, [contentType, issueType, debouncedQuery]);

  const showToast = (message: string, type: "success" | "error" = "success") => {
    setToast({ message, type });
    setTimeout(() => {
      setToast(null);
    }, 4500);
  };

  const loadStats = async () => {
    setStatsLoading(true);
    try {
      const data = await fetchApi("/audit/stats");
      setStats(data);
    } catch (e: any) {
      console.error("Audit stats error:", e);
    } finally {
      setStatsLoading(false);
    }
  };

  const loadCategories = async () => {
    try {
      const data = await fetchApi("/categories");
      setCategories(Array.isArray(data) ? data : data.items || []);
    } catch (e) {
      console.error(e);
    }
  };

  const loadItems = async (reset = true) => {
    if (reset) {
      setLoading(true);
    } else {
      setLoadingMore(true);
    }

    try {
      const skip = reset ? 0 : items.length;
      let url = `/audit/items?content_type=${contentType}&issue_type=${issueType}&skip=${skip}&limit=${PAGE_SIZE}`;
      if (debouncedQuery) {
        url += `&search=${encodeURIComponent(debouncedQuery)}`;
      }

      const res = await fetchApi(url);
      const newItems = res.items || [];
      if (reset) {
        setItems(newItems);
        setTotal(res.total || 0);
      } else {
        setItems((prev) => {
          const ids = new Set(prev.map((i) => i.id));
          return [...prev, ...newItems.filter((i: AuditItem) => !ids.has(i.id))];
        });
        setTotal(res.total || 0);
      }
    } catch (e: any) {
      console.error("Audit items error:", e);
      showToast("Ro'yxatni yuklashda xatolik: " + e.message, "error");
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  };

  // 1-Click TMDb Auto-Fix
  const handleAutoFix = async (item: AuditItem) => {
    setAutoFixingId(item.id);
    try {
      const res = await fetchApi(`/audit/autofix/${item.content_type}/${item.id}`, {
        method: "POST",
      });
      showToast(`⚡️ ${item.title}: ${res.message}`, "success");
      await loadStats();
      await loadItems(true);
    } catch (err: any) {
      showToast(`Avto-to'ldirishda xatolik: ${err.message}`, "error");
    } finally {
      setAutoFixingId(null);
    }
  };

  // Open Quick Edit
  const handleOpenEdit = (item: AuditItem) => {
    setEditingItem(item);
    setEditForm({
      title: item.title || "",
      original_title: item.original_title || "",
      description: item.description || "",
      poster_url: item.poster_url || "",
      trailer_url: item.trailer_url || "",
      genres: item.genres || "",
      release_year: item.release_year || new Date().getFullYear(),
      imdb_rating: item.imdb_rating || 0,
      tmdb_id: item.tmdb_id || 0,
      category_ids: (item.categories || []).map((c) => c.id),
    });
  };

  // Save Quick Edit
  const handleSaveEdit = async () => {
    if (!editingItem) return;
    setSavingEdit(true);
    try {
      const payload = {
        title: editForm.title.trim(),
        original_title: editForm.original_title.trim() || null,
        description: editForm.description.trim() || null,
        poster_url: editForm.poster_url.trim() || null,
        trailer_url: editForm.trailer_url.trim() || null,
        genres: editForm.genres.trim() || null,
        release_year: editForm.release_year ? Number(editForm.release_year) : null,
        imdb_rating: editForm.imdb_rating ? Number(editForm.imdb_rating) : null,
        tmdb_id: editForm.tmdb_id ? Number(editForm.tmdb_id) : null,
        category_ids: editForm.category_ids,
      };

      const res = await fetchApi(
        `/audit/quick-update/${editingItem.content_type}/${editingItem.id}`,
        {
          method: "PUT",
          body: JSON.stringify(payload),
        }
      );

      showToast(res.message || "Muvaffaqiyatli saqlandi!", "success");
      setEditingItem(null);
      await loadStats();
      await loadItems(true);
    } catch (err: any) {
      showToast("Saqlashda xatolik: " + err.message, "error");
    } finally {
      setSavingEdit(false);
    }
  };

  // Delete item
  const handleDeleteItem = async () => {
    if (!deletingItem) return;
    setIsDeleting(true);
    try {
      const endpoint =
        deletingItem.content_type === "movie"
          ? `/movies/${deletingItem.id}`
          : `/series/${deletingItem.id}`;
      await fetchApi(endpoint, { method: "DELETE" });
      showToast(`"${deletingItem.title}" muvaffaqiyatli o'chirildi`, "success");
      setDeletingItem(null);
      await loadStats();
      await loadItems(true);
    } catch (err: any) {
      showToast("O'chirishda xatolik: " + err.message, "error");
    } finally {
      setIsDeleting(false);
    }
  };

  // Active section stats
  const activeStats = stats ? (contentType === "movie" ? stats.movies : stats.series) : null;

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto space-y-6">
      {/* Toast notification */}
      {toast && (
        <div
          className={`fixed bottom-6 right-6 z-50 px-4 py-3 rounded-xl shadow-2xl flex items-center gap-3 border transition-all ${
            toast.type === "success"
              ? "bg-emerald-950/90 text-emerald-200 border-emerald-500/40"
              : "bg-rose-950/90 text-rose-200 border-rose-500/40"
          }`}
        >
          <span className="material-symbols-outlined text-xl">
            {toast.type === "success" ? "check_circle" : "error"}
          </span>
          <span className="text-sm font-medium">{toast.message}</span>
          <button
            onClick={() => setToast(null)}
            className="text-xs opacity-70 hover:opacity-100 ml-2"
          >
            ✕
          </button>
        </div>
      )}

      {/* Page Header & Health Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-primary-container/20 border border-primary-container/40 flex items-center justify-center text-primary-container">
              <span className="material-symbols-outlined text-2xl">fact_check</span>
            </div>
            <div>
              <h1 className="text-xl sm:text-2xl font-bold font-display text-text-primary">
                Kontent Auditi va Nosozliklar Nazorati
              </h1>
              <p className="text-xs sm:text-sm text-text-secondary mt-0.5">
                Baza sifatini tekshirish, nuqsonli kino/seriallarni saralash va tezkor to'g'rilash
              </p>
            </div>
          </div>
        </div>

        {/* Global Health Score Pill */}
        <div className="flex items-center gap-3 bg-surface-container-lowest/80 border border-white/10 p-3 rounded-2xl backdrop-blur-md">
          <div className="flex flex-col">
            <span className="text-[10px] uppercase font-bold text-text-secondary tracking-wider">
              Umumiy Baza Sifati (Health Score)
            </span>
            <div className="flex items-center gap-2 mt-0.5">
              <span
                className={`text-2xl font-black font-display ${
                  stats
                    ? stats.overall_health_score >= 85
                      ? "text-emerald-400"
                      : stats.overall_health_score >= 60
                      ? "text-amber-400"
                      : "text-rose-400"
                    : "text-text-secondary"
                }`}
              >
                {stats ? `${stats.overall_health_score}%` : "--%"}
              </span>
              <span className="text-xs text-text-secondary">
                ({stats ? stats.total_content - stats.total_issues_content : 0} / {stats?.total_content || 0} to'liq)
              </span>
            </div>
          </div>
          <button
            onClick={() => {
              loadStats();
              loadItems(true);
            }}
            disabled={statsLoading}
            className="p-2.5 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-text-secondary hover:text-white transition-all disabled:opacity-50"
            title="Qayta tekshirish"
          >
            <span className={`material-symbols-outlined text-lg ${statsLoading ? "animate-spin" : ""}`}>
              refresh
            </span>
          </button>
        </div>
      </div>

      {/* Content Type Selector (Kinolar vs Seriallar) */}
      <div className="flex border-b border-white/10 gap-2">
        <button
          onClick={() => {
            setContentType("movie");
            setIssueType("all_issues");
          }}
          className={`flex items-center gap-2.5 px-5 py-3 border-b-2 font-medium text-sm transition-all ${
            contentType === "movie"
              ? "border-primary-container text-primary-container bg-primary-container/10 rounded-t-xl"
              : "border-transparent text-text-secondary hover:text-text-primary"
          }`}
        >
          <span className="material-symbols-outlined text-lg">movie</span>
          <span>Kinolar ({stats?.movies.total || 0})</span>
          {stats && stats.movies.has_any_issue > 0 && (
            <span className="text-xs px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-300 border border-rose-500/30 font-mono">
              {stats.movies.has_any_issue} ta nuqson
            </span>
          )}
        </button>

        <button
          onClick={() => {
            setContentType("series");
            setIssueType("all_issues");
          }}
          className={`flex items-center gap-2.5 px-5 py-3 border-b-2 font-medium text-sm transition-all ${
            contentType === "series"
              ? "border-primary-container text-primary-container bg-primary-container/10 rounded-t-xl"
              : "border-transparent text-text-secondary hover:text-text-primary"
          }`}
        >
          <span className="material-symbols-outlined text-lg">live_tv</span>
          <span>Seriallar ({stats?.series.total || 0})</span>
          {stats && stats.series.has_any_issue > 0 && (
            <span className="text-xs px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-300 border border-rose-500/30 font-mono">
              {stats.series.has_any_issue} ta nuqson
            </span>
          )}
        </button>
      </div>

      {/* Stats Counter Cards Grid */}
      {activeStats && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          <div
            onClick={() => setIssueType("missing_video")}
            className={`metric-card p-3.5 rounded-xl cursor-pointer transition-all border ${
              issueType === "missing_video"
                ? "border-rose-500 bg-rose-500/15 ring-2 ring-rose-500/30"
                : "border-white/5 hover:border-white/20"
            }`}
          >
            <div className="flex items-center justify-between text-rose-400 mb-1">
              <span className="text-xs font-semibold">Videosi yo'q</span>
              <span className="material-symbols-outlined text-base">videocam_off</span>
            </div>
            <div className="text-xl sm:text-2xl font-black font-mono text-text-primary">
              {activeStats.missing_video}
            </div>
            <div className="text-[10px] text-text-secondary mt-1">Kritik kamchilik</div>
          </div>

          <div
            onClick={() => setIssueType("missing_poster")}
            className={`metric-card p-3.5 rounded-xl cursor-pointer transition-all border ${
              issueType === "missing_poster"
                ? "border-red-500 bg-red-500/15 ring-2 ring-red-500/30"
                : "border-white/5 hover:border-white/20"
            }`}
          >
            <div className="flex items-center justify-between text-red-400 mb-1">
              <span className="text-xs font-semibold">Posteri yo'q</span>
              <span className="material-symbols-outlined text-base">broken_image</span>
            </div>
            <div className="text-xl sm:text-2xl font-black font-mono text-text-primary">
              {activeStats.missing_poster}
            </div>
            <div className="text-[10px] text-text-secondary mt-1">Ko'rinish buziladi</div>
          </div>

          <div
            onClick={() => setIssueType("missing_description")}
            className={`metric-card p-3.5 rounded-xl cursor-pointer transition-all border ${
              issueType === "missing_description"
                ? "border-amber-500 bg-amber-500/15 ring-2 ring-amber-500/30"
                : "border-white/5 hover:border-white/20"
            }`}
          >
            <div className="flex items-center justify-between text-amber-400 mb-1">
              <span className="text-xs font-semibold">Tasnifi yo'q</span>
              <span className="material-symbols-outlined text-base">description</span>
            </div>
            <div className="text-xl sm:text-2xl font-black font-mono text-text-primary">
              {activeStats.missing_description}
            </div>
            <div className="text-[10px] text-text-secondary mt-1">Bo'sh yoki &lt;30 belgi</div>
          </div>

          <div
            onClick={() => setIssueType("missing_categories")}
            className={`metric-card p-3.5 rounded-xl cursor-pointer transition-all border ${
              issueType === "missing_categories"
                ? "border-purple-500 bg-purple-500/15 ring-2 ring-purple-500/30"
                : "border-white/5 hover:border-white/20"
            }`}
          >
            <div className="flex items-center justify-between text-purple-400 mb-1">
              <span className="text-xs font-semibold">Kategoriya yo'q</span>
              <span className="material-symbols-outlined text-base">category</span>
            </div>
            <div className="text-xl sm:text-2xl font-black font-mono text-text-primary">
              {activeStats.missing_categories}
            </div>
            <div className="text-[10px] text-text-secondary mt-1">Katalogda chiqmaydi</div>
          </div>

          <div
            onClick={() => setIssueType("missing_tmdb")}
            className={`metric-card p-3.5 rounded-xl cursor-pointer transition-all border ${
              issueType === "missing_tmdb"
                ? "border-blue-500 bg-blue-500/15 ring-2 ring-blue-500/30"
                : "border-white/5 hover:border-white/20"
            }`}
          >
            <div className="flex items-center justify-between text-blue-400 mb-1">
              <span className="text-xs font-semibold">TMDb ulanmagan</span>
              <span className="material-symbols-outlined text-base">sync_problem</span>
            </div>
            <div className="text-xl sm:text-2xl font-black font-mono text-text-primary">
              {activeStats.missing_tmdb}
            </div>
            <div className="text-[10px] text-text-secondary mt-1">Avto-yangilanmaydi</div>
          </div>

          <div
            onClick={() => setIssueType("healthy")}
            className={`metric-card p-3.5 rounded-xl cursor-pointer transition-all border ${
              issueType === "healthy"
                ? "border-emerald-500 bg-emerald-500/15 ring-2 ring-emerald-500/30"
                : "border-white/5 hover:border-white/20"
            }`}
          >
            <div className="flex items-center justify-between text-emerald-400 mb-1">
              <span className="text-xs font-semibold">To'liq (Sog'lom)</span>
              <span className="material-symbols-outlined text-base">verified</span>
            </div>
            <div className="text-xl sm:text-2xl font-black font-mono text-text-primary">
              {activeStats.healthy_count}
            </div>
            <div className="text-[10px] text-emerald-400 font-bold mt-1">
              {activeStats.health_score}% to'liq
            </div>
          </div>
        </div>
      )}

      {/* Filter Chips Bar & Search */}
      <div className="bg-surface-container-lowest/80 border border-white/10 p-4 rounded-2xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        {/* Filter Badges scroll container */}
        <div className="flex items-center gap-2 overflow-x-auto custom-scrollbar pb-1 max-w-full">
          {ISSUE_FILTERS.map((f) => {
            const isSelected = issueType === f.id;
            return (
              <button
                key={f.id}
                onClick={() => setIssueType(f.id)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-medium border whitespace-nowrap transition-all ${
                  isSelected
                    ? "bg-primary-container text-white border-primary-container shadow-lg shadow-primary-container/20 scale-105"
                    : "bg-surface-container-high/60 text-text-secondary hover:text-text-primary border-white/5 hover:bg-white/5"
                }`}
              >
                <span className="material-symbols-outlined text-[16px]">{f.icon}</span>
                <span>{f.label}</span>
              </button>
            );
          })}
        </div>

        {/* Search Bar */}
        <div className="relative w-full md:w-72 shrink-0">
          <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-text-secondary text-lg">
            search
          </span>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Nomi yoki kodi bo'yicha qidirish..."
            className="w-full bg-surface-container-high border border-white/10 rounded-xl pl-9 pr-8 py-2 text-xs sm:text-sm text-text-primary placeholder:text-text-secondary/50 focus:border-primary-container focus:outline-none"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery("")}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-text-secondary hover:text-white text-xs p-1"
            >
              ✕
            </button>
          )}
        </div>
      </div>

      {/* Results Header */}
      <div className="flex items-center justify-between px-1">
        <div className="flex items-center gap-2 text-sm text-text-secondary">
          <span>Topilgan kontentlar:</span>
          <span className="font-bold text-text-primary font-mono bg-white/5 px-2 py-0.5 rounded-lg border border-white/10">
            {total} ta
          </span>
          {loading && (
            <span className="w-3.5 h-3.5 border-2 border-primary-container border-t-transparent rounded-full animate-spin"></span>
          )}
        </div>
      </div>

      {/* Audit Items Table */}
      <div className="metric-card rounded-2xl overflow-hidden border border-white/10 shadow-xl">
        <div className="overflow-x-auto custom-scrollbar">
          <table className="w-full min-w-[800px] text-left border-collapse">
            <thead className="bg-surface-container-lowest border-b border-white/10 text-xs font-semibold text-text-secondary uppercase tracking-wider">
              <tr>
                <th className="px-4 py-3.5 w-16">Poster</th>
                <th className="px-4 py-3.5">Nomi va Ma'lumot</th>
                <th className="px-4 py-3.5">Aniqlangan Kamchiliklar</th>
                <th className="px-4 py-3.5 text-right w-56">Tezkor Amallar</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5 text-sm">
              {loading && items.length === 0 ? (
                <tr>
                  <td colSpan={4} className="py-16 text-center text-text-secondary">
                    <span className="w-6 h-6 border-2 border-primary-container border-t-transparent rounded-full animate-spin inline-block mb-2"></span>
                    <p className="text-xs">Ma'lumotlar tahlil qilinmoqda...</p>
                  </td>
                </tr>
              ) : items.length === 0 ? (
                <tr>
                  <td colSpan={4} className="py-16 text-center text-text-secondary">
                    <span className="material-symbols-outlined text-4xl text-emerald-400 mb-2">
                      verified
                    </span>
                    <p className="text-sm font-medium text-text-primary">
                      Bu filtr bo'yicha hech qanday nuqsonli kontent topilmadi!
                    </p>
                    <p className="text-xs mt-1">Barcha kontentlar talabga javob beradi.</p>
                  </td>
                </tr>
              ) : (
                items.map((item) => (
                  <tr key={item.id} className="data-table-row hover:bg-white/[0.03] transition-colors">
                    {/* Poster Thumbnail */}
                    <td className="px-4 py-3 align-top">
                      <div className="w-12 h-16 rounded-lg overflow-hidden bg-surface-container-high border border-white/10 shrink-0 flex items-center justify-center relative">
                        {item.poster_url ? (
                          <img
                            src={item.poster_url}
                            alt={item.title}
                            className="w-full h-full object-cover"
                            onError={(e) => {
                              // Fallback on broken image
                              (e.target as HTMLElement).style.display = "none";
                            }}
                          />
                        ) : (
                          <span className="material-symbols-outlined text-rose-400 text-xl" title="Poster yo'q">
                            image_not_supported
                          </span>
                        )}
                      </div>
                    </td>

                    {/* Title & Details */}
                    <td className="px-4 py-3 align-top">
                      <div className="flex flex-col gap-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="font-bold text-text-primary hover:text-primary-container transition-colors">
                            {item.title}
                          </span>
                          {item.code && (
                            <span className="text-xs font-mono px-2 py-0.5 rounded bg-white/5 border border-white/10 text-primary-container font-bold">
                              #{item.code}
                            </span>
                          )}
                          {item.tmdb_id ? (
                            <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">
                              TMDb #{item.tmdb_id}
                            </span>
                          ) : null}
                          {item.imdb_rating ? (
                            <span className="text-xs text-rating-gold font-bold">
                              ★ {item.imdb_rating}
                            </span>
                          ) : null}
                        </div>

                        <div className="text-xs text-text-secondary flex items-center gap-2 flex-wrap">
                          {item.original_title && (
                            <span className="italic">({item.original_title})</span>
                          )}
                          {item.release_year ? <span>{item.release_year}-yil</span> : null}
                          {item.categories && item.categories.length > 0 ? (
                            <span className="text-purple-300">
                              • {item.categories.map((c) => c.name).join(", ")}
                            </span>
                          ) : (
                            <span className="text-rose-400 font-semibold">• Kategoriya belgilanmagan</span>
                          )}
                        </div>

                        {/* Description Preview */}
                        {item.description ? (
                          <p className="text-xs text-text-secondary/70 line-clamp-2 max-w-xl mt-0.5">
                            {item.description}
                          </p>
                        ) : (
                          <p className="text-xs text-rose-400/80 italic mt-0.5">
                            Tasnif yozilmagan
                          </p>
                        )}
                      </div>
                    </td>

                    {/* Detected Issues Badges */}
                    <td className="px-4 py-3 align-top">
                      <div className="flex flex-wrap gap-1.5 max-w-md">
                        {item.issues.length === 0 ? (
                          <span className="text-xs text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-1 rounded-lg flex items-center gap-1">
                            <span className="material-symbols-outlined text-[14px]">check</span>
                            Nuqsonsiz (100% To'liq)
                          </span>
                        ) : (
                          item.issues.map((iss) => (
                            <span
                              key={iss.code}
                              className={`text-xs px-2 py-0.5 rounded-lg border font-medium flex items-center gap-1 ${
                                iss.severity === "danger"
                                  ? "bg-rose-500/15 text-rose-300 border-rose-500/30"
                                  : iss.severity === "warning"
                                  ? "bg-amber-500/15 text-amber-300 border-amber-500/30"
                                  : "bg-blue-500/15 text-blue-300 border-blue-500/30"
                              }`}
                            >
                              <span className="w-1.5 h-1.5 rounded-full bg-current"></span>
                              {iss.label}
                            </span>
                          ))
                        )}
                      </div>
                    </td>

                    {/* Actions */}
                    <td className="px-4 py-3 align-top text-right">
                      <div className="flex items-center justify-end gap-1.5 flex-wrap">
                        {/* 1-Click TMDb Auto-Fix */}
                        <button
                          onClick={() => handleAutoFix(item)}
                          disabled={autoFixingId === item.id}
                          className="text-xs font-bold bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 border border-amber-500/30 px-2.5 py-1.5 rounded-xl transition-all flex items-center gap-1 min-h-[32px] disabled:opacity-50"
                          title="TMDb orqali bo'sh maydonlarni avto-to'ldirish"
                        >
                          {autoFixingId === item.id ? (
                            <span className="w-3.5 h-3.5 border-2 border-amber-400 border-t-transparent rounded-full animate-spin"></span>
                          ) : (
                            <span className="material-symbols-outlined text-[15px]">auto_fix_high</span>
                          )}
                          <span>Avto-to'ldirish</span>
                        </button>

                        {/* Quick Edit */}
                        <button
                          onClick={() => handleOpenEdit(item)}
                          className="text-xs bg-white/5 hover:bg-white/10 text-text-primary border border-white/10 px-2.5 py-1.5 rounded-xl transition-colors min-h-[32px] flex items-center gap-1"
                          title="Tahrirlash"
                        >
                          <span className="material-symbols-outlined text-[15px]">edit</span>
                          <span>Tahrirlash</span>
                        </button>

                        {/* Video upload / navigate */}
                        {item.content_type === "movie" ? (
                          <button
                            onClick={() => {
                              setVideoMovieId(item.id);
                              setVideoModalOpen(true);
                            }}
                            className="text-xs bg-tertiary-container/20 hover:bg-tertiary-container/30 text-tertiary border border-tertiary-container/30 px-2.5 py-1.5 rounded-xl transition-colors min-h-[32px] flex items-center gap-1"
                            title="Video yuklash"
                          >
                            <span className="material-symbols-outlined text-[15px]">upload</span>
                            <span>Video</span>
                          </button>
                        ) : (
                          <Link
                            href={`/series/${item.id}`}
                            className="text-xs bg-tertiary-container/20 hover:bg-tertiary-container/30 text-tertiary border border-tertiary-container/30 px-2.5 py-1.5 rounded-xl transition-colors min-h-[32px] inline-flex items-center gap-1"
                            title="Serial qismlarini boshqarish"
                          >
                            <span className="material-symbols-outlined text-[15px]">playlist_play</span>
                            <span>Qismlar</span>
                          </Link>
                        )}

                        {/* Delete */}
                        <button
                          onClick={() => setDeletingItem(item)}
                          className="text-xs bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/20 p-1.5 rounded-xl transition-colors min-h-[32px] flex items-center justify-center"
                          title="O'chirish"
                        >
                          <span className="material-symbols-outlined text-[16px]">delete</span>
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Load More Button */}
        {items.length < total && (
          <div className="p-4 border-t border-white/5 bg-surface-container-lowest/50 text-center">
            <button
              onClick={() => loadItems(false)}
              disabled={loadingMore}
              className="bg-white/5 hover:bg-white/10 text-text-primary px-6 py-2.5 rounded-xl border border-white/10 text-xs sm:text-sm font-medium transition-all disabled:opacity-50 inline-flex items-center gap-2"
            >
              {loadingMore ? (
                <>
                  <span className="w-3.5 h-3.5 border-2 border-primary-container border-t-transparent rounded-full animate-spin"></span>
                  <span>Yuklanmoqda...</span>
                </>
              ) : (
                <>
                  <span>Yana yuklash ({total - items.length} ta qoldi)</span>
                  <span className="material-symbols-outlined text-sm">expand_more</span>
                </>
              )}
            </button>
          </div>
        )}
      </div>

      {/* Quick Edit Modal */}
      {editingItem && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-surface-container-lowest border border-white/10 rounded-2xl max-w-2xl w-full p-5 sm:p-6 shadow-2xl space-y-4 my-8">
            <div className="flex items-center justify-between border-b border-white/10 pb-3">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-primary-container">edit</span>
                <h3 className="font-bold text-lg text-text-primary">
                  {editingItem.content_type === "movie" ? "Kinoni" : "Serialni"} tahrirlash
                </h3>
              </div>
              <button
                onClick={() => setEditingItem(null)}
                className="text-text-secondary hover:text-white text-lg p-1"
              >
                ✕
              </button>
            </div>

            <div className="space-y-4 max-h-[70vh] overflow-y-auto custom-scrollbar pr-1">
              {/* Title & Original Title */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-text-secondary mb-1">
                    Sarlavha (Nomi) *
                  </label>
                  <input
                    type="text"
                    value={editForm.title}
                    onChange={(e) => setEditForm({ ...editForm, title: e.target.value })}
                    className="w-full bg-surface-container-high border border-white/10 rounded-xl px-3 py-2 text-sm text-text-primary focus:border-primary-container focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-text-secondary mb-1">
                    Asl nomi (Original title)
                  </label>
                  <input
                    type="text"
                    value={editForm.original_title}
                    onChange={(e) => setEditForm({ ...editForm, original_title: e.target.value })}
                    className="w-full bg-surface-container-high border border-white/10 rounded-xl px-3 py-2 text-sm text-text-primary focus:border-primary-container focus:outline-none"
                  />
                </div>
              </div>

              {/* Description */}
              <div>
                <label className="block text-xs font-semibold text-text-secondary mb-1">
                  Tasnif (Tavsif)
                </label>
                <textarea
                  rows={4}
                  value={editForm.description}
                  onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                  placeholder="Kino yoki serial haqida qisqacha ma'lumot..."
                  className="w-full bg-surface-container-high border border-white/10 rounded-xl p-3 text-sm text-text-primary focus:border-primary-container focus:outline-none"
                />
              </div>

              {/* Poster URL with live preview */}
              <div>
                <label className="block text-xs font-semibold text-text-secondary mb-1">
                  Poster URL (Rasm havolasi)
                </label>
                <div className="flex gap-3 items-center">
                  <input
                    type="text"
                    value={editForm.poster_url}
                    onChange={(e) => setEditForm({ ...editForm, poster_url: e.target.value })}
                    placeholder="https://image.tmdb.org/t/p/w500/..."
                    className="w-full bg-surface-container-high border border-white/10 rounded-xl px-3 py-2 text-sm text-text-primary focus:border-primary-container focus:outline-none font-mono text-xs"
                  />
                  {editForm.poster_url && (
                    <div className="w-10 h-14 rounded-lg overflow-hidden border border-white/10 shrink-0 bg-surface-container">
                      <img
                        src={editForm.poster_url}
                        alt="Preview"
                        className="w-full h-full object-cover"
                        onError={(e) => {
                          (e.target as HTMLElement).style.display = "none";
                        }}
                      />
                    </div>
                  )}
                </div>
              </div>

              {/* Trailer URL & TMDb ID */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-text-secondary mb-1">
                    Treyler URL (YouTube)
                  </label>
                  <input
                    type="text"
                    value={editForm.trailer_url}
                    onChange={(e) => setEditForm({ ...editForm, trailer_url: e.target.value })}
                    placeholder="https://www.youtube.com/watch?v=..."
                    className="w-full bg-surface-container-high border border-white/10 rounded-xl px-3 py-2 text-sm text-text-primary focus:border-primary-container focus:outline-none font-mono text-xs"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-text-secondary mb-1">
                    TMDb ID
                  </label>
                  <input
                    type="number"
                    value={editForm.tmdb_id || ""}
                    onChange={(e) => setEditForm({ ...editForm, tmdb_id: Number(e.target.value) })}
                    placeholder="Masalan: 550"
                    className="w-full bg-surface-container-high border border-white/10 rounded-xl px-3 py-2 text-sm text-text-primary focus:border-primary-container focus:outline-none"
                  />
                </div>
              </div>

              {/* Genres & Year & IMDb */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {editingItem.content_type === "movie" && (
                  <div>
                    <label className="block text-xs font-semibold text-text-secondary mb-1">
                      Janrlar
                    </label>
                    <input
                      type="text"
                      value={editForm.genres}
                      onChange={(e) => setEditForm({ ...editForm, genres: e.target.value })}
                      placeholder="Jangari, Komediya..."
                      className="w-full bg-surface-container-high border border-white/10 rounded-xl px-3 py-2 text-sm text-text-primary focus:border-primary-container focus:outline-none"
                    />
                  </div>
                )}
                <div>
                  <label className="block text-xs font-semibold text-text-secondary mb-1">
                    Chiqqan yili
                  </label>
                  <input
                    type="number"
                    value={editForm.release_year || ""}
                    onChange={(e) => setEditForm({ ...editForm, release_year: Number(e.target.value) })}
                    className="w-full bg-surface-container-high border border-white/10 rounded-xl px-3 py-2 text-sm text-text-primary focus:border-primary-container focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-text-secondary mb-1">
                    IMDb Reytingi (0-10)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    max="10"
                    value={editForm.imdb_rating || ""}
                    onChange={(e) => setEditForm({ ...editForm, imdb_rating: Number(e.target.value) })}
                    className="w-full bg-surface-container-high border border-white/10 rounded-xl px-3 py-2 text-sm text-text-primary focus:border-primary-container focus:outline-none"
                  />
                </div>
              </div>

              {/* Categories Checkboxes */}
              <div>
                <label className="block text-xs font-semibold text-text-secondary mb-1">
                  Kategoriyalar
                </label>
                <div className="flex flex-wrap gap-2 max-h-36 overflow-y-auto custom-scrollbar p-2 bg-surface-container-high rounded-xl border border-white/5">
                  {categories.map((c) => {
                    const isChecked = editForm.category_ids.includes(c.id);
                    return (
                      <label
                        key={c.id}
                        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs cursor-pointer transition-colors ${
                          isChecked
                            ? "bg-primary-container/20 text-white border-primary-container/40 font-bold"
                            : "bg-white/5 text-text-secondary border-white/10 hover:text-white"
                        }`}
                      >
                        <input
                          type="checkbox"
                          checked={isChecked}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setEditForm({ ...editForm, category_ids: [...editForm.category_ids, c.id] });
                            } else {
                              setEditForm({
                                ...editForm,
                                category_ids: editForm.category_ids.filter((id) => id !== c.id),
                              });
                            }
                          }}
                          className="hidden"
                        />
                        <span>{isChecked ? "✓" : "+"}</span>
                        <span>{c.name}</span>
                      </label>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Modal Actions */}
            <div className="flex justify-end gap-3 pt-3 border-t border-white/10">
              <button
                type="button"
                onClick={() => setEditingItem(null)}
                className="px-4 py-2 rounded-xl bg-white/5 hover:bg-white/10 text-text-secondary hover:text-white text-xs sm:text-sm font-medium transition-colors"
              >
                Bekor qilish
              </button>
              <button
                type="button"
                onClick={handleSaveEdit}
                disabled={savingEdit || !editForm.title.trim()}
                className="px-5 py-2 rounded-xl bg-primary-container hover:bg-primary-container/90 text-white text-xs sm:text-sm font-semibold transition-all disabled:opacity-50 flex items-center gap-2"
              >
                {savingEdit ? (
                  <>
                    <span className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                    <span>Saqlanmoqda...</span>
                  </>
                ) : (
                  <span>Saqlash</span>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deletingItem && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-surface-container-lowest border border-white/10 rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center gap-3 text-red-400">
              <span className="material-symbols-outlined text-3xl">warning</span>
              <h3 className="font-bold text-lg text-text-primary">O'chirishni tasdiqlang</h3>
            </div>
            <p className="text-sm text-text-secondary">
              Haqiqatan ham <strong className="text-text-primary">"{deletingItem.title}"</strong> ni butunlay o'chirib tashlamoqchimisiz? Bu amalni ortga qaytarib bo'lmaydi.
            </p>
            <div className="flex justify-end gap-3 pt-2">
              <button
                onClick={() => setDeletingItem(null)}
                disabled={isDeleting}
                className="px-4 py-2 rounded-xl bg-white/5 hover:bg-white/10 text-text-secondary text-sm font-medium transition-colors"
              >
                Bekor qilish
              </button>
              <button
                onClick={handleDeleteItem}
                disabled={isDeleting}
                className="px-4 py-2 rounded-xl bg-red-600 hover:bg-red-700 text-white text-sm font-bold transition-colors disabled:opacity-50 flex items-center gap-2"
              >
                {isDeleting ? (
                  <>
                    <span className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                    <span>O'chirilmoqda...</span>
                  </>
                ) : (
                  <span>Ha, o'chirish</span>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Video Upload Modal (for Movies) */}
      {videoMovieId && (
        <VideoUploadModal
          isOpen={videoModalOpen}
          onClose={() => {
            setVideoModalOpen(false);
            setVideoMovieId(null);
          }}
          entityName="Kino"
          entityId={videoMovieId}
          uploadEndpoint={`/movies/${videoMovieId}/upload-video`}
          linkEndpoint={`/movies/${videoMovieId}/link-video`}
          onSuccess={() => {
            showToast("Video muvaffaqiyatli yuklandi!", "success");
            setVideoModalOpen(false);
            setVideoMovieId(null);
            loadStats();
            loadItems(true);
          }}
        />
      )}
    </div>
  );
}
