import { fetchApi } from "@/lib/api";
import Link from "next/link";
import Image from "next/image";
import { Metadata } from "next";

export const revalidate = 60;

export const metadata: Metadata = {
  title: "Barcha Seriallar - KINOCHI",
  description: "Eng so'nggi va mashhur seriallarni kashf eting.",
};

type Series = {
  id: number;
  title: string;
  poster_url: string | null;
  imdb_rating: number | null;
  release_year: number | null;
  categories?: any[];
};

export default async function SeriesListPage() {
  let seriesList: Series[] = [];
  
  try {
    const data = await fetchApi("/series?limit=20");
    seriesList = data.items || [];
  } catch (error) {
    console.error("Failed to fetch series:", error);
  }

  return (
    <div className="min-h-screen bg-[#09090B] pt-24 pb-12 px-4 sm:px-6 lg:px-8 text-white">
      <div className="max-w-7xl mx-auto">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-10">
          <div>
            <h1 className="text-4xl md:text-5xl font-display font-black text-white tracking-tight mb-2">Barcha Seriallar</h1>
            <p className="text-gray-400 font-medium">Eng so'nggi va mashhur seriallarni kashf eting.</p>
          </div>
          
          {/* Premium Search Form */}
          <form action="/search" method="GET" className="relative w-full md:max-w-md group">
            <input type="hidden" name="type" value="series" />
            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
              <svg className="h-5 w-5 text-gray-500 group-focus-within:text-white transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <input 
              type="text" 
              name="q"
              required
              className="bg-surface/80 hover:bg-surface border border-white/10 text-white text-sm rounded-full focus:ring-1 focus:ring-white focus:border-white block w-full pl-12 p-3.5 outline-none transition-all placeholder-gray-500 font-medium" 
              placeholder="Serial qidirish..." 
            />
            <button type="submit" className="hidden">Qidirish</button>
          </form>
        </div>
        
        {seriesList.length === 0 ? (
          <div className="text-center py-20 text-gray-500">
            Hozircha seriallar mavjud emas.
          </div>
        ) : (
          <>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4 md:gap-6">
              {seriesList.map(series => (
                <Link href={`/series/${series.id}`} key={series.id} className="group relative rounded-xl overflow-hidden bg-surface transition-all duration-300 hover:scale-105 hover:z-10 hover:shadow-2xl hover:shadow-primary/20 hover:ring-2 hover:ring-primary">
                  <div className="aspect-[2/3] relative">
                    {series.poster_url ? (
                      <Image 
                        src={series.poster_url} 
                        alt={series.title}
                        fill
                        sizes="(max-width: 768px) 50vw, (max-width: 1200px) 25vw, 20vw"
                        className="object-cover transition-transform duration-500 group-hover:scale-110"
                      />
                    ) : (
                      <div className="absolute inset-0 flex flex-col items-center justify-center bg-surface">
                        <span className="text-xs font-medium uppercase tracking-wider opacity-60">Poster yo'q</span>
                      </div>
                    )}
                    {/* Gradient Overlay */}
                    <div className="absolute inset-0 bg-gradient-to-t from-[#09090B] via-[#09090B]/50 to-transparent opacity-90 group-hover:opacity-100 transition-opacity flex flex-col justify-end p-4">
                      <span className="absolute top-2 left-2 bg-primary text-white text-[10px] font-bold px-2 py-0.5 rounded-sm uppercase tracking-wider">
                        SERIAL
                      </span>
                      <h3 className="font-bold text-white text-sm md:text-base leading-tight mb-1.5 line-clamp-2">{series.title}</h3>
                      <div className="flex items-center justify-between text-xs font-medium">
                        <span className="text-gray-300">{series.release_year || ""}</span>
                        <span className="flex items-center gap-1 text-star bg-black/50 px-1.5 py-0.5 rounded backdrop-blur-sm">
                          ★ {series.imdb_rating || "N/A"}
                        </span>
                      </div>
                    </div>
                  </div>
                </Link>
              ))}
            </div>

            {/* Pagination Mockup to match design */}
            <div className="flex justify-center items-center space-x-2 mt-16 mb-8">
              <button className="w-10 h-10 rounded-full flex items-center justify-center text-gray-400 hover:text-white hover:bg-white/10 transition-colors">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" /></svg>
              </button>
              <button className="w-10 h-10 rounded-full bg-primary text-white font-bold flex items-center justify-center">1</button>
              <button className="w-10 h-10 rounded-full text-gray-400 hover:text-white hover:bg-white/10 font-medium flex items-center justify-center transition-colors">2</button>
              <button className="w-10 h-10 rounded-full text-gray-400 hover:text-white hover:bg-white/10 font-medium flex items-center justify-center transition-colors">3</button>
              <span className="text-gray-600 px-2">...</span>
              <button className="w-10 h-10 rounded-full text-gray-400 hover:text-white hover:bg-white/10 font-medium flex items-center justify-center transition-colors">12</button>
              <button className="w-10 h-10 rounded-full flex items-center justify-center text-gray-400 hover:text-white hover:bg-white/10 transition-colors">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" /></svg>
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
