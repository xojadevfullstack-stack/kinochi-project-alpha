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

type Source = {
  id: number;
  name: string;
  chat_id: number;
  topic_id: number | null;
  type: string;
};

type Series = {
  id: number;
  title: string;
  source_id?: number | null;
  source?: Source | null;
};

export default function SeasonsListPage() {
  const params = useParams();
  const router = useRouter();
  const seriesId = params.seriesId as string;

  const [series, setSeries] = useState<Series | null>(null);
  const [seasons, setSeasons] = useState<Season[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState<number | null>(null);

  const [announceInTopic, setAnnounceInTopic] = useState(true);
  const [announcingSeasonId, setAnnouncingSeasonId] = useState<number | null>(null);
  const [openingTopic, setOpeningTopic] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

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
      setSeasons(seasonsData || []);

      if (seasonsData && seasonsData.length > 0) {
        const nextNum =
          Math.max(...seasonsData.map((s: Season) => s.season_number)) + 1;
        if (!editingId) setForm((f) => ({ ...f, season_number: nextNum }));
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
    setErrorMsg(null);
    setSuccessMsg(null);
    try {
      if (editingId) {
        await fetchApi(`/series/seasons/${editingId}`, {
          method: "PUT",
          body: JSON.stringify({
            season_number: form.season_number,
            title: form.title || null,
            description: form.description || null,
            poster_url: form.poster_url || null,
            episode_count: form.episode_count
              ? parseInt(form.episode_count as string)
              : null,
            status: form.status,
          }),
        });
        setSuccessMsg("Mavsum muvaffaqiyatli tahrirlandi!");
      } else {
        const queryParam = announceInTopic ? "?announce_in_topic=true" : "";
        await fetchApi(`/series/${seriesId}/seasons${queryParam}`, {
          method: "POST",
          body: JSON.stringify({
            ...form,
            episode_count: form.episode_count
              ? parseInt(form.episode_count as string)
              : null,
            status: form.status,
          }),
        });
        setSuccessMsg(
          announceInTopic && series?.source?.topic_id
            ? `${form.season_number}-fasl yaratildi va Telegram topicga ajratgich xabari yuborildi!`
            : `${form.season_number}-fasl muvaffaqiyatli yaratildi!`
        );
      }
      handleCancel();
      loadData();
    } catch (e: any) {
      setErrorMsg("Saqlashda xato: " + e.message);
    }
  };

  const handleAnnounceSeason = async (seasonId: number, seasonNumber: number) => {
    if (!series?.source?.topic_id) {
      alert("Bu serial uchun Telegram topic biriktirilmagan.");
      return;
    }
    setAnnouncingSeasonId(seasonId);
    setErrorMsg(null);
    setSuccessMsg(null);
    try {
      const res = await fetchApi(
        `/series/${seriesId}/seasons/${seasonId}/announce`,
        { method: "POST" }
      );
      setSuccessMsg(
        res.message || `${seasonNumber}-fasl ajratgichi Telegram topicga yuborildi!`
      );
    } catch (err: any) {
      setErrorMsg("Ajratgich yuborishda xatolik: " + err.message);
    } finally {
      setAnnouncingSeasonId(null);
    }
  };

  const handleOpenTopic = async () => {
    setOpeningTopic(true);
    setErrorMsg(null);
    setSuccessMsg(null);
    try {
      const res = await fetchApi(`/series/${seriesId}/open-topic`, {
        method: "POST",
      });
      setSuccessMsg(res.message || "Topic muvaffaqiyatli ochildi!");
      await loadData();
    } catch (err: any) {
      setErrorMsg("Topic ochishda xatolik: " + err.message);
    } finally {
      setOpeningTopic(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (
      !confirm(
        "Ushbu mavsumni o'chirasizmi? (Uning barcha qismlari ham o'chib ketadi!)"
      )
    )
      return;
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
    setErrorMsg(null);
    const nextNum =
      seasons.length > 0
        ? Math.max(...seasons.map((s: Season) => s.season_number)) + 1
        : 1;
    setForm({
      series_id: parseInt(seriesId),
      season_number: nextNum,
      title: "",
      description: "",
      poster_url: "",
      episode_count: "",
      status: "ongoing",
    });
  };

  // Determine active incoming season for auto_indexer
  const getActiveSeasonId = () => {
    if (!seasons || seasons.length === 0) return null;
    const ongoing = seasons.filter((s) => s.status === "ongoing");
    if (ongoing.length > 0) return ongoing[ongoing.length - 1].id;
    return seasons[seasons.length - 1].id;
  };

  const activeSeasonId = getActiveSeasonId();

  if (loading)
    return <div className="p-8 text-center text-text-secondary">Yuklanmoqda...</div>;

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto">
      {/* Breadcrumb */}
      <nav
        className="flex text-xs sm:text-sm text-text-secondary mb-4 sm:mb-6"
        aria-label="Breadcrumb"
      >
        <ol className="inline-flex items-center space-x-1 sm:space-x-2">
          <li className="inline-flex items-center">
            <Link
              href="/series"
              className="hover:text-white transition flex items-center gap-1"
            >
              <span className="material-symbols-outlined text-base">arrow_back</span>
              Seriallar
            </Link>
          </li>
          <li>
            <div className="flex items-center">
              <span className="mx-1 text-white/30">/</span>
              <span className="text-text-primary font-medium truncate max-w-[200px]">
                {series?.title}
              </span>
            </div>
          </li>
        </ol>
      </nav>

      {/* Header & Topic Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-text-primary tracking-tight">
            {series?.title} — Fasllar
          </h1>
          <p className="text-xs sm:text-sm text-text-secondary mt-1">
            Fasllar, qismlar va Telegram forum topic ajratgichlarini boshqarish
          </p>
        </div>

        {/* Topic status header badge */}
        <div>
          {series?.source?.topic_id ? (
            <div className="inline-flex items-center gap-2 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 px-3.5 py-1.5 rounded-xl text-xs sm:text-sm font-medium">
              <span className="material-symbols-outlined text-base">forum</span>
              <span>Topic #{series.source.topic_id} ulangan</span>
            </div>
          ) : (
            <button
              type="button"
              onClick={handleOpenTopic}
              disabled={openingTopic}
              className="inline-flex items-center gap-1.5 bg-sky-500/20 hover:bg-sky-500/30 border border-sky-500/40 text-sky-300 px-3.5 py-2 rounded-xl text-xs sm:text-sm font-medium transition-all"
            >
              {openingTopic ? (
                <span className="animate-spin material-symbols-outlined text-base">
                  progress_activity
                </span>
              ) : (
                <span className="material-symbols-outlined text-base">add_comment</span>
              )}
              <span>Telegram'da Topic ochish</span>
            </button>
          )}
        </div>
      </div>

      {/* Notifications */}
      {successMsg && (
        <div className="mb-6 p-4 bg-emerald-500/15 border border-emerald-500/30 rounded-2xl text-xs sm:text-sm text-emerald-300 flex items-center justify-between animate-fadeIn">
          <div className="flex items-center gap-2.5">
            <span className="material-symbols-outlined text-emerald-400">check_circle</span>
            <span>{successMsg}</span>
          </div>
          <button
            onClick={() => setSuccessMsg(null)}
            className="text-emerald-400 hover:text-emerald-200 p-1"
          >
            ✕
          </button>
        </div>
      )}

      {errorMsg && (
        <div className="mb-6 p-4 bg-red-500/15 border border-red-500/30 rounded-2xl text-xs sm:text-sm text-red-300 flex items-center justify-between animate-fadeIn">
          <div className="flex items-center gap-2.5">
            <span className="material-symbols-outlined text-red-400">error</span>
            <span>{errorMsg}</span>
          </div>
          <button
            onClick={() => setErrorMsg(null)}
            className="text-red-400 hover:text-red-200 p-1"
          >
            ✕
          </button>
        </div>
      )}

      {/* Form Card */}
      <div className="metric-card p-4 sm:p-6 rounded-2xl mb-8">
        <h2 className="text-lg sm:text-xl font-semibold mb-4 text-text-primary flex items-center gap-2">
          <span className="material-symbols-outlined text-primary-container">
            {editingId ? "edit" : "add_circle"}
          </span>
          {editingId ? "Faslni tahrirlash" : "Yangi fasl qo'shish"}
        </h2>
        <form
          onSubmit={handleSubmit}
          className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 sm:gap-4"
        >
          <div>
            <label className="block text-xs sm:text-sm font-medium text-text-secondary mb-1">
              Fasl raqami
            </label>
            <input
              type="number"
              min="1"
              value={form.season_number}
              onChange={(e) =>
                setForm({ ...form, season_number: parseInt(e.target.value) || 1 })
              }
              className="w-full bg-surface-container-lowest border border-white/10 rounded-xl p-3 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container text-sm"
              required
            />
          </div>
          <div>
            <label className="block text-xs sm:text-sm font-medium text-text-secondary mb-1">
              Qismlar soni (taxminiy yoki aniq)
            </label>
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
            <label className="block text-xs sm:text-sm font-medium text-text-secondary mb-1">
              Maxsus nom (ixtiyoriy)
            </label>
            <input
              type="text"
              placeholder="Masalan: Maxfiy topshiriq"
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              className="w-full bg-surface-container-lowest border border-white/10 rounded-xl p-3 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container text-sm"
            />
          </div>

          <div className="sm:col-span-2 md:col-span-3">
            <label className="block text-xs sm:text-sm font-medium text-text-secondary mb-1">
              Status (Holati)
            </label>
            <select
              value={form.status}
              onChange={(e) => setForm({ ...form, status: e.target.value })}
              className="w-full bg-surface-container-lowest border border-white/10 rounded-xl p-3 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container text-sm"
            >
              <option value="ongoing">Davom etmoqda (yangi videolar qabul qiladi)</option>
              <option value="completed">Tugallangan</option>
            </select>
          </div>

          <div className="sm:col-span-2 md:col-span-3">
            <label className="block text-xs sm:text-sm font-medium text-text-secondary mb-1">
              Tavsif (ixtiyoriy)
            </label>
            <textarea
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              className="w-full bg-surface-container-lowest border border-white/10 rounded-xl p-3 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container text-sm"
              rows={2}
            />
          </div>

          <div className="sm:col-span-2 md:col-span-3">
            <label className="block text-xs sm:text-sm font-medium text-text-secondary mb-1">
              Poster URL (rasm havolasi)
            </label>
            <input
              type="text"
              placeholder="https://..."
              value={form.poster_url}
              onChange={(e) => setForm({ ...form, poster_url: e.target.value })}
              className="w-full bg-surface-container-lowest border border-white/10 rounded-xl p-3 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container text-sm"
            />
          </div>

          {/* Telegram Topic Announce Checkbox (for new seasons) */}
          {!editingId && (
            <div className="sm:col-span-2 md:col-span-3 bg-surface-container-high/40 border border-white/10 rounded-xl p-3.5">
              <label className="flex items-start gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={announceInTopic}
                  onChange={(e) => setAnnounceInTopic(e.target.checked)}
                  className="mt-0.5 w-4 h-4 rounded border-white/10 bg-surface-container-lowest focus:ring-primary-container text-primary-container"
                />
                <div>
                  <div className="text-sm font-medium text-text-primary flex items-center gap-1.5">
                    <span>
                      Telegram topicga &apos;{form.season_number}-FASL&apos; ajratgich xabari
                      yuborilsin
                    </span>
                    <span className="text-xs bg-emerald-500/20 text-emerald-400 px-2 py-0.5 rounded-full border border-emerald-500/30">
                      Tavsiya etiladi
                    </span>
                  </div>
                  <p className="text-xs text-text-secondary mt-0.5">
                    Yangi fasl ochilganda bot Telegram guruhidagi ushbu serial topiciga
                    chiroyli ajratgich bannerini yuboradi. Shu yozuvdan keyin yuborilgan
                    videolar {form.season_number}-faslga avtomatik biriktiriladi.
                  </p>
                </div>
              </label>
            </div>
          )}

          <div className="sm:col-span-2 md:col-span-3 flex flex-col sm:flex-row gap-3 pt-2">
            <button
              type="submit"
              className="bg-primary-container text-white px-6 py-3 rounded-xl font-medium hover:scale-[1.02] active:scale-95 transition-all text-sm w-full sm:w-auto text-center min-h-[44px]"
            >
              {editingId ? "O'zgarishlarni saqlash" : "Faslni saqlash"}
            </button>
            {editingId && (
              <button
                type="button"
                onClick={handleCancel}
                className="bg-white/5 border border-white/10 text-text-primary px-6 py-3 rounded-xl font-medium hover:bg-white/10 active:scale-95 transition-all text-sm w-full sm:w-auto text-center min-h-[44px]"
              >
                Bekor qilish
              </button>
            )}
          </div>
        </form>
      </div>

      {/* Seasons Table */}
      <div className="metric-card rounded-2xl overflow-hidden shadow-xl">
        <div className="p-4 sm:p-5 border-b border-white/5 bg-[#1a0908]/80 flex items-center justify-between">
          <h3 className="font-display font-bold text-base sm:text-lg text-text-primary">
            Mavjud fasllar ({seasons.length})
          </h3>
        </div>

        {seasons.length > 0 ? (
          <div className="overflow-x-auto custom-scrollbar">
            <table className="min-w-[700px] w-full text-left border-collapse">
              <thead className="bg-surface-container-lowest border-b border-white/10">
                <tr>
                  <th className="px-4 sm:px-6 py-3.5 text-xs font-semibold text-text-secondary uppercase tracking-wider">
                    Fasl
                  </th>
                  <th className="px-4 sm:px-6 py-3.5 text-xs font-semibold text-text-secondary uppercase tracking-wider">
                    Qismlar soni
                  </th>
                  <th className="px-4 sm:px-6 py-3.5 text-xs font-semibold text-text-secondary uppercase tracking-wider">
                    Tavsif
                  </th>
                  <th className="px-4 sm:px-6 py-3.5 text-right text-xs font-semibold text-text-secondary uppercase tracking-wider">
                    Amallar
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 text-sm">
                {seasons.map((s) => {
                  const isActive = s.id === activeSeasonId;
                  return (
                    <tr key={s.id} className="data-table-row">
                      <td className="px-4 sm:px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-primary-container text-base">
                            {s.season_number}-fasl
                          </span>
                          {isActive && (
                            <span className="text-[11px] bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 px-2 py-0.5 rounded-full font-medium flex items-center gap-1">
                              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                              Hozir videolar shu faslga tushadi
                            </span>
                          )}
                        </div>
                        {s.title && (
                          <div className="text-xs text-text-secondary">{s.title}</div>
                        )}
                        <div
                          className={`text-xs mt-1 font-medium ${
                            s.status === "completed"
                              ? "text-green-400"
                              : "text-yellow-400"
                          }`}
                        >
                          {s.status === "completed"
                            ? "✅ Tugallangan"
                            : "🔄 Davom etmoqda"}
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
                          {/* Send Separator to Topic Button */}
                          {series?.source?.topic_id && (
                            <button
                              type="button"
                              onClick={() =>
                                handleAnnounceSeason(s.id, s.season_number)
                              }
                              disabled={announcingSeasonId === s.id}
                              className="text-xs font-medium bg-emerald-500/10 hover:bg-emerald-500/25 border border-emerald-500/30 text-emerald-300 px-2.5 py-1.5 rounded-lg transition-all min-h-[32px] inline-flex items-center gap-1"
                              title="Telegram topicga ajratgich xabari yuborish"
                            >
                              {announcingSeasonId === s.id ? (
                                <span className="animate-spin material-symbols-outlined text-[15px]">
                                  progress_activity
                                </span>
                              ) : (
                                <span className="material-symbols-outlined text-[15px]">
                                  campaign
                                </span>
                              )}
                              <span>Ajratgich</span>
                            </button>
                          )}

                          <Link
                            href={`/series/${seriesId}/seasons/${s.id}`}
                            className="text-xs font-bold bg-white/5 border border-white/10 hover:border-white/30 text-text-primary px-3 py-1.5 rounded-lg transition-all min-h-[32px] inline-flex items-center gap-1"
                          >
                            <span className="material-symbols-outlined text-[16px]">
                              play_circle
                            </span>
                            Qismlar
                          </Link>
                          <button
                            onClick={() => handleEdit(s)}
                            className="text-xs bg-white/5 border border-white/10 hover:bg-white/15 text-text-primary px-3 py-1.5 rounded-lg transition-colors min-h-[32px]"
                          >
                            Tahrir
                          </button>
                          <button
                            onClick={() => handleDelete(s.id)}
                            className="text-xs bg-red-500/10 border border-red-500/20 hover:bg-red-500/20 text-red-400 px-3 py-1.5 rounded-lg transition-colors min-h-[32px]"
                          >
                            O'chirish
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="p-8 sm:p-12 text-center text-text-secondary text-sm">
            Hali hech qanday fasl qo'shilmagan.
          </div>
        )}
      </div>
    </div>
  );
}
