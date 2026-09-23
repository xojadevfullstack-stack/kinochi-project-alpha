"use client";

import { useEffect, useState } from "react";
import { fetchApi } from "@/lib/api";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";

type Season = {
  id: number;
  series_id: number;
  season_number: number;
  title: string | null;
  description: string | null;
  poster_url: string | null;
  episode_count: number | null;
  status: string;
  created_at: string;
};

type Series = {
  id: number;
  title: string;
};

export default function SeasonsListPage() {
  const params = useParams();
  const router = useRouter();
  const seriesId = params.seriesId as string;
  
  const [series, setSeries] = useState<Series | null>(null);
  const [seasons, setSeasons] = useState<Season[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState<number | null>(null);

  const [form, setForm] = useState({
    series_id: parseInt(seriesId),
    season_number: 1,
    title: "",
    description: "",
    poster_url: "",
    episode_count: "",
    status: "ongoing" as string,
  });

  useEffect(() => {
    if (seriesId) {
      loadData();
    }
  }, [seriesId]);

  const loadData = async () => {
    try {
      const seriesData = await fetchApi(`/series/${seriesId}`);
      setSeries(seriesData);
      
      const seasonsData = await fetchApi(`/series/${seriesId}/seasons`);
      setSeasons(seasonsData);
      
      if (seasonsData.length > 0) {
        const nextNum = Math.max(...seasonsData.map((s: Season) => s.season_number)) + 1;
        if (!editingId) setForm(f => ({ ...f, season_number: nextNum }));
      }
    } catch (e: any) {
      alert("Xato: " + e.message);
      if (e.message.includes("not found")) {
        router.push("/series");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingId) {
        await fetchApi(`/series/seasons/${editingId}`, { method: "PUT", body: JSON.stringify({
          season_number: form.season_number,
          title: form.title || null,
          description: form.description || null,
          poster_url: form.poster_url || null,
          episode_count: form.episode_count ? parseInt(form.episode_count as string) : null,
          status: form.status
        }) });
      } else {
        await fetchApi(`/series/${seriesId}/seasons`, { method: "POST", body: JSON.stringify({
          ...form,
          episode_count: form.episode_count ? parseInt(form.episode_count as string) : null,
          status: form.status
        }) });
      }
      handleCancel();
      loadData();
    } catch (e: any) {
      alert("Saqlashda xato: " + e.message);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Ushbu mavsumni o'chirasizmi? (Uning barcha qismlari ham o'chib ketadi!)")) return;
    try {
      await fetchApi(`/series/seasons/${id}`, { method: "DELETE" });
      loadData();
    } catch (e: any) {
      alert("O'chirishda xato: " + e.message);
    }
  };

  const handleEdit = (s: Season) => {
    setEditingId(s.id);
    setForm({
      series_id: s.series_id,
      season_number: s.season_number,
      title: s.title || "",
      description: s.description || "",
      poster_url: s.poster_url || "",
      episode_count: s.episode_count ? s.episode_count.toString() : "",
      status: s.status,
    });
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handleCancel = () => {
    setEditingId(null);
    const nextNum = seasons.length > 0 ? Math.max(...seasons.map((s: Season) => s.season_number)) + 1 : 1;
    setForm({ series_id: parseInt(seriesId), season_number: nextNum, title: "", description: "", poster_url: "", episode_count: "", status: "ongoing" });
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
              <span className="text-text-primary font-medium truncate max-w-[200px]">{series?.title}</span>
            </div>
          </li>
        </ol>
      </nav>

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-text-primary tracking-tight">
            {series?.title} — Mavsumlar
          </h1>
          <p className="text-xs sm:text-sm text-text-secondary mt-1">Mavsumlar va qismlar strukturasini boshqarish</p>
        </div>
      </div>

      {/* Form Card */}
      <div className="metric-card p-4 sm:p-6 rounded-2xl mb-8">
        <h2 className="text-lg sm:text-xl font-semibold mb-4 text-text-primary flex items-center gap-2">
          <span className="material-symbols-outlined text-primary-container">
            {editingId ? "edit" : "add_circle"}
          </span>
          {editingId ? "Mavsumni tahrirlash" : "Yangi mavsum qo'shish"}
        </h2>
        <form onSubmit={handleSubmit} className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 sm:gap-4">
          <div>
            <label className="block text-xs sm:text-sm font-medium text-text-secondary mb-1">Mavsum raqami</label>
            <input
              type="number"
              min="1"
              value={form.season_number}
              onChange={(e) => setForm({ ...form, season_number: parseInt(e.target.value) || 1 })}
              className="w-full bg-surface-container-lowest border border-white/10 rounded-xl p-3 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container text-sm"
              required
            />
          </div>
          <div>
            <label className="block text-xs sm:text-sm font-medium text-text-secondary mb-1">Qismlar soni</label>
            <input
              type="number"
              min="1"
              placeholder="Masalan: 12"
              value={form.episode_count}
              onChange={(e) => setForm({ ...form, episode_count: e.target.value })}
              className="w-full bg-surface-container-lowest border border-white/10 rounded-xl p-3 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container text-sm"
            />
          </div>
          <div className="sm:col-span-2 md:col-span-1">
            <label className="block text-xs sm:text-sm font-medium text-text-secondary mb-1">Maxsus nom (ixtiyoriy)</label>
            <input
              type="text"
              placeholder="Masalan: Maxfiy topshiriq"
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              className="w-full bg-surface-container-lowest border border-white/10 rounded-xl p-3 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container text-sm"
            />
          </div>
          <div className="sm:col-span-2 md:col-span-3">
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
          <div className="sm:col-span-2 md:col-span-3">
            <label className="block text-xs sm:text-sm font-medium text-text-secondary mb-1">Tavsif (ixtiyoriy)</label>
            <textarea
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              className="w-full bg-surface-container-lowest border border-white/10 rounded-xl p-3 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container text-sm"
              rows={2}
            />
          </div>
          <div className="sm:col-span-2 md:col-span-3">
            <label className="block text-xs sm:text-sm font-medium text-text-secondary mb-1">Poster URL (rasm havolasi)</label>
            <input
              type="text"
              placeholder="https://..."
              value={form.poster_url}
              onChange={(e) => setForm({ ...form, poster_url: e.target.value })}
              className="w-full bg-surface-container-lowest border border-white/10 rounded-xl p-3 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container text-sm"
            />
          </div>
          
          <div className="sm:col-span-2 md:col-span-3 flex flex-col sm:flex-row gap-3 pt-2">
            <button type="submit" className="bg-primary-container text-white px-6 py-3 rounded-xl font-medium hover:scale-[1.02] active:scale-95 transition-all text-sm w-full sm:w-auto text-center min-h-[44px]">
              {editingId ? "O'zgarishlarni saqlash" : "Mavsumni saqlash"}
            </button>
            {editingId && (
              <button type="button" onClick={handleCancel} className="bg-white/5 border border-white/10 text-text-primary px-6 py-3 rounded-xl font-medium hover:bg-white/10 active:scale-95 transition-all text-sm w-full sm:w-auto text-center min-h-[44px]">
                Bekor qilish
              </button>
            )}
          </div>
        </form>
      </div>

      {/* Seasons Table */}
      <div className="metric-card rounded-2xl overflow-hidden shadow-xl">
        <div className="p-4 sm:p-5 border-b border-white/5 bg-[#1a0908]/80 flex items-center justify-between">
          <h3 className="font-display font-bold text-base sm:text-lg text-text-primary">Mavjud mavsumlar ({seasons.length})</h3>
        </div>

        {seasons.length > 0 ? (
          <div className="overflow-x-auto custom-scrollbar">
            <table className="min-w-[650px] w-full text-left border-collapse">
              <thead className="bg-surface-container-lowest border-b border-white/10">
                <tr>
                  <th className="px-4 sm:px-6 py-3.5 text-xs font-semibold text-text-secondary uppercase tracking-wider">Mavsum</th>
                  <th className="px-4 sm:px-6 py-3.5 text-xs font-semibold text-text-secondary uppercase tracking-wider">Qismlar soni</th>
                  <th className="px-4 sm:px-6 py-3.5 text-xs font-semibold text-text-secondary uppercase tracking-wider">Tavsif</th>
                  <th className="px-4 sm:px-6 py-3.5 text-right text-xs font-semibold text-text-secondary uppercase tracking-wider">Amallar</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 text-sm">
                {seasons.map((s) => (
                  <tr key={s.id} className="data-table-row">
                    <td className="px-4 sm:px-6 py-4 whitespace-nowrap">
                      <div className="font-bold text-primary-container text-base">{s.season_number}-mavsum</div>
                      {s.title && <div className="text-xs text-text-secondary">{s.title}</div>}
                      <div className={`text-xs mt-1 font-medium ${s.status === 'completed' ? 'text-green-400' : 'text-yellow-400'}`}>
                        {s.status === 'completed' ? '✅ Tugallangan' : '🔄 Davom etmoqda'}
                      </div>
                    </td>
                    <td className="px-4 sm:px-6 py-4 whitespace-nowrap text-xs sm:text-sm text-text-secondary font-mono">
                      {s.episode_count ? `${s.episode_count} ta qism` : "-"}
                    </td>
                    <td className="px-4 sm:px-6 py-4 text-xs sm:text-sm text-text-secondary max-w-xs truncate">
                      {s.description || "-"}
                    </td>
                    <td className="px-4 sm:px-6 py-4 whitespace-nowrap text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Link
                          href={`/series/${seriesId}/seasons/${s.id}`}
                          className="text-xs font-bold bg-white/5 border border-white/10 hover:border-white/30 text-text-primary px-3 py-1.5 rounded-lg transition-all min-h-[32px] inline-flex items-center gap-1"
                        >
                          <span className="material-symbols-outlined text-[16px]">play_circle</span>
                          Qismlar
                        </Link>
                        <button onClick={() => handleEdit(s)} className="text-xs bg-white/5 border border-white/10 hover:bg-white/15 text-text-primary px-3 py-1.5 rounded-lg transition-colors min-h-[32px]">
                          Tahrir
                        </button>
                        <button onClick={() => handleDelete(s.id)} className="text-xs bg-red-500/10 border border-red-500/20 hover:bg-red-500/20 text-red-400 px-3 py-1.5 rounded-lg transition-colors min-h-[32px]">
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
            Hali hech qanday mavsum qo'shilmagan.
          </div>
        )}
      </div>
    </div>
  );
}
