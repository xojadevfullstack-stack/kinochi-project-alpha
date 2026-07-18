"use client";

import { useEffect, useState } from "react";
import { fetchApi } from "@/lib/api";
import VideoUploadModal from "@/components/VideoUploadModal";

type Category = { id: number; name: string };
type PageItem = { id: number; title: string };
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
  pages: PageItem[];
  source_link: string | null;
  translations: { id: number; language: string; telegram_file_id: string }[];
};

export default function MoviesPage() {
  const [movies, setMovies] = useState<Movie[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [pages, setPages] = useState<PageItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [uploadingId, setUploadingId] = useState<number | null>(null);
  
  // Video Modal states
  const [videoModalOpen, setVideoModalOpen] = useState(false);
  const [videoMovieId, setVideoMovieId] = useState<number | null>(null);

  const [form, setForm] = useState({
    title: "", description: "", genres: "", release_year: 2024, duration_minutes: 120, poster_url: "",
    director: "", cast: "", imdb_rating: 0,
    category_ids: [] as number[],
    page_ids: [] as number[],
    source_link: ""
  });
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([loadMovies(), loadCategories(), loadPages()]).then(() => setLoading(false));
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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    const payload = {
      ...form,
      source_link: form.source_link || null
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
      if (e.message && e.message.includes("Invalid Telegram URL")) {
        setErrorMsg("Noto'g'ri Telegram link formati");
      } else {
        setErrorMsg("Saqlashda xato: " + (e.message || "Noma'lum xato"));
      }
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
      category_ids: m.categories?.map(c => c.id) || [],
      page_ids: m.pages?.map(p => p.id) || [],
      source_link: m.source_link || ""
    });
  };

  const handleCancel = () => {
    setEditingId(null);
    setErrorMsg(null);
    setForm({ title: "", description: "", genres: "", release_year: 2024, duration_minutes: 120, poster_url: "", director: "", cast: "", imdb_rating: 0, category_ids: [], page_ids: [], source_link: "" });
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

  const handlePageChange = (id: number) => {
    setForm(prev => {
      const ids = prev.page_ids.includes(id) 
        ? prev.page_ids.filter(x => x !== id)
        : [...prev.page_ids, id];
      return { ...prev, page_ids: ids };
    });
  };

  if (loading) return <div>Yuklanmoqda...</div>;

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold mb-6 text-text-primary">Kinolar</h1>
      </div>
      
      <div className="metric-card p-6 rounded-xl mb-8">
        <h2 className="text-xl font-semibold mb-4 text-text-primary">{editingId ? "Tahrirlash" : "Yangi Kino"}</h2>
        <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="md:col-span-2"><label className="block text-sm font-medium text-text-secondary mb-1">Sarlavha</label><input required type="text" className="w-full bg-surface-container-lowest border border-white/10 rounded-lg p-2.5 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container" value={form.title} onChange={e => setForm({...form, title: e.target.value})} /></div>
          <div className="md:col-span-2"><label className="block text-sm font-medium text-text-secondary mb-1">Ta'rif</label><textarea className="w-full bg-surface-container-lowest border border-white/10 rounded-lg p-2.5 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container" value={form.description} onChange={e => setForm({...form, description: e.target.value})} /></div>
          <div className="md:col-span-2"><label className="block text-sm font-medium text-text-secondary mb-1">Poster URL (rasm havolasi)</label><input type="text" className="w-full bg-surface-container-lowest border border-white/10 rounded-lg p-2.5 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container" placeholder="https://..." value={form.poster_url} onChange={e => setForm({...form, poster_url: e.target.value})} /></div>
          <div><label className="block text-sm font-medium text-text-secondary mb-1">Janrlar</label><input type="text" className="w-full bg-surface-container-lowest border border-white/10 rounded-lg p-2.5 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container" value={form.genres} onChange={e => setForm({...form, genres: e.target.value})} /></div>
          <div><label className="block text-sm font-medium text-text-secondary mb-1">Rejissyor</label><input type="text" className="w-full bg-surface-container-lowest border border-white/10 rounded-lg p-2.5 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container" value={form.director} onChange={e => setForm({...form, director: e.target.value})} /></div>
          <div className="md:col-span-2"><label className="block text-sm font-medium text-text-secondary mb-1">Aktyorlar</label><input type="text" className="w-full bg-surface-container-lowest border border-white/10 rounded-lg p-2.5 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container" value={form.cast} onChange={e => setForm({...form, cast: e.target.value})} /></div>
          <div><label className="block text-sm font-medium text-text-secondary mb-1">Yil</label><input type="number" className="w-full bg-surface-container-lowest border border-white/10 rounded-lg p-2.5 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container" value={form.release_year} onChange={e => setForm({...form, release_year: parseInt(e.target.value)})} /></div>
          <div><label className="block text-sm font-medium text-text-secondary mb-1">Davomiylik (min)</label><input type="number" className="w-full bg-surface-container-lowest border border-white/10 rounded-lg p-2.5 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container" value={form.duration_minutes} onChange={e => setForm({...form, duration_minutes: parseInt(e.target.value)})} /></div>
          <div><label className="block text-sm font-medium text-text-secondary mb-1">Reyting (IMDb)</label><input type="number" step="0.1" min="0" max="10" className="w-full bg-surface-container-lowest border border-white/10 rounded-lg p-2.5 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container" value={form.imdb_rating} onChange={e => setForm({...form, imdb_rating: parseFloat(e.target.value)})} /></div>
          
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-text-secondary mb-1">Manba (Telegram) link (ixtiyoriy)</label>
            <input type="text" className="w-full bg-surface-container-lowest border border-white/10 rounded-lg p-2.5 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container" placeholder="https://t.me/c/..." value={form.source_link} onChange={e => setForm({...form, source_link: e.target.value})} />
            <p className="text-xs text-text-secondary mt-1">Faqat yopiq (private) guruh/kanal linklari qabul qilinadi (https://t.me/c/... formatida). Ommaviy (@username bilan) guruh linklari ishlamaydi.</p>
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
          
          <div className="md:col-span-2 flex gap-4 mt-2">
            <button type="submit" className="bg-primary-container text-white px-6 py-2.5 rounded-lg hover:scale-105 transition-all font-medium">Saqlash</button>
            {editingId && <button type="button" onClick={handleCancel} className="bg-white/5 border border-white/10 text-text-primary px-6 py-2.5 rounded-lg hover:bg-white/10 transition-all font-medium">Bekor qilish</button>}
          </div>
        </form>
      </div>

      <div className="metric-card rounded-xl overflow-hidden">
        <table className="min-w-full">
          <thead className="bg-surface-container-lowest border-b border-white/10">
            <tr>
              <th className="px-6 py-4 text-left text-xs font-semibold text-text-secondary uppercase tracking-wider">Kod</th>
              <th className="px-6 py-4 text-left text-xs font-semibold text-text-secondary uppercase tracking-wider">Sarlavha</th>
              <th className="px-6 py-4 text-left text-xs font-semibold text-text-secondary uppercase tracking-wider">Manba</th>
              <th className="px-6 py-4 text-left text-xs font-semibold text-text-secondary uppercase tracking-wider">Video</th>
              <th className="px-6 py-4 text-left text-xs font-semibold text-text-secondary uppercase tracking-wider">Amallar</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {movies.map(m => (
              <tr key={m.id} className="data-table-row">
                <td className="px-6 py-4 whitespace-nowrap font-bold text-primary-container">{m.code}</td>
                <td className="px-6 py-4 whitespace-nowrap text-text-primary font-medium">{m.title}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-text-secondary">
                  {m.source_link ? (
                    <a href={m.source_link} target="_blank" rel="noreferrer" className="text-tertiary-fixed hover:text-white transition-colors flex items-center gap-1" title={m.source_link}>
                      🔗 Link
                    </a>
                  ) : "-"}
                </td>
                <td className="px-6 py-4">
                  {m.translations && m.translations.length > 0 ? (
                    <div className="flex flex-col gap-1">
                      {m.translations.map((t) => (
                        <div key={t.id} className="flex items-center justify-between bg-surface-container-high border border-white/10 px-2 py-1 rounded text-sm text-text-secondary">
                          <span>✅ {t.language}</span>
                          <button onClick={() => handleDeleteTranslation(t.id)} className="text-rating-gold hover:text-red-400 ml-2 transition-colors" title="Videoni o'chirish">
                            ✕
                          </button>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <span className="text-rating-gold font-bold">❌ Yo'q</span>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                  {uploadingId === m.id ? (
                    <span className="text-text-secondary mr-4">
                      Yuklanmoqda...
                    </span>
                  ) : (
                    <button onClick={() => openVideoModal(m.id)} className="text-tertiary-fixed hover:text-white mr-4 font-bold border border-tertiary-fixed hover:border-white px-3 py-1.5 rounded transition-all">Video yuklash</button>
                  )}
                  <button onClick={() => handleEdit(m)} className="text-text-secondary hover:text-white mr-4 transition-colors">Tahrirlash</button>
                  <button onClick={() => handleDelete(m.id)} className="text-primary-container hover:text-red-400 transition-colors">O'chirish</button>
                </td>
              </tr>
            ))}
            {movies.length === 0 && <tr><td colSpan={5} className="px-6 py-8 text-center text-text-secondary">Hech qanday kino topilmadi</td></tr>}
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
