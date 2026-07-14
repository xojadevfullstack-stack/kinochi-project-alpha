"use client";

import { useEffect, useState } from "react";
import { fetchApi } from "@/lib/api";
import Link from "next/link";

type Category = { id: number; name: string };

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
  source_link: string | null;
};

export default function SeriesListPage() {
  const [seriesList, setSeriesList] = useState<Series[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
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
    source_link: "",
  });
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([loadSeries(), loadCategories()]).then(() => setLoading(false));
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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    const payload = {
      ...form,
      source_link: form.source_link || null
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
      if (e.message && e.message.includes("Invalid Telegram URL")) {
        setErrorMsg("Noto'g'ri Telegram link formati");
      } else {
        setErrorMsg("Saqlashda xato: " + (e.message || "Noma'lum xato"));
      }
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
      source_link: s.source_link || "",
    });
  };

  const handleCancel = () => {
    setEditingId(null);
    setErrorMsg(null);
    setForm({ title: "", description: "", poster_url: "", imdb_rating: 0, release_year: 2024, director: "", cast: "", category_ids: [], source_link: "" });
  };

  const handleCategoryChange = (id: number) => {
    setForm(prev => {
      const ids = prev.category_ids.includes(id) 
        ? prev.category_ids.filter(x => x !== id)
        : [...prev.category_ids, id];
      return { ...prev, category_ids: ids };
    });
  };

  if (loading) return <div className="p-8 text-center text-gray-500">Yuklanmoqda...</div>;

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Seriallar Boshqaruvi</h1>
      </div>

      <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 mb-8">
        <h2 className="text-xl font-semibold mb-4 text-gray-800">
          {editingId ? "Serialni tahrirlash" : "Yangi serial qo'shish"}
        </h2>
        <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">Nomi</label>
            <input
              type="text"
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              className="w-full border border-gray-300 rounded-lg p-2.5 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              required
            />
          </div>
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">Tavsif</label>
            <textarea
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              className="w-full border border-gray-300 rounded-lg p-2.5 focus:ring-2 focus:ring-blue-500"
              rows={3}
            />
          </div>
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">Poster URL (Rasm)</label>
            <input
              type="url"
              value={form.poster_url}
              onChange={(e) => setForm({ ...form, poster_url: e.target.value })}
              className="w-full border border-gray-300 rounded-lg p-2.5 focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Rejissyor</label>
            <input
              type="text"
              value={form.director}
              onChange={(e) => setForm({ ...form, director: e.target.value })}
              className="w-full border border-gray-300 rounded-lg p-2.5 focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Yil</label>
            <input
              type="number"
              value={form.release_year}
              onChange={(e) => setForm({ ...form, release_year: parseInt(e.target.value) })}
              className="w-full border border-gray-300 rounded-lg p-2.5 focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">Aktyorlar</label>
            <input
              type="text"
              value={form.cast}
              onChange={(e) => setForm({ ...form, cast: e.target.value })}
              className="w-full border border-gray-300 rounded-lg p-2.5 focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Reyting (IMDb)</label>
            <input
              type="number"
              step="0.1"
              min="0"
              max="10"
              value={form.imdb_rating}
              onChange={(e) => setForm({ ...form, imdb_rating: parseFloat(e.target.value) })}
              className="w-full border border-gray-300 rounded-lg p-2.5 focus:ring-2 focus:ring-blue-500"
            />
          </div>
          
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">Manba (Telegram) link (ixtiyoriy)</label>
            <input
              type="text"
              value={form.source_link}
              onChange={(e) => setForm({ ...form, source_link: e.target.value })}
              className="w-full border border-gray-300 rounded-lg p-2.5 focus:ring-2 focus:ring-blue-500"
              placeholder="https://t.me/c/..."
            />
            <p className="text-xs text-gray-500 mt-1">Faqat yopiq (private) guruh/kanal linklari qabul qilinadi (https://t.me/c/... formatida). Ommaviy (@username bilan) guruh linklari ishlamaydi.</p>
            {errorMsg && <p className="text-red-500 text-sm mt-1">{errorMsg}</p>}
          </div>

          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">Kategoriyalar</label>
            <div className="flex flex-wrap gap-2">
              {categories.map(c => (
                <label key={c.id} className="flex items-center bg-gray-100 px-2 py-1 rounded cursor-pointer">
                  <input type="checkbox" className="mr-2" checked={form.category_ids.includes(c.id)} onChange={() => handleCategoryChange(c.id)} />
                  {c.name}
                </label>
              ))}
            </div>
          </div>
          
          <div className="md:col-span-2 flex gap-3 pt-2">
            <button
              type="submit"
              className="bg-blue-600 text-white px-6 py-2 rounded-lg font-medium hover:bg-blue-700 transition"
            >
              Saqlash
            </button>
            {editingId && (
              <button
                type="button"
                onClick={handleCancel}
                className="bg-gray-100 text-gray-700 px-6 py-2 rounded-lg font-medium hover:bg-gray-200 transition"
              >
                Bekor qilish
              </button>
            )}
          </div>
        </form>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {seriesList.map((s) => (
          <div key={s.id} className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden flex flex-col">
            {s.poster_url && (
              <div className="h-48 w-full bg-gray-100 overflow-hidden">
                <img src={s.poster_url} alt={s.title} className="w-full h-full object-cover" />
              </div>
            )}
            <div className="p-5 flex-1 flex flex-col">
              <h3 className="text-lg font-bold text-gray-900 mb-2">{s.title}</h3>
              {s.categories && s.categories.length > 0 && (
                <div className="flex flex-wrap gap-1 mb-3">
                  {s.categories.map((c) => (
                    <span
                      key={c.id}
                      className="inline-block bg-blue-100 text-blue-800 text-xs px-2 py-0.5 rounded-full"
                    >
                      {c.name}
                    </span>
                  ))}
                </div>
              )}
              {s.source_link && (
                <a href={s.source_link} target="_blank" rel="noreferrer" className="text-blue-500 hover:underline text-sm mb-3 flex items-center gap-1" title={s.source_link}>
                  🔗 Telegram manba
                </a>
              )}
              <p className="text-sm text-gray-500 mb-4 line-clamp-3">{s.description || "Tavsif yo'q"}</p>
              <div className="mt-auto flex justify-between items-center gap-2">
                <Link
                  href={`/series/${s.id}`}
                  className="flex-1 bg-indigo-50 text-indigo-700 text-center px-4 py-2 rounded-lg text-sm font-medium hover:bg-indigo-100 transition"
                >
                  Mavsumlar
                </Link>
                <button
                  onClick={() => handleEdit(s)}
                  className="p-2 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition"
                  title="Tahrirlash"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" /></svg>
                </button>
                <button
                  onClick={() => handleDelete(s.id)}
                  className="p-2 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition"
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
        <div className="text-center py-12 bg-white rounded-xl border border-gray-200">
          <p className="text-gray-500">Hali hech qanday serial qo'shilmagan.</p>
        </div>
      )}
    </div>
  );
}
