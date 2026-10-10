"use client";

import { useState } from "react";
import ReportIssueModal from "./ReportIssueModal";

interface ReportIssueButtonProps {
  mediaType: "movie" | "series";
  movieId?: number;
  seriesId?: number;
  episodeId?: number;
  mediaTitle: string;
  seasonNumber?: number;
  episodeNumber?: number;
  className?: string;
  variant?: "button" | "icon" | "compact";
}

export default function ReportIssueButton({
  mediaType,
  movieId,
  seriesId,
  episodeId,
  mediaTitle,
  seasonNumber,
  episodeNumber,
  className = "",
  variant = "button"
}: ReportIssueButtonProps) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      {variant === "icon" ? (
        <button
          type="button"
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            setIsOpen(true);
          }}
          className={`p-1.5 sm:p-2 rounded-lg bg-black/40 hover:bg-amber-500/20 text-text-secondary hover:text-amber-300 border border-white/10 hover:border-amber-500/30 transition-all ${className}`}
          title="Xatolik haqida xabar berish"
        >
          <span className="material-symbols-outlined text-base">report_problem</span>
        </button>
      ) : variant === "compact" ? (
        <button
          type="button"
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            setIsOpen(true);
          }}
          className={`inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-lg bg-black/40 hover:bg-amber-500/15 text-text-secondary hover:text-amber-300 border border-white/10 hover:border-amber-500/30 transition-all ${className}`}
        >
          <span className="material-symbols-outlined text-[14px] text-amber-400">report_problem</span>
          <span>Muammo bormi?</span>
        </button>
      ) : (
        <button
          type="button"
          onClick={() => setIsOpen(true)}
          className={`flex items-center justify-center gap-2 px-5 py-3.5 sm:py-4 rounded-xl font-label-caps text-xs sm:text-sm uppercase tracking-wider font-bold bg-white/5 hover:bg-amber-500/15 text-text-secondary hover:text-amber-300 border border-white/10 hover:border-amber-500/30 transition-all active:scale-95 ${className}`}
        >
          <span className="material-symbols-outlined text-base sm:text-lg text-amber-400">report_problem</span>
          <span>Xatolik haqida xabar berish</span>
        </button>
      )}

      <ReportIssueModal
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        mediaType={mediaType}
        movieId={movieId}
        seriesId={seriesId}
        episodeId={episodeId}
        mediaTitle={mediaTitle}
        seasonNumber={seasonNumber}
        episodeNumber={episodeNumber}
      />
    </>
  );
}
