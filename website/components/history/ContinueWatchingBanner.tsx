"use client";

import Image from "next/image";
import Link from "next/link";
import { HistoryItem } from "@/lib/api/history";

export default function ContinueWatchingBanner({ items }: { items: HistoryItem[] }) {
  const latestInProgress = items.find(item => item.status === "in_progress");

  if (!latestInProgress) return null;

  const isSeries = latestInProgress.type === "episode";
  const title = isSeries && latestInProgress.episode 
    ? `${latestInProgress.episode.series_title} - ${latestInProgress.episode.display_code}`
    : latestInProgress.movie?.title || "Noma'lum";
  
  const posterUrl = isSeries 
    ? latestInProgress.episode?.series_poster 
    : latestInProgress.movie?.poster_url;

  const href = isSeries && latestInProgress.episode
    ? `/series/${latestInProgress.episode.series_id}`
    : `/movie/${latestInProgress.movie?.code}`;

  return (
    <Link 
      href={href} 
      className="group relative flex w-full max-w-4xl mx-auto h-[160px] md:h-[220px] rounded-2xl overflow-hidden bg-white/[0.04] hover:bg-white/[0.06] backdrop-blur-xl transition-all border border-white/10 hover:border-white/20 mb-10 shadow-lg hover:shadow-2xl"
    >
      <div className="w-[110px] md:w-[150px] shrink-0 relative h-full bg-white/5">
        {posterUrl ? (
          <Image 
            src={posterUrl} 
            alt={title} 
            fill 
            sizes="(max-width: 768px) 110px, 150px"
            className="object-cover group-hover:scale-105 transition-transform duration-500" 
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <span className="material-symbols-outlined text-4xl opacity-30 text-white">image</span>
          </div>
        )}
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-background-obsidian/40 to-background-obsidian/80 transition-colors"></div>
      </div>

      <div className="flex-1 flex flex-col justify-center p-4 md:p-8 z-10 relative">
        <div className="flex items-center gap-2 mb-2">
          <span className="px-2 py-1 bg-sky-500/15 text-sky-400 rounded text-[10px] md:text-xs font-bold uppercase tracking-wider border border-sky-500/25 flex items-center gap-1">
            <span className="material-symbols-outlined text-[14px]">schedule</span>
            Davom eting
          </span>
          {isSeries && (
            <span className="px-2 py-1 bg-white/10 text-text-secondary rounded text-[10px] md:text-xs font-semibold uppercase tracking-wider border border-white/10">
              Serial
            </span>
          )}
        </div>
        <h2 className="text-xl md:text-3xl font-display-hero font-bold text-white mb-4 line-clamp-2 drop-shadow-md">
          {title}
        </h2>
        <div className="flex items-center gap-2 text-primary-container font-label-caps text-sm tracking-widest font-bold group-hover:text-inverse-primary transition-colors">
          <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>play_circle</span>
          Tomosha qilish
        </div>
      </div>
      
      {/* Background ambient glow based on hover */}
      <div className="absolute inset-0 bg-gradient-to-t from-background-obsidian/40 to-transparent pointer-events-none"></div>
    </Link>
  );
}
