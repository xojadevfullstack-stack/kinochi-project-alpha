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
  trailer_url: string | null;
  release_year: number;
  duration_minutes: number;
  runtime?: number;
  categories: Category[];
  pages: PageItem[];
  source_id?: number | null;
  source_link?: string | null;
  translations: { id: number; language: string; telegram_file_id: string }[];
};

export default function MoviesPage() {
  const [movies, setMovies] = useState<Movie[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [pages, setPages] = useState<PageItem[]>([]);
  const [sources, setSources] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [uploadingId, setUploadingId] = useState<number | null>(null);
  
  // Video Modal states
  const [videoModalOpen, setVideoModalOpen] = useState(false);
  const [videoMovieId, setVideoMovieId] = useState<number | null>(null);

  const initialForm = {
    title: "", description: "", genres: "", release_year: 2024, duration_minutes: 120, poster_url: "", trailer_url: "",
    director: "", cast: "", imdb_rating: 0,
    category_ids: [] as number[],
    page_ids: [] as number[],
    source_id: "" as number | ""
  };

  const [form, setForm] = useState(initialForm);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([loadMovies(), loadCategories(), loadPages(), loadSources()]).then(() => setLoading(false));
  }, []);

  const loadSources = async () => {
    try {
      const data = await fetchApi("/sources");
      setSources(data);
    } catch (e: any) {
      console.error(e);
    }
  };

  const loadMovies = async () => {
    try {
      const data = await fetchApi("/movies?limit=100");
      setMovies(data.items);
    } catch (e: any) {
      alert("Xato: " + e.message);
    }
  };

  const loadCategories = async () => {
    try {
      const data = await fetchApi("/categories");
      setCategories(data);
    } catch (e: any) {
      console.error(e);
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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    const payload = {
      ...form,
      runtime: form.duration_minutes,
      source_id: form.source_id === "" ? null : form.source_id
    };

    try {
      if (editingId) {
        await fetchApi(`/movies/${editingId}`, { method: "PUT", body: JSON.stringify(payload) });
      } else {
        await fetchApi("/movies", { method: "POST", body: JSON.stringify(payload) });
      }
      handleCancel();
      loadMovies();
    } catch (e: any) {
      setErrorMsg(e.message || "Xato yuz berdi");
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
    let matchedSourceId: number | "" = "";
    if ((m as any).source_chat_id) {
       const source = sources.find(s => s.chat_id === (m as any).source_chat_id && s.topic_id === (m as any).source_topic_id);
       if (source) matchedSourceId = source.id;
    }
    setEditingId(m.id);
    setForm({
      title: m.title, description: m.description, genres: m.genres, 
      release_year: m.release_year, duration_minutes: m.runtime || m.duration_minutes,
      poster_url: m.poster_url || "",
      trailer_url: m.trailer_url || "",
      director: m.director || "",
      cast: m.cast || "",
      imdb_rating: m.imdb_rating || 0,
      category_ids: m.categories?.map(c => c.id) || [],
      page_ids: m.pages?.map(p => p.id) || [],
      source_id: matchedSourceId
    });
    // Smooth scroll up to form on mobile
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handleCancel = () => {
    setEditingId(null);
    setErrorMsg(null);
    setForm(initialForm);
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

  if (loading) return <div className="p-8 text-center text-text-secondary">Yuklanmoqda...</div>;

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto">
      {/* Page Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-text-primary tracking-tight">Kinolar</h1>
          <p className="text-xs sm:text-sm text-text-secondary mt-1">Kinolarni qo'shish, video yuklash va boshqarish</p>
        </div>
      </div>
      
      {/* Form Card */}
      <div className="metric-card p-4 sm:p-6 rounded-2xl mb-8">
        <h2 className="text-lg sm:text-xl font-semibold mb-4 text-text-primary flex items-center gap-2">
          <span className="material-symbols-outlined text-primary-container">
            {editingId ? "edit" : "add_circle"}
          </span>
          {editingId ? "Kinoni tahrirlash" : "Yangi Kino qo'shish"}
        </h2>
        
        <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-3 sm:gap-4">
          <div className="md:col-span-2">
            <label className="block text-xs sm:text-sm font-medium text-text-secondary mb-1">Sarlavha</label>
            <input required type="text" className="w-full bg-surface-container-lowest border border-white/10 rounded-xl p-3 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container text-sm" value={form.title} onChange={e => setForm({...form, title: e.target.value})} placeholder="Kino nomi..." />
          </div>

          <div className="md:col-span-2">
            <label className="block text-xs sm:text-sm font-medium text-text-secondary mb-1">Ta'rif</label>
            <textarea rows={3} className="w-full bg-surface-container-lowest border border-white/10 rounded-xl p-3 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container text-sm" value={form.description} onChange={e => setForm({...form, description: e.target.value})} placeholder="Kino haqida qisqacha..." />
          </div>

          <div className="md:col-span-2">
            <label className="block text-xs sm:text-sm font-medium text-text-secondary mb-1">Poster URL (rasm havolasi)</label>
            <input type="text" className="w-full bg-surface-container-lowest border border-white/10 rounded-xl p-3 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container text-sm" placeholder="https://..." value={form.poster_url} onChange={e => setForm({...form, poster_url: e.target.value})} />
          </div>

          <div className="md:col-span-2">
            <label className="block text-xs sm:text-sm font-medium text-text-secondary mb-1">Treyler URL (YouTube yoki havola, majburiy emas)</label>
            <input type="text" className="w-full bg-surface-container-lowest border border-white/10 rounded-xl p-3 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container text-sm" placeholder="https://youtube.com/watch?v=..." value={form.trailer_url} onChange={e => setForm({...form, trailer_url: e.target.value})} />
          </div>

          <div>
            <label className="block text-xs sm:text-sm font-medium text-text-secondary mb-1">Janrlar</label>
            <input type="text" className="w-full bg-surface-container-lowest border border-white/10 rounded-xl p-3 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container text-sm" placeholder="Jangari, Drama..." value={form.genres} onChange={e => setForm({...form, genres: e.target.value})} />
          </div>

          <div>
            <label className="block text-xs sm:text-sm font-medium text-text-secondary mb-1">Rejissyor</label>
            <input type="text" className="w-full bg-surface-container-lowest border border-white/10 rounded-xl p-3 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container text-sm" value={form.director} onChange={e => setForm({...form, director: e.target.value})} />
          </div>

          <div className="md:col-span-2">
            <label className="block text-xs sm:text-sm font-medium text-text-secondary mb-1">Aktyorlar</label>
            <input type="text" className="w-full bg-surface-container-lowest border border-white/10 rounded-xl p-3 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container text-sm" value={form.cast} onChange={e => setForm({...form, cast: e.target.value})} />
          </div>

          <div>
            <label className="block text-xs sm:text-sm font-medium text-text-secondary mb-1">Yil</label>
            <input type="number" className="w-full bg-surface-container-lowest border border-white/10 rounded-xl p-3 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container text-sm" value={form.release_year} onChange={e => setForm({...form, release_year: parseInt(e.target.value) || 2024})} />
          </div>

          <div>
            <label className="block text-xs sm:text-sm font-medium text-text-secondary mb-1">Davomiylik (daqiqa)</label>
            <input type="number" className="w-full bg-surface-container-lowest border border-white/10 rounded-xl p-3 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container text-sm" value={form.duration_minutes} onChange={e => setForm({...form, duration_minutes: parseInt(e.target.value) || 120})} />
          </div>

          <div className="md:col-span-2">
            <label className="block text-xs sm:text-sm font-medium text-text-secondary mb-1">Reyting (IMDb)</label>
            <input type="number" step="0.1" min="0" max="10" className="w-full bg-surface-container-lowest border border-white/10 rounded-xl p-3 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container text-sm" value={form.imdb_rating} onChange={e => setForm({...form, imdb_rating: parseFloat(e.target.value) || 0})} />
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
          
          {/* Submit / Cancel Buttons */}
          <div className="md:col-span-2 flex flex-col sm:flex-row gap-3 mt-3">
            <button type="submit" className="bg-primary-container text-white px-6 py-3 rounded-xl hover:scale-[1.02] active:scale-95 transition-all font-medium text-sm w-full sm:w-auto text-center min-h-[44px]">
              {editingId ? "O'zgarishlarni saqlash" : "Kinoni saqlash"}
            </button>
            {editingId && (
              <button type="button" onClick={handleCancel} className="bg-white/5 border border-white/10 text-text-primary px-6 py-3 rounded-xl hover:bg-white/10 active:scale-95 transition-all font-medium text-sm w-full sm:w-auto text-center min-h-[44px]">
                Bekor qilish
              </button>
            )}
          </div>
        </form>
      </div>

      {/* Movies List Table */}
      <div className="metric-card rounded-2xl overflow-hidden shadow-xl">
        <div className="p-4 sm:p-5 border-b border-white/5 bg-[#1a0908]/80 flex items-center justify-between">
          <h3 className="font-display font-bold text-base sm:text-lg text-text-primary">Mavjud kinolar ro'yxati ({movies.length})</h3>
        </div>

        <div className="overflow-x-auto custom-scrollbar">
          <table className="min-w-[700px] w-full text-left border-collapse">
            <thead className="bg-surface-container-lowest border-b border-white/10">
              <tr>
                <th className="px-4 sm:px-6 py-3.5 text-xs font-semibold text-text-secondary uppercase tracking-wider">Kod</th>
                <th className="px-4 sm:px-6 py-3.5 text-xs font-semibold text-text-secondary uppercase tracking-wider">Sarlavha</th>
                <th className="px-4 sm:px-6 py-3.5 text-xs font-semibold text-text-secondary uppercase tracking-wider">Manba</th>
                <th className="px-4 sm:px-6 py-3.5 text-xs font-semibold text-text-secondary uppercase tracking-wider">Video</th>
                <th className="px-4 sm:px-6 py-3.5 text-xs font-semibold text-text-secondary uppercase tracking-wider text-right">Amallar</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5 text-sm">
              {movies.map(m => (
                <tr key={m.id} className="data-table-row">
                  <td className="px-4 sm:px-6 py-4 whitespace-nowrap font-bold text-primary-container text-base">
                    #{m.code}
                  </td>
                  <td className="px-4 sm:px-6 py-4 whitespace-nowrap text-text-primary font-medium">
                    <div className="flex flex-col">
                      <span>{m.title}</span>
                      <span className="text-xs text-text-secondary">{m.release_year} • {m.duration_minutes || m.runtime} daq</span>
                    </div>
                  </td>
                  <td className="px-4 sm:px-6 py-4 whitespace-nowrap text-xs text-text-secondary">
                    {m.source_link ? (
                      <a href={m.source_link} target="_blank" rel="noreferrer" className="text-tertiary-fixed hover:text-white transition-colors inline-flex items-center gap-1 bg-white/5 px-2.5 py-1 rounded-lg" title={m.source_link}>
                        🔗 Link
                      </a>
                    ) : "-"}
                  </td>
                  <td className="px-4 sm:px-6 py-4">
                    {m.translations && m.translations.length > 0 ? (
                      <div className="flex flex-col gap-1.5 min-w-[120px]">
                        {m.translations.map((t) => (
                          <div key={t.id} className="flex items-center justify-between bg-surface-container-high border border-white/10 px-2 py-1 rounded-lg text-xs text-text-secondary">
                            <span>✅ {t.language}</span>
                            <button onClick={() => handleDeleteTranslation(t.id)} className="text-rating-gold hover:text-red-400 ml-2 p-0.5 transition-colors" title="Videoni o'chirish">
                              ✕
                            </button>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <span className="text-rating-gold font-bold text-xs bg-rating-gold/10 px-2 py-1 rounded-lg">❌ Yo'q</span>
                    )}
                  </td>
                  <td className="px-4 sm:px-6 py-4 whitespace-nowrap text-right">
                    <div className="flex items-center justify-end gap-2">
                      {uploadingId === m.id ? (
                        <span className="text-text-secondary text-xs">
                          Yuklanmoqda...
                        </span>
                      ) : (
                        <button 
                          onClick={() => openVideoModal(m.id)} 
                          className="text-xs font-bold bg-tertiary-container/20 text-tertiary hover:bg-tertiary-container/40 border border-tertiary-container/40 px-3 py-1.5 rounded-lg transition-all min-h-[32px] inline-flex items-center gap-1"
                        >
                          <span className="material-symbols-outlined text-[16px]">upload</span>
                          Video
                        </button>
                      )}
                      <button 
                        onClick={() => handleEdit(m)} 
                        className="text-xs bg-white/5 border border-white/10 hover:bg-white/15 text-text-primary px-3 py-1.5 rounded-lg transition-colors min-h-[32px]"
                      >
                        Tahrirlash
                      </button>
                      <button 
                        onClick={() => handleDelete(m.id)} 
                        className="text-xs bg-red-500/10 border border-red-500/20 hover:bg-red-500/20 text-red-400 px-3 py-1.5 rounded-lg transition-colors min-h-[32px]"
                      >
                        O'chirish
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {movies.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-text-secondary">Hech qanday kino topilmadi</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      <VideoUploadModal
        isOpen={videoModalOpen}
        onClose={closeVideoModal}
        entityName="Kino"
        entityId={videoMovieId}
        uploadEndpoint={`/movies/${videoMovieId}/upload-video`}
        linkEndpoint={`/movies/${videoMovieId}/link-video`}
        onSuccess={() => loadMovies()}
      />
    </div>
  );
}
