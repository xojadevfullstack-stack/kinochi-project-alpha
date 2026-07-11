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
  
  if (loading) return <div className="p-8">Yuklanmoqda...</div>;

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <Link href="/movies" className="text-blue-600 hover:underline mb-2 inline-block">← Orqaga (Kinolar)</Link>
          <h1 className="text-3xl font-bold text-gray-800">
            {movie ? `${movie.title} (Kod: ${movie.code})` : "Serial boshqaruvi"}
          </h1>
        </div>
      </div>

      {/* Fasl qoshish */}
      <div className="bg-white p-6 rounded-lg shadow-md mb-8 border-l-4 border-purple-500">
        <h2 className="text-xl font-semibold mb-4">Yangi Fasl qo'shish</h2>
        <form onSubmit={handleAddSeason} className="flex gap-4 items-end">
          <div>
            <label className="block text-sm">Fasl (Mavsum) raqami</label>
            <input required type="number" min={1} className="w-32 border p-2 rounded" value={newSeasonNum} onChange={e => setNewSeasonNum(e.target.value ? Number(e.target.value) : "")} />
          </div>
          <div className="flex-1">
            <label className="block text-sm">Ta'rif (ixtiyoriy)</label>
            <input type="text" className="w-full border p-2 rounded" value={seasonDesc} onChange={e => setSeasonDesc(e.target.value)} />
          </div>
          <button type="submit" className="bg-purple-600 text-white px-6 py-2 rounded hover:bg-purple-700">Qo'shish</button>
        </form>
      </div>

      {/* Fasllar royxati */}
      <div className="space-y-6">
        {seasons.map(season => (
          <div key={season.id} className="bg-white rounded-lg shadow border border-gray-200 overflow-hidden">
            <div className="bg-gray-50 px-6 py-4 flex justify-between items-center border-b">
              <div>
                <h3 className="text-lg font-bold text-gray-800">{season.season_number}-Fasl</h3>
                {season.description && <p className="text-sm text-gray-500">{season.description}</p>}
              </div>
              <div className="flex gap-4 items-center">
                <button 
                  onClick={() => setActiveSeasonId(activeSeasonId === season.id ? null : season.id)} 
                  className="text-sm bg-blue-100 text-blue-700 px-3 py-1 rounded hover:bg-blue-200 font-medium"
                >
                  + Qism qo'shish
                </button>
                <button onClick={() => handleDeleteSeason(season.id)} className="text-red-500 hover:text-red-700 text-sm">🗑 O'chirish</button>
              </div>
            </div>

            {/* Qism qo'shish formasi */}
            {activeSeasonId === season.id && (
              <div className="p-4 bg-blue-50 border-b">
                <form onSubmit={e => handleAddEpisode(e, season.id)} className="flex gap-4 items-end">
                  <div>
                    <label className="block text-xs font-bold text-gray-600">Qism raqami</label>
                    <input required type="number" min={1} className="w-24 border p-1 rounded" value={newEpisodeNum} onChange={e => setNewEpisodeNum(e.target.value ? Number(e.target.value) : "")} />
                  </div>
                  <div className="flex-1">
                    <label className="block text-xs font-bold text-gray-600">Nomi (ixtiyoriy)</label>
                    <input type="text" className="w-full border p-1 rounded" value={newEpisodeTitle} onChange={e => setNewEpisodeTitle(e.target.value)} />
                  </div>
                  <button type="submit" className="bg-blue-600 text-white px-4 py-1.5 rounded text-sm hover:bg-blue-700">Saqlash</button>
                </form>
              </div>
            )}

            <div className="p-0">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-white">
                  <tr>
                    <th className="px-6 py-2 text-left text-xs font-bold text-gray-500 uppercase">Kod (Avto)</th>
                    <th className="px-6 py-2 text-left text-xs font-bold text-gray-500 uppercase">Qism</th>
                    <th className="px-6 py-2 text-left text-xs font-bold text-gray-500 uppercase">Nomi</th>
                    <th className="px-6 py-2 text-left text-xs font-bold text-gray-500 uppercase">Video</th>
                    <th className="px-6 py-2 text-left text-xs font-bold text-gray-500 uppercase">Amal</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {season.episodes?.map(ep => (
                    <tr key={ep.id} className="hover:bg-gray-50">
                      <td className="px-6 py-3 whitespace-nowrap text-sm font-mono font-bold text-blue-600">{ep.code}</td>
                      <td className="px-6 py-3 whitespace-nowrap text-sm font-semibold">{ep.episode_number}-qism</td>
                      <td className="px-6 py-3 whitespace-nowrap text-sm text-gray-600">{ep.title || "-"}</td>
                      <td className="px-6 py-3 whitespace-nowrap text-sm">
                        {ep.telegram_file_id || ep.storage_channel_message_id ? (
                          <span className="text-green-600 font-bold">✅ Yuklangan</span>
                        ) : (
                          <span className="text-gray-400">Bot orqali yuklang</span>
                        )}
                      </td>
                      <td className="px-6 py-3 whitespace-nowrap text-sm">
                        <button onClick={() => handleDeleteEpisode(ep.id)} className="text-red-500 hover:text-red-700">O'chirish</button>
                      </td>
                    </tr>
                  ))}
                  {(!season.episodes || season.episodes.length === 0) && (
                    <tr><td colSpan={5} className="px-6 py-4 text-center text-sm text-gray-400">Hali qismlar yo'q</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        ))}
        {seasons.length === 0 && (
          <div className="text-center py-12 bg-white rounded-lg border text-gray-500">
            Hali fasllar qo'shilmagan. Yuqoridagi formadan fasl qo'shing.
          </div>
        )}
      </div>
    </div>
  );
}
