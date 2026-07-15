import { fetchApi } from "@/lib/api";
import Link from "next/link";
import Image from "next/image";

export const revalidate = 60;

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

type Series = {
  id: number;
  title: string;
  description: string | null;
  poster_url: string | null;
  imdb_rating: number | null;
  release_year: number | null;
  categories?: any[];
};

const MovieRow = ({ title, movies, viewAllLink }: { title: string, movies: Movie[], viewAllLink?: string }) => {
  if (!movies || movies.length === 0) return null;
  
  return (
    <div className="mb-12 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div className="flex justify-between items-end mb-6">
        <h2 className="text-2xl font-display font-bold text-white tracking-tight">{title}</h2>
        {viewAllLink && (
          <Link href={viewAllLink} className="text-sm font-medium text-gray-400 hover:text-white transition-colors flex items-center gap-1">
            Barchasi <span className="text-primary">&rarr;</span>
          </Link>
        )}
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4 md:gap-6">
        {movies.map(movie => (
          <Link href={`/movie/${movie.code}`} key={movie.code} className="group relative rounded-xl overflow-hidden bg-surface transition-all duration-300 hover:scale-105 hover:z-10 hover:shadow-2xl hover:shadow-primary/20 hover:ring-2 hover:ring-primary">
            <div className="aspect-[2/3] relative">
              {movie.poster_url ? (
                <Image 
                  src={movie.poster_url} 
                  alt={movie.title}
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
                <h3 className="font-bold text-white text-sm md:text-base leading-tight mb-1.5 line-clamp-2">{movie.title}</h3>
                <div className="flex items-center justify-between text-xs font-medium">
                  <span className="text-gray-300">{movie.release_year || ""}</span>
                  <span className="flex items-center gap-1 text-star bg-black/50 px-1.5 py-0.5 rounded backdrop-blur-sm">
                    ★ {movie.imdb_rating || movie.tmdb_rating || "N/A"}
                  </span>
                </div>
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
};

const SeriesRow = ({ title, seriesList, viewAllLink }: { title: string, seriesList: Series[], viewAllLink?: string }) => {
  if (!seriesList || seriesList.length === 0) return null;
  
  return (
    <div className="mb-12 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div className="flex justify-between items-end mb-6">
        <h2 className="text-2xl font-display font-bold text-white tracking-tight">{title}</h2>
        {viewAllLink && (
          <Link href={viewAllLink} className="text-sm font-medium text-gray-400 hover:text-white transition-colors flex items-center gap-1">
            Barchasi <span className="text-primary">&rarr;</span>
          </Link>
        )}
      </div>
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
    </div>
  );
};

export default async function Home() {
  let latestMovies: Movie[] = [];
  let latestSeries: Series[] = [];
  
  try {
    const moviesData = await fetchApi("/movies?limit=5");
    latestMovies = moviesData.items || [];

    const seriesData = await fetchApi("/series?limit=5");
    latestSeries = seriesData.items || [];
  } catch (error) {
    console.error("Failed to fetch initial data:", error);
  }

  const heroMovie = latestMovies.length > 0 ? latestMovies[0] : null;

  return (
    <div className="pb-20">
      {/* Hero Section */}
      <div className="relative h-[85vh] min-h-[600px] w-full bg-[#09090B] flex items-center overflow-hidden">
        {heroMovie && heroMovie.poster_url ? (
          <>
            <div className="absolute inset-0 z-0">
              <Image 
                src={heroMovie.poster_url}
                alt={heroMovie.title}
                fill
                priority
                className="object-cover object-[center_20%] opacity-50 blur-[2px] mix-blend-screen scale-105"
              />
            </div>
            {/* Cinematic Gradient Overlays */}
            <div className="absolute inset-0 z-0 bg-gradient-to-t from-[#09090B] via-[#09090B]/80 to-transparent"></div>
            <div className="absolute inset-0 z-0 bg-gradient-to-r from-[#09090B] via-[#09090B]/60 to-transparent"></div>
          </>
        ) : (
          <div className="absolute inset-0 z-0 bg-gradient-to-b from-surface to-background"></div>
        )}

        <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full pt-20">
          <div className="max-w-2xl">
            {/* Badge */}
            {heroMovie && (
              <div className="flex items-center gap-3 mb-6">
                <span className="bg-star text-black text-xs font-bold px-2 py-1 rounded-sm uppercase tracking-wide">
                  IMDb {heroMovie.imdb_rating || "8.4"}
                </span>
                <span className="text-xs font-bold text-white/80 bg-white/10 px-2 py-1 rounded-sm tracking-widest uppercase">
                  {heroMovie.release_year || "2024"}
                </span>
                <span className="text-xs font-bold text-white/80 bg-white/10 px-2 py-1 rounded-sm tracking-widest uppercase">
                  {heroMovie.genres ? heroMovie.genres.split(',')[0] : "KINO"}
                </span>
              </div>
            )}
            
            <h1 className="text-5xl md:text-7xl font-display font-black text-white tracking-tighter mb-6 leading-[1.1]">
              {heroMovie ? heroMovie.title : "Kinochi olamiga xush kelibsiz"}
            </h1>
            
            <p className="text-gray-300 text-lg md:text-xl mb-10 line-clamp-3 leading-relaxed max-w-xl font-medium">
              {heroMovie?.description || "Eng so'nggi kinolar, eksklyuziv seriallar va yuqori sifatdagi kontent. Chegarasiz tomosha dunyosini kashf eting."}
            </p>

            <div className="flex items-center gap-4">
              {heroMovie && (
                <Link 
                  href={`/movie/${heroMovie.code}`}
                  className="bg-primary hover:bg-red-700 text-white font-bold py-4 px-8 rounded-full transition-transform duration-300 flex items-center gap-3 hover:scale-105"
                >
                  <svg className="w-5 h-5 fill-current" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
                  Telegram orqali ko'rish
                </Link>
              )}
              
              <button className="w-14 h-14 rounded-full bg-white/10 hover:bg-white/20 backdrop-blur-md flex items-center justify-center transition-colors text-white">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content Rows */}
      <div className="relative z-10 -mt-10">
        <MovieRow title="Trenddagilar" movies={latestMovies} viewAllLink="/movies" />
        <SeriesRow title="Yangi chiqqanlar" seriesList={latestSeries} viewAllLink="/series" />
      </div>
    </div>
  );
}
