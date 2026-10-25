"use client";

import { useState, useEffect } from "react";
import Image from "next/image";
import Link from "next/link";
import RequestMovieModal, { RequestTargetItem } from "./RequestMovieModal";

interface ExternalItem {
  tmdb_id?: number | null;
  kinopoisk_id?: number | null;
  title: string;
  original_title?: string | null;
  media_type: "movie" | "series";
  release_year?: number | null;
  poster_url?: string | null;
  overview?: string | null;
  vote_average?: number | null;
  in_library: boolean;
  library_code?: string | null;
  library_id?: number | null;
  request_count: number;
  is_requested: boolean;
}

interface ExternalSearchSectionProps {
  query?: string;
  items: ExternalItem[];
  title?: string;
  subtitle?: string;
  onRefresh?: () => void;
}

const getItemKey = (it: { tmdb_id?: number | null; kinopoisk_id?: number | null; title: string }) => {
  if (it.tmdb_id) return `tmdb:${it.tmdb_id}`;
  if (it.kinopoisk_id) return `kp:${it.kinopoisk_id}`;
  return `title:${it.title.toLowerCase().trim()}`;
};

export default function ExternalSearchSection({
  query: _query,
  items,
  title = "Jahon kinolari katalogidan topildi (TMDB & Kinopoisk)",
  subtitle = "Ushbu kinolar hali bazamizga yuklanmagan. Istagan kinongizni tanlab, 'Qo'shishni so'rash' tugmasini bosing — adminlarimiz uni birinchi navbatda joylaydi!",
  onRefresh,
}: ExternalSearchSectionProps) {
  const [itemList, setItemList] = useState<ExternalItem[]>(items || []);
  const [selectedItem, setSelectedItem] = useState<RequestTargetItem | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [requestedKeys, setRequestedKeys] = useState<Set<string>>(new Set());

  useEffect(() => {
    setItemList(items || []);
  }, [items]);

  useEffect(() => {
    try {
      const saved = localStorage.getItem("kinochi_requested_content_keys");
      if (saved) {
        setRequestedKeys(new Set(JSON.parse(saved)));
      }
    } catch {}
  }, []);

  if (!itemList || itemList.length === 0) return null;

  const handleOpenRequest = (item: ExternalItem) => {
    setSelectedItem({
      tmdb_id: item.tmdb_id,
      kinopoisk_id: item.kinopoisk_id,
      title: item.title,
      original_title: item.original_title,
      media_type: item.media_type,
      release_year: item.release_year,
      poster_url: item.poster_url,
      overview: item.overview,
      vote_average: item.vote_average,
    });
    setIsModalOpen(true);
  };

  const handleSuccess = () => {
    if (selectedItem) {
      const key = getItemKey(selectedItem);
      setRequestedKeys((prev) => {
        const next = new Set(prev).add(key);
        try {
          localStorage.setItem("kinochi_requested_content_keys", JSON.stringify(Array.from(next)));
        } catch {}
        return next;
      });
      setItemList((prev) =>
        prev.map((it) => {
          if (getItemKey(it) === key) {
            return {
              ...it,
              request_count: Math.max(1, (it.request_count || 0) + 1),
              is_requested: true,
            };
          }
          return it;
        })
      );
    }
    if (onRefresh) onRefresh();
  };

  return (
    <div className="mt-8 mb-12 p-6 sm:p-8 rounded-3xl bg-gradient-to-b from-white/[0.05] to-transparent border border-white/10 shadow-2xl backdrop-blur-sm">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 pb-4 border-b border-white/10">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="flex h-2.5 w-2.5 rounded-full bg-cyan-400 animate-pulse"></span>
            <span className="text-[11px] font-bold tracking-wider text-cyan-400 uppercase">
              Global Qidiruv • TMDB & Kinopoisk
            </span>
          </div>
          <h3 className="text-xl sm:text-2xl font-bold text-white flex items-center gap-2">
            <span>{title}</span>
          </h3>
          <p className="text-xs sm:text-sm text-text-secondary mt-1 max-w-2xl leading-relaxed">
            {subtitle}
          </p>
        </div>

        <Link
          href="/requests"
          className="self-start sm:self-auto px-4 py-2 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-xs font-semibold text-text-secondary hover:text-white transition-all flex items-center gap-1.5 shrink-0"
        >
          <span className="material-symbols-outlined text-[16px]">format_list_bulleted</span>
          <span>Barcha so&apos;rovlar</span>
        </Link>
      </div>

      {/* Grid of Results */}
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3 sm:gap-4 md:gap-5">
        {itemList.map((item, idx) => {
          const itemKey = getItemKey(item);
          const isReq = item.is_requested || requestedKeys.has(itemKey);
          const currentCount = isReq ? Math.max(1, item.request_count || 1) : (item.request_count || 0);
          const cardKey = `ext-${item.tmdb_id || item.kinopoisk_id || idx}`;

          return (
            <div
              key={cardKey}
              className="group relative flex flex-col rounded-2xl overflow-hidden bg-surface-container border border-white/10 hover:border-cyan-500/40 transition-all duration-300 shadow-lg hover:shadow-cyan-500/10"
            >
              {/* Poster Aspect Ratio Container */}
              <div className="relative aspect-[2/3] w-full overflow-hidden bg-surface-container-high">
                {item.poster_url ? (
                  <Image
                    src={item.poster_url}
                    alt={item.title}
                    fill
                    sizes="(max-width: 640px) 50vw, (max-width: 1024px) 33vw, 16vw"
                    className="object-cover group-hover:scale-105 transition-transform duration-300"
                  />
                ) : (
                  <div className="w-full h-full flex flex-col items-center justify-center text-text-secondary">
                    <span className="material-symbols-outlined text-4xl mb-1 opacity-30">movie</span>
                    <span className="text-[10px] text-text-secondary">Poster yo&apos;q</span>
                  </div>
                )}

                <div className="absolute inset-0 bg-gradient-to-t from-background-obsidian via-background-obsidian/30 to-transparent opacity-80 group-hover:opacity-90 transition-opacity"></div>

                {/* Rating badge */}
                {item.vote_average ? (
                  <div className="absolute top-2 right-2 px-2 py-0.5 bg-black/70 backdrop-blur-sm rounded text-rating-gold flex items-center gap-1 border border-white/10 font-bold text-[11px]">
                    <span className="material-symbols-outlined text-[12px]" style={{ fontVariationSettings: "'FILL' 1" }}>star</span>
                    <span>{item.vote_average.toFixed(1)}</span>
                  </div>
                ) : null}

                {/* Status Badge */}
                <div className="absolute top-2 left-2">
                  {item.in_library ? (
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/80 text-white backdrop-blur-sm shadow flex items-center gap-1">
                      <span className="material-symbols-outlined text-[12px]">check</span>
                      <span>Mavjud</span>
                    </span>
                  ) : currentCount > 0 ? (
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/90 text-background-obsidian backdrop-blur-sm shadow flex items-center gap-0.5">
                      <span>🔥 {currentCount} so&apos;rov</span>
                    </span>
                  ) : (
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-black/60 text-text-secondary backdrop-blur-sm border border-white/10">
                      Bazada yo&apos;q
                    </span>
                  )}
                </div>

                {/* Bottom title inside poster */}
                <div className="absolute bottom-0 left-0 w-full p-3">
                  <div className="flex gap-1 mb-1 items-center">
                    <span className="px-1.5 py-0.5 bg-white/10 backdrop-blur-sm rounded text-[9px] font-bold text-text-secondary uppercase">
                      {item.media_type === "series" ? "Serial" : "Kino"}
                    </span>
                    {item.release_year && (
                      <span className="text-[10px] font-bold text-text-secondary">
                        {item.release_year}
                      </span>
                    )}
                  </div>
                  <h4 className="font-bold text-xs sm:text-sm text-white line-clamp-2 drop-shadow">
                    {item.title}
                  </h4>
                </div>
              </div>

              {/* Action Button */}
              <div className="p-2.5 bg-white/[0.02] border-t border-white/5">
                {item.in_library ? (
                  <Link
                    href={item.media_type === "series" ? `/series/${item.library_id}` : `/movie/${item.library_code}`}
                    className="w-full py-2 px-3 rounded-xl bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-400 border border-emerald-500/30 text-xs font-bold transition-all flex items-center justify-center gap-1.5"
                  >
                    <span className="material-symbols-outlined text-[16px]">play_arrow</span>
                    <span>Tomosha qilish</span>
                  </Link>
                ) : isReq ? (
                  <button
                    type="button"
                    disabled
                    className="w-full py-2 px-3 rounded-xl bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-xs font-bold transition-all flex items-center justify-center gap-1.5 cursor-default"
                  >
                    <span className="material-symbols-outlined text-[16px]">check_circle</span>
                    <span>So&apos;rov qoldirildi ({currentCount})</span>
                  </button>
                ) : (
                  <button
                    type="button"
                    onClick={() => handleOpenRequest(item)}
                    className="w-full py-2 px-3 rounded-xl bg-white/5 hover:bg-rating-gold hover:text-background-obsidian text-text-primary border border-white/10 hover:border-rating-gold text-xs font-bold transition-all flex items-center justify-center gap-1.5 group/btn"
                  >
                    <span className="material-symbols-outlined text-[16px] text-rating-gold group-hover/btn:text-background-obsidian">
                      add_circle
                    </span>
                    <span>Qo&apos;shishni so&apos;rash</span>
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>

      <RequestMovieModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        item={selectedItem}
        onSuccess={handleSuccess}
      />
    </div>
  );
}
