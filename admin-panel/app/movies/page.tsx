"use client";

import { useEffect, useState } from "react";
import { fetchApi } from "@/lib/api";
import VideoUploadModal from "@/components/VideoUploadModal";

type Category = { id: number; name: string };
type Movie = {
  id: number;
  title: string;
  code: string;
  description: string;
  genres: string;
  director: string | null;
  cast: string | null;
  imdb_rating: number | null;
  poster_url: string | null;
  release_year: number;
  duration_minutes: number;
  categories: Category[];
  translations: { id: number; language: string; telegram_file_id: string }[];
};

export default function MoviesPage() {
  const [movies, setMovies] = useState<Movie[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [uploadingId, setUploadingId] = useState<number | null>(null);
  
  // Video Modal states
  const [videoModalOpen, setVideoModalOpen] = useState(false);
  const [videoMovieId, setVideoMovieId] = useState<number | null>(null);

  const [form, setForm] = useState({
    title: "", description: "", genres: "", release_year: 2024, duration_minutes: 120, poster_url: "",
    director: "", cast: "", imdb_rating: 0,
    category_ids: [] as number[]
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
    const payload = {
      ...form,
    };

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

  const handleDeleteTranslation = async (translationId: number) => {
    if (!confirm("Bu video (studiya) o'chirilsinmi?")) return;
    try {
      await fetchApi(`/movies/translations/${translationId}`, { method: "DELETE" });
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
      director: m.director || "",
      cast: m.cast || "",
      imdb_rating: m.imdb_rating || 0,
      category_ids: m.categories.map(c => c.id)
    });
  };

  const handleCancel = () => {
    setEditingId(null);
    setForm({ title: "", description: "", genres: "", release_year: 2024, duration_minutes: 120, poster_url: "", director: "", cast: "", imdb_rating: 0, category_ids: [] });
  };

  const openVideoModal = (id: number) => {
    setVideoMovieId(id);
    setVideoModalOpen(true);
  };

  const closeVideoModal = () => {
    setVideoModalOpen(false);
    setVideoMovieId(null);
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
      <h1 className="text-3xl font-bold mb-6 text-gray-800">Kinolar</h1>
      
      <div className="bg-white p-6 rounded-lg shadow-md mb-8">
        <h2 className="text-xl font-semibold mb-4">{editingId ? "Tahrirlash" : "Yangi Kino"}</h2>
        <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="md:col-span-2"><label className="block text-sm">Sarlavha</label><input required type="text" className="w-full border p-2 rounded" value={form.title} onChange={e => setForm({...form, title: e.target.value})} /></div>
          <div className="md:col-span-2"><label className="block text-sm">Ta'rif</label><textarea className="w-full border p-2 rounded" value={form.description} onChange={e => setForm({...form, description: e.target.value})} /></div>
          <div className="md:col-span-2"><label className="block text-sm">Poster URL (rasm havolasi)</label><input type="text" className="w-full border p-2 rounded" placeholder="https://..." value={form.poster_url} onChange={e => setForm({...form, poster_url: e.target.value})} /></div>
          <div><label className="block text-sm">Janrlar</label><input type="text" className="w-full border p-2 rounded" value={form.genres} onChange={e => setForm({...form, genres: e.target.value})} /></div>
          <div><label className="block text-sm">Rejissyor</label><input type="text" className="w-full border p-2 rounded" value={form.director} onChange={e => setForm({...form, director: e.target.value})} /></div>
          <div className="md:col-span-2"><label className="block text-sm">Aktyorlar</label><input type="text" className="w-full border p-2 rounded" value={form.cast} onChange={e => setForm({...form, cast: e.target.value})} /></div>
          <div><label className="block text-sm">Yil</label><input type="number" className="w-full border p-2 rounded" value={form.release_year} onChange={e => setForm({...form, release_year: parseInt(e.target.value)})} /></div>
          <div><label className="block text-sm">Davomiylik (min)</label><input type="number" className="w-full border p-2 rounded" value={form.duration_minutes} onChange={e => setForm({...form, duration_minutes: parseInt(e.target.value)})} /></div>
          <div><label className="block text-sm">Reyting (IMDb)</label><input type="number" step="0.1" min="0" max="10" className="w-full border p-2 rounded" value={form.imdb_rating} onChange={e => setForm({...form, imdb_rating: parseFloat(e.target.value)})} /></div>
          
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
          

          
          <div className="md:col-span-2 flex gap-4 mt-2">
            <button type="submit" className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700">Saqlash</button>
            {editingId && <button type="button" onClick={handleCancel} className="bg-gray-300 text-gray-800 px-4 py-2 rounded-md hover:bg-gray-400">Bekor qilish</button>}
          </div>
        </form>
      </div>

      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Kod</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Sarlavha</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Video</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Amallar</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {movies.map(m => (
              <tr key={m.id}>
                <td className="px-4 py-4 whitespace-nowrap text-sm font-bold text-gray-900">{m.code}</td>
                <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900">{m.title}</td>
                <td className="px-4 py-4">
                  {m.translations && m.translations.length > 0 ? (
                    <div className="flex flex-col gap-1">
                      {m.translations.map((t) => (
                        <div key={t.id} className="flex items-center justify-between bg-gray-50 px-2 py-1 rounded text-sm">
                          <span>✅ {t.language}</span>
                          <button onClick={() => handleDeleteTranslation(t.id)} className="text-red-500 hover:text-red-700 ml-2" title="Videoni o'chirish">
                            ✕
                          </button>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <span className="text-red-600 font-bold">❌ Yo'q</span>
                  )}
                </td>
                <td className="px-4 py-4 whitespace-nowrap text-sm font-medium">
                  {uploadingId === m.id ? (
                    <span className="text-gray-500 mr-4">
                      Yuklanmoqda...
                    </span>
                  ) : (
                    <button onClick={() => openVideoModal(m.id)} className="text-blue-600 hover:text-blue-900 mr-4 font-bold border border-blue-600 px-2 py-1 rounded">Video yuklash</button>
                  )}
                  <button onClick={() => handleEdit(m)} className="text-indigo-600 hover:text-indigo-900 mr-4">Tahrirlash</button>
                  <button onClick={() => handleDelete(m.id)} className="text-red-600 hover:text-red-900">O'chirish</button>
                </td>
              </tr>
            ))}
            {movies.length === 0 && <tr><td colSpan={4} className="px-4 py-4 text-center text-gray-500">Hech qanday kino topilmadi</td></tr>}
          </tbody>
        </table>
      </div>

      <VideoUploadModal
        isOpen={videoModalOpen}
        onClose={closeVideoModal}
        entityName="Kino"
        uploadEndpoint={`/movies/${videoMovieId}/upload-video`}
        linkEndpoint={`/movies/${videoMovieId}/link-video`}
        onSuccess={() => loadMovies()}
      />
    </div>
  );
}
