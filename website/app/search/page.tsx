import { fetchApi } from "@/lib/api";
import Link from "next/link";
import Image from "next/image";
import { Metadata } from "next";

// This page reads query params, so it will be dynamically rendered
export const dynamic = "force-dynamic";

export async function generateMetadata({ searchParams }: { searchParams: { q?: string, type?: string } }): Promise<Metadata> {
  const query = searchParams.q || "";
  const type = searchParams.type === "series" ? "seriallar" : "kinolar";
  if (!query) {
    return {
      title: "Qidiruv va Kashf etish - Kinochi",
      description: "Eng so'nggi kinolar, seriallar, anime va doramalarni qidiring va tomosha qiling.",
    };
  }
  return {
    title: `"${query}" qidiruv natijalari - Kinochi`,
    description: `"${query}" bo'yicha topilgan barcha ${type} ro'yxati.`,
  };
}

const POPULAR_SEARCH_TAGS = [
  "Jangari",
  "Komediya",
  "Fantastika",
  "Anime",
  "Dorama",
  "Multfilm",
  "Qo'rqinchli",
  "Melodrama",
  "Kriminal",
  "Tarixiy"
];

export default async function SearchPage({ searchParams }: { searchParams: { q?: string, type?: string } }) {
  const query = searchParams.q || "";
  const specificType = searchParams.type; // "series" or "movie" or undefined
  
  let results: any[] = [];
  const defaultItems: any[] = [];
  let errorMsg: string | null = null;

  // 1. Fetch default trending/recommended items so the page is never empty
  try {
    const [moviesRes, seriesRes] = await Promise.all([
      fetchApi('/movies?limit=12&exclude_paged=true').catch(() => ({ items: [] })),
      fetchApi('/series?limit=12&exclude_paged=true').catch(() => ({ items: [] })),
    ]);

    const defaultMovies = (moviesRes?.items || []).map((m: any) => ({ ...m, isSeries: false }));
    const defaultSeries = (seriesRes?.items || []).map((s: any) => ({ ...s, isSeries: true }));

    // Interleave for a balanced recommendation mix
    const maxLen = Math.max(defaultMovies.length, defaultSeries.length);
    for (let i = 0; i < maxLen; i++) {
      if (i < defaultMovies.length) defaultItems.push(defaultMovies[i]);
      if (i < defaultSeries.length) defaultItems.push(defaultSeries[i]);
    }
  } catch (err) {
    console.error("Failed to load default recommendations for search page:", err);
  }

  // 2. Perform search if query is provided
  if (query.trim().length >= 2) {
    try {
      if (specificType === "series") {
        const res = await fetchApi(`/series/search?q=${encodeURIComponent(query)}&limit=40`);
        results = (res.items || []).map((i: any) => ({ ...i, isSeries: true }));
      } else if (specificType === "movie") {
        const res = await fetchApi(`/movies/search?q=${encodeURIComponent(query)}&limit=40`);
        results = (res.items || []).map((i: any) => ({ ...i, isSeries: false }));
      } else {
        // Search both
        const [moviesRes, seriesRes] = await Promise.all([
          fetchApi(`/movies/search?q=${encodeURIComponent(query)}&limit=24`),
          fetchApi(`/series/search?q=${encodeURIComponent(query)}&limit=24`)
        ]);
        const movies = (moviesRes.items || []).map((i: any) => ({ ...i, isSeries: false }));
        const series = (seriesRes.items || []).map((i: any) => ({ ...i, isSeries: true }));
        
        results = [...movies, ...series];
      }
    } catch (error: any) {
      errorMsg = error.message;
    }
  }

  const isSearchActive = query.trim().length >= 2;

  const renderCard = (item: any, idx: number) => {
    const isSeries = item.isSeries !== undefined ? item.isSeries : specificType === "series";
    const linkUrl = isSeries ? `/series/${item.id}` : `/movie/${item.code}`;
    const key = `${isSeries ? 's' : 'm'}-${isSeries ? item.id : item.code}-${idx}`;
    const rating = item.imdb_rating || item.tmdb_rating || "N/A";

    return (
      <Link 
        href={linkUrl} 
        key={key} 
        className="group relative aspect-[2/3] rounded-xl overflow-hidden cursor-pointer bg-surface-container hover:scale-105 transition-transform duration-300 shadow-lg ring-1 ring-white/10 hover:ring-white/25"
      >
        {item.poster_url ? (
          <Image 
            src={item.poster_url} 
            alt={item.title}
            fill
            sizes="(max-width: 640px) 50vw, (max-width: 1024px) 33vw, 16vw"
            className="object-cover"
          />
        ) : (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-surface-container-high text-gray-500 border border-white/5">
            <span className="material-symbols-outlined text-4xl mb-2 opacity-30">{isSeries ? "tv" : "movie"}</span>
          </div>
        )}
        
        <div className="absolute inset-0 bg-gradient-to-t from-background-obsidian via-background-obsidian/50 to-transparent opacity-80 group-hover:opacity-100 transition-opacity"></div>
        
        <div className="absolute top-2 right-2 px-2 py-1 bg-black/60 backdrop-blur-sm rounded text-rating-gold flex items-center gap-1 border border-white/10 font-bold text-xs">
          <span className="material-symbols-outlined text-[14px]" style={{ fontVariationSettings: "'FILL' 1" }}>star</span>
          <span>{rating}</span>
        </div>
        
        <div className="absolute bottom-0 left-0 w-full p-3 sm:p-4 transform translate-y-1 group-hover:translate-y-0 transition-transform">
          <div className="flex gap-1 mb-1 flex-wrap">
            <span className="px-1.5 py-0.5 bg-white/10 backdrop-blur-sm rounded text-[10px] font-bold text-text-secondary uppercase tracking-wider">
              {isSeries ? item.categories?.[0]?.name || "Serial" : item.genres?.split(',')[0] || "Kino"}
            </span>
            {item.release_year && (
              <span className="px-1.5 py-0.5 bg-white/10 backdrop-blur-sm rounded text-[10px] font-bold text-text-secondary uppercase tracking-wider">
                {item.release_year}
              </span>
            )}
          </div>
          <h3 className="font-body-lg text-sm sm:text-base text-text-primary font-bold line-clamp-2 drop-shadow-md">
            {item.title}
          </h3>
        </div>
      </Link>
    );
  };

  return (
    <div className="min-h-screen pt-20 sm:pt-24 md:pt-28 pb-margin-desktop px-gutter bg-background-obsidian">
      <div className="max-w-container-max mx-auto">
        
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl sm:text-3xl md:text-4xl font-display-hero font-bold text-white mb-2">
            {isSearchActive
              ? (specificType === "series" ? "Seriallar bo'yicha qidiruv natijalari" : 
                 specificType === "movie" ? "Kinolar bo'yicha qidiruv natijalari" : 
                 "Qidiruv natijalari")
              : "Qidiruv va Kashf etish"}
          </h1>
          <p className="text-text-secondary text-sm sm:text-base">
            {isSearchActive
              ? `"${query}" so'rovi bo'yicha ${results.length} ta natija topildi`
              : "Sevimli kinolaringiz, seriallaringiz yoki janrlarni oson toping"}
          </p>
        </div>

        {/* In-page Search Input */}
        <div className="mb-6 max-w-2xl">
          <form action="/search" method="GET" className="flex items-center bg-white/5 hover:bg-white/10 rounded-full px-5 py-3 border border-white/10 focus-within:border-white/30 focus-within:bg-white/10 transition-all shadow-inner">
            <span className="material-symbols-outlined text-text-secondary mr-3 text-[22px]">search</span>
            <input 
              type="text" 
              name="q"
              defaultValue={query}
              className="bg-transparent border-none focus:ring-0 text-text-primary text-base w-full outline-none placeholder:text-text-secondary" 
              placeholder="Kinolar va seriallarni qidirish..." 
            />
            {query && (
              <Link 
                href="/search" 
                className="text-text-secondary hover:text-white p-1 rounded-full hover:bg-white/10 transition-colors ml-2"
                title="Qidiruvni tozalash"
              >
                <span className="material-symbols-outlined text-[18px]">close</span>
              </Link>
            )}
          </form>
        </div>

        {/* Popular Category Chips */}
        <div className="mb-8">
          <div className="flex items-center gap-1.5 mb-2.5 text-xs text-text-secondary font-medium">
            <span className="material-symbols-outlined text-[16px] text-amber-400">local_fire_department</span>
            <span>Ommabop qidiruvlar:</span>
          </div>
          <div className="flex items-center gap-2 overflow-x-auto pb-2 hide-scrollbar">
            {POPULAR_SEARCH_TAGS.map((tag) => {
              const isSelected = query.toLowerCase() === tag.toLowerCase();
              return (
                <Link
                  key={tag}
                  href={`/search?q=${encodeURIComponent(tag)}`}
                  className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all shrink-0 active:scale-95 border ${
                    isSelected
                      ? "bg-white/20 text-white border-white/30 font-bold shadow-md"
                      : "bg-white/5 hover:bg-white/10 text-text-secondary hover:text-white border-white/10 hover:border-white/20"
                  }`}
                >
                  {tag}
                </Link>
              );
            })}
          </div>
        </div>

        {/* Search Results State */}
        {errorMsg ? (
          <div className="text-red-400 p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-base mb-8">
            Xatolik yuz berdi: {errorMsg}
          </div>
        ) : isSearchActive ? (
          results.length > 0 ? (
            <div className="mb-12">
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3 sm:gap-4 md:gap-6">
                {results.map((item, idx) => renderCard(item, idx))}
              </div>
            </div>
          ) : (
            <div className="mb-12">
              {/* Modern Obsidian Empty State */}
              <div className="text-center py-16 px-6 bg-white/[0.03] rounded-3xl border border-white/10 max-w-xl mx-auto mb-12">
                <span className="material-symbols-outlined text-6xl text-text-secondary mb-3 opacity-60">search_off</span>
                <h3 className="text-xl font-bold text-white mb-2">Hech narsa topilmadi</h3>
                <p className="text-sm text-text-secondary leading-relaxed">
                  &ldquo;{query}&rdquo; so&apos;rovi bo&apos;yicha film yoki serial topilmadi. So&apos;zni to&apos;g&apos;ri yozganingizni tekshiring yoki quyidagi sara premyeralarni tomosha qiling.
                </p>
              </div>

              {/* Suggestions below empty state */}
              {defaultItems.length > 0 && (
                <div>
                  <div className="mb-5 flex items-center justify-between">
                    <h2 className="font-headline-md text-xl sm:text-2xl font-bold text-text-primary flex items-center gap-2.5">
                      <span className="w-1 h-5 bg-rating-gold rounded-full block"></span>
                      <span>Sizga yoqishi mumkin bo&apos;lgan premyeralar</span>
                    </h2>
                  </div>
                  <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3 sm:gap-4 md:gap-6">
                    {defaultItems.slice(0, 12).map((item, idx) => renderCard(item, idx))}
                  </div>
                </div>
              )}
            </div>
          )
        ) : (
          /* Default state when user just opened /search */
          <div>
            <div className="mb-5 flex items-center justify-between">
              <div>
                <h2 className="font-headline-md text-xl sm:text-2xl font-bold text-text-primary flex items-center gap-2.5">
                  <span className="w-1 h-5 sm:h-6 bg-rating-gold rounded-full block"></span>
                  <span>Tavsiya etilayotgan premyeralar</span>
                </h2>
                <p className="text-xs sm:text-sm text-text-secondary mt-1">
                  Eng so&apos;nggi va sara kino hamda seriallar to&apos;plami
                </p>
              </div>
            </div>

            {defaultItems.length > 0 ? (
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3 sm:gap-4 md:gap-6">
                {defaultItems.map((item, idx) => renderCard(item, idx))}
              </div>
            ) : (
              <div className="text-center py-20 text-text-secondary">
                <span className="material-symbols-outlined text-5xl mb-2 opacity-30">movie</span>
                <p>Kinolar yuklanmoqda...</p>
              </div>
            )}
          </div>
        )}

      </div>
    </div>
  );
}
