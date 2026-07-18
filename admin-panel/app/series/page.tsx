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
  imdb_rating: number | null;
  release_year: number | null;
  director: string | null;
  cast: string | null;
  created_at: string;
  categories: Category[];
  pages: PageItem[];
  source_id: number | null;
  source: Source | null;
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
    imdb_rating: 0,
    release_year: 2024,
    director: "",
    cast: "",
    category_ids: [] as number[],
    page_ids: [] as number[],
    source_id: "" as number | "",
  });
  const [sources, setSources] = useState<Source[]>([]);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([loadSeries(), loadCategories(), loadSources(), loadPages()]).then(() => setLoading(false));
  }, []);

  const loadCategories = async () => {
    try {
      const data = await fetchApi("/categories/");
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
      const data = await fetchApi("/pages/");
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
    const payload = {
      ...form,
      source_id: form.source_id === "" ? null : form.source_id
    };

    try {
      if (editingId) {
        await fetchApi(`/series/${editingId}`, { method: "PUT", body: JSON.stringify(payload) });
      } else {
        await fetchApi("/series", { method: "POST", body: JSON.stringify(payload) });
      }
      handleCancel();
      loadSeries();
    } catch (e: any) {
      setErrorMsg("Saqlashda xato: " + (e.message || "Noma'lum xato"));
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Ushbu serialni o'chirasizmi? (Uning barcha mavsumlari va qismlari ham o'chib ketadi!)")) return;
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
      imdb_rating: s.imdb_rating || 0,
      release_year: s.release_year || 2024,
      director: s.director || "",
      cast: s.cast || "",
      category_ids: s.categories ? s.categories.map((c) => c.id) : [],
      page_ids: s.pages ? s.pages.map((p) => p.id) : [],
      source_id: s.source_id || "",
    });
  };

  const handleCancel = () => {
    setEditingId(null);
    setErrorMsg(null);
    setForm({ title: "", description: "", poster_url: "", imdb_rating: 0, release_year: 2024, director: "", cast: "", category_ids: [], page_ids: [], source_id: "" });
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

  if (loading) return <div className="p-8 text-center text-gray-500">Yuklanmoqda...</div>;

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-text-primary">Seriallar Boshqaruvi</h1>
      </div>

      <div className="metric-card p-6 rounded-xl mb-8">
        <h2 className="text-xl font-semibold mb-4 text-text-primary">
          {editingId ? "Serialni tahrirlash" : "Yangi serial qo'shish"}
        </h2>
        <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-text-secondary mb-1">Nomi</label>
            <input
              type="text"
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              className="w-full bg-surface-container-lowest border border-white/10 rounded-lg p-2.5 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container"
              required
            />
          </div>
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-text-secondary mb-1">Tavsif</label>
            <textarea
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              className="w-full bg-surface-container-lowest border border-white/10 rounded-lg p-2.5 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container"
              rows={3}
            />
          </div>
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-text-secondary mb-1">Poster URL (Rasm)</label>
            <input
              type="url"
              value={form.poster_url}
              onChange={(e) => setForm({ ...form, poster_url: e.target.value })}
              className="w-full bg-surface-container-lowest border border-white/10 rounded-lg p-2.5 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-1">Rejissyor</label>
            <input
              type="text"
              value={form.director}
              onChange={(e) => setForm({ ...form, director: e.target.value })}
              className="w-full bg-surface-container-lowest border border-white/10 rounded-lg p-2.5 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-1">Yil</label>
            <input
              type="number"
              value={form.release_year}
              onChange={(e) => setForm({ ...form, release_year: parseInt(e.target.value) })}
              className="w-full bg-surface-container-lowest border border-white/10 rounded-lg p-2.5 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container"
            />
          </div>
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-text-secondary mb-1">Aktyorlar</label>
            <input
              type="text"
              value={form.cast}
              onChange={(e) => setForm({ ...form, cast: e.target.value })}
              className="w-full bg-surface-container-lowest border border-white/10 rounded-lg p-2.5 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-1">Reyting (IMDb)</label>
            <input
              type="number"
              step="0.1"
              min="0"
              max="10"
              value={form.imdb_rating}
              onChange={(e) => setForm({ ...form, imdb_rating: parseFloat(e.target.value) })}
              className="w-full bg-surface-container-lowest border border-white/10 rounded-lg p-2.5 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container"
            />
          </div>
          
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-text-secondary mb-1">Manba (Source)</label>
            <select
              value={form.source_id}
              onChange={(e) => setForm({ ...form, source_id: e.target.value === "" ? "" : parseInt(e.target.value) })}
              className="w-full bg-surface-container-lowest border border-white/10 rounded-lg p-2.5 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container"
            >
              <option value="">Manba tanlanmagan</option>
              {sources.map(s => (
                <option key={s.id} value={s.id}>{s.name} ({s.type})</option>
              ))}
            </select>
            {errorMsg && <p className="text-red-400 text-sm mt-1">{errorMsg}</p>}
          </div>

          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-text-secondary mb-2">Kategoriyalar</label>
            <div className="flex flex-wrap gap-2">
              {categories.map(c => (
                <label key={c.id} className="flex items-center bg-surface-container-lowest border border-white/10 px-3 py-1.5 rounded-lg cursor-pointer text-text-primary hover:bg-white/5 transition-colors">
                  <input type="checkbox" className="mr-2 w-4 h-4 rounded border-white/10 bg-surface-container-lowest focus:ring-primary-container text-primary-container" checked={form.category_ids.includes(c.id)} onChange={() => handleCategoryChange(c.id)} />
                  {c.name}
                </label>
              ))}
            </div>
          </div>
          
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-text-secondary mb-2">Sahifalar</label>
            <div className="flex flex-wrap gap-2">
              {pages.map(p => (
                <label key={p.id} className="flex items-center bg-surface-container-lowest border border-white/10 px-3 py-1.5 rounded-lg cursor-pointer text-text-primary hover:bg-white/5 transition-colors">
                  <input type="checkbox" className="mr-2 w-4 h-4 rounded border-white/10 bg-surface-container-lowest focus:ring-primary-container text-primary-container" checked={form.page_ids.includes(p.id)} onChange={() => handlePageChange(p.id)} />
                  {p.title}
                </label>
              ))}
            </div>
          </div>

          <div className="md:col-span-2 flex gap-3 pt-2">
            <button
              type="submit"
              className="bg-primary-container text-white px-6 py-2.5 rounded-lg font-medium hover:scale-105 transition-all"
            >
              Saqlash
            </button>
            {editingId && (
              <button
                type="button"
                onClick={handleCancel}
                className="bg-white/5 border border-white/10 text-text-primary px-6 py-2.5 rounded-lg font-medium hover:bg-white/10 transition-all"
              >
                Bekor qilish
              </button>
            )}
          </div>
        </form>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {seriesList.map((s) => (
          <div key={s.id} className="metric-card rounded-xl overflow-hidden flex flex-col group border border-white/5">
            {s.poster_url && (
              <div className="h-48 w-full bg-surface-container-lowest overflow-hidden relative">
                <img src={s.poster_url} alt={s.title} className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110" />
                <div className="absolute inset-0 bg-gradient-to-t from-surface-container-high to-transparent opacity-80"></div>
              </div>
            )}
            <div className="p-5 flex-1 flex flex-col relative z-10 -mt-8 bg-surface-container-high">
              <h3 className="text-lg font-bold text-text-primary mb-2 truncate">{s.title}</h3>
              {s.categories && s.categories.length > 0 && (
                <div className="flex flex-wrap gap-1 mb-3">
                  {s.categories.map((c) => (
                    <span
                      key={c.id}
                      className="inline-block bg-primary-container/20 text-primary-container border border-primary-container/30 text-xs px-2.5 py-1 rounded-full font-medium"
                    >
                      {c.name}
                    </span>
                  ))}
                </div>
              )}
              {s.source && (
                <span className="text-tertiary-fixed text-sm mb-3 flex items-center gap-1 font-medium">
                  📦 Manba: {s.source.name}
                </span>
              )}
              <p className="text-sm text-text-secondary mb-4 line-clamp-3">{s.description || "Tavsif yo'q"}</p>
              <div className="mt-auto flex justify-between items-center gap-2">
                <Link
                  href={`/series/${s.id}`}
                  className="flex-1 bg-surface-container-lowest border border-white/10 text-text-primary hover:text-white hover:border-white/30 text-center px-4 py-2 rounded-lg text-sm font-medium transition-all hover:bg-white/5"
                >
                  Mavsumlar
                </Link>
                <button
                  onClick={() => handleEdit(s)}
                  className="p-2 text-text-secondary hover:text-tertiary-fixed hover:bg-white/5 rounded-lg transition-colors border border-transparent hover:border-white/10"
                  title="Tahrirlash"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" /></svg>
                </button>
                <button
                  onClick={() => handleDelete(s.id)}
                  className="p-2 text-text-secondary hover:text-primary-container hover:bg-white/5 rounded-lg transition-colors border border-transparent hover:border-white/10"
                  title="O'chirish"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
      
      {seriesList.length === 0 && (
        <div className="text-center py-12 metric-card rounded-xl border border-white/10">
          <p className="text-text-secondary">Hali hech qanday serial qo'shilmagan.</p>
        </div>
      )}
    </div>
  );
}
