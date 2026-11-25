"use client";

import { useEffect } from "react";
import { API_URL } from "@/lib/api";

interface MediaViewTrackerProps {
  mediaType: "movie" | "series";
  movieId?: number;
  seriesId?: number;
}

export default function MediaViewTracker({
  mediaType,
  movieId,
  seriesId,
}: MediaViewTrackerProps) {
  useEffect(() => {
    const targetId = mediaType === "movie" ? movieId : seriesId;
    if (!targetId) return;

    const storageKey = `mediaplus_viewed_${mediaType}_${targetId}`;
    try {
      if (sessionStorage.getItem(storageKey)) return;
      sessionStorage.setItem(storageKey, "1");
    } catch {
      // sessionStorage may be unavailable in restricted contexts
    }

    fetch(`${API_URL}/statistics/track-view`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        media_type: mediaType,
        movie_id: mediaType === "movie" ? movieId : undefined,
        series_id: mediaType === "series" ? seriesId : undefined,
        source: "web",
      }),
      keepalive: true,
    }).catch(() => {});
  }, [mediaType, movieId, seriesId]);

  return null;
}
