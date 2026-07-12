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
  const searchType = searchParams.type === "series" ? "series" : "movie";
  
  let results: any[] = [];
  let errorMsg = null;

  if (query.length >= 2) {
    try {
      // The backend API requires q to be at least 2 characters long
      const endpoint = searchType === "series" 
        ? `/series/search?q=${encodeURIComponent(query)}&limit=40` 
        : `/movies/search?q=${encodeURIComponent(query)}&limit=40`;
        
      const response = await fetchApi(endpoint);
      results = response.items || [];
    } catch (error: any) {
      errorMsg = error.message;
    }
  }

  return (
    <div className="min-h-screen bg-background pt-24 pb-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">
            {searchType === "series" ? "Seriallar bo'yicha qidiruv natijalari" : "Kinolar bo'yicha qidiruv natijalari"}
          </h1>
          <p className="text-gray-400">
            {query ? `"${query}" so'rovi bo'yicha` : "Iltimos, qidirish uchun so'z kiriting (kamida 2 ta harf)."}
          </p>
        </div>

        {/* Search Input again for convenience */}
        <div className="mb-12 max-w-xl">
          <form action="/search" method="GET" className="relative group">
            <input type="hidden" name="type" value={searchType} />
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <svg className="h-5 w-5 text-gray-400 group-focus-within:text-primary transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <input 
              type="text" 
              name="q"
              defaultValue={query}
              required
              className="bg-surface-hover/80 border border-white/10 text-white text-base rounded-full focus:ring-primary focus:border-primary block w-full pl-10 p-4 outline-none transition-all shadow-lg" 
              placeholder={searchType === "series" ? "Boshqa serial qidirish..." : "Boshqa kino qidirish..."} 
            />
            <button type="submit" className="hidden">Qidirish</button>
          </form>
        </div>

        {/* Results Grid */}
        {errorMsg ? (
          <div className="text-red-500 text-lg">Xatolik yuz berdi: {errorMsg}</div>
        ) : query.length > 0 && query.length < 2 ? (
          <div className="text-gray-400 text-lg">Qidiruv uchun kamida 2 ta harf kiritish kerak.</div>
        ) : results.length > 0 ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4 md:gap-6 pt-4">
            {results.map(item => {
              const linkUrl = searchType === "series" ? `/series/${item.id}` : `/movie/${item.code}`;
              const key = searchType === "series" ? item.id : item.code;
              const rating = item.imdb_rating || item.tmdb_rating || "N/A";
              const subtext = searchType === "series" 
                ? `${item.categories?.[0]?.name || "Serial"} • ${item.release_year || ""}`
                : `${item.genres || "Kino"} • ${item.release_year || ""}`;

              return (
                <Link href={linkUrl} key={key} className="group relative rounded-xl overflow-hidden bg-surface transition-transform duration-300 hover:scale-105 hover:z-10 ring-1 ring-white/10 hover:ring-primary/50 flex flex-col">
                  <div className="aspect-[2/3] relative bg-gray-800">
                    {item.poster_url ? (
                      <Image 
                        src={item.poster_url} 
                        alt={item.title}
                        fill
                        sizes="(max-width: 640px) 50vw, (max-width: 1024px) 25vw, 16vw"
                        className="object-cover"
                      />
                    ) : (
                      <div className="absolute inset-0 flex flex-col items-center justify-center bg-gradient-to-br from-surface to-background text-gray-500 border border-white/5">
                        <svg className="w-10 h-10 mb-2 opacity-30" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M7 4v16M17 4v16M3 8h4m10 0h4M3 12h18M3 16h4m10 0h4M4 20h16a1 1 0 001-1V5a1 1 0 00-1-1H4a1 1 0 00-1 1v14a1 1 0 001 1z" />
                        </svg>
                        <span className="text-xs font-medium uppercase tracking-wider opacity-60">Poster yo'q</span>
                      </div>
                    )}
                    {/* Gradient Overlay on hover */}
                    <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex flex-col justify-end p-4">
                      <div className="flex items-center gap-1 text-star font-bold text-sm mb-1">
                        ★ {rating}
                      </div>
                      <div className="text-xs text-gray-300 truncate">{subtext}</div>
                    </div>
                  </div>
                  <div className="p-3">
                    <h3 className="font-medium text-sm md:text-base text-white truncate" title={item.title}>{item.title}</h3>
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
              <p className="text-gray-400">"{query}" bo'yicha hech qanday {searchType === "series" ? "serial" : "kino"} mavjud emas.</p>
            </div>
          )
        )}
      </div>
    </div>
  );
}
