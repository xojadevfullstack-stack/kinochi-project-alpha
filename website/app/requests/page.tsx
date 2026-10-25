"use client";

import { useState, useEffect, useCallback } from "react";
import Image from "next/image";
import Link from "next/link";
import BackButton from "@/components/BackButton";
import RequestMovieModal, { RequestTargetItem } from "@/components/RequestMovieModal";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";

interface RequestItem {
  id: number;
  title: string;
  original_title?: string | null;
  media_type: string;
  release_year?: number | null;
  poster_url?: string | null;
  overview?: string | null;
  tmdb_id?: number | null;
  preferred_language: string;
  vote_count: number;
  status: string;
  created_at: string;
}

interface ExternalResult {
  tmdb_id?: number | null;
  kinopoisk_id?: number | null;
  title: string;
  original_title?: string | null;
  media_type: "movie" | "series";
  release_year?: number | null;
  poster_url?: string | null;
  overview?: string | null;
  vote_average?: number | null;
  in_library: boolean;
  library_code?: string | null;
  library_id?: number | null;
  request_count: number;
  is_requested: boolean;
}

export default function RequestsPage() {
  const [activeTab, setActiveTab] = useState<"search" | "leaderboard">("search");
  const [searchQuery, setSearchQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [searchResults, setSearchResults] = useState<ExternalResult[]>([]);
  const [searchError, setSearchError] = useState<string | null>(null);

  const [topRequests, setTopRequests] = useState<RequestItem[]>([]);
  const [loadingRequests, setLoadingRequests] = useState(true);

  const [selectedTarget, setSelectedTarget] = useState<RequestTargetItem | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [votedIds, setVotedIds] = useState<Set<number>>(new Set());

  // Fetch top requested movies
  const fetchTopRequests = useCallback(async () => {
    try {
      setLoadingRequests(true);
      const res = await fetch(`${API_URL}/content-requests?sort=votes&limit=30`);
      if (res.ok) {
        const data = await res.json();
        setTopRequests(data.items || []);
      }
    } catch (e) {
      console.error("Failed to load requests:", e);
    } finally {
      setLoadingRequests(false);
    }
  }, []);

  useEffect(() => {
    fetchTopRequests();
  }, [fetchTopRequests]);

  // Handle TMDB/Kinopoisk search
  const handleSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const q = searchQuery.trim();
    if (q.length < 2) return;

    setIsSearching(true);
    setSearchError(null);
    try {
      const res = await fetch(`${API_URL}/content-requests/external-search?q=${encodeURIComponent(q)}&limit=18`);
      if (!res.ok) {
        throw new Error("Qidiruvda xatolik yuz berdi");
      }
      const data = await res.json();
      setSearchResults(data.results || []);
    } catch (err: any) {
      setSearchError(err.message || "Tashqi serverdan ma'lumot olishda xatolik");
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  const handleOpenRequest = (item: ExternalResult | RequestItem) => {
    setSelectedTarget({
      tmdb_id: item.tmdb_id,
      kinopoisk_id: "kinopoisk_id" in item ? item.kinopoisk_id : null,
      title: item.title,
      original_title: item.original_title,
      media_type: (item.media_type as "movie" | "series") || "movie",
      release_year: item.release_year,
      poster_url: item.poster_url,
      overview: item.overview,
      vote_average: "vote_average" in item ? item.vote_average : null,
    });
    setIsModalOpen(true);
  };

  const handleVoteExisting = async (req: RequestItem) => {
    if (votedIds.has(req.id)) return;
    try {
      const res = await fetch(`${API_URL}/content-requests`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: req.title,
          original_title: req.original_title,
          media_type: req.media_type,
          release_year: req.release_year,
          tmdb_id: req.tmdb_id,
          preferred_language: req.preferred_language || "uz",
        }),
      });
      if (res.ok) {
        setVotedIds((prev) => new Set(prev).add(req.id));
        setTopRequests((prev) =>
          prev.map((it) => (it.id === req.id ? { ...it, vote_count: it.vote_count + 1 } : it))
        );
      }
    } catch (err) {
      console.error("Vote failed:", err);
    }
  };

  return (
    <div className="min-h-screen pt-20 sm:pt-24 md:pt-28 pb-16 px-4 sm:px-6 md:px-8 bg-background-obsidian text-text-primary">
      <div className="max-w-6xl mx-auto">
        
        {/* Navigation & Title */}
        <div className="mb-4">
          <BackButton fallbackUrl="/" />
        </div>

        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
          <div>
            <div className="flex items-center gap-2 mb-1.5 text-xs font-bold text-rating-gold uppercase tracking-wider">
              <span className="material-symbols-outlined text-[18px]">movie_edit</span>
              <span>Foydalanuvchilar Buyurtmalari</span>
            </div>
            <h1 className="text-2xl sm:text-3xl md:text-4xl font-extrabold text-white">
              Kino va Serial Qo&apos;shishni So&apos;rash
            </h1>
            <p className="text-sm text-text-secondary mt-1 max-w-2xl leading-relaxed">
              Platformamizda yo&apos;q kinoni TMDB yoki Kinopoisk orqali toping va adminlarimizga so&apos;rov yuboring. Eng ko&apos;p so&apos;ralgan kinolar birinchi bo&apos;lib yuklanadi!
            </p>
          </div>

          {/* Tab buttons */}
          <div className="flex bg-white/5 p-1 rounded-2xl border border-white/10 shrink-0 self-start md:self-auto">
            <button
              onClick={() => setActiveTab("search")}
              className={`px-4 py-2 rounded-xl text-xs sm:text-sm font-bold transition-all flex items-center gap-1.5 ${
                activeTab === "search"
                  ? "bg-rating-gold text-background-obsidian shadow-lg"
                  : "text-text-secondary hover:text-white"
              }`}
            >
              <span className="material-symbols-outlined text-[18px]">search</span>
              <span>Yangi kino so&apos;rash</span>
            </button>
            <button
              onClick={() => setActiveTab("leaderboard")}
              className={`px-4 py-2 rounded-xl text-xs sm:text-sm font-bold transition-all flex items-center gap-1.5 ${
                activeTab === "leaderboard"
                  ? "bg-rating-gold text-background-obsidian shadow-lg"
                  : "text-text-secondary hover:text-white"
              }`}
            >
              <span className="material-symbols-outlined text-[18px]">local_fire_department</span>
              <span>Top so&apos;rovlar ({topRequests.length})</span>
            </button>
          </div>
        </div>

        {/* Tab 1: Search TMDB/Kinopoisk */}
        {activeTab === "search" && (
          <div>
            {/* Search Input Box */}
            <div className="p-6 sm:p-8 rounded-3xl bg-white/[0.03] border border-white/10 mb-8 shadow-xl">
              <h2 className="text-base sm:text-lg font-bold text-white mb-2">
                Qaysi kino yoki serialni qidirmoqchisiz?
              </h2>
              <p className="text-xs sm:text-sm text-text-secondary mb-4">
                Kinoning o&apos;zbekcha, ruscha yoki inglizcha nomini kiriting:
              </p>

              <form onSubmit={handleSearch} className="flex flex-col sm:flex-row gap-3">
                <div className="relative flex-1">
                  <span className="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-text-secondary text-[22px]">
                    search
                  </span>
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Masalan: Inception, Qashqirlar makoni, Game of Thrones..."
                    className="w-full pl-12 pr-4 py-3.5 bg-white/5 border border-white/15 rounded-2xl text-text-primary text-sm focus:outline-none focus:border-rating-gold focus:bg-white/10 transition-all placeholder:text-text-secondary/60"
                  />
                </div>
                <button
                  type="submit"
                  disabled={isSearching || searchQuery.trim().length < 2}
                  className="px-6 py-3.5 bg-rating-gold text-background-obsidian font-bold rounded-2xl hover:brightness-110 active:scale-95 transition-all text-sm flex items-center justify-center gap-2 shadow-lg disabled:opacity-50"
                >
                  {isSearching ? (
                    <>
                      <span className="w-4 h-4 border-2 border-background-obsidian border-t-transparent rounded-full animate-spin"></span>
                      <span>Qidirilmoqda...</span>
                    </>
                  ) : (
                    <>
                      <span className="material-symbols-outlined text-[20px]">travel_explore</span>
                      <span>Global qidirish</span>
                    </>
                  )}
                </button>
              </form>

              {searchError && (
                <div className="mt-4 p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs">
                  {searchError}
                </div>
              )}
            </div>

            {/* Results Grid */}
            {searchResults.length > 0 ? (
              <div>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-base sm:text-lg font-bold text-white flex items-center gap-2">
                    <span className="w-1.5 h-4 bg-cyan-400 rounded-full"></span>
                    <span>Qidiruv natijalari ({searchResults.length})</span>
                  </h3>
                  <span className="text-xs text-text-secondary">
                    TMDB & Kinopoisk ma&apos;lumotlari
                  </span>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3 sm:gap-4 md:gap-5 mb-12">
                  {searchResults.map((item, idx) => (
                    <div
                      key={`res-${item.tmdb_id || idx}`}
                      className="group relative flex flex-col rounded-2xl overflow-hidden bg-surface-container border border-white/10 hover:border-cyan-500/40 transition-all shadow-lg"
                    >
                      <div className="relative aspect-[2/3] w-full overflow-hidden bg-surface-container-high">
                        {item.poster_url ? (
                          <Image
                            src={item.poster_url}
                            alt={item.title}
                            fill
                            sizes="(max-width: 640px) 50vw, 20vw"
                            className="object-cover group-hover:scale-105 transition-transform duration-300"
                          />
                        ) : (
                          <div className="w-full h-full flex flex-col items-center justify-center text-text-secondary">
                            <span className="material-symbols-outlined text-4xl mb-1 opacity-30">movie</span>
                            <span className="text-[10px]">Poster yo&apos;q</span>
                          </div>
                        )}
                        <div className="absolute inset-0 bg-gradient-to-t from-background-obsidian via-background-obsidian/30 to-transparent opacity-85 group-hover:opacity-90 transition-opacity"></div>

                        {item.vote_average ? (
                          <div className="absolute top-2 right-2 px-2 py-0.5 bg-black/70 backdrop-blur-sm rounded text-rating-gold flex items-center gap-1 border border-white/10 font-bold text-[11px]">
                            <span>★ {item.vote_average.toFixed(1)}</span>
                          </div>
                        ) : null}

                        <div className="absolute top-2 left-2">
                          {item.in_library ? (
                            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/90 text-white backdrop-blur-sm">
                              Bazada bor
                            </span>
                          ) : (
                            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-black/60 text-text-secondary border border-white/10">
                              Bazada yo&apos;q
                            </span>
                          )}
                        </div>

                        <div className="absolute bottom-0 left-0 w-full p-3">
                          <div className="flex gap-1 mb-1 items-center">
                            <span className="px-1.5 py-0.5 bg-white/10 backdrop-blur-sm rounded text-[9px] font-bold text-text-secondary uppercase">
                              {item.media_type === "series" ? "Serial" : "Kino"}
                            </span>
                            {item.release_year && (
                              <span className="text-[10px] font-bold text-text-secondary">
                                {item.release_year}
                              </span>
                            )}
                          </div>
                          <h4 className="font-bold text-xs sm:text-sm text-white line-clamp-2">
                            {item.title}
                          </h4>
                        </div>
                      </div>

                      <div className="p-2.5 bg-white/[0.02] border-t border-white/5">
                        {item.in_library ? (
                          <Link
                            href={item.media_type === "series" ? `/series/${item.library_id}` : `/movie/${item.library_code}`}
                            className="w-full py-2 px-3 rounded-xl bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-400 border border-emerald-500/30 text-xs font-bold transition-all flex items-center justify-center gap-1"
                          >
                            <span className="material-symbols-outlined text-[16px]">play_arrow</span>
                            <span>Ko&apos;rish</span>
                          </Link>
                        ) : (
                          <button
                            type="button"
                            onClick={() => handleOpenRequest(item)}
                            className="w-full py-2 px-3 rounded-xl bg-white/5 hover:bg-rating-gold hover:text-background-obsidian text-text-primary border border-white/10 text-xs font-bold transition-all flex items-center justify-center gap-1"
                          >
                            <span className="material-symbols-outlined text-[16px]">add_circle</span>
                            <span>So&apos;rash</span>
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : isSearching ? (
              <div className="text-center py-16">
                <span className="w-8 h-8 border-3 border-rating-gold border-t-transparent rounded-full animate-spin inline-block mb-3"></span>
                <p className="text-sm text-text-secondary">TMDB va Kinopoisk bazalari tekshirilmoqda...</p>
              </div>
            ) : null}
          </div>
        )}

        {/* Tab 2: Leaderboard of Requests */}
        {(activeTab === "leaderboard" || (activeTab === "search" && searchResults.length === 0 && !isSearching)) && (
          <div>
            <div className="flex items-center justify-between mb-5">
              <h3 className="text-lg sm:text-xl font-bold text-white flex items-center gap-2">
                <span className="w-1.5 h-5 bg-rating-gold rounded-full"></span>
                <span>Eng ko&apos;p kutilayotgan kinolar</span>
              </h3>
              <span className="text-xs text-text-secondary">Ovozlar bo&apos;yicha saralangan</span>
            </div>

            {loadingRequests ? (
              <div className="text-center py-16 text-text-secondary">
                <span className="w-7 h-7 border-2 border-rating-gold border-t-transparent rounded-full animate-spin inline-block mb-2"></span>
                <p className="text-xs">So&apos;rovlar ro&apos;yxati yuklanmoqda...</p>
              </div>
            ) : topRequests.length === 0 ? (
              <div className="text-center py-16 px-6 bg-white/[0.02] rounded-3xl border border-white/10">
                <span className="material-symbols-outlined text-5xl text-text-secondary mb-2 opacity-50">inbox</span>
                <h4 className="font-bold text-white mb-1">Hozircha faol so&apos;rovlar yo&apos;q</h4>
                <p className="text-xs text-text-secondary">
                  Birinchi bo&apos;lib sevimli kino yoki serialingizni so&apos;rang!
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4 mb-12">
                {topRequests.map((req) => {
                  const hasVoted = votedIds.has(req.id);
                  return (
                    <div
                      key={`req-${req.id}`}
                      className="flex gap-3.5 p-3.5 rounded-2xl bg-surface-container border border-white/10 hover:border-white/20 transition-all items-center shadow-md"
                    >
                      <div className="relative w-14 h-20 rounded-xl overflow-hidden shrink-0 bg-white/5 border border-white/10">
                        {req.poster_url ? (
                          <Image
                            src={req.poster_url}
                            alt={req.title}
                            fill
                            sizes="56px"
                            className="object-cover"
                          />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center text-text-secondary">
                            <span className="material-symbols-outlined text-2xl opacity-40">movie</span>
                          </div>
                        )}
                      </div>

                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-1.5 mb-1">
                          <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-white/10 text-text-secondary uppercase">
                            {req.media_type === "series" ? "Serial" : "Kino"}
                          </span>
                          {req.release_year && (
                            <span className="text-[11px] text-text-secondary">{req.release_year}</span>
                          )}
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 font-bold uppercase">
                            {req.preferred_language?.toUpperCase() || "UZ"}
                          </span>
                        </div>

                        <h4 className="font-bold text-sm text-white truncate">{req.title}</h4>
                        {req.original_title && (
                          <p className="text-xs text-text-secondary truncate">{req.original_title}</p>
                        )}
                        <p className="text-[11px] text-emerald-400 font-medium mt-1">
                          {req.status === "in_review" ? "⏳ Ko'rib chiqilmoqda" : "⚡ Kutilmoqda"}
                        </p>
                      </div>

                      {/* Vote Count & Button */}
                      <button
                        type="button"
                        onClick={() => handleVoteExisting(req)}
                        disabled={hasVoted}
                        className={`flex flex-col items-center justify-center px-3 py-2 rounded-xl border transition-all shrink-0 ${
                          hasVoted
                            ? "bg-emerald-500/20 border-emerald-500/40 text-emerald-400"
                            : "bg-white/5 hover:bg-rating-gold/20 border-white/10 hover:border-rating-gold text-text-primary"
                        }`}
                        title="Ovoz berish"
                      >
                        <span className="material-symbols-outlined text-[18px]">
                          {hasVoted ? "thumb_up" : "arrow_upward"}
                        </span>
                        <span className="text-xs font-bold mt-0.5">{req.vote_count}</span>
                      </button>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* Modal */}
        <RequestMovieModal
          isOpen={isModalOpen}
          onClose={() => setIsModalOpen(false)}
          item={selectedTarget}
          onSuccess={() => {
            fetchTopRequests();
          }}
        />

      </div>
    </div>
  );
}
