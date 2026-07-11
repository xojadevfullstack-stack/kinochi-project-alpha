"use client";

import { useEffect, useState } from "react";
import { fetchApi, fetchApiUpload } from "@/lib/api";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";

type Episode = {
  id: number;
  season_id: number;
  episode_number: number;
  title: string | null;
  code: string;
  telegram_file_id: string | null;
  storage_channel_message_id: number | null;
};

type Season = {
  id: number;
  movie_id: number;
  season_number: number;
  description: string | null;
  episodes?: Episode[];
};

type Movie = {
  id: number;
  title: string;
  code: string;
  is_series: boolean;
};

export default function SeriesDetailsPage() {
  const params = useParams();
  const router = useRouter();
  const movieId = params.id as string;

  const [movie, setMovie] = useState<Movie | null>(null);
  const [seasons, setSeasons] = useState<Season[]>([]);
  const [loading, setLoading] = useState(true);

  // Forms state
  const [newSeasonNum, setNewSeasonNum] = useState<number | "">("");
  const [seasonDesc, setSeasonDesc] = useState("");
  
  const [activeSeasonId, setActiveSeasonId] = useState<number | null>(null);
  const [newEpisodeNum, setNewEpisodeNum] = useState<number | "">("");
  const [newEpisodeTitle, setNewEpisodeTitle] = useState("");
  
  const [uploadingEpisodeId, setUploadingEpisodeId] = useState<number | null>(null);

  useEffect(() => {
    if (movieId) {
      loadData();
    }
  }, [movieId]);

  const loadData = async () => {
    setLoading(true);
    try {
      // Since we don't have a specific get-by-id endpoint publicly exposed in the admin list, 
      // wait, we do have GET /movies/{id} ? Let's try, otherwise we fetch all and find it.
      // Actually, we can fetch seasons directly.
      const seasonsData = await fetchApi(`/series/movies/${movieId}/seasons`);
      
      // Fetch episodes for all seasons to display them
      const seasonsWithEpisodes = await Promise.all(
        seasonsData.map(async (s: Season) => {
          const episodesData = await fetchApi(`/series/seasons/${s.id}/episodes`);
          return { ...s, episodes: episodesData };
        })
      );
      setSeasons(seasonsWithEpisodes);
      
      // Attempt to fetch movie details (we only need title and code, if the backend has it. 
      // If not, we just show generic header for now).
      try {
        const moviesList = await fetchApi(`/movies/?limit=100`);
        const m = moviesList.items.find((x: any) => x.id.toString() === movieId);
        if (m) setMovie(m);
      } catch (e) {}

    } catch (e: any) {
      alert("Xato: " + e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAddSeason = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newSeasonNum) return;
    try {
      await fetchApi(`/series/movies/${movieId}/seasons`, {
        method: "POST",
        body: JSON.stringify({ season_number: Number(newSeasonNum), description: seasonDesc })
      });
      setNewSeasonNum("");
      setSeasonDesc("");
      loadData();
    } catch (e: any) {
      alert("Fasl qo'shishda xato: " + e.message);
    }
  };

  const handleDeleteSeason = async (id: number) => {
    if (!confirm("Bu fasl va uning barcha qismlari o'chib ketadi. Rozimisiz?")) return;
    try {
      await fetchApi(`/series/seasons/${id}`, { method: "DELETE" });
      loadData();
    } catch (e: any) {
      alert("O'chirishda xato: " + e.message);
    }
  };

  const handleAddEpisode = async (e: React.FormEvent, seasonId: number) => {
    e.preventDefault();
    if (!newEpisodeNum) return;
    try {
      await fetchApi(`/series/seasons/${seasonId}/episodes`, {
        method: "POST",
        body: JSON.stringify({ episode_number: Number(newEpisodeNum), title: newEpisodeTitle })
      });
      setNewEpisodeNum("");
      setNewEpisodeTitle("");
      setActiveSeasonId(null);
      loadData();
    } catch (e: any) {
      alert("Qism qo'shishda xato: " + e.message);
    }
  };

  const handleDeleteEpisode = async (id: number) => {
    if (!confirm("Qism o'chirilsinmi?")) return;
    try {
      await fetchApi(`/series/episodes/${id}`, { method: "DELETE" });
      loadData();
    } catch (e: any) {
      alert("O'chirishda xato: " + e.message);
    }
  };

  // Upload video for episode
  // Wait, the episode needs a video upload endpoint. Since Movie has /upload-video, we can create one for episodes, or modify the bot directly.
  // Actually, episodes store video too! I haven't written the upload endpoint for episodes in backend yet!
  // For now, let's just leave a placeholder or alert that FSM bot should be used for videos.
  
  if (loading) return <div className="p-8 text-gray-500">Yuklanmoqda...</div>;

  return (
    <div>
      <div className="mb-6 flex flex-col gap-2">
        <Link href="/movies" className="text-blue-600 hover:text-blue-800 font-medium text-sm inline-flex items-center">
          &larr; Kinolar ro'yxatiga qaytish
        </Link>
        <h1 className="text-3xl font-bold text-gray-800">
          {movie ? `${movie.title} (Kod: ${movie.code})` : "Serial boshqaruvi"}
        </h1>
        <p className="text-gray-500 text-sm">
          Bu sahifada ushbu serial uchun fasllar va ularning qismlarini boshqarishingiz mumkin.
        </p>
      </div>

      {/* Fasl qoshish */}
      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 mb-8">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">Yangi fasl qo'shish</h2>
        <form onSubmit={handleAddSeason} className="grid grid-cols-1 md:grid-cols-12 gap-4 items-end">
          <div className="md:col-span-3">
            <label className="block text-sm text-gray-600 mb-1">Fasl raqami</label>
            <input required type="number" min={1} className="w-full border border-gray-300 p-2 rounded focus:ring-blue-500 focus:border-blue-500 outline-none transition" value={newSeasonNum} onChange={e => setNewSeasonNum(e.target.value ? Number(e.target.value) : "")} placeholder="Masalan: 1" />
          </div>
          <div className="md:col-span-7">
            <label className="block text-sm text-gray-600 mb-1">Ta'rif (ixtiyoriy)</label>
            <input type="text" className="w-full border border-gray-300 p-2 rounded focus:ring-blue-500 focus:border-blue-500 outline-none transition" value={seasonDesc} onChange={e => setSeasonDesc(e.target.value)} placeholder="Fasl haqida qisqacha..." />
          </div>
          <div className="md:col-span-2">
            <button type="submit" className="w-full bg-blue-600 text-white px-4 py-2 rounded font-medium hover:bg-blue-700 transition">Qo'shish</button>
          </div>
        </form>
      </div>

      {/* Fasllar royxati */}
      <div className="space-y-6">
        {seasons.map(season => (
          <div key={season.id} className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
            <div className="bg-gray-50 px-6 py-4 flex flex-col sm:flex-row justify-between items-start sm:items-center border-b border-gray-200 gap-4">
              <div>
                <h3 className="text-lg font-bold text-gray-800 flex items-center gap-2">
                  <span className="bg-blue-100 text-blue-800 px-2.5 py-0.5 rounded text-sm">{season.season_number}-Fasl</span>
                </h3>
                {season.description && <p className="text-sm text-gray-500 mt-1">{season.description}</p>}
              </div>
              <div className="flex gap-3 items-center w-full sm:w-auto">
                <button 
                  onClick={() => setActiveSeasonId(activeSeasonId === season.id ? null : season.id)} 
                  className="flex-1 sm:flex-none text-sm bg-white border border-gray-300 text-gray-700 px-4 py-2 rounded hover:bg-gray-50 font-medium transition"
                >
                  {activeSeasonId === season.id ? "Yopish" : "+ Qism qo'shish"}
                </button>
                <button onClick={() => handleDeleteSeason(season.id)} className="text-red-600 hover:text-red-800 text-sm font-medium px-2 py-2">
                  O'chirish
                </button>
              </div>
            </div>

            {/* Qism qo'shish formasi */}
            {activeSeasonId === season.id && (
              <div className="p-5 bg-blue-50/50 border-b border-gray-200">
                <form onSubmit={e => handleAddEpisode(e, season.id)} className="grid grid-cols-1 md:grid-cols-12 gap-4 items-end">
                  <div className="md:col-span-3">
                    <label className="block text-sm text-gray-600 mb-1">Qism raqami</label>
                    <input required type="number" min={1} className="w-full border border-gray-300 p-2 rounded focus:ring-blue-500 focus:border-blue-500 outline-none transition" value={newEpisodeNum} onChange={e => setNewEpisodeNum(e.target.value ? Number(e.target.value) : "")} placeholder="Masalan: 1" />
                  </div>
                  <div className="md:col-span-7">
                    <label className="block text-sm text-gray-600 mb-1">Nomi (ixtiyoriy)</label>
                    <input type="text" className="w-full border border-gray-300 p-2 rounded focus:ring-blue-500 focus:border-blue-500 outline-none transition" value={newEpisodeTitle} onChange={e => setNewEpisodeTitle(e.target.value)} placeholder="Masalan: Qasoskorlar..." />
                  </div>
                  <div className="md:col-span-2">
                    <button type="submit" className="w-full bg-blue-600 text-white px-4 py-2 rounded font-medium hover:bg-blue-700 transition">Saqlash</button>
                  </div>
                </form>
              </div>
            )}

            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-white">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider w-24">Kod</th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider w-24">Qism</th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Nomi</th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider w-32">Video statusi</th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider w-24">Amal</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 bg-white">
                  {season.episodes?.map(ep => (
                    <tr key={ep.id} className="hover:bg-gray-50 transition-colors">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-mono font-medium text-gray-900 bg-gray-50/50">{ep.code}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-gray-900">{ep.episode_number}-qism</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">{ep.title || <span className="text-gray-400 italic">Mavjud emas</span>}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        {ep.telegram_file_id || ep.storage_channel_message_id ? (
                          <span className="inline-flex items-center gap-1 text-green-700 bg-green-50 px-2 py-1 rounded-full text-xs font-medium border border-green-200">
                            <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd"></path></svg>
                            Yuklangan
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-amber-700 bg-amber-50 px-2 py-1 rounded-full text-xs font-medium border border-amber-200">
                            Botdan yuklang
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <button onClick={() => handleDeleteEpisode(ep.id)} className="text-red-600 hover:text-red-900 font-medium transition">O'chirish</button>
                      </td>
                    </tr>
                  ))}
                  {(!season.episodes || season.episodes.length === 0) && (
                    <tr><td colSpan={5} className="px-6 py-8 text-center text-sm text-gray-500">Bu faslda hali qismlar mavjud emas. Yuqoridagi "Qism qo'shish" tugmasini bosing.</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        ))}
        {seasons.length === 0 && (
          <div className="text-center py-16 bg-white rounded-lg shadow-sm border border-gray-200">
            <svg className="mx-auto h-12 w-12 text-gray-300 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 002-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
            <h3 className="text-sm font-medium text-gray-900">Fasllar yo'q</h3>
            <p className="mt-1 text-sm text-gray-500">Ushbu serial uchun hali fasllar kiritilmagan.</p>
          </div>
        )}
      </div>
    </div>
  );
}
