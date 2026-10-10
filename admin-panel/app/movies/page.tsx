"use client";

import { useEffect, useState } from "react";
import { fetchApi } from "@/lib/api";
import VideoUploadModal from "@/components/VideoUploadModal";

type Category = { id: number; name: string };
type PageItem = { id: number; title: string };
type Movie = {
  id: number;
  title: string;
  code: string;
  description: string;
  genres: string;
  director: string | null;
  cast: string | null;
  imdb_rating: number | null;
  tmdb_id?: number | null;
  poster_url: string | null;
  trailer_url: string | null;
  release_year: number;
  duration_minutes: number;
  runtime?: number;
  is_18_plus?: boolean;
  categories: Category[];
  pages: PageItem[];
  source_id?: number | null;
  source_chat_id?: number | null;
  source_topic_id?: number | null;
  source_link?: string | null;
  translations: { id: number; language: string; telegram_file_id: string }[];
};

export default function MoviesPage() {
  const [movies, setMovies] = useState<Movie[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [pages, setPages] = useState<PageItem[]>([]);
  const [sources, setSources] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [uploadingId, setUploadingId] = useState<number | null>(null);

  // Video Modal states
  const [videoModalOpen, setVideoModalOpen] = useState(false);
  const [videoMovieId, setVideoMovieId] = useState<number | null>(null);

  // TMDb Lookup & Duplicates states
  const [tmdbSearchQuery, setTmdbSearchQuery] = useState("");
  const [tmdbSearching, setTmdbSearching] = useState(false);
  const [tmdbResults, setTmdbResults] = useState<any[]>([]);
  const [showTmdbResults, setShowTmdbResults] = useState(false);
  const [fetchingTmdbDetails, setFetchingTmdbDetails] = useState(false);
  const [duplicateWarning, setDuplicateWarning] = useState<{
    exact: any[];
    similar: any[];
  } | null>(null);
  const [autoOpenTopic, setAutoOpenTopic] = useState(true);
  const [openingTopicId, setOpeningTopicId] = useState<number | null>(null);
  const [titleVariants, setTitleVariants] = useState<{
    uz?: string;
    orig?: string;
    ru?: string;
  } | null>(null);

  const initialForm = {
    title: "",
    description: "",
    genres: "",
    tmdb_id: null as number | null,
    release_year: new Date().getFullYear(),
    duration_minutes: 120,
    poster_url: "",
    trailer_url: "",
    director: "",
    cast: "",
    imdb_rating: 0,
    category_ids: [] as number[],
    page_ids: [] as number[],
    source_id: "" as number | "",
    is_18_plus: false,
  };

  const [totalMovies, setTotalMovies] = useState<number>(0);
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [debouncedQuery, setDebouncedQuery] = useState<string>("");
  const [loadingMore, setLoadingMore] = useState<boolean>(false);
  const [isSearching, setIsSearching] = useState<boolean>(false);

  const PAGE_SIZE = 50;

  const [form, setForm] = useState(initialForm);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([loadCategories(), loadPages(), loadSources()]);
  }, []);

  // Debounce search query
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(searchQuery.trim());
    }, 350);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Load movies on query change or initial mount
  useEffect(() => {
    setIsSearching(true);
    loadMovies(true, debouncedQuery).finally(() => {
      setIsSearching(false);
      setLoading(false);
    });
  }, [debouncedQuery]);

  const loadSources = async () => {
    try {
      const data = await fetchApi("/sources");
      setSources(data);
    } catch (e: any) {
      console.error(e);
    }
  };

  const loadMovies = async (reset = true, queryOverride?: string) => {
    try {
      const query = queryOverride !== undefined ? queryOverride : debouncedQuery;
      let url = "";
      if (reset) {
        if (query.length >= 2) {
          url = `/movies/search?q=${encodeURIComponent(query)}&skip=0&limit=${PAGE_SIZE}`;
        } else {
          url = `/movies?skip=0&limit=${PAGE_SIZE}`;
        }
        const data = await fetchApi(url);
        setMovies(data.items || []);
        setTotalMovies(typeof data.total === "number" ? data.total : (data.items || []).length);
      } else {
        const skip = movies.length;
        if (query.length >= 2) {
          url = `/movies/search?q=${encodeURIComponent(query)}&skip=${skip}&limit=${PAGE_SIZE}`;
        } else {
          url = `/movies?skip=${skip}&limit=${PAGE_SIZE}`;
        }
        const data = await fetchApi(url);
        const newItems: Movie[] = data.items || [];
        setMovies((prev) => {
          const existingIds = new Set(prev.map((m) => m.id));
          const uniqueNew = newItems.filter((m) => !existingIds.has(m.id));
          return [...prev, ...uniqueNew];
        });
        if (typeof data.total === "number") {
          setTotalMovies(data.total);
        }
      }
    } catch (e: any) {
      console.error("loadMovies error:", e);
    }
  };

  const handleLoadMore = async () => {
    if (loadingMore || movies.length >= totalMovies) return;
    setLoadingMore(true);
    try {
      await loadMovies(false, debouncedQuery);
    } finally {
      setLoadingMore(false);
    }
  };

  const loadCategories = async () => {
    try {
      const data = await fetchApi("/categories");
      setCategories(data);
    } catch (e: any) {
      console.error(e);
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

  // TMDb Search
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
        )}&content_type=movie`
      );
      setTmdbResults(data || []);
      setShowTmdbResults(true);
    } catch (err: any) {
      setErrorMsg("TMDb qidiruvda xatolik: " + err.message);
    } finally {
      setTmdbSearching(false);
    }
  };

  // TMDb Selection
  const handleSelectTmdbMovie = async (movieItem: any) => {
    setFetchingTmdbDetails(true);
    setErrorMsg(null);
    setDuplicateWarning(null);
    try {
      const details = await fetchApi(
        `/content-lookup/details/movie/${movieItem.id}`
      );
      if (details) {
        // Match suggested categories with available categories
        const matchedCategoryIds: number[] = [];
        if (Array.isArray(details.suggested_category_ids)) {
          matchedCategoryIds.push(
            ...details.suggested_category_ids.filter((catId: number) =>
              categories.some((c) => c.id === catId)
            )
          );
        }

        setTitleVariants({
          uz: details.uz_title || details.title,
          orig: details.original_title,
          ru: details.raw_title,
        });

        setForm((prev) => ({
          ...prev,
          title: details.title || movieItem.title || prev.title,
          description: details.description || prev.description,
          tmdb_id: details.tmdb_id || movieItem.id,
          poster_url: details.poster_url || prev.poster_url,
          trailer_url: details.trailer_url || prev.trailer_url,
          genres: details.genres
            ? Array.isArray(details.genres)
              ? details.genres.join(", ")
              : String(details.genres)
            : prev.genres,
          director: details.director || prev.director,
          cast: details.cast || prev.cast,
          release_year: details.release_year || prev.release_year,
          duration_minutes:
            details.runtime || details.duration_minutes || prev.duration_minutes,
          imdb_rating:
            details.tmdb_rating ??
            details.vote_average ??
            (movieItem.vote_average
              ? Math.round(movieItem.vote_average * 10) / 10
              : prev.imdb_rating),
          category_ids: Array.from(
            new Set([...prev.category_ids, ...matchedCategoryIds])
          ),
        }));

        // Duplicate check
        try {
          const dupRes = await fetchApi(
            `/content-lookup/duplicates?tmdb_id=${movieItem.id}&title=${encodeURIComponent(
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

    const payload = {
      ...form,
      runtime: form.duration_minutes,
      source_id: form.source_id === "" ? null : form.source_id,
    };

    try {
      if (editingId) {
        await fetchApi(`/movies/${editingId}`, {
          method: "PUT",
          body: JSON.stringify(payload),
        });
        setSuccessMsg("Kino muvaffaqiyatli tahrirlandi!");
      } else {
        const created = await fetchApi("/movies", {
          method: "POST",
          body: JSON.stringify(payload),
        });

        if (autoOpenTopic && created?.id) {
          try {
            await fetchApi(`/movies/${created.id}/open-topic`, { method: "POST" });
            setSuccessMsg(
              `Kino saqlandi va Telegram'da topic ochildi! (Kod: #${created.code})`
            );
          } catch (topicErr: any) {
            setErrorMsg(
              `Kino saqlandi (#${created.code}), lekin Telegram'da topic ochilmadi: ${topicErr.message}`
            );
          }
        } else {
          setSuccessMsg(
            `Kino muvaffaqiyatli saqlandi! (Kod: #${created.code})`
          );
        }
      }
      handleCancel();
      loadMovies();
    } catch (e: any) {
      setErrorMsg(e.message || "Xato yuz berdi");
    }
  };

  const handleOpenTopic = async (movieId: number) => {
    setOpeningTopicId(movieId);
    setErrorMsg(null);
    try {
      const res = await fetchApi(`/movies/${movieId}/open-topic`, { method: "POST" });
      setSuccessMsg(res.message || "Topic muvaffaqiyatli ochildi!");
      loadMovies();
    } catch (e: any) {
      alert("Topic ochishda xatolik: " + e.message);
    } finally {
      setOpeningTopicId(null);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("O'chirilsinmi?")) return;
    try {
      await fetchApi(`/movies/${id}`, { method: "DELETE" });
      setMovies((prev) => prev.filter((m) => m.id !== id));
      setSuccessMsg("Kino muvaffaqiyatli o'chirildi!");
      loadMovies();
    } catch (e: any) {
      if (e.message && e.message.includes("Movie not found")) {
        setMovies((prev) => prev.filter((m) => m.id !== id));
        setSuccessMsg("Kino allaqachon o'chirilgan.");
      } else {
        alert("O'chirishda xato: " + e.message);
      }
    }
  };

  const handleDeleteTranslation = async (translationId: number) => {
    if (!confirm("Bu video (studiya) o'chirilsinmi?")) return;
    try {
      await fetchApi(`/movies/translations/${translationId}`, { method: "DELETE" });
      loadMovies();
    } catch (e: any) {
      alert("O'chirishda xato: " + e.message);
    }
  };

  const handleEdit = (m: Movie) => {
    let matchedSourceId: number | "" = "";
    if (m.source_chat_id) {
      const source = sources.find(
        (s) => s.chat_id === m.source_chat_id && s.topic_id === m.source_topic_id
      );
      if (source) matchedSourceId = source.id;
    }
    setEditingId(m.id);
    setDuplicateWarning(null);
    setTitleVariants(null);
    setForm({
      title: m.title,
      description: m.description,
      genres: m.genres,
      tmdb_id: m.tmdb_id || null,
      release_year: m.release_year,
      duration_minutes: m.runtime || m.duration_minutes,
      poster_url: m.poster_url || "",
      trailer_url: m.trailer_url || "",
      director: m.director || "",
      cast: m.cast || "",
      imdb_rating: m.imdb_rating || 0,
      category_ids: m.categories?.map((c) => c.id) || [],
      page_ids: m.pages?.map((p) => p.id) || [],
      source_id: matchedSourceId,
      is_18_plus: m.is_18_plus || false,
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
    setTitleVariants(null);
  };

  const openVideoModal = (id: number) => {
    setVideoMovieId(id);
    setVideoModalOpen(true);
  };

  const closeVideoModal = () => {
    setVideoModalOpen(false);
    setVideoMovieId(null);
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
      {/* Page Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-text-primary tracking-tight">
            Kinolar
          </h1>
          <p className="text-xs sm:text-sm text-text-secondary mt-1">
            Kinolarni avtomatik qidirish, qo'shish va Telegram topic ochish
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

      {/* Error Notification */}
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
          {editingId ? "Kinoni tahrirlash" : "Yangi Kino qo'shish"}
        </h2>

        {/* TMDb Search & Auto-fill Block */}
        {!editingId && (
          <div className="mb-6 bg-surface-container-high/40 border border-primary-container/30 rounded-2xl p-4">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-primary-container text-xl">
                  auto_awesome
                </span>
                <span className="text-sm font-semibold text-text-primary">
                  TMDb orqali tezkor qidirish va to'ldirish
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
                  placeholder="Kino nomi yoki TMDb ID (masalan: Avatar, Interstellar, 19995)..."
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

            {/* TMDb Results Dropdown */}
            {showTmdbResults && (
              <div className="mt-3 bg-surface-container-lowest border border-white/10 rounded-xl p-2 max-h-72 overflow-y-auto custom-scrollbar">
                <div className="flex items-center justify-between px-2 py-1 mb-1 border-b border-white/5">
                  <span className="text-xs text-text-secondary">
                    Topilgan natijalar ({tmdbResults.length})
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
                    Hech qanday film topilmadi
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
                          onClick={() => handleSelectTmdbMovie(item)}
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
                <span>TMDb ma'lumotlari olinmoqda va o'zbek tiliga tarjima qilinmoqda...</span>
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
                    ⛔ Diqqat: Ushbu film bazada allaqachon mavjud (Aniq dublikat)!
                  </div>
                  <div className="mt-1 space-y-0.5">
                    {duplicateWarning.exact.map((d: any, idx: number) => (
                      <div key={idx} className="text-red-300">
                        • <b>{d.title}</b> ({d.year || "Yil noma'lum"}) — Kod:{" "}
                        <code className="bg-black/30 px-1 py-0.5 rounded">#{d.code}</code> (
                        {d.type === "movie" ? "Kino" : "Serial"})
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
                          • <b>{s.title}</b> ({s.year || "Yil noma'lum"}) — Kod:{" "}
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
              required
              type="text"
              className="w-full bg-surface-container-lowest border border-white/10 rounded-xl p-3 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container text-sm"
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              placeholder="Kino nomi..."
            />
            {titleVariants && (titleVariants.orig || titleVariants.ru) && (
              <div className="flex flex-wrap items-center gap-1.5 mt-2">
                <span className="text-[11px] text-text-secondary">Sarlavha variantlari:</span>
                {titleVariants.uz && (
                  <button
                    type="button"
                    onClick={() => setForm((prev) => ({ ...prev, title: titleVariants.uz! }))}
                    className={`px-2 py-0.5 rounded-lg text-xs font-medium transition-all ${
                      form.title === titleVariants.uz
                        ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                        : "bg-surface-container-high/60 text-text-secondary hover:text-text-primary border border-white/5"
                    }`}
                  >
                    🇺🇿 O'zbekcha: {titleVariants.uz}
                  </button>
                )}
                {titleVariants.orig && titleVariants.orig !== titleVariants.uz && (
                  <button
                    type="button"
                    onClick={() => setForm((prev) => ({ ...prev, title: titleVariants.orig! }))}
                    className={`px-2 py-0.5 rounded-lg text-xs font-medium transition-all ${
                      form.title === titleVariants.orig
                        ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                        : "bg-surface-container-high/60 text-text-secondary hover:text-text-primary border border-white/5"
                    }`}
                  >
                    🌐 Original: {titleVariants.orig}
                  </button>
                )}
                {titleVariants.ru &&
                  titleVariants.ru !== titleVariants.uz &&
                  titleVariants.ru !== titleVariants.orig && (
                    <button
                      type="button"
                      onClick={() => setForm((prev) => ({ ...prev, title: titleVariants.ru! }))}
                      className={`px-2 py-0.5 rounded-lg text-xs font-medium transition-all ${
                        form.title === titleVariants.ru
                          ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                          : "bg-surface-container-high/60 text-text-secondary hover:text-text-primary border border-white/5"
                      }`}
                    >
                      🇷🇺 Ruscha: {titleVariants.ru}
                    </button>
                  )}
              </div>
            )}
          </div>

          <div className="md:col-span-2">
            <label className="block text-xs sm:text-sm font-medium text-text-secondary mb-1">
              Ta'rif (O'zbek tilida)
            </label>
            <textarea
              rows={3}
              className="w-full bg-surface-container-lowest border border-white/10 rounded-xl p-3 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container text-sm"
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              placeholder="Kino haqida qisqacha..."
            />
          </div>

          <div className="md:col-span-2">
            <label className="block text-xs sm:text-sm font-medium text-text-secondary mb-1">
              Poster URL (rasm havolasi)
            </label>
            <input
              type="text"
              className="w-full bg-surface-container-lowest border border-white/10 rounded-xl p-3 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container text-sm"
              placeholder="https://..."
              value={form.poster_url}
              onChange={(e) => setForm({ ...form, poster_url: e.target.value })}
            />
          </div>

          <div className="md:col-span-2">
            <label className="block text-xs sm:text-sm font-medium text-text-secondary mb-1">
              Treyler URL (YouTube yoki havola, majburiy emas)
            </label>
            <input
              type="text"
              className="w-full bg-surface-container-lowest border border-white/10 rounded-xl p-3 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container text-sm"
              placeholder="https://youtube.com/watch?v=..."
              value={form.trailer_url}
              onChange={(e) => setForm({ ...form, trailer_url: e.target.value })}
            />
          </div>

          <div>
            <label className="block text-xs sm:text-sm font-medium text-text-secondary mb-1">
              Janrlar
            </label>
            <input
              type="text"
              className="w-full bg-surface-container-lowest border border-white/10 rounded-xl p-3 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container text-sm"
              placeholder="Jangari, Drama..."
              value={form.genres}
              onChange={(e) => setForm({ ...form, genres: e.target.value })}
            />
          </div>

          <div>
            <label className="block text-xs sm:text-sm font-medium text-text-secondary mb-1">
              Rejissyor
            </label>
            <input
              type="text"
              className="w-full bg-surface-container-lowest border border-white/10 rounded-xl p-3 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container text-sm"
              value={form.director}
              onChange={(e) => setForm({ ...form, director: e.target.value })}
            />
          </div>

          <div className="md:col-span-2">
            <label className="block text-xs sm:text-sm font-medium text-text-secondary mb-1">
              Aktyorlar
            </label>
            <input
              type="text"
              className="w-full bg-surface-container-lowest border border-white/10 rounded-xl p-3 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container text-sm"
              value={form.cast}
              onChange={(e) => setForm({ ...form, cast: e.target.value })}
            />
          </div>

          <div>
            <label className="block text-xs sm:text-sm font-medium text-text-secondary mb-1">
              Yil
            </label>
            <input
              type="number"
              className="w-full bg-surface-container-lowest border border-white/10 rounded-xl p-3 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container text-sm"
              value={form.release_year}
              onChange={(e) =>
                setForm({ ...form, release_year: parseInt(e.target.value) || 2024 })
              }
            />
          </div>

          <div>
            <label className="block text-xs sm:text-sm font-medium text-text-secondary mb-1">
              Davomiylik (daqiqa)
            </label>
            <input
              type="number"
              className="w-full bg-surface-container-lowest border border-white/10 rounded-xl p-3 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container text-sm"
              value={form.duration_minutes}
              onChange={(e) =>
                setForm({ ...form, duration_minutes: parseInt(e.target.value) || 120 })
              }
            />
          </div>

          <div className="md:col-span-2">
            <label className="block text-xs sm:text-sm font-medium text-text-secondary mb-1">
              Reyting (IMDb)
            </label>
            <input
              type="number"
              step="0.1"
              min="0"
              max="10"
              className="w-full bg-surface-container-lowest border border-white/10 rounded-xl p-3 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container text-sm"
              value={form.imdb_rating}
              onChange={(e) =>
                setForm({ ...form, imdb_rating: parseFloat(e.target.value) || 0 })
              }
            />
          </div>

          {/* Telegram Auto Topic Option (For new movies) */}
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
                    <span>Telegram guruhida avtomatik Topic ochilsin</span>
                    <span className="text-xs bg-emerald-500/20 text-emerald-400 px-2 py-0.5 rounded-full border border-emerald-500/30">
                      Tavsiya etiladi
                    </span>
                  </div>
                  <p className="text-xs text-text-secondary mt-0.5">
                    Kino saqlanishi bilan birga Telegram forum guruhida kino nomi va yili bilan alohida topic yaratiladi va kino kodi xabar sifatida yuboriladi.
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
            {editingId && movies.find((m) => m.id === editingId)?.source_topic_id && (
              <div className="mt-2 text-xs text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-3 py-1.5 rounded-lg flex items-center gap-1.5">
                <span className="material-symbols-outlined text-sm">forum</span>
                Telegram 'manba' guruhidagi faol Topic:{" "}
                <b>#{movies.find((m) => m.id === editingId)?.source_topic_id}</b>
              </div>
            )}
            {errorMsg && <p className="text-red-400 text-xs sm:text-sm mt-1">{errorMsg}</p>}
          </div>

          {/* 18+ Yosh chegarasi Toggle */}
          <div className="md:col-span-2 bg-red-950/20 border border-red-500/30 rounded-xl p-3.5">
            <label className="flex items-center justify-between cursor-pointer">
              <div className="flex items-center gap-3">
                <span className="text-2xl">🔞</span>
                <div>
                  <div className="text-sm font-bold text-red-300 flex items-center gap-2">
                    <span>18+ Yosh chegarasi (Kattalar uchun)</span>
                    {form.is_18_plus && (
                      <span className="text-[10px] bg-red-600/40 text-red-200 px-2 py-0.5 rounded-full border border-red-500/40 uppercase font-black">
                        Faol
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-text-secondary mt-0.5">
                    Saytda poster xiralashtiriladi (blur) va foydalanuvchidan 18 yoshni tasdiqlash so&apos;raladi.
                  </p>
                </div>
              </div>
              <input
                type="checkbox"
                checked={form.is_18_plus}
                onChange={(e) => setForm({ ...form, is_18_plus: e.target.checked })}
                className="w-5 h-5 rounded border-red-500/40 bg-surface-container-lowest focus:ring-red-500 text-red-600 cursor-pointer"
              />
            </label>
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

          {/* Submit / Cancel Buttons */}
          <div className="md:col-span-2 flex flex-col sm:flex-row gap-3 mt-3">
            <button
              type="submit"
              className="bg-primary-container text-white px-6 py-3 rounded-xl hover:scale-[1.02] active:scale-95 transition-all font-medium text-sm w-full sm:w-auto text-center min-h-[44px]"
            >
              {editingId ? "O'zgarishlarni saqlash" : "Kinoni saqlash"}
            </button>
            {editingId && (
              <button
                type="button"
                onClick={handleCancel}
                className="bg-white/5 border border-white/10 text-text-primary px-6 py-3 rounded-xl hover:bg-white/10 active:scale-95 transition-all font-medium text-sm w-full sm:w-auto text-center min-h-[44px]"
              >
                Bekor qilish
              </button>
            )}
          </div>
        </form>
      </div>

      {/* Movies List Table */}
      <div className="metric-card rounded-2xl overflow-hidden shadow-xl">
        <div className="p-4 sm:p-5 border-b border-white/5 bg-[#1a0908]/80 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <h3 className="font-display font-bold text-base sm:text-lg text-text-primary">
              Mavjud kinolar ro'yxati
            </h3>
            <span className="text-xs bg-white/5 border border-white/10 text-text-secondary px-2.5 py-1 rounded-full font-mono">
              {totalMovies > 0 ? `${movies.length} / ${totalMovies}` : movies.length}
            </span>
            {isSearching && (
              <span className="w-3.5 h-3.5 border-2 border-primary-container border-t-transparent rounded-full animate-spin"></span>
            )}
          </div>

          {/* Search Input */}
          <div className="relative w-full sm:w-72 md:w-80">
            <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-text-secondary text-[18px]">
              search
            </span>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Kinolar bo'yicha qidirish (nomi yoki kodi)..."
              className="w-full bg-surface-container-lowest border border-white/10 rounded-xl pl-9 pr-8 py-2 text-xs sm:text-sm text-text-primary placeholder:text-text-secondary/50 focus:border-primary-container focus:outline-none transition-colors"
            />
            {searchQuery && (
              <button
                type="button"
                onClick={() => setSearchQuery("")}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-text-secondary hover:text-white text-xs p-1"
                title="Tozalash"
              >
                ✕
              </button>
            )}
          </div>
        </div>

        <div className="overflow-x-auto custom-scrollbar">
          <table className="min-w-[700px] w-full text-left border-collapse">
            <thead className="bg-surface-container-lowest border-b border-white/10">
              <tr>
                <th className="px-4 sm:px-6 py-3.5 text-xs font-semibold text-text-secondary uppercase tracking-wider">
                  Kod
                </th>
                <th className="px-4 sm:px-6 py-3.5 text-xs font-semibold text-text-secondary uppercase tracking-wider">
                  Sarlavha
                </th>
                <th className="px-4 sm:px-6 py-3.5 text-xs font-semibold text-text-secondary uppercase tracking-wider">
                  Manba / Topic
                </th>
                <th className="px-4 sm:px-6 py-3.5 text-xs font-semibold text-text-secondary uppercase tracking-wider">
                  Video
                </th>
                <th className="px-4 sm:px-6 py-3.5 text-xs font-semibold text-text-secondary uppercase tracking-wider text-right">
                  Amallar
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5 text-sm">
              {movies.map((m) => (
                <tr key={m.id} className="data-table-row">
                  <td className="px-4 sm:px-6 py-4 whitespace-nowrap font-bold text-primary-container text-base">
                    #{m.code}
                  </td>
                  <td className="px-4 sm:px-6 py-4 whitespace-nowrap text-text-primary font-medium">
                    <div className="flex flex-col">
                      <div className="flex items-center gap-2">
                        <span>{m.title}</span>
                        {m.tmdb_id && (
                          <span className="text-[10px] bg-blue-500/10 text-blue-400 border border-blue-500/20 px-1.5 py-0.2 rounded font-mono">
                            TMDb
                          </span>
                        )}
                      </div>
                      <span className="text-xs text-text-secondary">
                        {m.release_year} • {m.duration_minutes || m.runtime} daq
                      </span>
                    </div>
                  </td>
                  <td className="px-4 sm:px-6 py-4 whitespace-nowrap text-xs text-text-secondary">
                    {m.source_topic_id ? (
                      <div className="flex items-center gap-1.5">
                        <span className="inline-flex items-center gap-1 text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded-lg font-medium">
                          <span className="material-symbols-outlined text-[14px]">
                            forum
                          </span>
                          Topic #{m.source_topic_id}
                        </span>
                        {m.source_link && (
                          <a
                            href={m.source_link}
                            target="_blank"
                            rel="noreferrer"
                            className="text-tertiary-fixed hover:text-white transition-colors"
                            title={m.source_link}
                          >
                            🔗
                          </a>
                        )}
                      </div>
                    ) : (
                      <div className="flex items-center gap-2">
                        <button
                          type="button"
                          onClick={() => handleOpenTopic(m.id)}
                          disabled={openingTopicId === m.id}
                          className="inline-flex items-center gap-1 text-xs text-sky-400 bg-sky-500/10 hover:bg-sky-500/20 border border-sky-500/30 px-2 py-1 rounded-lg transition-colors"
                          title="Telegram'da topic ochish"
                        >
                          {openingTopicId === m.id ? (
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
                        {m.source_link && (
                          <a
                            href={m.source_link}
                            target="_blank"
                            rel="noreferrer"
                            className="text-tertiary-fixed hover:text-white transition-colors"
                            title={m.source_link}
                          >
                            🔗 Link
                          </a>
                        )}
                      </div>
                    )}
                  </td>
                  <td className="px-4 sm:px-6 py-4">
                    {m.translations && m.translations.length > 0 ? (
                      <div className="flex flex-col gap-1.5 min-w-[120px]">
                        {m.translations.map((t) => (
                          <div
                            key={t.id}
                            className="flex items-center justify-between bg-surface-container-high border border-white/10 px-2 py-1 rounded-lg text-xs text-text-secondary"
                          >
                            <span>✅ {t.language}</span>
                            <button
                              onClick={() => handleDeleteTranslation(t.id)}
                              className="text-rating-gold hover:text-red-400 ml-2 p-0.5 transition-colors"
                              title="Videoni o'chirish"
                            >
                              ✕
                            </button>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <span className="text-rating-gold font-bold text-xs bg-rating-gold/10 px-2 py-1 rounded-lg">
                        ❌ Yo'q
                      </span>
                    )}
                  </td>
                  <td className="px-4 sm:px-6 py-4 whitespace-nowrap text-right">
                    <div className="flex items-center justify-end gap-2">
                      {uploadingId === m.id ? (
                        <span className="text-text-secondary text-xs">
                          Yuklanmoqda...
                        </span>
                      ) : (
                        <button
                          onClick={() => openVideoModal(m.id)}
                          className="text-xs font-bold bg-tertiary-container/20 text-tertiary hover:bg-tertiary-container/40 border border-tertiary-container/40 px-3 py-1.5 rounded-lg transition-all min-h-[32px] inline-flex items-center gap-1"
                        >
                          <span className="material-symbols-outlined text-[16px]">
                            upload
                          </span>
                          Video
                        </button>
                      )}
                      <button
                        onClick={() => handleEdit(m)}
                        className="text-xs bg-white/5 border border-white/10 hover:bg-white/15 text-text-primary px-3 py-1.5 rounded-lg transition-colors min-h-[32px]"
                      >
                        Tahrirlash
                      </button>
                      <button
                        onClick={() => handleDelete(m.id)}
                        className="text-xs bg-red-500/10 border border-red-500/20 hover:bg-red-500/20 text-red-400 px-3 py-1.5 rounded-lg transition-colors min-h-[32px]"
                      >
                        O'chirish
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {movies.length === 0 && (
                <tr>
                  <td
                    colSpan={5}
                    className="px-6 py-8 text-center text-text-secondary"
                  >
                    {searchQuery
                      ? `"${searchQuery}" bo'yicha hech qanday kino topilmadi`
                      : "Hech qanday kino topilmadi"}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Load More Button */}
        {movies.length < totalMovies ? (
          <div className="p-4 sm:p-5 border-t border-white/5 flex flex-col items-center justify-center gap-2 bg-surface-container-lowest/50">
            <button
              type="button"
              onClick={handleLoadMore}
              disabled={loadingMore}
              className="flex items-center justify-center gap-2 h-11 px-7 bg-white/10 hover:bg-white/15 border border-white/15 hover:border-white/30 rounded-xl text-xs sm:text-sm font-semibold text-white shadow-md shadow-black/20 transition-all duration-200 hover:scale-[1.02] active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
            >
              {loadingMore ? (
                <span className="w-4 h-4 border-2 border-primary-container border-t-transparent rounded-full animate-spin"></span>
              ) : (
                <span className="material-symbols-outlined text-[18px]">expand_more</span>
              )}
              <span>Yana yuklash</span>
            </button>
            <span className="text-xs text-text-secondary font-medium">
              Jami {totalMovies} tadan {movies.length} tasi ko'rsatilmoqda
            </span>
          </div>
        ) : (
          movies.length > 0 && (
            <div className="p-4 border-t border-white/5 text-center text-xs text-text-secondary/70 bg-surface-container-lowest/30">
              <span>Barcha {movies.length} ta kino ko'rsatildi</span>
            </div>
          )
        )}
      </div>

      <VideoUploadModal
        isOpen={videoModalOpen}
        onClose={closeVideoModal}
        entityName="Kino"
        entityId={videoMovieId}
        uploadEndpoint={`/movies/${videoMovieId}/upload-video`}
        linkEndpoint={`/movies/${videoMovieId}/link-video`}
        onSuccess={() => loadMovies()}
      />
    </div>
  );
}
