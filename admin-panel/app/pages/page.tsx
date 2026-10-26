"use client";

import { useEffect, useState, useMemo } from "react";
import { fetchApi } from "@/lib/api";

type PageItem = {
  id: number;
  title: string;
  slug: string;
  is_active: boolean;
  movies_count?: number;
  series_count?: number;
  created_at?: string;
  updated_at?: string;
};

type ContentItem = {
  id: number;
  title: string;
  code?: number | string | null;
  year?: number | null;
  poster_url?: string | null;
  genres?: string | null;
  publish_status?: string | null;
};

export default function PagesPage() {
  const [pages, setPages] = useState<PageItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Search & Filter
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<"all" | "active" | "inactive">("all");

  // Create / Edit Form State
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState({ title: "", slug: "", is_active: true });
  const [submitting, setSubmitting] = useState(false);

  // Content Management Modal State
  const [contentModalPage, setContentModalPage] = useState<PageItem | null>(null);
  const [contentLoading, setContentLoading] = useState(false);
  const [contentTab, setContentTab] = useState<"movies" | "series">("movies");
  const [attachedMovies, setAttachedMovies] = useState<ContentItem[]>([]);
  const [attachedSeries, setAttachedSeries] = useState<ContentItem[]>([]);
  const [contentSearch, setContentSearch] = useState("");

  // Attach Content Form State inside Modal
  const [attachType, setAttachType] = useState<"movie" | "series">("movie");
  const [attachIdOrCode, setAttachIdOrCode] = useState("");
  const [isAttaching, setIsAttaching] = useState(false);
  const [modalMsg, setModalMsg] = useState<{ text: string; isError?: boolean } | null>(null);

  useEffect(() => {
    loadPages();
  }, []);

  const loadPages = async () => {
    try {
      setLoading(true);
      const data = await fetchApi("/pages?limit=100");
      if (data && data.items) {
        setPages(data.items);
      } else if (Array.isArray(data)) {
        setPages(data);
      } else {
        setPages([]);
      }
      setErrorMsg(null);
    } catch (e: any) {
      console.error("Xato:", e);
      setErrorMsg(e.message || "Sahifalarni yuklashda xatolik yuz berdi");
    } finally {
      setLoading(false);
    }
  };

  // Auto-slug generator from title
  const handleTitleChange = (val: string) => {
    const slugified = val
      .toLowerCase()
      .trim()
      .replace(/[^a-z0-9\s-]/g, "")
      .replace(/\s+/g, "-");
    setForm((prev) => ({
      ...prev,
      title: val,
      slug: editingId ? prev.slug : slugified,
    }));
  };

  const handleOpenCreate = () => {
    setEditingId(null);
    setForm({ title: "", slug: "", is_active: true });
    setIsFormOpen(true);
  };

  const handleOpenEdit = (p: PageItem) => {
    setEditingId(p.id);
    setForm({ title: p.title, slug: p.slug, is_active: p.is_active });
    setIsFormOpen(true);
  };

  const handleToggleStatus = async (p: PageItem) => {
    try {
      const updated = await fetchApi(`/pages/${p.id}`, {
        method: "PUT",
        body: JSON.stringify({ is_active: !p.is_active }),
      });
      setPages((prev) =>
        prev.map((item) =>
          item.id === p.id ? { ...item, is_active: updated.is_active } : item
        )
      );
    } catch (e: any) {
      alert("Holatni o'zgartirishda xato: " + e.message);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setErrorMsg(null);
    try {
      if (editingId) {
        await fetchApi(`/pages/${editingId}`, {
          method: "PUT",
          body: JSON.stringify(form),
        });
        setSuccessMsg("Sahifa muvaffaqiyatli yangilandi!");
      } else {
        await fetchApi("/pages", {
          method: "POST",
          body: JSON.stringify(form),
        });
        setSuccessMsg("Yangi sahifa muvaffaqiyatli yaratildi!");
      }
      setIsFormOpen(false);
      setEditingId(null);
      setForm({ title: "", slug: "", is_active: true });
      loadPages();
    } catch (e: any) {
      setErrorMsg("Saqlashda xato: " + e.message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id: number, title: string) => {
    if (!confirm(`Haqiqatan ham "${title}" sahifasini o'chirmoqchimisiz?`)) return;
    try {
      await fetchApi(`/pages/${id}`, { method: "DELETE" });
      setPages((prev) => prev.filter((p) => p.id !== id));
      setSuccessMsg(`"${title}" sahifasi o'chirildi`);
    } catch (e: any) {
      alert("O'chirishda xato: " + e.message);
    }
  };

  // Open Content Management Modal
  const openContentManager = async (page: PageItem) => {
    setContentModalPage(page);
    setContentLoading(true);
    setContentSearch("");
    setModalMsg(null);
    setAttachIdOrCode("");
    try {
      const res = await fetchApi(`/pages/${page.id}/content`);
      setAttachedMovies(res.movies || []);
      setAttachedSeries(res.series || []);
      if ((res.series || []).length > 0 && (res.movies || []).length === 0) {
        setContentTab("series");
      } else {
        setContentTab("movies");
      }
    } catch (e: any) {
      console.error(e);
      setModalMsg({ text: "Kontentni yuklashda xato: " + e.message, isError: true });
    } finally {
      setContentLoading(false);
    }
  };

  // Attach item (movie or series)
  const handleAttachContent = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!contentModalPage || !attachIdOrCode.trim()) return;

    setIsAttaching(true);
    setModalMsg(null);

    const val = attachIdOrCode.trim();
    let numericId: number | null = parseInt(val);

    // If user provided a code or search term, try lookup
    if (isNaN(numericId) || numericId <= 0) {
      try {
        const searchEndpoint = attachType === "movie" ? "/movies/search?q=" : "/series?search=";
        const lookupRes = await fetchApi(`${searchEndpoint}${encodeURIComponent(val)}&limit=1`);
        const item = lookupRes.items?.[0] || lookupRes[0];
        if (item && item.id) {
          numericId = item.id;
        } else {
          setModalMsg({ text: `Bunday ${attachType === "movie" ? "kino" : "serial"} topilmadi`, isError: true });
          setIsAttaching(false);
          return;
        }
      } catch (err: any) {
        setModalMsg({ text: "Qidirishda xato: " + err.message, isError: true });
        setIsAttaching(false);
        return;
      }
    }

    try {
      const payload = {
        movie_ids: attachType === "movie" ? [numericId] : [],
        series_ids: attachType === "series" ? [numericId] : [],
      };
      await fetchApi(`/pages/${contentModalPage.id}/attach`, {
        method: "POST",
        body: JSON.stringify(payload),
      });

      // Refresh page content
      const res = await fetchApi(`/pages/${contentModalPage.id}/content`);
      setAttachedMovies(res.movies || []);
      setAttachedSeries(res.series || []);
      setModalMsg({ text: `${attachType === "movie" ? "Kino" : "Serial"} muvaffaqiyatli biriktirildi!` });
      setAttachIdOrCode("");

      // Update parent list counts
      setPages((prev) =>
        prev.map((p) =>
          p.id === contentModalPage.id
            ? {
                ...p,
                movies_count: (res.movies || []).length,
                series_count: (res.series || []).length,
              }
            : p
        )
      );
    } catch (e: any) {
      setModalMsg({ text: "Biriktirishda xato: " + e.message, isError: true });
    } finally {
      setIsAttaching(false);
    }
  };

  // Detach item
  const handleDetachContent = async (itemId: number, type: "movie" | "series") => {
    if (!contentModalPage) return;
    try {
      const payload = {
        movie_ids: type === "movie" ? [itemId] : [],
        series_ids: type === "series" ? [itemId] : [],
      };
      await fetchApi(`/pages/${contentModalPage.id}/detach`, {
        method: "POST",
        body: JSON.stringify(payload),
      });

      if (type === "movie") {
        setAttachedMovies((prev) => prev.filter((m) => m.id !== itemId));
      } else {
        setAttachedSeries((prev) => prev.filter((s) => s.id !== itemId));
      }

      setPages((prev) =>
        prev.map((p) => {
          if (p.id !== contentModalPage.id) return p;
          return {
            ...p,
            movies_count: type === "movie" ? Math.max(0, (p.movies_count || 1) - 1) : p.movies_count,
            series_count: type === "series" ? Math.max(0, (p.series_count || 1) - 1) : p.series_count,
          };
        })
      );
    } catch (e: any) {
      alert("Chiqarishda xato: " + e.message);
    }
  };

  // Filtered pages calculation
  const filteredPages = useMemo(() => {
    return pages.filter((p) => {
      const matchesSearch =
        p.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.slug.toLowerCase().includes(searchQuery.toLowerCase()) ||
        String(p.id) === searchQuery.trim();
      const matchesStatus =
        statusFilter === "all"
          ? true
          : statusFilter === "active"
          ? p.is_active
          : !p.is_active;
      return matchesSearch && matchesStatus;
    });
  }, [pages, searchQuery, statusFilter]);

  // Overall statistics
  const stats = useMemo(() => {
    const total = pages.length;
    const active = pages.filter((p) => p.is_active).length;
    const totalMovies = pages.reduce((acc, p) => acc + (p.movies_count || 0), 0);
    const totalSeries = pages.reduce((acc, p) => acc + (p.series_count || 0), 0);
    return { total, active, totalMovies, totalSeries };
  }, [pages]);

  // Filtered modal items
  const filteredModalMovies = useMemo(() => {
    if (!contentSearch.trim()) return attachedMovies;
    const q = contentSearch.toLowerCase();
    return attachedMovies.filter(
      (m) =>
        m.title.toLowerCase().includes(q) ||
        String(m.id).includes(q) ||
        String(m.code || "").includes(q)
    );
  }, [attachedMovies, contentSearch]);

  const filteredModalSeries = useMemo(() => {
    if (!contentSearch.trim()) return attachedSeries;
    const q = contentSearch.toLowerCase();
    return attachedSeries.filter(
      (s) =>
        s.title.toLowerCase().includes(q) ||
        String(s.id).includes(q) ||
        String(s.code || "").includes(q)
    );
  }, [attachedSeries, contentSearch]);

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-white/10">
        <div>
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-primary-container text-2xl">
              layers
            </span>
            <h1 className="text-2xl sm:text-3xl font-bold text-text-primary tracking-tight">
              Bo'limlar va Sahifalar
            </h1>
          </div>
          <p className="text-xs sm:text-sm text-text-secondary mt-1">
            Saytdagi barcha tematik sahifalar, bo'limlar va ularga biriktirilgan kinolar/seriallarni to'liq boshqarish
          </p>
        </div>

        <button
          onClick={handleOpenCreate}
          className="flex items-center justify-center gap-2 bg-primary-container hover:brightness-110 active:scale-95 text-white px-5 py-2.5 rounded-xl font-medium text-sm transition-all shadow-lg shadow-red-900/20"
        >
          <span className="material-symbols-outlined text-lg">add</span>
          <span>Yangi Sahifa Qo'shish</span>
        </button>
      </div>

      {/* Global Alerts */}
      {errorMsg && (
        <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400 text-sm flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined">error</span>
            <span>{errorMsg}</span>
          </div>
          <button onClick={() => setErrorMsg(null)} className="text-white/60 hover:text-white">
            <span className="material-symbols-outlined text-sm">close</span>
          </button>
        </div>
      )}

      {successMsg && (
        <div className="p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-emerald-400 text-sm flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined">check_circle</span>
            <span>{successMsg}</span>
          </div>
          <button onClick={() => setSuccessMsg(null)} className="text-white/60 hover:text-white">
            <span className="material-symbols-outlined text-sm">close</span>
          </button>
        </div>
      )}

      {/* Stats Cards Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        <div className="bg-surface-container-lowest/80 border border-white/10 rounded-2xl p-4 flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-primary-container/20 border border-primary-container/30 flex items-center justify-center text-primary-container">
            <span className="material-symbols-outlined text-xl">layers</span>
          </div>
          <div>
            <div className="text-xs text-text-secondary">Jami sahifalar</div>
            <div className="text-xl font-bold text-white">{stats.total}</div>
          </div>
        </div>

        <div className="bg-surface-container-lowest/80 border border-white/10 rounded-2xl p-4 flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
            <span className="material-symbols-outlined text-xl">check_circle</span>
          </div>
          <div>
            <div className="text-xs text-text-secondary">Faol sahifalar</div>
            <div className="text-xl font-bold text-emerald-400">{stats.active}</div>
          </div>
        </div>

        <div className="bg-surface-container-lowest/80 border border-white/10 rounded-2xl p-4 flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-blue-500/20 border border-blue-500/30 flex items-center justify-center text-blue-400">
            <span className="material-symbols-outlined text-xl">movie</span>
          </div>
          <div>
            <div className="text-xs text-text-secondary">Biriktirilgan kinolar</div>
            <div className="text-xl font-bold text-blue-400">{stats.totalMovies}</div>
          </div>
        </div>

        <div className="bg-surface-container-lowest/80 border border-white/10 rounded-2xl p-4 flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-purple-500/20 border border-purple-500/30 flex items-center justify-center text-purple-400">
            <span className="material-symbols-outlined text-xl">tv</span>
          </div>
          <div>
            <div className="text-xs text-text-secondary">Biriktirilgan seriallar</div>
            <div className="text-xl font-bold text-purple-400">{stats.totalSeries}</div>
          </div>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="bg-surface-container-lowest/60 border border-white/10 rounded-2xl p-3 sm:p-4 flex flex-col md:flex-row md:items-center justify-between gap-3">
        <div className="relative flex-1">
          <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-text-secondary text-lg">
            search
          </span>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Sahifa nomi yoki slug bo'yicha qidirish..."
            className="w-full bg-black/40 border border-white/10 rounded-xl pl-9 pr-4 py-2.5 text-sm text-text-primary focus:outline-none focus:border-primary-container"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery("")}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-text-secondary hover:text-white"
            >
              <span className="material-symbols-outlined text-sm">close</span>
            </button>
          )}
        </div>

        <div className="flex items-center gap-1.5 bg-black/40 p-1 border border-white/10 rounded-xl text-xs font-medium">
          <button
            onClick={() => setStatusFilter("all")}
            className={`px-3 py-1.5 rounded-lg transition-all ${
              statusFilter === "all"
                ? "bg-primary-container text-white font-bold"
                : "text-text-secondary hover:text-white"
            }`}
          >
            Barchasi ({pages.length})
          </button>
          <button
            onClick={() => setStatusFilter("active")}
            className={`px-3 py-1.5 rounded-lg transition-all ${
              statusFilter === "active"
                ? "bg-primary-container text-white font-bold"
                : "text-text-secondary hover:text-white"
            }`}
          >
            Faol ({stats.active})
          </button>
          <button
            onClick={() => setStatusFilter("inactive")}
            className={`px-3 py-1.5 rounded-lg transition-all ${
              statusFilter === "inactive"
                ? "bg-primary-container text-white font-bold"
                : "text-text-secondary hover:text-white"
            }`}
          >
            Nofaol ({pages.length - stats.active})
          </button>
        </div>
      </div>

      {/* Pages Table */}
      <div className="bg-surface-container-lowest border border-white/10 rounded-2xl overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-white/5 border-b border-white/10 text-xs text-text-secondary uppercase">
              <tr>
                <th className="px-4 py-3.5 w-16">ID</th>
                <th className="px-4 py-3.5">Sahifa Nomi</th>
                <th className="px-4 py-3.5">Slug (URL)</th>
                <th className="px-4 py-3.5 text-center">Biriktirilgan Kontent</th>
                <th className="px-4 py-3.5 text-center">Holat</th>
                <th className="px-4 py-3.5 text-right">Amallar</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {loading ? (
                <tr>
                  <td colSpan={6} className="px-4 py-12 text-center text-text-secondary">
                    <span className="material-symbols-outlined animate-spin text-3xl mb-2 text-primary-container">
                      progress_activity
                    </span>
                    <div>Sahifalar yuklanmoqda...</div>
                  </td>
                </tr>
              ) : filteredPages.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-12 text-center text-text-secondary">
                    <span className="material-symbols-outlined text-4xl mb-2 opacity-50">
                      folder_off
                    </span>
                    <div>Hech qanday sahifa topilmadi</div>
                  </td>
                </tr>
              ) : (
                filteredPages.map((p) => (
                  <tr key={p.id} className="hover:bg-white/[0.02] transition-colors">
                    <td className="px-4 py-4 font-mono text-xs text-text-secondary">
                      #{p.id}
                    </td>

                    <td className="px-4 py-4">
                      <div className="font-semibold text-text-primary text-base flex items-center gap-2">
                        <span>{p.title}</span>
                      </div>
                    </td>

                    <td className="px-4 py-4">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs bg-white/5 text-zinc-300 px-2 py-1 rounded-md border border-white/10">
                          /{p.slug}
                        </span>
                        <a
                          href={`/catalog?page_id=${p.id}`}
                          target="_blank"
                          rel="noreferrer"
                          title="Saytda ko'rish"
                          className="text-text-secondary hover:text-white transition"
                        >
                          <span className="material-symbols-outlined text-sm">open_in_new</span>
                        </a>
                      </div>
                    </td>

                    <td className="px-4 py-4">
                      <div className="flex items-center justify-center gap-2">
                        <span className="inline-flex items-center gap-1 bg-blue-500/10 text-blue-400 border border-blue-500/20 px-2.5 py-1 rounded-lg text-xs font-medium">
                          <span className="material-symbols-outlined text-[14px]">movie</span>
                          <span>{p.movies_count || 0} kino</span>
                        </span>
                        <span className="inline-flex items-center gap-1 bg-purple-500/10 text-purple-400 border border-purple-500/20 px-2.5 py-1 rounded-lg text-xs font-medium">
                          <span className="material-symbols-outlined text-[14px]">tv</span>
                          <span>{p.series_count || 0} serial</span>
                        </span>
                      </div>
                    </td>

                    <td className="px-4 py-4 text-center">
                      <button
                        onClick={() => handleToggleStatus(p)}
                        className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium border transition-all cursor-pointer ${
                          p.is_active
                            ? "bg-emerald-500/15 border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/25"
                            : "bg-red-500/15 border-red-500/30 text-red-400 hover:bg-red-500/25"
                        }`}
                      >
                        <span
                          className={`w-1.5 h-1.5 rounded-full ${
                            p.is_active ? "bg-emerald-400" : "bg-red-400"
                          }`}
                        />
                        <span>{p.is_active ? "Faol" : "Nofaol"}</span>
                      </button>
                    </td>

                    <td className="px-4 py-4 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <button
                          onClick={() => openContentManager(p)}
                          className="flex items-center gap-1 bg-primary-container/20 hover:bg-primary-container text-primary-container hover:text-white border border-primary-container/40 px-3 py-1.5 rounded-xl text-xs font-medium transition-all"
                          title="Kinolar va seriallarni boshqarish"
                        >
                          <span className="material-symbols-outlined text-[15px]">settings</span>
                          <span>Kontentni boshqarish</span>
                        </button>

                        <button
                          onClick={() => handleOpenEdit(p)}
                          className="p-1.5 bg-white/5 hover:bg-white/10 text-text-secondary hover:text-white rounded-lg border border-white/10 transition"
                          title="Tahrirlash"
                        >
                          <span className="material-symbols-outlined text-base">edit</span>
                        </button>

                        <button
                          onClick={() => handleDelete(p.id, p.title)}
                          className="p-1.5 bg-red-500/10 hover:bg-red-500/20 text-red-400 rounded-lg border border-red-500/20 transition"
                          title="O'chirish"
                        >
                          <span className="material-symbols-outlined text-base">delete</span>
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* CREATE / EDIT MODAL */}
      {isFormOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
          <div className="bg-surface-container-low border border-white/15 rounded-2xl p-6 max-w-lg w-full shadow-2xl relative">
            <div className="flex items-center justify-between pb-4 border-b border-white/10 mb-5">
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <span className="material-symbols-outlined text-primary-container">
                  {editingId ? "edit_note" : "add_circle"}
                </span>
                <span>{editingId ? "Sahifani tahrirlash" : "Yangi Sahifa Qo'shish"}</span>
              </h2>
              <button
                onClick={() => setIsFormOpen(false)}
                className="text-text-secondary hover:text-white transition"
              >
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-text-secondary mb-1">
                  Sahifa Sarlavhasi (Nomi) *
                </label>
                <input
                  required
                  type="text"
                  value={form.title}
                  onChange={(e) => handleTitleChange(e.target.value)}
                  placeholder="Masalan: Turk Kinolari"
                  className="w-full bg-black/50 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-text-primary focus:outline-none focus:border-primary-container"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-text-secondary mb-1">
                  Slug (URL identifikatori) *
                </label>
                <input
                  required
                  type="text"
                  value={form.slug}
                  onChange={(e) => setForm({ ...form, slug: e.target.value })}
                  placeholder="turk-kinolari"
                  className="w-full bg-black/50 border border-white/10 rounded-xl px-4 py-2.5 text-sm font-mono text-text-primary focus:outline-none focus:border-primary-container"
                />
                <p className="text-[11px] text-text-secondary mt-1">
                  Havola formati: <span className="text-zinc-400">/catalog?page_id=... yoki /{form.slug || "slug"}</span>
                </p>
              </div>

              <div className="pt-2">
                <label className="flex items-center gap-3 bg-black/30 border border-white/10 p-3 rounded-xl cursor-pointer">
                  <input
                    type="checkbox"
                    checked={form.is_active}
                    onChange={(e) => setForm({ ...form, is_active: e.target.checked })}
                    className="w-4 h-4 text-primary-container rounded border-white/20 bg-black/50 focus:ring-primary-container"
                  />
                  <div>
                    <div className="text-sm font-medium text-white">Faol sahifa</div>
                    <div className="text-xs text-text-secondary">
                      Sayt va menyularda ushbu sahifa ko'rsatiladi
                    </div>
                  </div>
                </label>
              </div>

              <div className="flex items-center justify-end gap-3 pt-4 border-t border-white/10">
                <button
                  type="button"
                  onClick={() => setIsFormOpen(false)}
                  className="px-4 py-2 bg-white/5 hover:bg-white/10 text-text-secondary hover:text-white rounded-xl text-sm font-medium transition"
                >
                  Bekor qilish
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-5 py-2 bg-primary-container hover:brightness-110 active:scale-95 text-white rounded-xl text-sm font-medium transition flex items-center gap-1.5"
                >
                  {submitting && (
                    <span className="material-symbols-outlined animate-spin text-sm">
                      progress_activity
                    </span>
                  )}
                  <span>{editingId ? "Saqlash" : "Yaratish"}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* CONTENT MANAGEMENT MODAL */}
      {contentModalPage && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-black/85 backdrop-blur-md animate-fade-in">
          <div className="bg-surface-container-low border border-white/15 rounded-2xl max-w-4xl w-full h-[90vh] flex flex-col shadow-2xl overflow-hidden">
            {/* Modal Header */}
            <div className="px-6 py-4 border-b border-white/10 flex items-center justify-between bg-black/40">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-primary-container/20 border border-primary-container/40 flex items-center justify-center text-primary-container">
                  <span className="material-symbols-outlined text-xl">tune</span>
                </div>
                <div>
                  <h2 className="text-lg font-bold text-white flex items-center gap-2">
                    <span>{contentModalPage.title}</span>
                    <span className="text-xs font-mono px-2 py-0.5 rounded bg-white/5 text-zinc-400 border border-white/10">
                      /{contentModalPage.slug}
                    </span>
                  </h2>
                  <p className="text-xs text-text-secondary">
                    Sahifaga tegishli kinolar va seriallarni biriktirish yoki olib tashlash
                  </p>
                </div>
              </div>

              <button
                onClick={() => setContentModalPage(null)}
                className="text-text-secondary hover:text-white p-2 rounded-lg hover:bg-white/5 transition"
              >
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>

            {/* Modal Quick Attach Form */}
            <div className="p-4 sm:p-6 bg-surface-container-lowest/80 border-b border-white/10">
              <form onSubmit={handleAttachContent} className="flex flex-col sm:flex-row items-stretch sm:items-end gap-3">
                <div className="w-full sm:w-36">
                  <label className="block text-[11px] font-semibold text-text-secondary uppercase mb-1">
                    Kontent Turi
                  </label>
                  <select
                    value={attachType}
                    onChange={(e) => setAttachType(e.target.value as any)}
                    className="w-full bg-black/60 border border-white/10 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-primary-container"
                  >
                    <option value="movie">🎬 Kino</option>
                    <option value="series">📺 Serial</option>
                  </select>
                </div>

                <div className="flex-1">
                  <label className="block text-[11px] font-semibold text-text-secondary uppercase mb-1">
                    Kino / Serial ID, Kodi yoki Nomi
                  </label>
                  <input
                    type="text"
                    value={attachIdOrCode}
                    onChange={(e) => setAttachIdOrCode(e.target.value)}
                    placeholder="Masalan: 831 yoki Qashqirlar makoni"
                    className="w-full bg-black/60 border border-white/10 rounded-xl px-4 py-2 text-sm text-white focus:outline-none focus:border-primary-container"
                  />
                </div>

                <button
                  type="submit"
                  disabled={isAttaching || !attachIdOrCode.trim()}
                  className="bg-primary-container hover:brightness-110 active:scale-95 disabled:opacity-50 text-white px-5 py-2 rounded-xl text-sm font-medium transition flex items-center justify-center gap-1.5 h-[38px]"
                >
                  {isAttaching ? (
                    <span className="material-symbols-outlined animate-spin text-sm">
                      progress_activity
                    </span>
                  ) : (
                    <span className="material-symbols-outlined text-base">add_link</span>
                  )}
                  <span>Biriktirish</span>
                </button>
              </form>

              {modalMsg && (
                <div
                  className={`mt-3 p-3 rounded-xl text-xs flex items-center justify-between ${
                    modalMsg.isError
                      ? "bg-red-500/10 border border-red-500/30 text-red-400"
                      : "bg-emerald-500/10 border border-emerald-500/30 text-emerald-400"
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <span className="material-symbols-outlined text-sm">
                      {modalMsg.isError ? "error" : "check_circle"}
                    </span>
                    <span>{modalMsg.text}</span>
                  </div>
                  <button onClick={() => setModalMsg(null)} className="opacity-70 hover:opacity-100">
                    <span className="material-symbols-outlined text-xs">close</span>
                  </button>
                </div>
              )}
            </div>

            {/* Modal Tabs & Search */}
            <div className="px-6 py-3 border-b border-white/10 flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-black/20">
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setContentTab("movies")}
                  className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
                    contentTab === "movies"
                      ? "bg-primary-container text-white shadow"
                      : "bg-white/5 text-text-secondary hover:text-white"
                  }`}
                >
                  <span className="material-symbols-outlined text-[15px]">movie</span>
                  <span>Biriktirilgan Kinolar ({attachedMovies.length})</span>
                </button>

                <button
                  onClick={() => setContentTab("series")}
                  className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
                    contentTab === "series"
                      ? "bg-primary-container text-white shadow"
                      : "bg-white/5 text-text-secondary hover:text-white"
                  }`}
                >
                  <span className="material-symbols-outlined text-[15px]">tv</span>
                  <span>Biriktirilgan Seriallar ({attachedSeries.length})</span>
                </button>
              </div>

              <div className="relative w-full sm:w-64">
                <span className="material-symbols-outlined absolute left-2.5 top-1/2 -translate-y-1/2 text-text-secondary text-base">
                  search
                </span>
                <input
                  type="text"
                  value={contentSearch}
                  onChange={(e) => setContentSearch(e.target.value)}
                  placeholder="Ro'yxatdan qidirish..."
                  className="w-full bg-black/40 border border-white/10 rounded-xl pl-8 pr-3 py-1.5 text-xs text-white focus:outline-none focus:border-primary-container"
                />
              </div>
            </div>

            {/* Attached Items List Body */}
            <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-2">
              {contentLoading ? (
                <div className="py-20 text-center text-text-secondary">
                  <span className="material-symbols-outlined animate-spin text-3xl mb-2 text-primary-container">
                    progress_activity
                  </span>
                  <div>Kontent yuklanmoqda...</div>
                </div>
              ) : contentTab === "movies" ? (
                filteredModalMovies.length === 0 ? (
                  <div className="py-16 text-center text-text-secondary border border-dashed border-white/10 rounded-2xl">
                    <span className="material-symbols-outlined text-4xl mb-2 opacity-40">
                      movie
                    </span>
                    <div className="text-sm font-medium">Bu sahifada hali kinolar biriktirilmagan</div>
                    <div className="text-xs text-text-secondary mt-1">
                      Yuqoridagi forma orqali kino ID yoki kodini kiritib sahifaga qo'shishingiz mumkin
                    </div>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {filteredModalMovies.map((m) => (
                      <div
                        key={m.id}
                        className="bg-black/40 border border-white/10 rounded-xl p-3 flex items-center justify-between gap-3 hover:border-white/20 transition"
                      >
                        <div className="flex items-center gap-3 overflow-hidden">
                          {m.poster_url ? (
                            <img
                              src={m.poster_url}
                              alt={m.title}
                              className="w-12 h-16 rounded-lg object-cover flex-shrink-0 bg-white/5 border border-white/10"
                            />
                          ) : (
                            <div className="w-12 h-16 rounded-lg bg-white/5 border border-white/10 flex items-center justify-center flex-shrink-0 text-text-secondary">
                              <span className="material-symbols-outlined text-lg">movie</span>
                            </div>
                          )}
                          <div className="truncate">
                            <div className="font-semibold text-white text-sm truncate">{m.title}</div>
                            <div className="flex items-center gap-2 text-xs text-text-secondary mt-1">
                              <span className="font-mono bg-white/5 px-1.5 py-0.5 rounded text-[11px] text-zinc-300">
                                ID: {m.id}
                              </span>
                              {m.code && (
                                <span className="font-mono bg-primary-container/20 text-primary-container px-1.5 py-0.5 rounded text-[11px]">
                                  #{m.code}
                                </span>
                              )}
                              {m.year && <span>{m.year}</span>}
                            </div>
                            {m.genres && (
                              <div className="text-[11px] text-text-secondary truncate mt-0.5 opacity-80">
                                {m.genres}
                              </div>
                            )}
                          </div>
                        </div>

                        <button
                          onClick={() => handleDetachContent(m.id, "movie")}
                          className="p-2 bg-red-500/10 hover:bg-red-500/20 text-red-400 rounded-lg border border-red-500/20 transition flex-shrink-0"
                          title="Sahifadan chiqarish"
                        >
                          <span className="material-symbols-outlined text-base">link_off</span>
                        </button>
                      </div>
                    ))}
                  </div>
                )
              ) : filteredModalSeries.length === 0 ? (
                <div className="py-16 text-center text-text-secondary border border-dashed border-white/10 rounded-2xl">
                  <span className="material-symbols-outlined text-4xl mb-2 opacity-40">tv</span>
                  <div className="text-sm font-medium">Bu sahifada hali seriallar biriktirilmagan</div>
                  <div className="text-xs text-text-secondary mt-1">
                    Yuqoridagi forma orqali serial ID yoki kodini kiritib sahifaga qo'shishingiz mumkin
                  </div>
                </div>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {filteredModalSeries.map((s) => (
                    <div
                      key={s.id}
                      className="bg-black/40 border border-white/10 rounded-xl p-3 flex items-center justify-between gap-3 hover:border-white/20 transition"
                    >
                      <div className="flex items-center gap-3 overflow-hidden">
                        {s.poster_url ? (
                          <img
                            src={s.poster_url}
                            alt={s.title}
                            className="w-12 h-16 rounded-lg object-cover flex-shrink-0 bg-white/5 border border-white/10"
                          />
                        ) : (
                          <div className="w-12 h-16 rounded-lg bg-white/5 border border-white/10 flex items-center justify-center flex-shrink-0 text-text-secondary">
                            <span className="material-symbols-outlined text-lg">tv</span>
                          </div>
                        )}
                        <div className="truncate">
                          <div className="font-semibold text-white text-sm truncate">{s.title}</div>
                          <div className="flex items-center gap-2 text-xs text-text-secondary mt-1">
                            <span className="font-mono bg-white/5 px-1.5 py-0.5 rounded text-[11px] text-zinc-300">
                              ID: {s.id}
                            </span>
                            {s.code && (
                              <span className="font-mono bg-purple-500/20 text-purple-400 px-1.5 py-0.5 rounded text-[11px]">
                                #{s.code}
                              </span>
                            )}
                            {s.year && <span>{s.year}</span>}
                          </div>
                          {s.genres && (
                            <div className="text-[11px] text-text-secondary truncate mt-0.5 opacity-80">
                              {s.genres}
                            </div>
                          )}
                        </div>
                      </div>

                      <button
                        onClick={() => handleDetachContent(s.id, "series")}
                        className="p-2 bg-red-500/10 hover:bg-red-500/20 text-red-400 rounded-lg border border-red-500/20 transition flex-shrink-0"
                        title="Sahifadan chiqarish"
                      >
                        <span className="material-symbols-outlined text-base">link_off</span>
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="px-6 py-3 border-t border-white/10 bg-black/40 flex items-center justify-between">
              <div className="text-xs text-text-secondary">
                Jami: {attachedMovies.length} ta kino, {attachedSeries.length} ta serial
              </div>
              <button
                onClick={() => setContentModalPage(null)}
                className="px-5 py-2 bg-white/10 hover:bg-white/20 text-white rounded-xl text-xs font-semibold transition"
              >
                Yopish
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
