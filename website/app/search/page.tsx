import { fetchApi } from "@/lib/api";
import Link from "next/link";
import Image from "next/image";
import { Metadata } from "next";

// This page reads query params, so it will be dynamically rendered
export const dynamic = "force-dynamic";

export async function generateMetadata({ searchParams }: { searchParams: { q?: string, type?: string } }): Promise<Metadata> {
  const query = searchParams.q || "";
  const type = searchParams.type === "series" ? "seriallar" : "kinolar";
  return {
    title: `"${query}" qidiruv natijalari - Kinochi`,
    description: `"${query}" bo'yicha topilgan barcha ${type} ro'yxati.`,
  };
}

export default async function SearchPage({ searchParams }: { searchParams: { q?: string, type?: string } }) {
  const query = searchParams.q || "";
  const specificType = searchParams.type; // "series" or "movie" or undefined
  
  let results: any[] = [];
  let errorMsg = null;

  if (query.length >= 2) {
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
          fetchApi(`/movies/search?q=${encodeURIComponent(query)}&limit=20`),
          fetchApi(`/series/search?q=${encodeURIComponent(query)}&limit=20`)
        ]);
        const movies = (moviesRes.items || []).map((i: any) => ({ ...i, isSeries: false }));
        const series = (seriesRes.items || []).map((i: any) => ({ ...i, isSeries: true }));
        
        // Merge and sort somewhat (e.g. by newest) or just concat
        results = [...movies, ...series];
      }
    } catch (error: any) {
      errorMsg = error.message;
    }
  }

  return (
    <div className="min-h-screen pt-32 pb-margin-desktop px-gutter bg-gradient-to-b from-primary-container/[0.10] via-background-obsidian to-background-obsidian">
      <div className="max-w-7xl mx-auto">
        
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">
            {specificType === "series" ? "Seriallar bo'yicha qidiruv natijalari" : 
             specificType === "movie" ? "Kinolar bo'yicha qidiruv natijalari" : 
             "Qidiruv natijalari"}
          </h1>
          <p className="text-gray-400">
            {query ? `"${query}" so'rovi bo'yicha` : "Iltimos, qidirish uchun so'z kiriting (kamida 2 ta harf)."}
          </p>
        </div>

        {/* Search Input removed from here, only keeping navbar search */}

        {/* Results Grid */}
        {errorMsg ? (
          <div className="text-red-500 text-lg">Xatolik yuz berdi: {errorMsg}</div>
        ) : query.length > 0 && query.length < 2 ? (
          <div className="text-gray-400 text-lg">Qidiruv uchun kamida 2 ta harf kiritish kerak.</div>
        ) : results.length > 0 ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4 md:gap-6 pt-4">
            {results.map((item, idx) => {
              const isSeries = item.isSeries !== undefined ? item.isSeries : specificType === "series";
              const linkUrl = isSeries ? `/series/${item.id}` : `/movie/${item.code}`;
              const key = `${isSeries ? 's' : 'm'}-${isSeries ? item.id : item.code}-${idx}`;
              const rating = item.imdb_rating || item.tmdb_rating || "N/A";
              const subtext = isSeries 
                ? `${item.categories?.[0]?.name || "Serial"} • ${item.release_year || ""}`
                : `${item.genres || "Kino"} • ${item.release_year || ""}`;

              return (
                <Link 
                  href={linkUrl} 
                  key={key} 
                  className="group relative aspect-[2/3] rounded-xl overflow-hidden cursor-pointer bg-surface-container hover:scale-105 transition-transform duration-300 shadow-lg hover:shadow-[0_0_20px_rgba(229,9,20,0.3)] ring-1 ring-white/5 hover:ring-primary-container"
                >
                  {item.poster_url ? (
                    <Image 
                      src={item.poster_url} 
                      alt={item.title}
                      fill
                      sizes="(max-width: 768px) 160px, 240px"
                      className="object-cover"
                    />
                  ) : (
                    <div className="absolute inset-0 flex flex-col items-center justify-center bg-surface-container-high text-gray-500 border border-white/5">
                      <span className="material-symbols-outlined text-4xl mb-2 opacity-30">movie</span>
                    </div>
                  )}
                  
                  <div className="absolute inset-0 bg-gradient-to-t from-background-obsidian via-background-obsidian/50 to-transparent opacity-80 group-hover:opacity-100 transition-opacity"></div>
                  
                  <div className="absolute top-2 right-2 px-2 py-1 bg-black/60 backdrop-blur-sm rounded text-rating-gold flex items-center gap-1 border border-white/10">
                    <span className="material-symbols-outlined text-[14px]" style={{ fontVariationSettings: "'FILL' 1" }}>star</span>
                    <span className="font-label-caps text-xs font-bold">{rating}</span>
                  </div>
                  
                  <div className="absolute bottom-0 left-0 w-full p-4 transform translate-y-2 group-hover:translate-y-0 transition-transform">
                    <div className="flex gap-1 mb-1">
                      <span className="px-1.5 py-0.5 bg-white/10 backdrop-blur-sm rounded text-[10px] font-bold text-text-secondary uppercase tracking-wider">{isSeries ? item.categories?.[0]?.name || "Serial" : item.genres?.split(',')[0] || "Kino"}</span>
                      {item.release_year && <span className="px-1.5 py-0.5 bg-white/10 backdrop-blur-sm rounded text-[10px] font-bold text-text-secondary uppercase tracking-wider">{item.release_year}</span>}
                    </div>
                    <h3 className="font-body-lg text-text-primary font-bold line-clamp-2 drop-shadow-md">{item.title}</h3>
                  </div>
                </Link>
              );
            })}
          </div>
        ) : (
          query.length >= 2 && (
            <div className="text-center py-20 bg-surface rounded-2xl border border-white/5">
              <svg className="w-16 h-16 text-gray-600 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <h2 className="text-2xl font-bold text-white mb-2">Hech narsa topilmadi</h2>
              <p className="text-gray-400">"{query}" bo'yicha hech qanday natija mavjud emas.</p>
            </div>
          )
        )}
      </div>
    </div>
  );
}
