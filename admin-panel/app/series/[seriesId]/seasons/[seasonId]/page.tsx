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
            duration: form.duration ? parseInt(form.duration as string) : null
          }) 
        });
      } else {
        await fetchApi(`/series/seasons/${seasonId}/episodes`, { 
          method: "POST", 
          body: JSON.stringify({
            season_id: form.season_id,
            episode_number: form.episode_number,
            title: form.title || null,
            duration: form.duration ? parseInt(form.duration as string) : null
          }) 
        });
      }

      handleCancel();
      await loadData();
      alert("Muvaffaqiyatli saqlandi!");
    } catch (e: any) {
      alert(e.message || "Kutilmagan xato yuz berdi");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Ushbu qismni o'chirasizmi? (Telegramdagi video ham o'chib ketishi mumkin)")) return;
    try {
      await fetchApi(`/series/episodes/${id}`, { method: "DELETE" });
      loadData();
    } catch (e: any) {
      alert("O'chirishda xato: " + e.message);
    }
  };

  const handleDeleteTranslation = async (translationId: number) => {
    if (!confirm("Bu video (studiya) o'chib ketadimi?")) return;
    try {
      await fetchApi(`/series/episodes/translations/${translationId}`, { method: "DELETE" });
      loadData();
    } catch (e: any) {
      alert("O'chirishda xato: " + e.message);
    }
  };

  const handleEdit = (e: Episode) => {
    setEditingId(e.id);
    setForm({
      season_id: e.season_id,
      episode_number: e.episode_number,
      title: e.title || "",
      duration: e.duration?.toString() || "",
    });
  };

  const handleCancel = () => {
    setEditingId(null);
    
    const nextNum = episodes.length > 0 ? Math.max(...episodes.map((e: Episode) => e.episode_number)) + 1 : 1;
    setForm({ season_id: parseInt(seasonId), episode_number: nextNum, title: "", duration: "" });
  };

  if (loading) return <div className="p-8 text-center text-gray-500">Yuklanmoqda...</div>;

  return (
    <div className="p-8 max-w-7xl mx-auto">
      {/* Breadcrumb */}
      <nav className="flex text-sm text-text-secondary mb-6" aria-label="Breadcrumb">
        <ol className="inline-flex items-center space-x-1 md:space-x-3">
          <li className="inline-flex items-center">
            <Link href="/series" className="hover:text-white transition">Seriallar</Link>
          </li>
          <li>
            <div className="flex items-center">
              <span className="mx-2 text-white/30">/</span>
              <Link href={`/series/${seriesId}`} className="hover:text-white transition">{series?.title}</Link>
            </div>
          </li>
          <li>
            <div className="flex items-center">
              <span className="mx-2 text-white/30">/</span>
              <span className="text-text-primary font-medium">{season?.season_number}-mavsum</span>
            </div>
          </li>
        </ol>
      </nav>

      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-text-primary">
          {series?.title} ({season?.season_number}-mavsum) — Qismlar
        </h1>
      </div>

      <div className="metric-card p-6 rounded-xl mb-8">
        <h2 className="text-xl font-semibold mb-4 text-text-primary">
          {editingId ? "Qismni tahrirlash" : "Yangi qism qo'shish"}
        </h2>
        <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-1">Qism raqami</label>
            <input
              type="number"
              min="1"
              value={form.episode_number}
              onChange={(e) => setForm({ ...form, episode_number: parseInt(e.target.value) || 1 })}
              className="w-full bg-surface-container-lowest border border-white/10 rounded-lg p-2.5 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-1">Davomiyligi (daqiqa)</label>
            <input
              type="number"
              min="1"
              placeholder="Masalan: 45"
              value={form.duration}
              onChange={(e) => setForm({ ...form, duration: e.target.value })}
              className="w-full bg-surface-container-lowest border border-white/10 rounded-lg p-2.5 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container"
            />
          </div>
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-text-secondary mb-1">Maxsus nom (ixtiyoriy)</label>
            <input
              type="text"
              placeholder="Masalan: Uyga qaytish"
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              className="w-full bg-surface-container-lowest border border-white/10 rounded-lg p-2.5 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container"
            />
          </div>
          
          <div className="md:col-span-2 flex gap-3 pt-2">
            <button 
              type="submit" 
              disabled={saving}
              className={`px-6 py-2.5 rounded-lg font-medium transition-all ${saving ? 'bg-primary-container/50 text-white cursor-not-allowed' : 'bg-primary-container text-white hover:scale-105'}`}
            >
              {saving ? "Yuklanmoqda..." : "Saqlash"}
            </button>
            {editingId && (
              <button 
                type="button" 
                onClick={handleCancel}
                disabled={saving}
                className="bg-white/5 border border-white/10 text-text-primary px-6 py-2.5 rounded-lg font-medium hover:bg-white/10 transition-all"
              >
                Bekor qilish
              </button>
            )}
          </div>
        </form>
      </div>

      <div className="metric-card rounded-xl overflow-hidden">
        {episodes.length > 0 ? (
          <table className="min-w-full">
            <thead className="bg-surface-container-lowest border-b border-white/10">
              <tr>
                <th className="px-6 py-4 text-left text-xs font-semibold text-text-secondary uppercase tracking-wider">Qism</th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-text-secondary uppercase tracking-wider">Kod / URL</th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-text-secondary uppercase tracking-wider">Video Status</th>
                <th className="px-6 py-4 text-right text-xs font-semibold text-text-secondary uppercase tracking-wider">Amallar</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {episodes.map((e) => (
                <tr key={e.id} className="data-table-row">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="font-bold text-primary-container">{e.episode_number}-qism</div>
                    {e.title && <div className="text-sm text-text-secondary">{e.title}</div>}
                    {e.duration && <div className="text-xs text-tertiary-fixed mt-1 font-medium">{e.duration} daqiqa</div>}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-mono text-text-primary bg-surface-container-lowest border border-white/10 px-2 py-1 rounded inline-block mb-1">
                      {e.code}
                    </div>
                    <div className="text-xs text-text-secondary">
                      Display: {e.display_code}
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    {e.translations && e.translations.length > 0 ? (
                      <div className="flex flex-col gap-1">
                        {e.translations.map((t) => (
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
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium flex items-center justify-end gap-2">
                    <button 
                      onClick={() => {
                        setVideoEpisodeId(e.id);
                        setVideoModalOpen(true);
                      }} 
                      className="text-tertiary-fixed hover:text-white mr-2 font-bold border border-tertiary-fixed hover:border-white px-3 py-1.5 rounded transition-all"
                    >
                      Video yuklash
                    </button>
                    <button onClick={() => handleEdit(e)} className="text-text-secondary hover:text-white p-2 transition-colors">Tahrirlash</button>
                    <button onClick={() => handleDelete(e.id)} className="text-primary-container hover:text-red-400 p-2 transition-colors">O'chirish</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="p-12 text-center text-text-secondary">
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
        uploadEndpoint={`/series/episodes/${videoEpisodeId}/upload-video`}
        linkEndpoint={`/series/episodes/${videoEpisodeId}/link-video`}
        onSuccess={() => loadData()}
      />
    </div>
  );
}
