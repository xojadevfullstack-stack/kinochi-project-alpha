"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { useAuth } from "@/lib/auth/AuthProvider";
import { getRecommendations, RecommendationItem } from "@/lib/api/history";
import MovieCard from "../catalog/MovieCard";

export default function RecommendationsSection() {
  const { status } = useAuth();
  const [items, setItems] = useState<RecommendationItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (status === "authenticated") {
      setLoading(true);
      getRecommendations()
        .then(res => {
          setItems(res.items);
          setLoading(false);
        })
        .catch(err => {
          console.error(err);
          setLoading(false);
        });
    } else {
      setLoading(false);
    }
  }, [status]);

  if (status !== "authenticated" || items.length === 0) {
    return null;
  }

  return (
    <section className="max-w-container-max mx-auto mb-16 mt-8 relative z-20 bg-background-obsidian">
      <div className="px-gutter mb-stack-md flex items-center justify-between">
        <h2 className="font-headline-md text-headline-md text-text-primary flex items-center gap-2">
          <span className="w-1 h-6 bg-rating-gold rounded-full block"></span>
          Siz uchun maxsus
        </h2>
      </div>
      
      {loading ? (
        <div className="flex gap-4 overflow-x-auto px-gutter pb-8 pt-4">
          {[1, 2, 3, 4, 5].map(i => (
            <div key={i} className="w-[160px] md:w-[240px] shrink-0 aspect-[2/3] rounded-xl bg-surface-container animate-pulse"></div>
          ))}
        </div>
      ) : (
        <div className="flex gap-4 overflow-x-auto snap-x hide-scrollbar px-gutter pb-8 pt-4">
          {items.map((item, index) => {
            const isSeries = item.type === "series";
            const catalogItem = {
              id: item.id,
              title: item.title,
              original_title: null,
              imdb_rating: item.rating,
              tmdb_rating: null,
              release_year: null,
              poster_url: item.poster_url,
              code: item.code || "0",
              is_series: isSeries,
              genres: item.genres?.join(', ') || null
            };
            
            return (
              <div key={`${item.id}-${index}`} className="w-[160px] md:w-[240px] shrink-0 snap-start flex flex-col">
                <MovieCard item={catalogItem} />
                <div className="mt-3 px-2">
                  <p className="text-[11px] md:text-xs text-text-secondary italic flex items-center gap-1.5 opacity-80">
                    <span className="material-symbols-outlined text-[14px] text-rating-gold">auto_awesome</span>
                    Sizga tavsiya qilingan
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}
