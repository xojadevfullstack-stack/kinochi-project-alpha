"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import Image from "next/image";
import BackButton from "@/components/BackButton";
import { fetchApi } from "@/lib/api";

interface Actor {
  id: number;
  name: string;
  original_name?: string;
  photo_url?: string | null;
  role?: string;
}

interface FilmographyItem {
  tmdb_id: number;
  title: string;
  original_title?: string;
  release_year?: number | null;
  poster_url?: string | null;
  character?: string;
  is_available: boolean;
  local_movie?: {
    id: number;
    code: string;
    title: string;
    is_series: boolean;
  } | null;
}

function ActorCard({
  actor,
  onOpenFilmography,
}: {
  actor: Actor;
  onOpenFilmography: (actor: Actor) => void;
}) {
  const [imgError, setImgError] = useState(false);

  return (
    <button
      type="button"
      onClick={() => onOpenFilmography(actor)}
      className="bg-white/[0.04] hover:bg-white/[0.08] active:bg-white/[0.12] border border-white/10 hover:border-primary/50 active:border-primary rounded-xl sm:rounded-2xl p-2.5 sm:p-3.5 flex flex-col items-center text-center transition-all duration-200 active:scale-95 group shadow-sm hover:shadow-md cursor-pointer select-none"
    >
      {/* Actor Photo */}
      <div className="w-16 h-16 xs:w-18 xs:h-18 sm:w-20 sm:h-20 md:w-24 md:h-24 rounded-full overflow-hidden relative mb-2 sm:mb-2.5 border-2 border-white/10 group-hover:border-primary/60 group-active:border-primary transition-all bg-[#1e1f26] shadow-md shrink-0 flex items-center justify-center">
        {actor.photo_url && !imgError ? (
          <Image
            src={actor.photo_url}
            alt={actor.name}
            fill
            sizes="(max-width: 640px) 72px, 96px"
            className="object-cover group-hover:scale-105 transition-transform duration-300 pointer-events-none"
            onError={() => setImgError(true)}
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-white/30">
            <span className="material-symbols-outlined text-2xl sm:text-3xl">person</span>
          </div>
        )}
      </div>

      <h3 className="font-bold text-xs sm:text-sm text-white group-hover:text-primary transition-colors leading-tight line-clamp-1 w-full">
        {actor.name}
      </h3>
      {actor.original_name && (
        <span className="text-[10px] sm:text-[11px] text-text-secondary truncate w-full mt-0.5">
          {actor.original_name}
        </span>
      )}

      {actor.role && (
        <div className="text-[9px] sm:text-[10px] text-text-secondary bg-white/5 px-2 py-0.5 rounded-full border border-white/5 mt-1.5 truncate max-w-full">
          {actor.role}
        </div>
      )}
    </button>
  );
}

