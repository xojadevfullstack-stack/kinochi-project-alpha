"use client";

import { useEffect, useState } from "react";
import { fetchApi } from "@/lib/api";
import VideoUploadModal from "@/components/VideoUploadModal";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";

type Episode = {
  id: number;
  season_id: number;
  episode_number: number;
  title: string | null;
  duration: number | null;
  code: string;
  display_code: string;
  translations: { id: number; language: string; telegram_file_id: string }[];
  created_at: string;
};

type Season = {
  id: number;
  season_number: number;
  title: string | null;
  series_id: number;
};

type Series = {
  id: number;
  title: string;
};

export default function EpisodesListPage() {
  const params = useParams();
  const router = useRouter();
  const seriesId = params.seriesId as string;
  const seasonId = params.seasonId as string;
  
  const [series, setSeries] = useState<Series | null>(null);
  const [season, setSeason] = useState<Season | null>(null);
  const [episodes, setEpisodes] = useState<Episode[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  
  const [editingId, setEditingId] = useState<number | null>(null);
  
  // Video Modal states
  const [videoModalOpen, setVideoModalOpen] = useState(false);
  const [videoEpisodeId, setVideoEpisodeId] = useState<number | null>(null);

  const [form, setForm] = useState({
    season_id: parseInt(seasonId),
    episode_number: 1,
    title: "",
    duration: "",
  });

  const [editingTranslationId, setEditingTranslationId] = useState<number | null>(null);
  const [editingLanguage, setEditingLanguage] = useState<string>("");

  useEffect(() => {
    if (seriesId && seasonId) {
      loadData();
    }
  }, [seriesId, seasonId]);

  const loadData = async () => {
    try {
      const [seriesData, seasonData, episodesData] = await Promise.all([
        fetchApi(`/series/${seriesId}`),
        fetchApi(`/series/seasons/${seasonId}`),
        fetchApi(`/series/seasons/${seasonId}/episodes`)
      ]);
      
      setSeries(seriesData);
      setSeason(seasonData);
      setEpisodes(episodesData);
      
      if (episodesData.length > 0) {
        const nextNum = Math.max(...episodesData.map((e: Episode) => e.episode_number)) + 1;
        if (!editingId) setForm(f => ({ ...f, episode_number: nextNum }));
      }
    } catch (e: any) {
      alert("Xato: " + e.message);
      if (e.message.includes("not found")) {
        router.push(`/series/${seriesId}`);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    setSaving(true);
    try {
      if (editingId) {
        await fetchApi(`/series/episodes/${editingId}`, { 
          method: "PUT", 
          body: JSON.stringify({
            episode_number: form.episode_number,
            title: form.title || null,
            duration: form.duration ? parseInt(form.duration) : null
          }) 
        });
      } else {
        await fetchApi(`/series/seasons/${seasonId}/episodes`, { 
          method: "POST", 
          body: JSON.stringify({
            episode_number: form.episode_number,
            title: form.title || null,
            duration: form.duration ? parseInt(form.duration) : null
          }) 
        });
      }
      handleCancel();
      loadData();
    } catch (e: any) {
      alert("Saqlashda xato: " + e.message);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Ushbu qismni o'chirasizmi?")) return;
    try {
      await fetchApi(`/series/episodes/${id}`, { method: "DELETE" });
      loadData();
    } catch (e: any) {
      alert("O'chirishda xato: " + e.message);
    }
  };

  const handleDeleteTranslation = async (translationId: number) => {
    if (!confirm("Ushbu video (studiya)ni o'chirasizmi?")) return;
    try {
      await fetchApi(`/series/episodes/translations/${translationId}`, { method: "DELETE" });
      loadData();
    } catch (e: any) {
      alert("O'chirishda xato: " + e.message);
    }
  };

  const handleEditTranslationSubmit = async (translationId: number) => {
    if (!editingLanguage.trim()) return;
    try {
      await fetchApi(`/series/episodes/translations/${translationId}`, {
        method: "PUT",
        body: JSON.stringify({ language: editingLanguage.trim() })
      });
      setEditingTranslationId(null);
      loadData();
    } catch (e: any) {
      alert("Xato: " + e.message);
    }
  };

  const handleEdit = (e: Episode) => {
    setEditingId(e.id);
    setForm({
      season_id: e.season_id,
      episode_number: e.episode_number,
      title: e.title || "",
      duration: e.duration ? e.duration.toString() : "",
    });
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handleCancel = () => {
    setEditingId(null);
    const nextNum = episodes.length > 0 ? Math.max(...episodes.map((e: Episode) => e.episode_number)) + 1 : 1;
    setForm({ season_id: parseInt(seasonId), episode_number: nextNum, title: "", duration: "" });
  };

  if (loading) return <div className="p-8 text-center text-text-secondary">Yuklanmoqda...</div>;

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto">
      {/* Breadcrumb */}
      <nav className="flex text-xs sm:text-sm text-text-secondary mb-4 sm:mb-6" aria-label="Breadcrumb">
        <ol className="inline-flex items-center space-x-1 sm:space-x-2">
          <li className="inline-flex items-center">
            <Link href="/series" className="hover:text-white transition flex items-center gap-1">
              <span className="material-symbols-outlined text-base">arrow_back</span>
              Seriallar
            </Link>
          </li>
          <li>
            <div className="flex items-center">
              <span className="mx-1 text-white/30">/</span>
              <Link href={`/series/${seriesId}`} className="hover:text-white transition truncate max-w-[150px]">
                {series?.title}
              </Link>
            </div>
          </li>
          <li>
            <div className="flex items-center">
              <span className="mx-1 text-white/30">/</span>
              <span className="text-text-primary font-medium">{season?.season_number}-mavsum</span>
            </div>
          </li>
        </ol>
      </nav>

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-text-primary tracking-tight">
            {series?.title} ({season?.season_number}-mavsum) — Qismlar
          </h1>
          <p className="text-xs sm:text-sm text-text-secondary mt-1">Qismlar ro'yxati va videolarni boshqarish</p>
        </div>
      </div>

      {/* Form Card */}
      <div className="metric-card p-4 sm:p-6 rounded-2xl mb-8">
        <h2 className="text-lg sm:text-xl font-semibold mb-4 text-text-primary flex items-center gap-2">
          <span className="material-symbols-outlined text-primary-container">
            {editingId ? "edit" : "add_circle"}
          </span>
          {editingId ? "Qismni tahrirlash" : "Yangi qism qo'shish"}
        </h2>
        
        <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-3 sm:gap-4">
          <div>
            <label className="block text-xs sm:text-sm font-medium text-text-secondary mb-1">Qism raqami</label>
            <input
              type="number"
              min="1"
              value={form.episode_number}
              onChange={(e) => setForm({ ...form, episode_number: parseInt(e.target.value) || 1 })}
              className="w-full bg-surface-container-lowest border border-white/10 rounded-xl p-3 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container text-sm"
              required
            />
          </div>
          <div>
            <label className="block text-xs sm:text-sm font-medium text-text-secondary mb-1">Davomiyligi (daqiqa)</label>
            <input
              type="number"
              min="1"
              placeholder="Masalan: 45"
              value={form.duration}
              onChange={(e) => setForm({ ...form, duration: e.target.value })}
              className="w-full bg-surface-container-lowest border border-white/10 rounded-xl p-3 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container text-sm"
            />
          </div>
          <div className="md:col-span-2">
            <label className="block text-xs sm:text-sm font-medium text-text-secondary mb-1">Maxsus nom (ixtiyoriy)</label>
            <input
              type="text"
              placeholder="Masalan: Uyga qaytish"
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              className="w-full bg-surface-container-lowest border border-white/10 rounded-xl p-3 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container text-sm"
            />
          </div>
          
          <div className="md:col-span-2 flex flex-col sm:flex-row gap-3 pt-2">
            <button 
              type="submit" 
              disabled={saving}
              className={`px-6 py-3 rounded-xl font-medium transition-all text-sm w-full sm:w-auto text-center min-h-[44px] ${saving ? 'bg-primary-container/50 text-white cursor-not-allowed' : 'bg-primary-container text-white hover:scale-[1.02] active:scale-95'}`}
            >
              {saving ? "Yuklanmoqda..." : editingId ? "O'zgarishlarni saqlash" : "Qismni saqlash"}
            </button>
            {editingId && (
              <button 
                type="button" 
                onClick={handleCancel}
                disabled={saving}
                className="bg-white/5 border border-white/10 text-text-primary px-6 py-3 rounded-xl font-medium hover:bg-white/10 active:scale-95 transition-all text-sm w-full sm:w-auto text-center min-h-[44px]"
              >
                Bekor qilish
              </button>
            )}
          </div>
        </form>
      </div>

      {/* Episodes Table */}
      <div className="metric-card rounded-2xl overflow-hidden shadow-xl">
        <div className="p-4 sm:p-5 border-b border-white/5 bg-[#1a0908]/80 flex items-center justify-between">
          <h3 className="font-display font-bold text-base sm:text-lg text-text-primary">Qismlar ro'yxati ({episodes.length})</h3>
        </div>

        {episodes.length > 0 ? (
          <div className="overflow-x-auto custom-scrollbar">
            <table className="min-w-[700px] w-full text-left border-collapse">
              <thead className="bg-surface-container-lowest border-b border-white/10">
                <tr>
                  <th className="px-4 sm:px-6 py-3.5 text-xs font-semibold text-text-secondary uppercase tracking-wider">Qism</th>
                  <th className="px-4 sm:px-6 py-3.5 text-xs font-semibold text-text-secondary uppercase tracking-wider">Kod</th>
                  <th className="px-4 sm:px-6 py-3.5 text-xs font-semibold text-text-secondary uppercase tracking-wider">Video Status</th>
                  <th className="px-4 sm:px-6 py-3.5 text-right text-xs font-semibold text-text-secondary uppercase tracking-wider">Amallar</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 text-sm">
                {episodes.map((e) => (
                  <tr key={e.id} className="data-table-row">
                    <td className="px-4 sm:px-6 py-4 whitespace-nowrap">
                      <div className="font-bold text-primary-container text-base">{e.episode_number}-qism</div>
                      {e.title && <div className="text-xs text-text-secondary">{e.title}</div>}
                      {e.duration && <div className="text-xs text-tertiary-fixed mt-1 font-medium">{e.duration} daqiqa</div>}
                    </td>
                    <td className="px-4 sm:px-6 py-4 whitespace-nowrap">
                      <div className="text-xs font-mono text-text-primary bg-surface-container-lowest border border-white/10 px-2.5 py-1 rounded-lg inline-block mb-1">
                        #{e.code}
                      </div>
                      <div className="text-[11px] text-text-secondary">
                        {e.display_code}
                      </div>
                    </td>
                    <td className="px-4 sm:px-6 py-4">
                      {e.translations && e.translations.length > 0 ? (
                        <div className="flex flex-col gap-1.5 min-w-[140px]">
                          {e.translations.map((t) => (
                            <div key={t.id} className="flex flex-col gap-1 bg-surface-container-high border border-white/10 px-2 py-1.5 rounded-lg text-xs text-text-secondary">
                              {editingTranslationId === t.id ? (
                                <div className="flex items-center gap-1.5">
                                  <input
                                    type="text"
                                    value={editingLanguage}
                                    onChange={(ev) => setEditingLanguage(ev.target.value)}
                                    className="bg-surface-container-lowest border border-white/10 rounded px-2 py-1 text-xs text-text-primary flex-1 min-w-0"
                                  />
                                  <button onClick={() => handleEditTranslationSubmit(t.id)} className="text-green-400 hover:text-green-300 font-bold p-1">Saql</button>
                                  <button onClick={() => setEditingTranslationId(null)} className="text-gray-400 hover:text-white p-1">Bekor</button>
                                </div>
                              ) : (
                                <div className="flex items-center justify-between">
                                  <span>✅ {t.language}</span>
                                  <div className="flex items-center">
                                    <button 
                                      onClick={() => {
                                        setEditingTranslationId(t.id);
                                        setEditingLanguage(t.language);
                                      }} 
                                      className="text-primary-container hover:text-white p-1 transition-colors" 
                                      title="Tahrirlash"
                                      aria-label="Tahrirlash"
                                    >
                                      <span className="material-symbols-outlined text-[16px]">edit</span>
                                    </button>
                                    <button 
                                      onClick={() => handleDeleteTranslation(t.id)} 
                                      className="text-rating-gold hover:text-red-400 p-1 transition-colors" 
                                      title="Videoni o'chirish"
                                      aria-label="Videoni o'chirish"
                                    >
                                      ✕
                                    </button>
                                  </div>
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      ) : (
                        <span className="text-rating-gold font-bold text-xs bg-rating-gold/10 px-2 py-1 rounded-lg">❌ Yo'q</span>
                      )}
                    </td>
                    <td className="px-4 sm:px-6 py-4 whitespace-nowrap text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button 
                          onClick={() => {
                            setVideoEpisodeId(e.id);
                            setVideoModalOpen(true);
                          }} 
                          className="text-xs font-bold bg-tertiary-container/20 text-tertiary hover:bg-tertiary-container/40 border border-tertiary-container/40 px-3 py-1.5 rounded-lg transition-all min-h-[32px] inline-flex items-center gap-1"
                        >
                          <span className="material-symbols-outlined text-[16px]">upload</span>
                          Video
                        </button>
                        <button onClick={() => handleEdit(e)} className="text-xs bg-white/5 border border-white/10 hover:bg-white/15 text-text-primary px-3 py-1.5 rounded-lg transition-colors min-h-[32px]">
                          Tahrir
                        </button>
                        <button onClick={() => handleDelete(e.id)} className="text-xs bg-red-500/10 border border-red-500/20 hover:bg-red-500/20 text-red-400 px-3 py-1.5 rounded-lg transition-colors min-h-[32px]">
                          O'chirish
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="p-8 sm:p-12 text-center text-text-secondary text-sm">
            Hali hech qanday qism qo'shilmagan.
          </div>
        )}
      </div>

      <VideoUploadModal
        isOpen={videoModalOpen}
        onClose={() => {
          setVideoModalOpen(false);
          setVideoEpisodeId(null);
        }}
        entityName="Qism"
        entityId={videoEpisodeId}
        uploadEndpoint={`/series/episodes/${videoEpisodeId}/upload-video`}
        linkEndpoint={`/series/episodes/${videoEpisodeId}/link-video`}
        onSuccess={() => loadData()}
      />
    </div>
  );
}
