"use client";

import React, { useState } from "react";
import { triggerTelegramHaptic } from "@/lib/telegram";
import { saveContinueWatching } from "@/lib/streamHelpers.mjs";
import WebVideoPlayerModal, {
  StreamTranslationItem,
} from "@/components/media/WebVideoPlayerModal";

interface MovieWatchButtonProps {
  movieTitle: string;
  movieCode: string;
  movieId: number;
  posterUrl?: string;
  releaseYear?: number | null;
  imdbRating?: number | null;
  genres?: string | null;
  translations: StreamTranslationItem[];
  telegramUrl: string;
  className?: string;
}

export default function MovieWatchButton({
  movieTitle,
  movieCode,
  movieId,
  posterUrl,
  releaseYear,
  imdbRating,
  genres,
  translations,
  telegramUrl,
  className,
}: MovieWatchButtonProps) {
  const [isOpen, setIsOpen] = useState(false);

  const handleOpen = () => {
    triggerTelegramHaptic("medium");
    saveContinueWatching({
      id: movieId || movieCode,
      code: movieCode,
      title: movieTitle || "Noma'lum film",
      poster_url: posterUrl || null,
      is_series: false,
      release_year: releaseYear || null,
      imdb_rating: imdbRating || null,
      genres: genres || "Kino",
      type: "movie",
    });
    setIsOpen(true);
  };

  return (
    <>
      <button
        type="button"
        onClick={handleOpen}
        className={
          className ||
          "col-span-2 sm:col-span-1 sm:w-auto flex items-center justify-center gap-2 bg-[#E50914] text-white px-5 sm:px-7 py-3 sm:py-3.5 rounded-xl font-label-caps text-xs sm:text-sm uppercase tracking-wider hover:bg-[#B80710] hover:scale-[1.02] hover:-translate-y-0.5 active:scale-95 shadow-lg shadow-[#E50914]/30 transition-all duration-200 font-bold cursor-pointer"
        }
      >
        <span className="material-symbols-outlined text-[20px]" style={{ fontVariationSettings: "'FILL' 1" }}>
          play_circle
        </span>
        <span>SAYTDA KO&apos;RISH</span>
      </button>

      <WebVideoPlayerModal
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        mediaType="movie"
        title={movieTitle}
        posterUrl={posterUrl}
        translations={translations}
        telegramUrl={telegramUrl}
      />
    </>
  );
}