export default function ActorsPage() {
  const [actors, setActors] = useState<Actor[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");

  // Modal / Filmography state
  const [selectedActor, setSelectedActor] = useState<Actor | null>(null);
  const [filmography, setFilmography] = useState<FilmographyItem[]>([]);
  const [loadingFilms, setLoadingFilms] = useState(false);
  const [requestedIds, setRequestedIds] = useState<Record<number, boolean>>({});
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // Debounced fetch of actors (loads 40+ curated stars or dynamic TMDb search results)
  useEffect(() => {
    let isCancelled = false;
    const trimmed = searchQuery.trim();

    const timer = setTimeout(async () => {
      try {
        const endpoint = trimmed
          ? `/actors?search=${encodeURIComponent(trimmed)}`
          : "/actors";
        const data = await fetchApi(endpoint);
        if (!isCancelled && Array.isArray(data)) {
          setActors(data);
        }
      } catch (err) {
        // Fallback gracefully
      } finally {
        if (!isCancelled) setLoading(false);
      }
    }, trimmed ? 350 : 0);

    return () => {
      isCancelled = true;
      clearTimeout(timer);
    };
  }, [searchQuery]);

  const openActorFilmography = async (actor: Actor) => {
    setSelectedActor(actor);
    setLoadingFilms(true);
    setFilmography([]);
    try {
      const res = await fetchApi(`/actors/${actor.id}/movies`);
      if (res?.movies) {
        setFilmography(res.movies);
      }
    } catch (err) {
      // Fallback
    } finally {
      setLoadingFilms(false);
    }
  };

  const handleOrderMovie = async (movie: FilmographyItem) => {
    try {
      await fetchApi("/content-requests", {
        method: "POST",
        body: JSON.stringify({
          title: movie.title,
          original_title: movie.original_title,
          tmdb_id: movie.tmdb_id,
          media_type: "movie",
          release_year: movie.release_year,
          poster_url: movie.poster_url,
        }),
      });
      setRequestedIds((prev) => ({ ...prev, [movie.tmdb_id]: true }));
      setToastMessage(`"${movie.title}" buyurtmasi qabul qilindi!`);
      setTimeout(() => setToastMessage(null), 4000);
    } catch (err) {
      setToastMessage("Buyurtma yuborishda xatolik yuz berdi");
      setTimeout(() => setToastMessage(null), 3000);
    }
  };

  return (
    <div className="min-h-screen pt-20 sm:pt-24 pb-28 xl:pb-16 px-4 md:px-8 bg-background-obsidian text-text-primary">
      {/* Toast Alert */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 bg-emerald-500 text-black font-bold px-4 py-3 rounded-xl shadow-2xl flex items-center gap-2 animate-bounce">
          <span className="material-symbols-outlined text-xl">check_circle</span>
          <span className="text-xs sm:text-sm">{toastMessage}</span>
        </div>
      )}

      <div className="max-w-5xl mx-auto space-y-6">
        {/* Header Bar */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-white/10">
          <div className="flex items-center gap-3">
            <BackButton fallbackUrl="/" />
            <div>
              <h1 className="text-xl sm:text-2xl font-black text-text-primary font-headline-md tracking-tight flex items-center gap-2">
                <span className="material-symbols-outlined text-rating-gold text-2xl">groups</span>
                <span>Aktyorlar va Ijodkorlar</span>
              </h1>
              <p className="text-xs text-text-secondary mt-0.5">
                Mashhur kino yulduzlari va ularning TMDb filmlari to&apos;plami ({actors.length} ta ijodkor)
              </p>
            </div>
          </div>

          {/* Actor Search Input */}
          <div className="relative w-full sm:w-72">
            <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-text-secondary text-lg pointer-events-none">
              search
            </span>
            <input
              type="text"
              placeholder="Aktyor ismini qidiring..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-white/5 border border-white/10 rounded-xl pl-10 pr-4 py-2 text-white text-xs outline-none focus:border-white/20 transition-colors"
            />
          </div>
        </div>

        {/* Actors Grid: Compact 3-col on mobile, 4 on sm, 5 on md, 6 on lg */}
        {loading ? (
          <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 gap-2.5 sm:gap-4 md:gap-5">
            {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12].map((i) => (
              <div key={i} className="h-36 sm:h-44 rounded-xl sm:rounded-2xl bg-white/5 animate-pulse" />
            ))}
          </div>
        ) : actors.length === 0 ? (
          <div className="text-center py-16 bg-white/[0.02] border border-white/5 rounded-3xl">
            <span className="material-symbols-outlined text-4xl text-text-secondary mb-2 opacity-40">person_search</span>
            <p className="text-sm text-text-secondary">Aktyor topilmadi. Boshqa ism bilan qidirib ko&apos;ring.</p>
          </div>
        ) : (
          <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 gap-2.5 sm:gap-4 md:gap-5">
            {actors.map((actor) => (
              <ActorCard
                key={actor.id}
                actor={actor}
                onOpenFilmography={openActorFilmography}
              />
            ))}
          </div>
        )}
      </div>

      {/* Filmography Modal */}
      {selectedActor && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-4 overflow-y-auto">
          <div className="bg-[#181920] border border-white/15 rounded-3xl w-full max-w-3xl max-h-[85vh] flex flex-col overflow-hidden shadow-2xl">
            {/* Modal Header */}
            <div className="p-4 sm:p-6 border-b border-white/10 flex items-center justify-between bg-white/[0.02]">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-full overflow-hidden relative shrink-0 border border-white/20 bg-white/5">
                  {selectedActor.photo_url ? (
                    <Image
                      src={selectedActor.photo_url}
                      alt={selectedActor.name}
                      fill
                      sizes="48px"
                      className="object-cover"
                    />
                  ) : (
                    <span className="material-symbols-outlined text-2xl text-white/40 flex items-center justify-center h-full">person</span>
                  )}
                </div>
                <div>
                  <h2 className="text-base sm:text-lg font-bold text-white">
                    {selectedActor.name} &mdash; Filmografiya
                  </h2>
                  <p className="text-xs text-text-secondary">
                    {selectedActor.original_name} ishtirokidagi filmlar ro&apos;yxati
                  </p>
                </div>
              </div>

              <button
                onClick={() => setSelectedActor(null)}
                className="w-9 h-9 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center text-white transition-all cursor-pointer"
                aria-label="Yopish"
              >
                <span className="material-symbols-outlined text-lg">close</span>
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-4 sm:p-6 overflow-y-auto flex-1">
              {loadingFilms ? (
                <div className="space-y-3">
                  {[1, 2, 3, 4].map((i) => (
                    <div key={i} className="h-16 rounded-xl bg-white/5 animate-pulse" />
                  ))}
                </div>
              ) : filmography.length === 0 ? (
                <div className="text-center py-12 text-text-secondary text-sm">
                  Ushbu aktyor ishtirokidagi filmlar topilmadi.
                </div>
              ) : (
                <div className="space-y-2.5">
                  {filmography.map((movie) => {
                    const isRequested = Boolean(requestedIds[movie.tmdb_id]);

                    return (
                      <div
                        key={movie.tmdb_id}
                        className="flex items-center justify-between gap-3 p-3 rounded-2xl bg-white/[0.03] hover:bg-white/[0.06] border border-white/5 transition-all"
                      >
                        <div className="flex items-center gap-3 min-w-0">
                          <div className="relative w-10 h-14 rounded-lg overflow-hidden shrink-0 bg-white/10">
                            {movie.poster_url ? (
                              <Image
                                src={movie.poster_url}
                                alt={movie.title}
                                fill
                                sizes="40px"
                                className="object-cover"
                              />
                            ) : (
                              <div className="w-full h-full flex items-center justify-center text-white/30 text-[10px]">
                                Rasm
                              </div>
                            )}
                          </div>
                          <div className="min-w-0">
                            <h4 className="text-xs sm:text-sm font-semibold text-white truncate">
                              {movie.title}
                            </h4>
                            <p className="text-[11px] text-text-secondary truncate">
                              {movie.release_year ? `${movie.release_year} y.` : ""} {movie.character ? `• ${movie.character}` : ""}
                            </p>
                          </div>
                        </div>

                        {/* Action buttons based on availability */}
                        <div className="shrink-0 flex items-center gap-2">
                          {movie.is_available && movie.local_movie ? (
                            <Link
                              href={movie.local_movie.is_series ? `/series/${movie.local_movie.id}` : `/movie/${movie.local_movie.code}`}
                              className="px-3.5 py-1.5 rounded-xl bg-emerald-500/20 hover:bg-emerald-500 text-emerald-300 hover:text-black border border-emerald-500/40 text-xs font-bold transition-all flex items-center gap-1.5"
                            >
                              <span className="material-symbols-outlined text-sm">play_circle</span>
                              <span>Tomosha qilish</span>
                            </Link>
                          ) : (
                            <button
                              type="button"
                              onClick={() => handleOrderMovie(movie)}
                              disabled={isRequested}
                              className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 border cursor-pointer ${
                                isRequested
                                  ? "bg-white/10 border-white/20 text-white/60 cursor-default"
                                  : "bg-white/5 hover:bg-primary/20 text-primary border-primary/30 hover:border-primary"
                              }`}
                            >
                              <span className="material-symbols-outlined text-sm">
                                {isRequested ? "check" : "add_task"}
                              </span>
                              <span>{isRequested ? "Buyurtma berildi" : "Buyurtma berish"}</span>
                            </button>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
