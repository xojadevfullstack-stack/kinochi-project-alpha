import { fetchApi } from "@/lib/api";
import Link from "next/link";
import Image from "next/image";

// Ensure this page is rendered dynamically or ISR if we want fresh data
export const revalidate = 60; // revalidate every 60 seconds

type Movie = {
  id: number;
  title: string;
  original_title: string | null;
  description: string | null;
  imdb_rating: number | null;
  tmdb_rating: number | null;
  genres: string | null;
  release_year: number | null;
  poster_url: string | null;
  code: string;
};

type Category = {
  id: number;
  name: string;
  is_active: boolean;
};

type Series = {
  id: number;
  title: string;
  description: string | null;
  poster_url: string | null;
};

// Component for the horizontal movie card row
const MovieRow = ({ title, movies }: { title: string, movies: Movie[] }) => {
  if (!movies || movies.length === 0) return null;
  
  return (
    <div className="mb-12">
      <h2 className="text-2xl font-semibold mb-4 px-4 md:px-8 text-white/90">{title}</h2>
      <div className="flex overflow-x-auto hide-scrollbar gap-4 px-4 md:px-8 pb-4">
        {movies.map(movie => (
          <Link href={`/movie/${movie.code}`} key={movie.code} className="flex-none w-40 md:w-48 lg:w-56 group relative rounded-xl overflow-hidden bg-surface transition-transform duration-300 hover:scale-105 hover:z-10 ring-1 ring-white/10 hover:ring-primary/50">
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
            <div className="p-3">
              <h3 className="font-medium text-sm md:text-base text-white truncate" title={movie.title}>{movie.title}</h3>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
};

// Component for the horizontal series card row
const SeriesRow = ({ title, seriesList }: { title: string, seriesList: Series[] }) => {
  if (!seriesList || seriesList.length === 0) return null;
  
  return (
    <div className="mb-12">
      <h2 className="text-2xl font-semibold mb-4 px-4 md:px-8 text-white/90">{title}</h2>
      <div className="flex overflow-x-auto hide-scrollbar gap-4 px-4 md:px-8 pb-4">
        {seriesList.map(series => (
          <Link href={`/series/${series.id}`} key={series.id} className="flex-none w-40 md:w-48 lg:w-56 group relative rounded-xl overflow-hidden bg-surface transition-transform duration-300 hover:scale-105 hover:z-10 ring-1 ring-white/10 hover:ring-primary/50">
            <div className="aspect-[2/3] relative bg-gray-800">
              {series.poster_url ? (
                <Image 
                  src={series.poster_url} 
                  alt={series.title}
                  fill
                  sizes="(max-width: 768px) 160px, 224px"
                  className="object-cover"
                />
              ) : (
                <div className="absolute inset-0 flex flex-col items-center justify-center bg-gradient-to-br from-surface to-background text-gray-500 border border-white/5">
                  <span className="text-xs font-medium uppercase tracking-wider opacity-60">Poster yo'q</span>
                </div>
              )}
              {/* Gradient Overlay on hover */}
              <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex flex-col justify-end p-4">
                <div className="text-xs text-gray-300 line-clamp-3">{series.description || "Serial"}</div>
              </div>
            </div>
            <div className="p-3">
              <h3 className="font-medium text-sm md:text-base text-white truncate" title={series.title}>{series.title}</h3>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
};

export default async function Home() {
  let latestMovies: Movie[] = [];
  let latestSeries: Series[] = [];
  let categories: Category[] = [];
  
  try {
    const moviesData = await fetchApi("/movies?limit=20");
    latestMovies = moviesData.items || [];

    const seriesData = await fetchApi("/series?limit=10");
    latestSeries = seriesData.items || [];
    
    const catsData = await fetchApi("/categories");
    // Filter out inactive categories just in case
    categories = (catsData || []).filter((c: Category) => c.is_active);
  } catch (error) {
    console.error("Failed to fetch initial data:", error);
  }

  // Pick a featured movie for the Hero section (highest rating or newest)
  const heroMovie = latestMovies.length > 0 ? latestMovies[0] : null;

  return (
    <div className="pb-20">
      {/* Hero Section */}
      <div className="relative h-[70vh] min-h-[500px] w-full bg-background flex items-center">
        {heroMovie && heroMovie.poster_url ? (
          <>
            <div className="absolute inset-0 z-0">
              <Image 
                src={heroMovie.poster_url}
                alt={heroMovie.title}
                fill
                priority
                className="object-cover object-top opacity-40 blur-sm mix-blend-screen"
              />
            </div>
            {/* Gradient overlay for fade out at bottom */}
            <div className="absolute inset-0 z-0 bg-gradient-to-t from-background via-background/60 to-transparent"></div>
            <div className="absolute inset-0 z-0 bg-gradient-to-r from-background via-background/40 to-transparent"></div>
          </>
        ) : (
          <div className="absolute inset-0 z-0 bg-gradient-to-b from-surface to-background"></div>
        )}

        <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full pt-16">
          <div className="max-w-2xl">
            <h1 className="text-4xl md:text-6xl font-bold text-white tracking-tight mb-4 drop-shadow-lg">
              {heroMovie ? heroMovie.title : "Kinochi olamiga xush kelibsiz"}
            </h1>
            
            <div className="flex items-center gap-4 text-sm md:text-base text-gray-300 mb-6 drop-shadow-md">
              {heroMovie && (
                <>
                  <span className="flex items-center gap-1 text-star font-bold">
                    ★ {heroMovie.imdb_rating || heroMovie.tmdb_rating || "N/A"}
                  </span>
                  <span>|</span>
                  <span>{heroMovie.release_year || "2026"}</span>
                  <span>|</span>
                  <span>{heroMovie.genres || "Kino"}</span>
                </>
              )}
            </div>

            <p className="text-gray-300 text-lg md:text-xl mb-8 line-clamp-3 drop-shadow-md max-w-xl">
              {heroMovie?.description || "Telegram tarmog'idagi eng katta va qulay kino bazasi. O'zingiz yoqtirgan filmlarni toping va bepul tomosha qiling."}
            </p>

            <div className="flex flex-col sm:flex-row gap-4">
              {heroMovie && (
                <Link 
                  href={`/movie/${heroMovie.code}`}
                  className="bg-primary hover:bg-red-700 text-white font-semibold py-3 px-8 rounded-full transition-all flex items-center justify-center gap-2 shadow-lg shadow-primary/30 hover:scale-105"
                >
                  <svg className="w-5 h-5 fill-current" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
                  Ko'rish
                </Link>
              )}
              
              {/* Functional Search Input */}
              <form action="/search" method="GET" className="relative flex-1 max-w-sm group">
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
                  placeholder="Kino yoki serial qidirish..." 
                />
                <button type="submit" className="hidden">Qidirish</button>
              </form>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content Rows */}
      <div className="relative z-10 -mt-20">
        <MovieRow title="Yangi qo'shilganlar" movies={latestMovies} />
        
        <SeriesRow title="So'nggi Seriallar" seriesList={latestSeries} />
        
        {/* Placeholder for categories: Since we might not have a /categories/{id}/movies endpoint yet, 
            we will just display the latest movies repeatedly for demonstration, or if the API supports it, 
            we could fetch per category. For now, we show the same list to prove the UI works. */}
        {categories.map(cat => (
          <MovieRow key={cat.id} title={`${cat.name} turkumidagi kinolar`} movies={latestMovies.slice().reverse()} />
        ))}
      </div>
    </div>
  );
}
