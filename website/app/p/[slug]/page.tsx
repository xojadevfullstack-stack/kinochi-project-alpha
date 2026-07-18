import { fetchApi } from "@/lib/api";
import Link from "next/link";
import Image from "next/image";
import { Metadata } from "next";

export const revalidate = 60;

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

type Series = {
  id: number;
  title: string;
  poster_url: string | null;
  imdb_rating: number | null;
  release_year: number | null;
  categories: { id: number; name: string }[];
};

export async function generateMetadata({ params }: { params: { slug: string } }): Promise<Metadata> {
  try {
    const page = await fetchApi(`/pages/${params.slug}`);
    return {
      title: `${page.title} - Kinochi`,
      description: `${page.title} turidagi barcha kino va seriallar.`,
    };
  } catch (error) {
    return {
      title: "Sahifa - Kinochi",
    };
  }
}

export default async function DynamicPage({ params }: { params: { slug: string } }) {
  let page = null;
  let movies: Movie[] = [];
  let seriesList: Series[] = [];
  
  try {
    page = await fetchApi(`/pages/${params.slug}`);
    if (page && page.id) {
      const [moviesData, seriesData] = await Promise.all([
        fetchApi(`/movies?limit=50&page_id=${page.id}`),
        fetchApi(`/series?limit=50&page_id=${page.id}`)
      ]);
      movies = moviesData.items || [];
      seriesList = seriesData.items || [];
    }
  } catch (error) {
    console.error("Failed to fetch page data:", error);
  }

  if (!page) {
    return (
      <div className="min-h-screen pt-32 pb-margin-desktop px-gutter flex items-center justify-center">
        <h1 className="text-3xl font-bold text-text-primary">Sahifa topilmadi</h1>
      </div>
    );
  }

  return (
    <div className="min-h-screen pt-32 pb-margin-desktop px-gutter bg-gradient-to-b from-primary-container/[0.10] via-background-obsidian to-background-obsidian">
      <div className="max-w-container-max mx-auto">
        
        {/* Header */}
        <div className="mb-stack-lg">
          <div className="mb-stack-md">
            <h1 className="font-display-hero text-display-hero-mobile md:text-[56px] font-black text-text-primary mb-2 tracking-tighter">{page.title}</h1>
            <p className="text-text-secondary font-body-lg text-body-lg">Bizning maxsus to'plamlarimiz.</p>
          </div>
        </div>

        {movies.length === 0 && seriesList.length === 0 ? (
          <div className="text-center py-20 text-text-secondary">
            <span className="material-symbols-outlined text-6xl mb-4 opacity-50">movie</span>
            <p>Hozircha ma'lumotlar mavjud emas.</p>
          </div>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4 md:gap-6">
            
            {movies.map(movie => (
              <Link 
                href={`/movie/${movie.code}`} 
                key={`movie-${movie.code}`} 
                className="group relative aspect-[2/3] rounded-xl overflow-hidden cursor-pointer bg-surface-container hover:scale-105 transition-transform duration-300 shadow-lg hover:shadow-[0_0_20px_rgba(229,9,20,0.3)] ring-1 ring-white/5 hover:ring-primary-container"
              >
                {movie.poster_url ? (
                  <Image 
                    src={movie.poster_url} 
                    alt={movie.title}
                    fill
                    sizes="(max-width: 768px) 50vw, (max-width: 1024px) 33vw, 16vw"
                    className="object-cover"
                  />
                ) : (
                  <div className="absolute inset-0 flex flex-col items-center justify-center bg-surface-container-high text-gray-500">
                    <span className="material-symbols-outlined text-4xl mb-2 opacity-30">movie</span>
                  </div>
                )}
                
                <div className="absolute inset-0 bg-gradient-to-t from-background-obsidian via-background-obsidian/50 to-transparent opacity-80 group-hover:opacity-100 transition-opacity"></div>
                
                <div className="absolute top-2 right-2 px-2 py-1 bg-black/60 backdrop-blur-sm rounded text-rating-gold flex items-center gap-1 border border-white/10">
                  <span className="material-symbols-outlined text-[14px]" style={{ fontVariationSettings: "'FILL' 1" }}>star</span>
                  <span className="font-label-caps text-xs font-bold">{movie.imdb_rating || movie.tmdb_rating || "N/A"}</span>
                </div>
                
                <div className="absolute bottom-0 left-0 w-full p-4 transform translate-y-2 group-hover:translate-y-0 transition-transform">
                  <div className="flex gap-1 mb-1">
                    <span className="px-1.5 py-0.5 bg-white/10 backdrop-blur-sm rounded text-[10px] font-bold text-text-secondary uppercase tracking-wider">{movie.genres?.split(',')[0] || "Kino"}</span>
                    {movie.release_year && <span className="px-1.5 py-0.5 bg-white/10 backdrop-blur-sm rounded text-[10px] font-bold text-text-secondary uppercase tracking-wider">{movie.release_year}</span>}
                  </div>
                  <h3 className="font-display text-[18px] font-bold leading-tight text-white mb-1 group-hover:text-primary transition-colors line-clamp-2">
                    {movie.title}
                  </h3>
                </div>
              </Link>
            ))}

            {seriesList.map(s => (
              <Link 
                href={`/series/${s.id}`} 
                key={`series-${s.id}`} 
                className="group relative aspect-[2/3] rounded-xl overflow-hidden cursor-pointer bg-surface-container hover:scale-105 transition-transform duration-300 shadow-lg hover:shadow-[0_0_20px_rgba(229,9,20,0.3)] ring-1 ring-white/5 hover:ring-primary-container"
              >
                {s.poster_url ? (
                  <Image 
                    src={s.poster_url} 
                    alt={s.title}
                    fill
                    sizes="(max-width: 768px) 50vw, (max-width: 1024px) 33vw, 16vw"
                    className="object-cover"
                  />
                ) : (
                  <div className="absolute inset-0 flex flex-col items-center justify-center bg-surface-container-high text-gray-500">
                    <span className="material-symbols-outlined text-4xl mb-2 opacity-30">tv</span>
                  </div>
                )}
                
                <div className="absolute inset-0 bg-gradient-to-t from-background-obsidian via-background-obsidian/50 to-transparent opacity-80 group-hover:opacity-100 transition-opacity"></div>
                
                <div className="absolute top-2 right-2 px-2 py-1 bg-black/60 backdrop-blur-sm rounded text-rating-gold flex items-center gap-1 border border-white/10">
                  <span className="material-symbols-outlined text-[14px]" style={{ fontVariationSettings: "'FILL' 1" }}>star</span>
                  <span className="font-label-caps text-xs font-bold">{s.imdb_rating || "N/A"}</span>
                </div>
                
                <div className="absolute bottom-0 left-0 w-full p-4 transform translate-y-2 group-hover:translate-y-0 transition-transform">
                  <div className="flex gap-1 mb-1">
                    <span className="px-1.5 py-0.5 bg-white/10 backdrop-blur-sm rounded text-[10px] font-bold text-text-secondary uppercase tracking-wider">{s.categories?.[0]?.name || "Serial"}</span>
                    {s.release_year && <span className="px-1.5 py-0.5 bg-white/10 backdrop-blur-sm rounded text-[10px] font-bold text-text-secondary uppercase tracking-wider">{s.release_year}</span>}
                  </div>
                  <h3 className="font-display text-[18px] font-bold leading-tight text-white mb-1 group-hover:text-primary transition-colors line-clamp-2">
                    {s.title}
                  </h3>
                </div>
              </Link>
            ))}
          </div>
        )}
        
      </div>
    </div>
  );
}
