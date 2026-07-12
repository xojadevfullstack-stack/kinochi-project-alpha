import { fetchApi } from "@/lib/api";
import Link from "next/link";
import Image from "next/image";
import { Metadata } from "next";

export const revalidate = 60;

export const metadata: Metadata = {
  title: "Kinolar - Kinochi",
  description: "Eng sara va so'nggi kinolarni bepul tomosha qiling.",
};

type Movie = {
  id: number;
  code: number;
  title: string;
  poster_url: string | null;
  imdb_rating: number | null;
  tmdb_rating: number | null;
  release_year: number | null;
  genres: string | null;
};

export default async function MoviesListPage() {
  let movies: Movie[] = [];
  
  try {
    const data = await fetchApi("/movies?limit=50");
    movies = data.items || [];
  } catch (error) {
    console.error("Failed to fetch movies:", error);
  }

  return (
    <div className="min-h-screen bg-background pt-24 pb-12 px-4 sm:px-6 lg:px-8 text-white">
      <div className="max-w-7xl mx-auto">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-8">
          <h1 className="text-3xl md:text-5xl font-bold text-white/90">Barcha Kinolar</h1>
          
          {/* Search Form for Movies */}
          <form action="/search" method="GET" className="relative w-full md:max-w-sm group">
            <input type="hidden" name="type" value="movie" />
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <svg className="h-5 w-5 text-gray-400 group-focus-within:text-primary transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <input 
              type="text" 
              name="q"
              required
              className="bg-surface-hover/80 backdrop-blur-sm border border-white/10 text-white text-sm rounded-full focus:ring-primary focus:border-primary block w-full pl-10 p-3 outline-none transition-all" 
              placeholder="Kino qidirish..." 
            />
            <button type="submit" className="hidden">Qidirish</button>
          </form>
        </div>
        
        {movies.length === 0 ? (
          <div className="text-center py-20 text-gray-500">
            Hozircha kinolar mavjud emas.
          </div>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-6 pt-4">
            {movies.map(movie => (
              <Link 
                href={`/movie/${movie.code}`} 
                key={movie.code} 
                className="group relative rounded-xl overflow-hidden bg-surface transition-transform duration-300 hover:scale-105 hover:z-10 ring-1 ring-white/10 hover:ring-primary/50 flex flex-col"
              >
                <div className="aspect-[2/3] relative bg-gray-800">
                  {movie.poster_url ? (
                    <Image 
                      src={movie.poster_url} 
                      alt={movie.title}
                      fill
                      sizes="(max-width: 768px) 160px, 224px"
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
                      ★ {movie.imdb_rating || movie.tmdb_rating || "N/A"}
                    </div>
                    <div className="text-xs text-gray-300 truncate">{movie.genres || "Kino"} • {movie.release_year || ""}</div>
                  </div>
                </div>
                <div className="p-3 flex-1 flex flex-col justify-center">
                  <h3 className="font-medium text-sm md:text-base text-white truncate" title={movie.title}>{movie.title}</h3>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
