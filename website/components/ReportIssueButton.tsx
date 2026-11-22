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
          className={`p-1.5 sm:p-2 rounded-lg bg-black/40 hover:bg-primary/20 text-text-secondary hover:text-white border border-white/10 hover:border-primary/40 transition-all ${className}`}
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
          className={`inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-lg bg-black/40 hover:bg-primary/15 text-text-secondary hover:text-white border border-white/10 hover:border-primary/40 transition-all ${className}`}
        >
          <span className="material-symbols-outlined text-[14px] text-primary">report_problem</span>
          <span>Muammo bormi?</span>
        </button>
      ) : (
        <button
          type="button"
          onClick={() => setIsOpen(true)}
          title="Xatolik haqida xabar berish"
          className={`flex items-center justify-center gap-1.5 px-3 sm:px-6 py-3 sm:py-3.5 rounded-xl font-label-caps text-xs sm:text-sm uppercase tracking-wider font-bold bg-white/10 hover:bg-[#E50914]/15 text-white border border-white/15 hover:border-[#E50914]/50 shadow-md shadow-black/20 transition-all duration-200 active:scale-95 cursor-pointer ${className}`}
        >
          <span className="material-symbols-outlined text-[18px] text-[#E50914] shrink-0">report_problem</span>
          <span className="truncate">Xatolik haqida</span>
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
