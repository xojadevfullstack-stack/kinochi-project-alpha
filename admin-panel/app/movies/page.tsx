"use client";

import { useEffect, useState } from "react";
import { fetchApi, fetchApiUpload } from "@/lib/api";
import Link from "next/link";

type Category = { id: number; name: string };
type Movie = {
  id: number;
  title: string;
  code: string;
  description: string;
  genres: string;
  poster_url: string | null;
  release_year: number;
  duration_minutes: number;
  telegram_file_id: string;
  storage_channel_message_id: number | null;
  categories: Category[];
  is_series: boolean;
};

export default function MoviesPage() {
  const [movies, setMovies] = useState<Movie[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [uploadingId, setUploadingId] = useState<number | null>(null);
  const [uploadingPoster, setUploadingPoster] = useState(false);

  const [form, setForm] = useState({
    title: "", description: "", genres: "", release_year: 2024, duration_minutes: 120, poster_url: "",
    category_ids: [] as number[], is_series: false
  });

  useEffect(() => {
    Promise.all([loadMovies(), loadCategories()]).then(() => setLoading(false));
  }, []);

  const loadMovies = async () => {
    try {
      const data = await fetchApi("/movies/?limit=100");
      setMovies(data.items);
    } catch (e: any) {
      alert("Xato: " + e.message);
    }
  };

  const loadCategories = async () => {
    try {
      const data = await fetchApi("/categories/");
      setCategories(data);
    } catch (e: any) {
      console.error(e);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const payload = { ...form };

    try {
      if (editingId) {
        await fetchApi(`/movies/${editingId}`, { method: "PUT", body: JSON.stringify(payload) });
      } else {
        await fetchApi("/movies/", { method: "POST", body: JSON.stringify(payload) });
      }
      handleCancel();
      loadMovies();
    } catch (e: any) {
      alert("Saqlashda xato: " + e.message);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("O'chirilsinmi?")) return;
    try {
      await fetchApi(`/movies/${id}`, { method: "DELETE" });
      loadMovies();
    } catch (e: any) {
      alert("O'chirishda xato: " + e.message);
    }
  };

  const handleEdit = (m: Movie) => {
    setEditingId(m.id);
    setForm({
      title: m.title, description: m.description, genres: m.genres, 
      release_year: m.release_year, duration_minutes: m.duration_minutes,
      poster_url: m.poster_url || "",
      category_ids: m.categories.map(c => c.id),
      is_series: m.is_series || false
    });
  };

  const handleCancel = () => {
    setEditingId(null);
    setForm({ title: "", description: "", genres: "", release_year: 2024, duration_minutes: 120, poster_url: "", category_ids: [], is_series: false });
  };

  const handlePosterUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploadingPoster(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const data = await fetchApiUpload("/uploads/poster", {
        method: "POST",
        body: formData,
      });
      // Set the returned URL to the form
      setForm(prev => ({ ...prev, poster_url: data.url }));
    } catch (err: any) {
      alert("Poster yuklashda xato: " + err.message);
    } finally {
      setUploadingPoster(false);
    }
  };

  const handleUploadVideo = async (id: number, file: File) => {
    setUploadingId(id);
    const formData = new FormData();
    formData.append("file", file);

    try {
      await fetchApiUpload(`/movies/${id}/upload-video`, {
        method: "POST",
        body: formData,
      });
      loadMovies();
      alert("Video muvaffaqiyatli yuklandi!");
    } catch (e: any) {
      alert("Yuklashda xato: " + e.message);
    } finally {
      setUploadingId(null);
    }
  };

  const triggerFileInput = (id: number) => {
    const input = document.createElement("input");
    input.type = "file";
    input.accept = "video/*";
    input.onchange = (e: any) => {
      const file = e.target.files[0];
      if (file) handleUploadVideo(id, file);
    };
    input.click();
  };

  const handleCategoryChange = (id: number) => {
    setForm(prev => {
      const ids = prev.category_ids.includes(id) 
        ? prev.category_ids.filter(x => x !== id)
        : [...prev.category_ids, id];
      return { ...prev, category_ids: ids };
    });
  };

  if (loading) return <div>Yuklanmoqda...</div>;

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6 text-gray-800">Kinolar / Seriallar</h1>
      
      <div className="bg-white p-6 rounded-lg shadow-md mb-8">
        <h2 className="text-xl font-semibold mb-4">{editingId ? "Tahrirlash" : "Yangi qo'shish"}</h2>
        <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-4">
          
          <div className="md:col-span-2 flex items-center bg-gray-50 p-4 rounded-md border border-gray-200">
            <input 
              type="checkbox" 
              id="is_series" 
              className="w-5 h-5 mr-3 cursor-pointer" 
              checked={form.is_series} 
              onChange={e => setForm({...form, is_series: e.target.checked})} 
            />
            <label htmlFor="is_series" className="text-lg font-medium cursor-pointer">
              Bu Serial (Bir nechta mavsum va qismlarga ega)
            </label>
          </div>

          <div className="md:col-span-2">
            <label className="block text-sm">Sarlavha</label>
            <input required type="text" className="w-full border p-2 rounded" value={form.title} onChange={e => setForm({...form, title: e.target.value})} />
          </div>
          
          <div className="md:col-span-2">
            <label className="block text-sm">Ta'rif</label>
            <textarea className="w-full border p-2 rounded" value={form.description} onChange={e => setForm({...form, description: e.target.value})} />
          </div>
          
          <div className="md:col-span-2">
            <label className="block text-sm font-semibold mb-1">Poster Yuklash (Rasm)</label>
            <div className="flex gap-4 items-center">
              <input 
                type="file" 
                accept="image/png, image/jpeg, image/webp" 
                onChange={handlePosterUpload} 
                className="border p-1 rounded" 
              />
              {uploadingPoster && <span className="text-sm text-blue-600 animate-pulse">Yuklanmoqda...</span>}
            </div>
            <div className="mt-2 flex gap-2 items-center">
              <span className="text-xs text-gray-500">Yoki URL:</span>
              <input type="text" className="w-full border p-2 rounded text-sm" placeholder="https://..." value={form.poster_url} onChange={e => setForm({...form, poster_url: e.target.value})} />
            </div>
            {form.poster_url && (
              <div className="mt-2">
                <img src={form.poster_url} alt="Poster preview" className="h-24 rounded shadow" />
              </div>
            )}
          </div>

          <div><label className="block text-sm">Janrlar</label><input type="text" className="w-full border p-2 rounded" value={form.genres} onChange={e => setForm({...form, genres: e.target.value})} /></div>
          <div><label className="block text-sm">Yil</label><input type="number" className="w-full border p-2 rounded" value={form.release_year} onChange={e => setForm({...form, release_year: parseInt(e.target.value)})} /></div>
          <div><label className="block text-sm">Davomiylik (min)</label><input type="number" className="w-full border p-2 rounded" value={form.duration_minutes} onChange={e => setForm({...form, duration_minutes: parseInt(e.target.value)})} /></div>
          
          <div className="md:col-span-2">
            <label className="block text-sm mb-2">Kategoriyalar</label>
            <div className="flex flex-wrap gap-2">
              {categories.map(c => (
                <label key={c.id} className="flex items-center bg-gray-100 px-2 py-1 rounded cursor-pointer">
                  <input type="checkbox" className="mr-2" checked={form.category_ids.includes(c.id)} onChange={() => handleCategoryChange(c.id)} />
                  {c.name}
                </label>
              ))}
            </div>
          </div>
          
          <div className="md:col-span-2 flex gap-4 mt-4 border-t pt-4">
            <button type="submit" disabled={uploadingPoster} className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50">Saqlash</button>
            {editingId && <button type="button" onClick={handleCancel} className="bg-gray-300 text-gray-800 px-6 py-2 rounded-md hover:bg-gray-400">Bekor qilish</button>}
          </div>
        </form>
      </div>

      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Kod</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Sarlavha</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tur</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Video</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Amallar</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {movies.map(m => (
              <tr key={m.id}>
                <td className="px-4 py-4 whitespace-nowrap text-sm font-bold text-gray-900">{m.code}</td>
                <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900 font-semibold">{m.title}</td>
                <td className="px-4 py-4 whitespace-nowrap text-sm">
                  {m.is_series ? (
                    <span className="bg-purple-100 text-purple-800 px-2 py-1 rounded text-xs font-bold">Serial</span>
                  ) : (
                    <span className="bg-green-100 text-green-800 px-2 py-1 rounded text-xs font-bold">Kino</span>
                  )}
                </td>
                <td className="px-4 py-4 whitespace-nowrap">
                  {m.is_series ? (
                    <span className="text-gray-400 text-sm">Qismlarda</span>
                  ) : m.telegram_file_id || m.storage_channel_message_id ? (
                    <span className="text-green-600 font-bold text-sm">✅ Bor</span>
                  ) : (
                    <span className="text-red-600 font-bold text-sm">❌ Yo'q</span>
                  )}
                </td>
                <td className="px-4 py-4 whitespace-nowrap text-sm font-medium">
                  {m.is_series ? (
                     <Link href={`/series/${m.id}`} className="text-purple-600 hover:text-purple-900 mr-4 font-bold border border-purple-600 px-2 py-1 rounded">
                       Fasllar & Qismlar
                     </Link>
                  ) : uploadingId === m.id ? (
                    <span className="text-gray-500 mr-4">Yuklanmoqda...</span>
                  ) : (
                    <button onClick={() => triggerFileInput(m.id)} className="text-blue-600 hover:text-blue-900 mr-4 font-bold border border-blue-600 px-2 py-1 rounded">
                      Video yuklash
                    </button>
                  )}
                  <button onClick={() => handleEdit(m)} className="text-indigo-600 hover:text-indigo-900 mr-4">Tahrir</button>
                  <button onClick={() => handleDelete(m.id)} className="text-red-600 hover:text-red-900">O'chirish</button>
                </td>
              </tr>
            ))}
            {movies.length === 0 && <tr><td colSpan={5} className="px-4 py-4 text-center text-gray-500">Hech qanday ma'lumot topilmadi</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}
