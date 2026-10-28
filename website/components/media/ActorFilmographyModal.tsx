"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { fetchApi } from "@/lib/api";

export interface FilmographyMovie {
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

export interface ActorModalData {
  id: number;
  name: string;
  original_name?: string;
  photo_url?: string | null;
  role?: string;
}

interface ActorFilmographyModalProps {
  actor: ActorModalData | null;
  onClose: () => void;
}

export default function ActorFilmographyModal({
  actor,
  onClose,
}: ActorFilmographyModalProps) {
  const [filmography, setFilmography] = useState<FilmographyMovie[]>([]);
  const [loading, setLoading] = useState(false);
  const [requestedIds, setRequestedIds] = useState<Record<number, boolean>>({});
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!actor) {
      setFilmography([]);
      return;
    }

    let isMounted = true;
    setLoading(true);
    setFilmography([]);

    async function loadFilmography() {
      try {
        const res = await fetchApi(`/actors/${actor!.id}/movies`);
        if (isMounted && res?.movies && Array.isArray(res.movies)) {
          setFilmography(res.movies);
        }
      } catch (err) {
        // Graceful error fallback
      } finally {
        if (isMounted) setLoading(false);
      }
    }

    loadFilmography();
    return () => {
      isMounted = false;
    };
  }, [actor]);

  // Handle escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    if (actor) {
      window.addEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "hidden";
    }
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "";
    };
  }, [actor, onClose]);

  if (!actor) return null;

  const handleOrderMovie = async (movie: FilmographyMovie) => {
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
    } catch {
      setToastMessage("Buyurtma yuborishda xatolik yuz berdi");
      setTimeout(() => setToastMessage(null), 3000);
    }
  };

  return (
    <div
      onClick={onClose}
      className="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-md p-4 overflow-y-auto"
    >
      {/* Toast Alert */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-[110] bg-emerald-500 text-black font-bold px-4 py-3 rounded-xl shadow-2xl flex items-center gap-2 animate-bounce">
          <span className="material-symbols-outlined text-xl">check_circle</span>
          <span className="text-xs sm:text-sm">{toastMessage}</span>
        </div>
      )}

      <div
        onClick={(e) => e.stopPropagation()}
        className="bg-[#181920] border border-white/15 rounded-3xl w-full max-w-3xl max-h-[85vh] flex flex-col overflow-hidden shadow-2xl animate-in fade-in zoom-in-95 duration-200"
      >
        {/* Modal Header */}
        <div className="p-4 sm:p-6 border-b border-white/10 flex items-center justify-between bg-white/[0.02]">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-full overflow-hidden relative shrink-0 border border-white/20 bg-white/5 flex items-center justify-center">
              {actor.photo_url ? (
                <Image
                  src={actor.photo_url}
                  alt={actor.name}
                  fill
                  sizes="48px"
                  className="object-cover"
                />
              ) : (
                <span className="material-symbols-outlined text-2xl text-white/40">
                  person
                </span>
              )}
            </div>
            <div>
              <h2 className="text-base sm:text-lg font-bold text-white flex items-center gap-2">
                <span>{actor.name}</span>
                {actor.role && (
                  <span className="text-[11px] font-normal text-white/50 bg-white/5 px-2 py-0.5 rounded-full border border-white/5">
                    {actor.role}
                  </span>
                )}
              </h2>
              <p className="text-xs text-text-secondary">
                {actor.original_name ? `${actor.original_name} — ` : ""}
                TMDb filmografiyasi
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="w-9 h-9 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center text-white transition-all cursor-pointer"
            aria-label="Yopish"
          >
            <span className="material-symbols-outlined text-lg">close</span>
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-4 sm:p-6 overflow-y-auto flex-1">
          {loading ? (
            <div className="space-y-3">
              {[1, 2, 3, 4, 5].map((i) => (
                <div
                  key={i}
                  className="h-16 rounded-xl bg-white/5 animate-pulse"
                />
              ))}
            </div>
          ) : filmography.length === 0 ? (
            <div className="text-center py-12 text-text-secondary text-sm">
              Ushbu ijodkor ishtirokidagi filmlar topilmadi.
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
                          {movie.release_year ? `${movie.release_year} y.` : ""}{" "}
                          {movie.character ? `• ${movie.character}` : ""}
                        </p>
                      </div>
                    </div>

                    {/* Action buttons based on availability */}
                    <div className="shrink-0 flex items-center gap-2">
                      {movie.is_available && movie.local_movie ? (
                        <Link
                          href={
                            movie.local_movie.is_series
                              ? `/series/${movie.local_movie.id}`
                              : `/movie/${movie.local_movie.code}`
                          }
                          className="px-3.5 py-1.5 rounded-xl bg-emerald-500/20 hover:bg-emerald-500 text-emerald-300 hover:text-black border border-emerald-500/40 text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer"
                        >
                          <span className="material-symbols-outlined text-sm">
                            play_circle
                          </span>
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
                          <span>
                            {isRequested ? "Buyurtma berildi" : "Buyurtma berish"}
                          </span>
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
  );
}
