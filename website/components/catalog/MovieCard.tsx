import Link from "next/link";
import Image from "next/image";
import { CatalogItem } from "@/lib/api/catalog";

export default function MovieCard({ item, statusBadge }: { item: CatalogItem, statusBadge?: "completed" | "in_progress" }) {
  const isSeries = item.is_series;
  const href = isSeries ? `/series/${item.id}` : `/movie/${item.code}`;
  
  return (
    <Link 
      href={href} 
      className="group relative aspect-[2/3] rounded-xl overflow-hidden cursor-pointer bg-surface-container hover:scale-105 transition-transform duration-300 shadow-lg hover:shadow-[0_0_20px_rgba(229,9,20,0.3)] ring-1 ring-white/5 hover:ring-primary-container"
    >
      {item.poster_url ? (
        <Image 
          src={item.poster_url} 
          alt={item.title}
          fill
          sizes="(max-width: 768px) 50vw, (max-width: 1024px) 33vw, 16vw"
          className="object-cover group-hover:scale-110 transition-transform duration-500 ease-out"
        />
      ) : (
        <div className="absolute inset-0 flex flex-col items-center justify-center bg-surface-container-high text-gray-500">
          <span className="material-symbols-outlined text-4xl mb-2 opacity-30">
            {isSeries ? "live_tv" : "movie"}
          </span>
        </div>
      )}
      
      {/* Gradient overlays */}
      <div className="absolute inset-0 bg-gradient-to-t from-background-obsidian via-background-obsidian/50 to-transparent opacity-80 group-hover:opacity-100 transition-opacity duration-300"></div>
      
      {/* Top badges */}
      <div className="absolute top-2 right-2 px-2 py-1 bg-black/60 backdrop-blur-sm rounded text-rating-gold flex items-center gap-1 border border-white/10">
        <span className="material-symbols-outlined text-[14px]" style={{ fontVariationSettings: "'FILL' 1" }}>star</span>
        <span className="font-label-caps text-xs font-bold">{item.imdb_rating || item.tmdb_rating || "N/A"}</span>
      </div>

      {/* Top Left Badges Container */}
      <div className="absolute top-2 left-2 flex flex-col gap-1 items-start">
        {isSeries && (
          <div className="px-2 py-1 bg-primary-container/80 backdrop-blur-sm rounded text-white text-[10px] font-bold uppercase tracking-wider border border-white/10">
            Serial
          </div>
        )}
        {statusBadge === "completed" && (
          <div className="px-2 py-1 bg-green-500/80 backdrop-blur-sm rounded text-white text-[10px] font-bold uppercase tracking-wider border border-white/10 flex items-center gap-1">
            <span className="material-symbols-outlined text-[12px]">check_circle</span>
            Ko'rilgan
          </div>
        )}
        {statusBadge === "in_progress" && (
          <div className="px-2 py-1 bg-blue-500/80 backdrop-blur-sm rounded text-white text-[10px] font-bold uppercase tracking-wider border border-white/10 flex items-center gap-1">
            <span className="material-symbols-outlined text-[12px]">schedule</span>
            Davom etmoqda
          </div>
        )}
      </div>
      
      {/* Bottom content */}
      <div className="absolute bottom-0 left-0 w-full p-3 md:p-4 transform translate-y-2 group-hover:translate-y-0 transition-transform duration-300">
        <div className="flex gap-1 mb-1.5 flex-wrap">
          {item.genres && (
            <span className="px-1.5 py-0.5 bg-white/10 backdrop-blur-sm rounded text-[10px] font-bold text-text-secondary uppercase tracking-wider truncate max-w-[120px]">
              {item.genres}
            </span>
          )}
          {item.release_year && (
            <span className="px-1.5 py-0.5 bg-white/10 backdrop-blur-sm rounded text-[10px] font-bold text-text-secondary uppercase tracking-wider">
              {item.release_year}
            </span>
          )}
        </div>
        <h3 className="font-body-lg text-sm md:text-[16px] font-bold leading-tight text-white mb-1 group-hover:text-primary-container transition-colors line-clamp-2">
          {item.title}
        </h3>
      </div>
    </Link>
  );
}
