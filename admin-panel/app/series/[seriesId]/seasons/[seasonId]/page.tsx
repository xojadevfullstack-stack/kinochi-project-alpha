"use client";

import { useEffect, useState, useRef } from "react";
import { fetchApi, fetchApiUpload } from "@/lib/api";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";

type Episode = {
  id: number;
  season_id: number;
  episode_number: number;
  title: string | null;
  code: string;
  display_code: string;
  telegram_file_id: string | null;
  storage_channel_message_id: number | null;
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
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const [uploadMethod, setUploadMethod] = useState<"file" | "message">("file");
  const [messageId, setMessageId] = useState<string>("");

  const [form, setForm] = useState({
    season_id: parseInt(seasonId),
    episode_number: 1,
    title: "",
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

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setSelectedFile(e.target.files[0]);
    } else {
      setSelectedFile(null);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingId) {
      if (uploadMethod === "file" && !selectedFile) {
        alert("Iltimos, video faylni tanlang!");
        return;
      }
      if (uploadMethod === "message" && !messageId) {
        alert("Iltimos, xabar ID sini kiriting!");
        return;
      }
    }

    setSaving(true);
    try {
      let currentEpisodeId = editingId;

      // 1. Create or Update Episode Metadata
      if (editingId) {
        await fetchApi(`/series/episodes/${editingId}`, { 
          method: "PUT", 
          body: JSON.stringify({
            episode_number: form.episode_number,
            title: form.title || null
          }) 
        });
      } else {
        const newEpisode = await fetchApi(`/series/seasons/${seasonId}/episodes`, { 
          method: "POST", 
          body: JSON.stringify({
            season_id: form.season_id,
            episode_number: form.episode_number,
            title: form.title || null
          }) 
        });
        currentEpisodeId = newEpisode.id;
      }

      // 2. Upload or Link Video
      if (uploadMethod === "file" && selectedFile && currentEpisodeId) {
        const formData = new FormData();
        formData.append("file", selectedFile);
        
        await fetchApiUpload(`/series/episodes/${currentEpisodeId}/upload-video`, {
          method: "POST",
          body: formData
        });
      } else if (uploadMethod === "message" && messageId && currentEpisodeId) {
        await fetchApi(`/series/episodes/${currentEpisodeId}/link-video`, {
          method: "POST",
          body: JSON.stringify({ message_id: parseInt(messageId) })
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

  const handleEdit = (e: Episode) => {
    setEditingId(e.id);
    setForm({
      season_id: e.season_id,
      episode_number: e.episode_number,
      title: e.title || "",
    });
    setSelectedFile(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const handleCancel = () => {
    setEditingId(null);
    setSelectedFile(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
    
    const nextNum = episodes.length > 0 ? Math.max(...episodes.map((e: Episode) => e.episode_number)) + 1 : 1;
    setForm({ season_id: parseInt(seasonId), episode_number: nextNum, title: "" });
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
              <Link href={`/series/${seriesId}`} className="hover:text-blue-600 transition">{series?.title}</Link>
            </div>
          </li>
          <li>
            <div className="flex items-center">
              <span className="mx-2">/</span>
              <span className="text-gray-900 font-medium">{season?.season_number}-mavsum</span>
            </div>
          </li>
        </ol>
      </nav>

      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-900">
          {series?.title} ({season?.season_number}-mavsum) — Qismlar
        </h1>
      </div>

      <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 mb-8">
        <h2 className="text-xl font-semibold mb-4 text-gray-800">
          {editingId ? "Qismni tahrirlash" : "Yangi qism qo'shish"}
        </h2>
        <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Qism raqami</label>
            <input
              type="number"
              min="1"
              value={form.episode_number}
              onChange={(e) => setForm({ ...form, episode_number: parseInt(e.target.value) || 1 })}
              className="w-full border border-gray-300 rounded-lg p-2.5 focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Maxsus nom (ixtiyoriy)</label>
            <input
              type="text"
              placeholder="Masalan: Uyga qaytish"
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              className="w-full border border-gray-300 rounded-lg p-2.5 focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-2">Video manbasini tanlang</label>
            <div className="flex gap-6 mb-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input 
                  type="radio" 
                  name="uploadMethod" 
                  value="file" 
                  checked={uploadMethod === 'file'} 
                  onChange={() => setUploadMethod('file')}
                  className="w-4 h-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                />
                <span className="text-sm text-gray-700">Komp'yuterdan fayl yuklash</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input 
                  type="radio" 
                  name="uploadMethod" 
                  value="message" 
                  checked={uploadMethod === 'message'} 
                  onChange={() => setUploadMethod('message')}
                  className="w-4 h-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                />
                <span className="text-sm text-gray-700">Kanal xabaridan ID orqali olish</span>
              </label>
            </div>

            {uploadMethod === 'file' ? (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Video fayl {editingId ? "(Faqat videoni o'zgartirish kerak bo'lsa tanlang)" : "(Majburiy)"}
                </label>
                <input
                  type="file"
                  accept="video/*"
                  ref={fileInputRef}
                  onChange={handleFileChange}
                  className="w-full border border-gray-300 rounded-lg p-2.5 focus:ring-2 focus:ring-blue-500"
                />
              </div>
            ) : (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Xabar ID'si (Message ID) {editingId ? "(Faqat videoni o'zgartirish kerak bo'lsa kiritish)" : "(Majburiy)"}
                </label>
                <input
                  type="number"
                  placeholder="Masalan: 12345"
                  value={messageId}
                  onChange={(e) => setMessageId(e.target.value)}
                  className="w-full border border-gray-300 rounded-lg p-2.5 focus:ring-2 focus:ring-blue-500"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Storage kanalidagi video xabarini toping va uning ID'sini (Message ID) kiriting.
                </p>
              </div>
            )}
          </div>
          
          <div className="md:col-span-2 flex gap-3 pt-2">
            <button 
              type="submit" 
              disabled={saving || (uploadMethod === 'message' && !editingId && (!messageId || isNaN(Number(messageId))))}
              className={`px-6 py-2 rounded-lg font-medium transition ${saving || (uploadMethod === 'message' && !editingId && (!messageId || isNaN(Number(messageId)))) ? 'bg-blue-400 text-white cursor-not-allowed' : 'bg-blue-600 text-white hover:bg-blue-700'}`}
            >
              {saving ? "Yuklanmoqda..." : "Saqlash"}
            </button>
            {editingId && (
              <button 
                type="button" 
                onClick={handleCancel}
                disabled={saving}
                className="bg-gray-100 text-gray-700 px-6 py-2 rounded-lg font-medium hover:bg-gray-200 transition"
              >
                Bekor qilish
              </button>
            )}
          </div>
        </form>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        {episodes.length > 0 ? (
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Qism</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Kod / URL</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Video Status</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Amallar</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {episodes.map((e) => (
                <tr key={e.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="font-medium text-gray-900">{e.episode_number}-qism</div>
                    {e.title && <div className="text-sm text-gray-500">{e.title}</div>}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-mono text-gray-900 bg-gray-100 px-2 py-1 rounded inline-block mb-1">
                      {e.code}
                    </div>
                    <div className="text-xs text-gray-500">
                      Display: {e.display_code}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {e.telegram_file_id ? (
                      <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                        Yuklangan
                      </span>
                    ) : (
                      <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-yellow-100 text-yellow-800">
                        Kutilmoqda
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button onClick={() => handleEdit(e)} className="text-blue-600 hover:text-blue-900 p-2">Tahrir</button>
                    <button onClick={() => handleDelete(e.id)} className="text-red-600 hover:text-red-900 p-2 ml-2">O'chirish</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="p-12 text-center text-gray-500">
            Hali hech qanday qism qo'shilmagan.
          </div>
        )}
      </div>
    </div>
  );
}
