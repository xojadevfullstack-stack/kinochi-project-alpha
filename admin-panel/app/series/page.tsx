"use client";

import { useEffect, useState } from "react";
import { fetchApi } from "@/lib/api";
import Link from "next/link";

type Category = { id: number; name: string };
type PageItem = { id: number; title: string };

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
  description: string | null;
  poster_url: string | null;
  trailer_url: string | null;
  imdb_rating: number | null;
  tmdb_id?: number | null;
  release_year: number | null;
  director: string | null;
  cast: string | null;
  created_at: string;
  categories: Category[];
  pages: PageItem[];
  source_id: number | null;
  source: Source | null;
  status: string;
};

export default function SeriesListPage() {
  const [seriesList, setSeriesList] = useState<Series[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [pages, setPages] = useState<PageItem[]>([]);
  const [sources, setSources] = useState<Source[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState<number | null>(null);

  // TMDb states
  const [tmdbSearchQuery, setTmdbSearchQuery] = useState("");
  const [tmdbSearching, setTmdbSearching] = useState(false);
  const [tmdbResults, setTmdbResults] = useState<any[]>([]);
  const [showTmdbResults, setShowTmdbResults] = useState(false);
  const [fetchingTmdbDetails, setFetchingTmdbDetails] = useState(false);
  const [tmdbSeasonsHint, setTmdbSeasonsHint] = useState<string | null>(null);
  const [duplicateWarning, setDuplicateWarning] = useState<{
    exact: any[];
    similar: any[];
  } | null>(null);

  // Telegram topic states
  const [autoOpenTopic, setAutoOpenTopic] = useState(true);
  const [openingTopicId, setOpeningTopicId] = useState<number | null>(null);

  const initialForm = {
    title: "",
    description: "",
    poster_url: "",
    trailer_url: "",
    imdb_rating: 0,
    tmdb_id: null as number | null,
    release_year: new Date().getFullYear(),
    director: "",
    cast: "",
    category_ids: [] as number[],
    page_ids: [] as number[],
    source_id: "" as number | "",
    status: "ongoing" as string,
  };

  const [form, setForm] = useState(initialForm);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([loadSeries(), loadCategories(), loadSources(), loadPages()]).then(() =>
      setLoading(false)
    );
  }, []);

  const loadCategories = async () => {
    try {
      const data = await fetchApi("/categories");
      setCategories(data);
    } catch (e: any) {
      console.error(e);
    }
  };

  const loadSeries = async () => {
    try {
      const data = await fetchApi("/series?limit=100");
      setSeriesList(data.items);
    } catch (e: any) {
      alert("Xato: " + e.message);
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

  const loadSources = async () => {
    try {
      const data = await fetchApi("/sources");
      setSources(data);
    } catch (e: any) {
      console.error(e);
    }
  };

  // TMDb TV Search
  const handleTmdbSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!tmdbSearchQuery.trim()) return;
    setTmdbSearching(true);
    setErrorMsg(null);
    setDuplicateWarning(null);
    try {
      const data = await fetchApi(
        `/content-lookup/search?query=${encodeURIComponent(
          tmdbSearchQuery.trim()
        )}&content_type=tv`
      );
      setTmdbResults(data || []);
      setShowTmdbResults(true);
    } catch (err: any) {
      setErrorMsg("TMDb qidiruvda xatolik: " + err.message);
    } finally {
      setTmdbSearching(false);
    }
  };

  // Select TV from TMDb
  const handleSelectTmdbSeries = async (tvItem: any) => {
    setFetchingTmdbDetails(true);
    setErrorMsg(null);
    setDuplicateWarning(null);
    setTmdbSeasonsHint(null);
    try {
      const details = await fetchApi(`/content-lookup/details/tv/${tvItem.id}`);
      if (details) {
        // Match suggested categories
        const matchedCategoryIds: number[] = [];
        if (Array.isArray(details.suggested_category_ids)) {
          matchedCategoryIds.push(
            ...details.suggested_category_ids.filter((catId: number) =>
              categories.some((c) => c.id === catId)
            )
          );
        }

        if (details.number_of_seasons) {
          setTmdbSeasonsHint(
            `TMDb bo'yicha: ${details.number_of_seasons} ta fasl (${details.number_of_episodes || "?"} qism)`
          );
        }

        setForm((prev) => ({
          ...prev,
          title: details.title || tvItem.title || prev.title,
          description: details.description || prev.description,
          tmdb_id: details.tmdb_id || tvItem.id,
          poster_url: details.poster_url || prev.poster_url,
          trailer_url: details.trailer_url || prev.trailer_url,
          director: details.director || prev.director,
          cast: details.cast || prev.cast,
          release_year: details.release_year || prev.release_year,
          imdb_rating: details.vote_average
            ? Math.round(details.vote_average * 10) / 10
            : prev.imdb_rating,
          category_ids: Array.from(
            new Set([...prev.category_ids, ...matchedCategoryIds])
          ),
        }));

        // Duplicate check
        try {
          const dupRes = await fetchApi(
            `/content-lookup/duplicates?tmdb_id=${tvItem.id}&title=${encodeURIComponent(
              details.title || ""
            )}&original_title=${encodeURIComponent(
              details.original_title || ""
            )}&year=${details.release_year || ""}`
          );
          if (
            dupRes &&
            ((dupRes.exact && dupRes.exact.length > 0) ||
              (dupRes.similar && dupRes.similar.length > 0))
          ) {
            setDuplicateWarning(dupRes);
          }
        } catch (dupErr) {
          console.error("Duplicate check error:", dupErr);
        }
      }
      setShowTmdbResults(false);
    } catch (err: any) {
      setErrorMsg("TMDb ma'lumotlarini olishda xatolik: " + err.message);
    } finally {
      setFetchingTmdbDetails(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setSuccessMsg(null);
    try {
      const payload = {
        ...form,
        source_id: form.source_id === "" ? null : form.source_id,
      };

      if (editingId) {
        await fetchApi(`/series/${editingId}`, {
          method: "PUT",
          body: JSON.stringify(payload),
        });
        setSuccessMsg("Serial muvaffaqiyatli tahrirlandi!");
      } else {
        const created = await fetchApi("/series", {
          method: "POST",
          body: JSON.stringify(payload),
        });

        if (autoOpenTopic && created?.id) {
          try {
            await fetchApi(`/series/${created.id}/open-topic`, { method: "POST" });
            setSuccessMsg(
              `Serial yaratildi va Telegram forumida alohida Topic ochildi! (ID: s_${created.id})`
            );
          } catch (topErr: any) {
            setErrorMsg(
              `Serial yaratildi (ID: s_${created.id}), lekin Telegram'da topic ochilmadi: ${topErr.message}`
            );
          }
        } else {
          setSuccessMsg(`Serial muvaffaqiyatli saqlandi! (ID: s_${created.id})`);
        }
      }
      handleCancel();
      loadSeries();
    } catch (e: any) {
      setErrorMsg(e.message || "Xato yuz berdi");
    }
  };

  const handleOpenTopic = async (seriesId: number) => {
    setOpeningTopicId(seriesId);
    setErrorMsg(null);
    try {
      const res = await fetchApi(`/series/${seriesId}/open-topic`, {
        method: "POST",
      });
      setSuccessMsg(res.message || "Topic muvaffaqiyatli ochildi!");
      loadSeries();
    } catch (e: any) {
      alert("Topic ochishda xatolik: " + e.message);
    } finally {
      setOpeningTopicId(null);
    }
  };

  const handleDelete = async (id: number) => {
    if (
      !confirm(
        "Ushbu serialni o'chirasizmi? (Uning barcha mavsum va qismlari ham o'chib ketadi!)"
      )
    )
      return;
    try {
      await fetchApi(`/series/${id}`, { method: "DELETE" });
      loadSeries();
    } catch (e: any) {
      alert("O'chirishda xato: " + e.message);
    }
  };

  const handleEdit = (s: Series) => {
    setEditingId(s.id);
    setDuplicateWarning(null);
    setTmdbSeasonsHint(null);
    setForm({
      title: s.title,
      description: s.description || "",
      poster_url: s.poster_url || "",
      trailer_url: s.trailer_url || "",
      imdb_rating: s.imdb_rating || 0,
      tmdb_id: s.tmdb_id || null,
      release_year: s.release_year || 2024,
      director: s.director || "",
      cast: s.cast || "",
      category_ids: s.categories.map((c) => c.id),
      page_ids: s.pages ? s.pages.map((p) => p.id) : [],
      source_id: s.source_id || "",
      status: s.status || "ongoing",
    });
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handleCancel = () => {
    setEditingId(null);
    setErrorMsg(null);
    setForm(initialForm);
    setTmdbSearchQuery("");
    setTmdbResults([]);
    setShowTmdbResults(false);
    setDuplicateWarning(null);
    setTmdbSeasonsHint(null);
  };

  const handleCategoryChange = (id: number) => {
    setForm((prev) => {
      const ids = prev.category_ids.includes(id)
        ? prev.category_ids.filter((x) => x !== id)
        : [...prev.category_ids, id];
      return { ...prev, category_ids: ids };
    });
  };

  const handlePageChange = (id: number) => {
    setForm((prev) => {
      const ids = prev.page_ids.includes(id)
        ? prev.page_ids.filter((x) => x !== id)
        : [...prev.page_ids, id];
      return { ...prev, page_ids: ids };
    });
  };

  if (loading)
    return <div className="p-8 text-center text-text-secondary">Yuklanmoqda...</div>;

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-text-primary tracking-tight">
            Seriallar
          </h1>
          <p className="text-xs sm:text-sm text-text-secondary mt-1">
            Seriallar, avtomatik ma'lumotlar, topiclar va fasllarni boshqarish
          </p>
        </div>
      </div>

      {/* Success Notification */}
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

      {/* Form Card */}
      <div className="metric-card p-4 sm:p-6 rounded-2xl mb-8">
        <h2 className="text-lg sm:text-xl font-semibold mb-4 text-text-primary flex items-center gap-2">
          <span className="material-symbols-outlined text-primary-container">
            {editingId ? "edit" : "add_circle"}
          </span>
          {editingId ? "Serialni tahrirlash" : "Yangi Serial qo'shish"}
        </h2>

        {/* TMDb TV Search & Auto-fill Block */}
        {!editingId && (
          <div className="mb-6 bg-surface-container-high/40 border border-primary-container/30 rounded-2xl p-4">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-primary-container text-xl">
                  auto_awesome
                </span>
                <span className="text-sm font-semibold text-text-primary">
                  TMDb orqali serial qidirish va to'ldirish
                </span>
              </div>
              <span className="text-xs text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded-full">
                O'zbekcha tarjima bilan
              </span>
            </div>

            <div className="flex gap-2">
              <div className="relative flex-1">
                <input
                  type="text"
                  className="w-full bg-surface-container-lowest border border-white/10 rounded-xl pl-10 pr-4 py-2.5 text-sm text-text-primary placeholder:text-text-secondary/60 focus:ring-2 focus:ring-primary-container focus:border-primary-container"
                  placeholder="Serial nomi yoki TMDb ID (masalan: Breaking Bad, Chernobyl, 1396)..."
                  value={tmdbSearchQuery}
                  onChange={(e) => setTmdbSearchQuery(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      handleTmdbSearch();
                    }
                  }}
                />
                <span className="material-symbols-outlined absolute left-3 top-2.5 text-text-secondary text-lg">
                  search
                </span>
              </div>
              <button
                type="button"
                onClick={() => handleTmdbSearch()}
                disabled={tmdbSearching || !tmdbSearchQuery.trim()}
                className="bg-primary-container hover:bg-primary-container/80 disabled:opacity-50 text-white px-5 py-2.5 rounded-xl text-sm font-medium transition-all flex items-center gap-1.5 min-h-[40px] shrink-0"
              >
                {tmdbSearching ? (
                  <>
                    <span className="animate-spin material-symbols-outlined text-sm">
                      progress_activity
                    </span>
                    <span>Qidirilmoqda...</span>
                  </>
                ) : (
                  <>
                    <span className="material-symbols-outlined text-sm">travel_explore</span>
                    <span>Qidirish</span>
                  </>
                )}
              </button>
            </div>

            {/* TMDb TV Results */}
            {showTmdbResults && (
              <div className="mt-3 bg-surface-container-lowest border border-white/10 rounded-xl p-2 max-h-72 overflow-y-auto custom-scrollbar">
                <div className="flex items-center justify-between px-2 py-1 mb-1 border-b border-white/5">
                  <span className="text-xs text-text-secondary">
                    Topilgan seriallar ({tmdbResults.length})
                  </span>
                  <button
                    type="button"
                    onClick={() => setShowTmdbResults(false)}
                    className="text-xs text-text-secondary hover:text-white px-1.5 py-0.5 rounded"
                  >
                    Yopish ✕
                  </button>
                </div>
                {tmdbResults.length === 0 ? (
                  <div className="p-3 text-center text-xs text-text-secondary">
                    Hech qanday serial topilmadi
                  </div>
                ) : (
                  <div className="space-y-1">
                    {tmdbResults.map((item) => (
                      <div
                        key={item.id}
                        className="flex items-center justify-between p-2 rounded-lg hover:bg-white/5 transition-colors gap-3"
                      >
                        <div className="flex items-center gap-3 min-w-0">
                          {item.poster_url ? (
                            <img
                              src={item.poster_url}
                              alt={item.title}
                              className="w-10 h-14 object-cover rounded shadow shrink-0"
                            />
                          ) : (
                            <div className="w-10 h-14 bg-surface-container-high rounded flex items-center justify-center text-text-secondary text-xs shrink-0">
                              Rasm yo'q
                            </div>
                          )}
                          <div className="min-w-0">
                            <div className="text-sm font-medium text-text-primary truncate">
                              {item.title}
                            </div>
                            <div className="text-xs text-text-secondary flex items-center gap-2 mt-0.5">
                              {item.original_title && item.original_title !== item.title && (
                                <span className="truncate">({item.original_title})</span>
                              )}
                              <span>{item.release_year || "Yil noma'lum"}</span>
                              {item.vote_average ? (
                                <span className="text-rating-gold">
                                  ★ {item.vote_average.toFixed(1)}
                                </span>
                              ) : null}
                            </div>
                          </div>
                        </div>
                        <button
                          type="button"
                          onClick={() => handleSelectTmdbSeries(item)}
                          disabled={fetchingTmdbDetails}
                          className="bg-primary-container/20 hover:bg-primary-container text-primary hover:text-white border border-primary-container/30 px-3 py-1.5 rounded-lg text-xs font-medium transition-all shrink-0"
                        >
                          {fetchingTmdbDetails ? "Yuklanmoqda..." : "Tanlash"}
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {fetchingTmdbDetails && (
              <div className="mt-3 p-3 bg-surface-container-lowest border border-white/5 rounded-xl flex items-center justify-center gap-2 text-xs text-primary-container">
                <span className="animate-spin material-symbols-outlined text-sm">
                  progress_activity
                </span>
                <span>Serial ma'lumotlari yuklanmoqda va tarjima qilinmoqda...</span>
              </div>
            )}

            {tmdbSeasonsHint && (
              <div className="mt-2.5 p-2.5 bg-blue-500/10 border border-blue-500/20 rounded-xl text-xs text-blue-300 flex items-center gap-2">
                <span className="material-symbols-outlined text-blue-400 text-base">info</span>
                <span>{tmdbSeasonsHint} (Fasllarni fasllar bo'limida qo'lda sozlashingiz mumkin)</span>
              </div>
            )}
          </div>
        )}

        {/* Duplicate Warnings */}
        {duplicateWarning && (
          <div className="mb-6 space-y-2">
            {duplicateWarning.exact && duplicateWarning.exact.length > 0 && (
              <div className="bg-red-500/15 border border-red-500/40 rounded-xl p-3.5 text-xs text-red-300 flex items-start gap-2.5">
                <span className="material-symbols-outlined text-red-400 text-lg shrink-0">
                  error
                </span>
                <div>
                  <div className="font-bold text-red-200">
                    ⛔ Diqqat: Ushbu serial bazada allaqachon mavjud (Aniq dublikat)!
                  </div>
                  <div className="mt-1 space-y-0.5">
                    {duplicateWarning.exact.map((d: any, idx: number) => (
                      <div key={idx} className="text-red-300">
                        • <b>{d.title}</b> ({d.year || "Yil noma'lum"}) — ID/Kod:{" "}
                        <code className="bg-black/30 px-1 py-0.5 rounded">
                          #{d.code || d.id}
                        </code>{" "}
                        ({d.type === "movie" ? "Kino" : "Serial"})
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {duplicateWarning.similar &&
              duplicateWarning.similar.length > 0 &&
              (!duplicateWarning.exact || duplicateWarning.exact.length === 0) && (
                <div className="bg-amber-500/15 border border-amber-500/40 rounded-xl p-3.5 text-xs text-amber-300 flex items-start gap-2.5">
                  <span className="material-symbols-outlined text-amber-400 text-lg shrink-0">
                    warning
                  </span>
                  <div>
                    <div className="font-bold text-amber-200">
                      ⚠️ O'xshash nomdagi film yoki serial(lar) topildi:
                    </div>
                    <div className="mt-1 space-y-0.5">
                      {duplicateWarning.similar.map((s: any, idx: number) => (
                        <div key={idx} className="text-amber-300">
                          • <b>{s.title}</b> ({s.year || "Yil noma'lum"}) — ID/Kod:{" "}
                          <code className="bg-black/30 px-1 py-0.5 rounded">
                            #{s.code || s.id}
                          </code>{" "}
                          ({s.type === "movie" ? "Kino" : "Serial"})
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
          </div>
        )}

        <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-3 sm:gap-4">
          <div className="md:col-span-2">
            <label className="block text-xs sm:text-sm font-medium text-text-secondary mb-1">
              Sarlavha
            </label>
            <input
              type="text"
              required
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              className="w-full bg-surface-container-lowest border border-white/10 rounded-xl p-3 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container text-sm"
              placeholder="Serial nomi..."
            />
          </div>

          <div className="md:col-span-2">
            <label className="block text-xs sm:text-sm font-medium text-text-secondary mb-1">
              Tavsif (O'zbek tilida)
            </label>
            <textarea
              rows={3}
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              className="w-full bg-surface-container-lowest border border-white/10 rounded-xl p-3 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container text-sm"
              placeholder="Serial haqida qisqacha..."
            />
          </div>

          <div className="md:col-span-2">
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

          <div className="md:col-span-2">
            <label className="block text-xs sm:text-sm font-medium text-text-secondary mb-1">
              Treyler URL (YouTube yoki havola, majburiy emas)
            </label>
            <input
              type="text"
              placeholder="https://youtube.com/watch?v=... yoki Telegram xabar havolasi"
              value={form.trailer_url}
              onChange={(e) => setForm({ ...form, trailer_url: e.target.value })}
              className="w-full bg-surface-container-lowest border border-white/10 rounded-xl p-3 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container text-sm"
            />
            <p className="text-xs text-text-secondary mt-1">
              YouTube havolasi yoki Telegram kanaldagi video xabari havolasi
            </p>
          </div>

          <div>
            <label className="block text-xs sm:text-sm font-medium text-text-secondary mb-1">
              Rejissyor
            </label>
            <input
              type="text"
              value={form.director}
              onChange={(e) => setForm({ ...form, director: e.target.value })}
              className="w-full bg-surface-container-lowest border border-white/10 rounded-xl p-3 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container text-sm"
            />
          </div>

          <div>
            <label className="block text-xs sm:text-sm font-medium text-text-secondary mb-1">
              Yil
            </label>
            <input
              type="number"
              value={form.release_year}
              onChange={(e) =>
                setForm({ ...form, release_year: parseInt(e.target.value) || 2024 })
              }
              className="w-full bg-surface-container-lowest border border-white/10 rounded-xl p-3 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container text-sm"
            />
          </div>

          <div className="md:col-span-2">
            <label className="block text-xs sm:text-sm font-medium text-text-secondary mb-1">
              Aktyorlar
            </label>
            <input
              type="text"
              value={form.cast}
              onChange={(e) => setForm({ ...form, cast: e.target.value })}
              className="w-full bg-surface-container-lowest border border-white/10 rounded-xl p-3 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container text-sm"
            />
          </div>

          <div>
            <label className="block text-xs sm:text-sm font-medium text-text-secondary mb-1">
              Reyting (IMDb)
            </label>
            <input
              type="number"
              step="0.1"
              min="0"
              max="10"
              value={form.imdb_rating}
              onChange={(e) =>
                setForm({ ...form, imdb_rating: parseFloat(e.target.value) || 0 })
              }
              className="w-full bg-surface-container-lowest border border-white/10 rounded-xl p-3 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container text-sm"
            />
          </div>

          <div>
            <label className="block text-xs sm:text-sm font-medium text-text-secondary mb-1">
              Status (Holati)
            </label>
            <select
              value={form.status}
              onChange={(e) => setForm({ ...form, status: e.target.value })}
              className="w-full bg-surface-container-lowest border border-white/10 rounded-xl p-3 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container text-sm"
            >
              <option value="ongoing">Davom etmoqda</option>
              <option value="completed">Tugallangan</option>
            </select>
          </div>

          {/* Telegram Auto Topic Option (For new series) */}
          {!editingId && (
            <div className="md:col-span-2 bg-surface-container-high/40 border border-white/10 rounded-xl p-3.5">
              <label className="flex items-start gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={autoOpenTopic}
                  onChange={(e) => setAutoOpenTopic(e.target.checked)}
                  className="mt-0.5 w-4 h-4 rounded border-white/10 bg-surface-container-lowest focus:ring-primary-container text-primary-container"
                />
                <div>
                  <div className="text-sm font-medium text-text-primary flex items-center gap-1.5">
                    <span>Telegram guruhida serial uchun Topic ochilsin</span>
                    <span className="text-xs bg-emerald-500/20 text-emerald-400 px-2 py-0.5 rounded-full border border-emerald-500/30">
                      Tavsiya etiladi
                    </span>
                  </div>
                  <p className="text-xs text-text-secondary mt-0.5">
                    Serial saqlangach, Telegram forum guruhida uning nomi bilan alohida 1 ta topic ochiladi va manba sifatida ulanadi. Barcha fasllar va qismlar shu bitta topic ichida yuboriladi.
                  </p>
                </div>
              </label>
            </div>
          )}

          {/* Manual Source Selection */}
          <div className="md:col-span-2">
            <label className="block text-xs sm:text-sm font-medium text-text-secondary mb-1">
              Manba (Source)
            </label>
            <select
              value={form.source_id}
              onChange={(e) =>
                setForm({
                  ...form,
                  source_id: e.target.value === "" ? "" : parseInt(e.target.value),
                })
              }
              className="w-full bg-surface-container-lowest border border-white/10 rounded-xl p-3 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container text-sm"
            >
              <option value="">Manba tanlanmagan (yoki avtomatik topic ochiladi)</option>
              {sources.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name} ({s.type})
                </option>
              ))}
            </select>
          </div>

          {/* Categories */}
          <div className="md:col-span-2">
            <label className="block text-xs sm:text-sm font-medium text-text-secondary mb-2">
              Kategoriyalar
            </label>
            <div className="flex flex-wrap gap-2">
              {categories.map((c) => (
                <label
                  key={c.id}
                  className="flex items-center bg-surface-container-lowest border border-white/10 px-3 py-2 rounded-xl cursor-pointer text-text-primary hover:bg-white/5 transition-colors text-xs sm:text-sm min-h-[38px]"
                >
                  <input
                    type="checkbox"
                    className="mr-2 w-4 h-4 rounded border-white/10 bg-surface-container-lowest focus:ring-primary-container text-primary-container"
                    checked={form.category_ids.includes(c.id)}
                    onChange={() => handleCategoryChange(c.id)}
                  />
                  {c.name}
                </label>
              ))}
            </div>
          </div>

          {/* Pages */}
          <div className="md:col-span-2">
            <label className="block text-xs sm:text-sm font-medium text-text-secondary mb-2">
              Sahifalar
            </label>
            <div className="flex flex-wrap gap-2">
              {pages.map((p) => (
                <label
                  key={p.id}
                  className="flex items-center bg-surface-container-lowest border border-white/10 px-3 py-2 rounded-xl cursor-pointer text-text-primary hover:bg-white/5 transition-colors text-xs sm:text-sm min-h-[38px]"
                >
                  <input
                    type="checkbox"
                    className="mr-2 w-4 h-4 rounded border-white/10 bg-surface-container-lowest focus:ring-primary-container text-primary-container"
                    checked={form.page_ids.includes(p.id)}
                    onChange={() => handlePageChange(p.id)}
                  />
                  {p.title}
                </label>
              ))}
            </div>
          </div>

          {errorMsg && (
            <div className="md:col-span-2 p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs sm:text-sm">
              {errorMsg}
            </div>
          )}

          {/* Action buttons */}
          <div className="md:col-span-2 flex flex-col sm:flex-row gap-3 pt-3">
            <button
              type="submit"
              className="bg-primary-container text-white px-6 py-3 rounded-xl font-medium hover:scale-[1.02] active:scale-95 transition-all text-sm w-full sm:w-auto text-center min-h-[44px]"
            >
              {editingId ? "O'zgarishlarni saqlash" : "Serialni saqlash"}
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

      {/* Series Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
        {seriesList.map((s) => (
          <div
            key={s.id}
            className="metric-card rounded-2xl overflow-hidden flex flex-col group border border-white/5 shadow-lg"
          >
            {s.poster_url && (
              <div className="h-44 sm:h-48 w-full bg-surface-container-lowest overflow-hidden relative">
                <img
                  src={s.poster_url}
                  alt={s.title}
                  className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-surface-container-high to-transparent opacity-90"></div>
              </div>
            )}
            <div
              className={`p-4 sm:p-5 flex-1 flex flex-col relative z-10 ${
                s.poster_url ? "-mt-8" : ""
              } bg-surface-container-high rounded-t-xl`}
            >
              <div className="flex items-start justify-between gap-2 mb-2">
                <h3 className="text-base sm:text-lg font-bold text-text-primary truncate">
                  {s.title}
                </h3>
                {s.tmdb_id && (
                  <span className="text-[10px] bg-blue-500/10 text-blue-400 border border-blue-500/20 px-1.5 py-0.2 rounded font-mono shrink-0">
                    TMDb
                  </span>
                )}
              </div>

              {s.categories && s.categories.length > 0 && (
                <div className="flex flex-wrap gap-1 mb-2.5">
                  {s.categories.map((c) => (
                    <span
                      key={c.id}
                      className="inline-block bg-primary-container/20 text-primary-container border border-primary-container/30 text-[11px] px-2 py-0.5 rounded-full font-medium"
                    >
                      {c.name}
                    </span>
                  ))}
                </div>
              )}

              {/* Source / Topic Info */}
              {s.source && s.source.topic_id ? (
                <span className="text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-1 rounded-lg text-xs mb-2 flex items-center gap-1 font-medium w-fit">
                  <span className="material-symbols-outlined text-[14px]">forum</span>
                  Topic #{s.source.topic_id} ({s.source.name})
                </span>
              ) : s.source ? (
                <span className="text-tertiary-fixed text-xs sm:text-sm mb-2 flex items-center gap-1 font-medium">
                  📦 Manba: {s.source.name}
                </span>
              ) : (
                <div className="mb-2">
                  <button
                    type="button"
                    onClick={() => handleOpenTopic(s.id)}
                    disabled={openingTopicId === s.id}
                    className="inline-flex items-center gap-1 text-xs text-sky-400 bg-sky-500/10 hover:bg-sky-500/20 border border-sky-500/30 px-2.5 py-1 rounded-lg transition-colors font-medium"
                  >
                    {openingTopicId === s.id ? (
                      <span className="animate-spin material-symbols-outlined text-[14px]">
                        progress_activity
                      </span>
                    ) : (
                      <span className="material-symbols-outlined text-[14px]">
                        add_comment
                      </span>
                    )}
                    Topic ochish
                  </button>
                </div>
              )}

              <span
                className={`text-xs sm:text-sm mb-2 font-medium ${
                  s.status === "completed" ? "text-green-400" : "text-yellow-400"
                }`}
              >
                {s.status === "completed" ? "✅ Tugallangan" : "🔄 Davom etmoqda"}
              </span>

              <p className="text-xs sm:text-sm text-text-secondary mb-4 line-clamp-3">
                {s.description || "Tavsif yo'q"}
              </p>

              <div className="mt-auto flex items-center gap-2 pt-2 border-t border-white/5">
                <Link
                  href={`/series/${s.id}`}
                  className="flex-1 bg-surface-container-lowest border border-white/10 text-text-primary hover:text-white hover:border-white/30 text-center px-4 py-2.5 rounded-xl text-xs sm:text-sm font-medium transition-all hover:bg-white/5 min-h-[40px] flex items-center justify-center gap-1"
                >
                  <span className="material-symbols-outlined text-[18px]">layers</span>
                  Fasllar
                </Link>
                <button
                  onClick={() => handleEdit(s)}
                  className="p-2.5 text-text-secondary hover:text-tertiary-fixed hover:bg-white/5 rounded-xl transition-colors border border-white/5 min-h-[40px] min-w-[40px] flex items-center justify-center"
                  title="Tahrirlash"
                  aria-label="Tahrirlash"
                >
                  <span className="material-symbols-outlined text-[18px]">edit</span>
                </button>
                <button
                  onClick={() => handleDelete(s.id)}
                  className="p-2.5 text-text-secondary hover:text-primary-container hover:bg-white/5 rounded-xl transition-colors border border-white/5 min-h-[40px] min-w-[40px] flex items-center justify-center"
                  title="O'chirish"
                  aria-label="O'chirish"
                >
                  <span className="material-symbols-outlined text-[18px]">delete</span>
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {seriesList.length === 0 && (
        <div className="text-center py-12 metric-card rounded-2xl border border-white/10">
          <p className="text-text-secondary text-sm">Hali hech qanday serial qo'shilmagan.</p>
        </div>
      )}
    </div>
  );
}
