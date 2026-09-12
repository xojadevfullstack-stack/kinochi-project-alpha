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
      className="flex items-center gap-1.5 text-primary-container bg-primary-container/10 px-3 py-1.5 rounded backdrop-blur-sm border border-primary-container/30 font-bold transition-all" 
      title="Kinochi hamjamiyat reytingi"
    >
      <span className="material-symbols-outlined text-[16px]" style={{ fontVariationSettings: "'FILL' 1" }}>
        hotel_class
      </span>
      <span>{hasRating ? Number(rating).toFixed(1) : "Yangi"}</span>
      <span className="text-[10px] text-primary-container/80 font-normal">
        {votesCount > 0 ? `(${votesCount})` : "Kinochi"}
      </span>
    </div>
  );
}
