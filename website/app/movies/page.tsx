import { fetchApi } from "@/lib/api";
import Link from "next/link";
import Image from "next/image";
import { Metadata } from "next";
import CategoryFilter from "@/components/CategoryFilter";
import CatalogTypeNav from "@/components/catalog/CatalogTypeNav";

export const dynamic = 'force-dynamic';

export const metadata: Metadata = {
  title: "Kinolar - Kinochi",
  description: "Eng so'nggi va qiziqarli kinolarni tomosha qiling.",
};

type Movie = {
  id: number;
  code: string;
  title: string;
  poster_url: string | null;
  imdb_rating: number | null;
  tmdb_rating: number | null;
  release_year: number | null;
  genres: string | null;
};

type Category = {
  id: number;
  name: string;
};

export default async function MoviesListPage({ searchParams }: { searchParams: { category?: string } }) {
  let movies: Movie[] = [];
  let categories: Category[] = [];
  let pages: any[] = [];
  
  try {
    const query = searchParams.category 
      ? `/movies?limit=50&category_id=${searchParams.category}&exclude_paged=true` 
      : "/movies?limit=50&exclude_paged=true";
    const [moviesData, categoriesData, pagesData] = await Promise.all([
      fetchApi(query),
      fetchApi("/categories"),
      fetchApi("/pages/")
    ]);
    movies = moviesData?.items || [];
    categories = categoriesData || [];
    pages = pagesData?.items || pagesData || [];
  } catch (error) {
    console.error("Failed to fetch movies, categories or pages:", error);
  }

  return (
    <div className="min-h-screen pt-32 pb-margin-desktop px-gutter bg-gradient-to-b from-primary-container/[0.10] via-background-obsidian to-background-obsidian">
      <div className="max-w-container-max mx-auto">
        
        {/* Header & Categories */}
        <div className="mb-stack-lg">
          <div className="mb-stack-md text-center md:text-left">
            <h1 className="font-display-hero text-display-hero-mobile md:text-[56px] font-black text-text-primary mb-2 tracking-tighter">
              Kinolar
            </h1>
            <p className="text-text-secondary font-body-lg text-body-lg">
              Bizning katta kinolar, seriallar va sara to&apos;plamlar kolleksiyamiz bilan tanishing.
            </p>
          </div>

          {/* Catalog Type Switcher (Kinolar / Seriallar / Anime / Dorama) */}
          <CatalogTypeNav currentType="movies" pages={pages} />

          {/* Category Filter */}
          <CategoryFilter categories={categories} currentCategory={searchParams.category} baseUrl="/movies" />
        </div>

        {movies.length === 0 ? (
          <div className="text-center py-20 text-text-secondary">
            <span className="material-symbols-outlined text-6xl mb-4 opacity-50">movie</span>
            <p>Hozircha kinolar mavjud emas.</p>
          </div>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4 md:gap-6">
            {movies.map(movie => (
              <Link 
                href={`/movie/${movie.code}`} 
                key={movie.code} 
                className="group relative aspect-[2/3] rounded-xl overflow-hidden cursor-pointer bg-surface-container hover:scale-105 transition-transform duration-300 shadow-lg ring-1 ring-white/10 hover:ring-white/25"
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
                    <span className="px-1.5 py-0.5 bg-white/10 backdrop-blur-sm rounded text-[10px] font-bold text-text-secondary uppercase tracking-wider">
                      {movie.genres?.split(',')[0] || "Kino"}
                    </span>
                    {movie.release_year && (
                      <span className="px-1.5 py-0.5 bg-white/10 backdrop-blur-sm rounded text-[10px] font-bold text-text-secondary uppercase tracking-wider">
                        {movie.release_year}
                      </span>
                    )}
                  </div>
                  <h3 className="font-display text-[18px] font-bold leading-tight text-white mb-1 group-hover:text-white transition-colors line-clamp-2">
                    {movie.title}
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
