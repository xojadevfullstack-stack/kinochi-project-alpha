"use client";

import { useEffect, useState } from "react";
import { fetchApi } from "@/lib/api";
import Link from "next/link";

type Category = { id: number; name: string };
type PageItem = { id: number; title: string };

type Series = {
  id: number;
  title: string;
  description: string | null;
  poster_url: string | null;
  trailer_url: string | null;
  imdb_rating: number | null;
  release_year: number | null;
  director: string | null;
  cast: string | null;
  created_at: string;
  categories: Category[];
  pages: PageItem[];
  source_id: number | null;
  source: Source | null;
  status: string;
};

type Source = {
  id: number;
  name: string;
  chat_id: number;
  topic_id: number | null;
  type: string;
};

export default function SeriesListPage() {
  const [seriesList, setSeriesList] = useState<Series[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [pages, setPages] = useState<PageItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState<number | null>(null);

  const [form, setForm] = useState({
    title: "",
    description: "",
    poster_url: "",
    trailer_url: "",
    imdb_rating: 0,
    release_year: 2024,
    director: "",
    cast: "",
    category_ids: [] as number[],
    page_ids: [] as number[],
    source_id: "" as number | "",
    status: "ongoing" as string,
  });
  const [sources, setSources] = useState<Source[]>([]);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([loadSeries(), loadCategories(), loadSources(), loadPages()]).then(() => setLoading(false));
  }, []);

  const loadCategories = async () => {
    try {
      const data = await fetchApi("/categories");
      setCategories(data);
    } catch (e: any) {
      console.error(e);
    }
  };

  const loadSeries = async () => {
    try {
      const data = await fetchApi("/series?limit=100");
      setSeriesList(data.items);
    } catch (e: any) {
      alert("Xato: " + e.message);
    }
  };

  const loadPages = async () => {
    try {
      const data = await fetchApi("/pages");
      if (data && data.items) {
          setPages(data.items);
      } else if (Array.isArray(data)) {
          setPages(data);
      }
    } catch (e: any) {
      console.error(e);
    }
  };

  const loadSources = async () => {
    try {
      const data = await fetchApi("/sources");
      setSources(data);
    } catch (e: any) {
      console.error(e);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    try {
      const payload = {
        ...form,
        source_id: form.source_id === "" ? null : form.source_id
      };
      if (editingId) {
        await fetchApi(`/series/${editingId}`, { method: "PUT", body: JSON.stringify(payload) });
      } else {
        await fetchApi("/series", { method: "POST", body: JSON.stringify(payload) });
      }
      handleCancel();
      loadSeries();
    } catch (e: any) {
      setErrorMsg(e.message || "Xato yuz berdi");
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Ushbu serialni o'chirasizmi? (Uning barcha mavsum va qismlari ham o'chib ketishi mumkin!)")) return;
    try {
      await fetchApi(`/series/${id}`, { method: "DELETE" });
      loadSeries();
    } catch (e: any) {
      alert("O'chirishda xato: " + e.message);
    }
  };

  const handleEdit = (s: Series) => {
    setEditingId(s.id);
    setForm({
      title: s.title,
      description: s.description || "",
      poster_url: s.poster_url || "",
      trailer_url: s.trailer_url || "",
      imdb_rating: s.imdb_rating || 0,
      release_year: s.release_year || 2024,
      director: s.director || "",
      cast: s.cast || "",
      category_ids: s.categories.map((c) => c.id),
      page_ids: s.pages ? s.pages.map((p) => p.id) : [],
      source_id: s.source_id || "",
      status: s.status || "ongoing",
    });
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handleCancel = () => {
    setEditingId(null);
    setErrorMsg(null);
    setForm({
      title: "",
      description: "",
      poster_url: "",
      trailer_url: "",
      imdb_rating: 0,
      release_year: 2024,
      director: "",
      cast: "",
      category_ids: [],
      page_ids: [],
      source_id: "",
      status: "ongoing",
    });
  };

  const handleCategoryChange = (id: number) => {
    setForm(prev => {
      const ids = prev.category_ids.includes(id) 
        ? prev.category_ids.filter(x => x !== id)
        : [...prev.category_ids, id];
      return { ...prev, category_ids: ids };
    });
  };

  const handlePageChange = (id: number) => {
    setForm(prev => {
      const ids = prev.page_ids.includes(id) 
        ? prev.page_ids.filter(x => x !== id)
        : [...prev.page_ids, id];
      return { ...prev, page_ids: ids };
    });
  };

  if (loading) return <div className="p-8 text-center text-text-secondary">Yuklanmoqda...</div>;

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-text-primary tracking-tight">Seriallar</h1>
          <p className="text-xs sm:text-sm text-text-secondary mt-1">Seriallar, mavsumlar va qismlarni boshqarish</p>
        </div>
      </div>
      
      {/* Form Card */}
      <div className="metric-card p-4 sm:p-6 rounded-2xl mb-8">
        <h2 className="text-lg sm:text-xl font-semibold mb-4 text-text-primary flex items-center gap-2">
          <span className="material-symbols-outlined text-primary-container">
            {editingId ? "edit" : "add_circle"}
          </span>
          {editingId ? "Serialni tahrirlash" : "Yangi Serial qo'shish"}
        </h2>
        
        <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-3 sm:gap-4">
          <div className="md:col-span-2">
            <label className="block text-xs sm:text-sm font-medium text-text-secondary mb-1">Sarlavha</label>
            <input
              type="text"
              required
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              className="w-full bg-surface-container-lowest border border-white/10 rounded-xl p-3 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container text-sm"
              placeholder="Serial nomi..."
            />
          </div>

          <div className="md:col-span-2">
            <label className="block text-xs sm:text-sm font-medium text-text-secondary mb-1">Tavsif</label>
            <textarea
              rows={3}
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              className="w-full bg-surface-container-lowest border border-white/10 rounded-xl p-3 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container text-sm"
              placeholder="Serial haqida qisqacha..."
            />
          </div>

          <div className="md:col-span-2">
            <label className="block text-xs sm:text-sm font-medium text-text-secondary mb-1">Poster URL (rasm havolasi)</label>
            <input
              type="text"
              placeholder="https://..."
              value={form.poster_url}
              onChange={(e) => setForm({ ...form, poster_url: e.target.value })}
              className="w-full bg-surface-container-lowest border border-white/10 rounded-xl p-3 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container text-sm"
            />
          </div>

          <div className="md:col-span-2">
            <label className="block text-xs sm:text-sm font-medium text-text-secondary mb-1">Treyler URL (YouTube yoki havola, majburiy emas)</label>
            <input
              type="text"
              placeholder="https://youtube.com/watch?v=..."
              value={form.trailer_url}
              onChange={(e) => setForm({ ...form, trailer_url: e.target.value })}
              className="w-full bg-surface-container-lowest border border-white/10 rounded-xl p-3 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container text-sm"
            />
          </div>

          <div>
            <label className="block text-xs sm:text-sm font-medium text-text-secondary mb-1">Rejissyor</label>
            <input
              type="text"
              value={form.director}
              onChange={(e) => setForm({ ...form, director: e.target.value })}
              className="w-full bg-surface-container-lowest border border-white/10 rounded-xl p-3 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container text-sm"
            />
          </div>

          <div>
            <label className="block text-xs sm:text-sm font-medium text-text-secondary mb-1">Yil</label>
            <input
              type="number"
              value={form.release_year}
              onChange={(e) => setForm({ ...form, release_year: parseInt(e.target.value) || 2024 })}
              className="w-full bg-surface-container-lowest border border-white/10 rounded-xl p-3 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container text-sm"
            />
          </div>

          <div className="md:col-span-2">
            <label className="block text-xs sm:text-sm font-medium text-text-secondary mb-1">Aktyorlar</label>
            <input
              type="text"
              value={form.cast}
              onChange={(e) => setForm({ ...form, cast: e.target.value })}
              className="w-full bg-surface-container-lowest border border-white/10 rounded-xl p-3 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container text-sm"
            />
          </div>

          <div>
            <label className="block text-xs sm:text-sm font-medium text-text-secondary mb-1">Reyting (IMDb)</label>
            <input
              type="number"
              step="0.1"
              min="0"
              max="10"
              value={form.imdb_rating}
              onChange={(e) => setForm({ ...form, imdb_rating: parseFloat(e.target.value) || 0 })}
              className="w-full bg-surface-container-lowest border border-white/10 rounded-xl p-3 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container text-sm"
            />
          </div>
          
          <div className="md:col-span-2">
            <label className="block text-xs sm:text-sm font-medium text-text-secondary mb-1">Manba (Source)</label>
            <select
              value={form.source_id}
              onChange={(e) => setForm({ ...form, source_id: e.target.value === "" ? "" : parseInt(e.target.value) })}
              className="w-full bg-surface-container-lowest border border-white/10 rounded-xl p-3 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container text-sm"
            >
              <option value="">Manba tanlanmagan</option>
              {sources.map(s => (
                <option key={s.id} value={s.id}>{s.name} ({s.type})</option>
              ))}
            </select>
            {errorMsg && <p className="text-red-400 text-xs sm:text-sm mt-1">{errorMsg}</p>}
          </div>

          <div className="md:col-span-2">
            <label className="block text-xs sm:text-sm font-medium text-text-secondary mb-1">Status (Holati)</label>
            <select
              value={form.status}
              onChange={(e) => setForm({ ...form, status: e.target.value })}
              className="w-full bg-surface-container-lowest border border-white/10 rounded-xl p-3 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container text-sm"
            >
              <option value="ongoing">Davom etmoqda</option>
              <option value="completed">Tugallangan</option>
            </select>
          </div>

          {/* Categories */}
          <div className="md:col-span-2">
            <label className="block text-xs sm:text-sm font-medium text-text-secondary mb-2">Kategoriyalar</label>
            <div className="flex flex-wrap gap-2">
              {categories.map(c => (
                <label key={c.id} className="flex items-center bg-surface-container-lowest border border-white/10 px-3 py-2 rounded-xl cursor-pointer text-text-primary hover:bg-white/5 transition-colors text-xs sm:text-sm min-h-[38px]">
                  <input type="checkbox" className="mr-2 w-4 h-4 rounded border-white/10 bg-surface-container-lowest focus:ring-primary-container text-primary-container" checked={form.category_ids.includes(c.id)} onChange={() => handleCategoryChange(c.id)} />
                  {c.name}
                </label>
              ))}
            </div>
          </div>
          
          {/* Pages */}
          <div className="md:col-span-2">
            <label className="block text-xs sm:text-sm font-medium text-text-secondary mb-2">Sahifalar</label>
            <div className="flex flex-wrap gap-2">
              {pages.map(p => (
                <label key={p.id} className="flex items-center bg-surface-container-lowest border border-white/10 px-3 py-2 rounded-xl cursor-pointer text-text-primary hover:bg-white/5 transition-colors text-xs sm:text-sm min-h-[38px]">
                  <input type="checkbox" className="mr-2 w-4 h-4 rounded border-white/10 bg-surface-container-lowest focus:ring-primary-container text-primary-container" checked={form.page_ids.includes(p.id)} onChange={() => handlePageChange(p.id)} />
                  {p.title}
                </label>
              ))}
            </div>
          </div>

          {/* Action buttons */}
          <div className="md:col-span-2 flex flex-col sm:flex-row gap-3 pt-3">
            <button
              type="submit"
              className="bg-primary-container text-white px-6 py-3 rounded-xl font-medium hover:scale-[1.02] active:scale-95 transition-all text-sm w-full sm:w-auto text-center min-h-[44px]"
            >
              {editingId ? "O'zgarishlarni saqlash" : "Serialni saqlash"}
            </button>
            {editingId && (
              <button
                type="button"
                onClick={handleCancel}
                className="bg-white/5 border border-white/10 text-text-primary px-6 py-3 rounded-xl font-medium hover:bg-white/10 active:scale-95 transition-all text-sm w-full sm:w-auto text-center min-h-[44px]"
              >
                Bekor qilish
              </button>
            )}
          </div>
        </form>
      </div>

      {/* Series Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
        {seriesList.map((s) => (
          <div key={s.id} className="metric-card rounded-2xl overflow-hidden flex flex-col group border border-white/5 shadow-lg">
            {s.poster_url && (
              <div className="h-44 sm:h-48 w-full bg-surface-container-lowest overflow-hidden relative">
                <img src={s.poster_url} alt={s.title} className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105" />
                <div className="absolute inset-0 bg-gradient-to-t from-surface-container-high to-transparent opacity-90"></div>
              </div>
            )}
            <div className={`p-4 sm:p-5 flex-1 flex flex-col relative z-10 ${s.poster_url ? "-mt-8" : ""} bg-surface-container-high rounded-t-xl`}>
              <h3 className="text-base sm:text-lg font-bold text-text-primary mb-2 truncate">{s.title}</h3>
              
              {s.categories && s.categories.length > 0 && (
                <div className="flex flex-wrap gap-1 mb-2.5">
                  {s.categories.map((c) => (
                    <span
                      key={c.id}
                      className="inline-block bg-primary-container/20 text-primary-container border border-primary-container/30 text-[11px] px-2 py-0.5 rounded-full font-medium"
                    >
                      {c.name}
                    </span>
                  ))}
                </div>
              )}
              
              {s.source && (
                <span className="text-tertiary-fixed text-xs sm:text-sm mb-2 flex items-center gap-1 font-medium">
                  📦 Manba: {s.source.name}
                </span>
              )}
              
              <span className={`text-xs sm:text-sm mb-2 font-medium ${s.status === 'completed' ? 'text-green-400' : 'text-yellow-400'}`}>
                {s.status === 'completed' ? '✅ Tugallangan' : '🔄 Davom etmoqda'}
              </span>
              
              <p className="text-xs sm:text-sm text-text-secondary mb-4 line-clamp-3">{s.description || "Tavsif yo'q"}</p>
              
              <div className="mt-auto flex items-center gap-2 pt-2 border-t border-white/5">
                <Link
                  href={`/series/${s.id}`}
                  className="flex-1 bg-surface-container-lowest border border-white/10 text-text-primary hover:text-white hover:border-white/30 text-center px-4 py-2.5 rounded-xl text-xs sm:text-sm font-medium transition-all hover:bg-white/5 min-h-[40px] flex items-center justify-center gap-1"
                >
                  <span className="material-symbols-outlined text-[18px]">layers</span>
                  Mavsumlar
                </Link>
                <button
                  onClick={() => handleEdit(s)}
                  className="p-2.5 text-text-secondary hover:text-tertiary-fixed hover:bg-white/5 rounded-xl transition-colors border border-white/5 min-h-[40px] min-w-[40px] flex items-center justify-center"
                  title="Tahrirlash"
                  aria-label="Tahrirlash"
                >
                  <span className="material-symbols-outlined text-[18px]">edit</span>
                </button>
                <button
                  onClick={() => handleDelete(s.id)}
                  className="p-2.5 text-text-secondary hover:text-primary-container hover:bg-white/5 rounded-xl transition-colors border border-white/5 min-h-[40px] min-w-[40px] flex items-center justify-center"
                  title="O'chirish"
                  aria-label="O'chirish"
                >
                  <span className="material-symbols-outlined text-[18px]">delete</span>
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
      
      {seriesList.length === 0 && (
        <div className="text-center py-12 metric-card rounded-2xl border border-white/10">
          <p className="text-text-secondary text-sm">Hali hech qanday serial qo'shilmagan.</p>
        </div>
      )}
    </div>
  );
}
