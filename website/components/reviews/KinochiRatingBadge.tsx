"use client";

import { useState, useEffect } from "react";

interface KinochiRatingBadgeProps {
  initialRating?: number | null;
  initialVotesCount?: number;
}

export default function KinochiRatingBadge({ initialRating, initialVotesCount = 0 }: KinochiRatingBadgeProps) {
  const [rating, setRating] = useState<number | null | undefined>(initialRating);
  const [votesCount, setVotesCount] = useState<number>(initialVotesCount);

  useEffect(() => {
    setRating(initialRating);
    setVotesCount(initialVotesCount);
  }, [initialRating, initialVotesCount]);

  useEffect(() => {
    const handleUpdate = (e: any) => {
      if (e.detail) {
        if (e.detail.rating !== undefined) {
          setRating(e.detail.rating);
        }
        if (e.detail.votesCount !== undefined) {
          setVotesCount(e.detail.votesCount);
        }
      }
    };

    window.addEventListener("kinochi:rating_updated", handleUpdate);
    return () => window.removeEventListener("kinochi:rating_updated", handleUpdate);
  }, []);

  const hasRating = rating !== null && rating !== undefined;

  return (
    <div 
      className="inline-flex items-center gap-1.5 h-7 sm:h-8 px-2.5 sm:px-3 rounded-lg bg-sky-500/10 backdrop-blur-md border border-sky-500/20 text-white shadow-sm hover:border-sky-500/35 transition-colors font-medium text-xs" 
      title="Kinochi hamjamiyat reytingi"
    >
      <span className="material-symbols-outlined text-[15px] text-sky-400" style={{ fontVariationSettings: "'FILL' 1" }}>
        hotel_class
      </span>
      <span className="text-sky-200 font-bold tracking-tight">
        {hasRating ? Number(rating).toFixed(1) : "Yangi"}
      </span>
      <span className="text-[10px] text-sky-400/80 font-normal uppercase tracking-wider">
        {votesCount > 0 ? `(${votesCount})` : "Kinochi"}
      </span>
    </div>
  );
}

