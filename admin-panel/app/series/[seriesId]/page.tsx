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
          description: form.description || null
        }) });
      } else {
        await fetchApi(`/series/${seriesId}/seasons`, { method: "POST", body: JSON.stringify(form) });
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
    });
  };

  const handleCancel = () => {
    setEditingId(null);
    const nextNum = seasons.length > 0 ? Math.max(...seasons.map((s: Season) => s.season_number)) + 1 : 1;
    setForm({ series_id: parseInt(seriesId), season_number: nextNum, title: "", description: "" });
  };

  if (loading) return <div className="p-8 text-center text-gray-500">Yuklanmoqda...</div>;

  return (
    <div className="p-8 max-w-7xl mx-auto">
      {/* Breadcrumb */}
      <nav className="flex text-sm text-gray-500 mb-6" aria-label="Breadcrumb">
        <ol className="inline-flex items-center space-x-1 md:space-x-3">
          <li className="inline-flex items-center">
            <Link href="/series" className="hover:text-blue-600 transition">Seriallar</Link>
          </li>
          <li>
            <div className="flex items-center">
              <span className="mx-2">/</span>
              <span className="text-gray-900 font-medium">{series?.title}</span>
            </div>
          </li>
        </ol>
      </nav>

      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-900">{series?.title} — Mavsumlar</h1>
      </div>

      <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 mb-8">
        <h2 className="text-xl font-semibold mb-4 text-gray-800">
          {editingId ? "Mavsumni tahrirlash" : "Yangi mavsum qo'shish"}
        </h2>
        <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Mavsum raqami</label>
            <input
              type="number"
              min="1"
              value={form.season_number}
              onChange={(e) => setForm({ ...form, season_number: parseInt(e.target.value) || 1 })}
              className="w-full border border-gray-300 rounded-lg p-2.5 focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">Maxsus nom (ixtiyoriy)</label>
            <input
              type="text"
              placeholder="Masalan: Maxfiy topshiriq"
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              className="w-full border border-gray-300 rounded-lg p-2.5 focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div className="md:col-span-3">
            <label className="block text-sm font-medium text-gray-700 mb-1">Tavsif (ixtiyoriy)</label>
            <textarea
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              className="w-full border border-gray-300 rounded-lg p-2.5 focus:ring-2 focus:ring-blue-500"
              rows={2}
            />
          </div>
          
          <div className="md:col-span-3 flex gap-3 pt-2">
            <button type="submit" className="bg-blue-600 text-white px-6 py-2 rounded-lg font-medium hover:bg-blue-700 transition">
              Saqlash
            </button>
            {editingId && (
              <button type="button" onClick={handleCancel} className="bg-gray-100 text-gray-700 px-6 py-2 rounded-lg font-medium hover:bg-gray-200 transition">
                Bekor qilish
              </button>
            )}
          </div>
        </form>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        {seasons.length > 0 ? (
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Mavsum</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tavsif</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Amallar</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {seasons.map((s) => (
                <tr key={s.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="font-medium text-gray-900">{s.season_number}-mavsum</div>
                    {s.title && <div className="text-sm text-gray-500">{s.title}</div>}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500 max-w-xs truncate">
                    {s.description || "-"}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <Link
                      href={`/series/${seriesId}/seasons/${s.id}`}
                      className="text-indigo-600 hover:text-indigo-900 bg-indigo-50 px-3 py-1.5 rounded-lg mr-3 transition"
                    >
                      Qismlar
                    </Link>
                    <button onClick={() => handleEdit(s)} className="text-blue-600 hover:text-blue-900 p-2">Tahrir</button>
                    <button onClick={() => handleDelete(s.id)} className="text-red-600 hover:text-red-900 p-2 ml-2">O'chirish</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="p-12 text-center text-gray-500">
            Hali hech qanday mavsum qo'shilmagan.
          </div>
        )}
      </div>
    </div>
  );
}
