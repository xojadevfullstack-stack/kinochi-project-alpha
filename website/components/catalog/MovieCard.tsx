import Link from "next/link";
import { CatalogItem } from "@/lib/api/catalog";
import { isAdultContent } from "@/lib/adult";
import AdultPoster from "@/components/AdultPoster";

export default function MovieCard({ item, statusBadge }: { item: CatalogItem, statusBadge?: "completed" | "in_progress" }) {
  const isSeries = !!item.is_series || (!item.code && !!item.id);
  const is18Plus = isAdultContent(item);
  const href = isSeries ? `/series/${item.id}` : `/movie/${item.code}`;
  
  return (
    <Link 
      href={href} 
      className="group relative aspect-[2/3] rounded-xl overflow-hidden cursor-pointer bg-surface-container hover:scale-105 transition-transform duration-300 shadow-lg ring-1 ring-white/10 hover:ring-white/25"
    >
      {item.poster_url ? (
        <AdultPoster 
          src={item.poster_url} 
          alt={item.title}
          is18Plus={is18Plus}
          fill
          sizes="(max-width: 768px) 50vw, (max-width: 1024px) 33vw, 16vw"
          imageClassName="object-cover group-hover:scale-110 transition-transform duration-500 ease-out"
        />
      ) : (
        <div className="absolute inset-0 flex flex-col items-center justify-center bg-surface-container-high text-gray-500">
          <span className="material-symbols-outlined text-4xl mb-2 opacity-30">
            {isSeries ? "live_tv" : "movie"}
          </span>
        </div>
      )}
      
      {/* Gradient overlays */}
      <div className="absolute inset-0 bg-gradient-to-t from-background-obsidian via-background-obsidian/50 to-transparent opacity-80 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"></div>
      
      {/* Top badges */}
      <div className="absolute top-2 right-2 z-10 px-2 py-1 bg-black/70 backdrop-blur-md rounded text-rating-gold flex items-center gap-1 border border-white/10 pointer-events-none">
        <span className="material-symbols-outlined text-[14px]" style={{ fontVariationSettings: "'FILL' 1" }}>star</span>
        <span className="font-label-caps text-xs font-bold">{item.imdb_rating || item.tmdb_rating || "N/A"}</span>
      </div>

      {/* Top Left Badges Container */}
      <div className="absolute top-2 left-2 z-10 flex flex-col gap-1 items-start pointer-events-none">
        {is18Plus && (
          <div className="px-2 py-0.5 bg-red-600/90 backdrop-blur-md rounded text-white text-[10px] font-black uppercase tracking-wider border border-red-500/40 flex items-center gap-1 shadow-sm shadow-black/50">
            <span className="text-[11px]">🔞</span>
            <span>18+</span>
          </div>
        )}
        {statusBadge === "completed" && (
          <div className="px-2 py-0.5 bg-emerald-500/90 backdrop-blur-md rounded text-white text-[10px] font-bold uppercase tracking-wider border border-emerald-400/30 flex items-center gap-1 shadow-sm shadow-black/40">
            <span className="material-symbols-outlined text-[12px]">check_circle</span>
            Ko'rilgan
          </div>
        )}
        {statusBadge === "in_progress" && (
          <div className="px-2 py-0.5 bg-sky-500/90 backdrop-blur-md rounded text-white text-[10px] font-bold uppercase tracking-wider border border-sky-400/30 flex items-center gap-1 shadow-sm shadow-black/40">
            <span className="material-symbols-outlined text-[12px]">schedule</span>
            Davom etmoqda
          </div>
        )}
      </div>
      
      {/* Bottom content */}
      <div className="absolute bottom-0 left-0 w-full p-3 md:p-4 transform translate-y-2 group-hover:translate-y-0 transition-transform duration-300 z-10 pointer-events-none">
        <div className="flex gap-1 mb-1.5 flex-wrap">
          <span className="px-1.5 py-0.5 bg-white/10 backdrop-blur-sm rounded text-[10px] font-bold text-text-secondary uppercase tracking-wider truncate max-w-[120px]">
            {item.genres?.split(',')[0] || (isSeries ? (item.categories?.[0]?.name || "Serial") : "Kino")}
          </span>
          {item.release_year && (
            <span className="px-1.5 py-0.5 bg-white/10 backdrop-blur-sm rounded text-[10px] font-bold text-text-secondary uppercase tracking-wider">
              {item.release_year}
            </span>
          )}
        </div>
        <h3 className="font-body-lg text-sm md:text-[16px] font-bold leading-tight text-white mb-1 group-hover:text-white transition-colors line-clamp-2">
          {item.title}
        </h3>
      </div>
    </Link>
  );
}
