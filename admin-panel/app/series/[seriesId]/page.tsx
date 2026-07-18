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
          episode_count: form.episode_count ? parseInt(form.episode_count as string) : null
        }) });
      } else {
        await fetchApi(`/series/${seriesId}/seasons`, { method: "POST", body: JSON.stringify({
          ...form,
          episode_count: form.episode_count ? parseInt(form.episode_count as string) : null
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
      episode_count: s.episode_count?.toString() || "",
    });
  };

  const handleCancel = () => {
    setEditingId(null);
    const nextNum = seasons.length > 0 ? Math.max(...seasons.map((s: Season) => s.season_number)) + 1 : 1;
    setForm({ series_id: parseInt(seriesId), season_number: nextNum, title: "", description: "", poster_url: "", episode_count: "" });
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
              <span className="text-text-primary font-medium">{series?.title}</span>
            </div>
          </li>
        </ol>
      </nav>

      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-text-primary">{series?.title} — Mavsumlar</h1>
      </div>

      <div className="metric-card p-6 rounded-xl mb-8">
        <h2 className="text-xl font-semibold mb-4 text-text-primary">
          {editingId ? "Mavsumni tahrirlash" : "Yangi mavsum qo'shish"}
        </h2>
        <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-1">Mavsum raqami</label>
            <input
              type="number"
              min="1"
              value={form.season_number}
              onChange={(e) => setForm({ ...form, season_number: parseInt(e.target.value) || 1 })}
              className="w-full bg-surface-container-lowest border border-white/10 rounded-lg p-2.5 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-1">Qismlar soni</label>
            <input
              type="number"
              min="1"
              placeholder="Masalan: 12"
              value={form.episode_count}
              onChange={(e) => setForm({ ...form, episode_count: e.target.value })}
              className="w-full bg-surface-container-lowest border border-white/10 rounded-lg p-2.5 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-1">Maxsus nom (ixtiyoriy)</label>
            <input
              type="text"
              placeholder="Masalan: Maxfiy topshiriq"
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              className="w-full bg-surface-container-lowest border border-white/10 rounded-lg p-2.5 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container"
            />
          </div>
          <div className="md:col-span-3">
            <label className="block text-sm font-medium text-text-secondary mb-1">Tavsif (ixtiyoriy)</label>
            <textarea
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              className="w-full bg-surface-container-lowest border border-white/10 rounded-lg p-2.5 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container"
              rows={2}
            />
          </div>
          <div className="md:col-span-3">
            <label className="block text-sm font-medium text-text-secondary mb-1">Poster URL (rasm havolasi)</label>
            <input
              type="text"
              placeholder="https://..."
              value={form.poster_url}
              onChange={(e) => setForm({ ...form, poster_url: e.target.value })}
              className="w-full bg-surface-container-lowest border border-white/10 rounded-lg p-2.5 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container"
            />
          </div>
          
          <div className="md:col-span-3 flex gap-3 pt-2">
            <button type="submit" className="bg-primary-container text-white px-6 py-2.5 rounded-lg font-medium hover:scale-105 transition-all">
              Saqlash
            </button>
            {editingId && (
              <button type="button" onClick={handleCancel} className="bg-white/5 border border-white/10 text-text-primary px-6 py-2.5 rounded-lg font-medium hover:bg-white/10 transition-all">
                Bekor qilish
              </button>
            )}
          </div>
        </form>
      </div>

      <div className="metric-card rounded-xl overflow-hidden">
        {seasons.length > 0 ? (
          <table className="min-w-full">
            <thead className="bg-surface-container-lowest border-b border-white/10">
              <tr>
                <th className="px-6 py-4 text-left text-xs font-semibold text-text-secondary uppercase tracking-wider">Mavsum</th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-text-secondary uppercase tracking-wider">Qismlar soni</th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-text-secondary uppercase tracking-wider">Tavsif</th>
                <th className="px-6 py-4 text-right text-xs font-semibold text-text-secondary uppercase tracking-wider">Amallar</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {seasons.map((s) => (
                <tr key={s.id} className="data-table-row">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="font-bold text-primary-container">{s.season_number}-mavsum</div>
                    {s.title && <div className="text-sm text-text-secondary">{s.title}</div>}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-text-secondary">
                    {s.episode_count ? `${s.episode_count} ta qism` : "-"}
                  </td>
                  <td className="px-6 py-4 text-sm text-text-secondary max-w-xs truncate">
                    {s.description || "-"}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium flex items-center justify-end gap-2">
                    <Link
                      href={`/series/${seriesId}/seasons/${s.id}`}
                      className="text-tertiary-fixed hover:text-white bg-white/5 border border-white/10 px-3 py-1.5 rounded-lg transition-all hover:border-white/30"
                    >
                      Qismlar
                    </Link>
                    <button onClick={() => handleEdit(s)} className="text-text-secondary hover:text-white p-2 transition-colors">Tahrir</button>
                    <button onClick={() => handleDelete(s.id)} className="text-primary-container hover:text-red-400 p-2 transition-colors">O'chirish</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="p-12 text-center text-text-secondary">
            Hali hech qanday mavsum qo'shilmagan.
          </div>
        )}
      </div>
    </div>
  );
}
