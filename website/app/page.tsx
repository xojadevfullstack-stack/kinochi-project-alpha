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
  imdb_rating: number | null;
  release_year: number | null;
  categories?: any[];
};

const MovieRow = ({ title, items, isSeries = false }: { title: string, items: any[], isSeries?: boolean }) => {
  if (!items || items.length === 0) return null;
  
  return (
    <section className="max-w-container-max mx-auto mb-16">
      <div className="px-gutter mb-stack-md flex items-center justify-between">
        <h2 className="font-headline-md text-headline-md text-text-primary flex items-center gap-2">
          <span className="w-1 h-6 bg-primary-container rounded-full block"></span>
          {title}
        </h2>
        <Link href={isSeries ? "/series" : "/movies"} className="text-text-secondary hover:text-primary-container text-sm font-bold transition-colors">
          Barchasi
        </Link>
      </div>
      <div className="flex gap-4 overflow-x-auto snap-x hide-scrollbar px-gutter pb-8 pt-4">
        {items.map(item => (
          <Link 
            href={isSeries ? `/series/${item.id}` : `/movie/${item.code}`} 
            key={isSeries ? item.id : item.code} 
            className="w-[160px] md:w-[240px] aspect-[2/3] shrink-0 snap-start relative rounded-xl overflow-hidden group cursor-pointer transition-all duration-300 hover:scale-105 ring-0 hover:ring-2 hover:ring-primary-container hover:shadow-[0_0_25px_rgba(229,9,20,0.5)]"
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
              <div className="absolute inset-0 bg-surface-container-high flex items-center justify-center">
                <span className="material-symbols-outlined text-4xl text-white/20">movie</span>
              </div>
            )}
            
            <div className="absolute inset-0 bg-gradient-to-t from-background-obsidian via-background-obsidian/40 to-transparent opacity-90 transition-opacity"></div>
            
            <div className="absolute bottom-0 left-0 w-full p-4 flex flex-col justify-end">
              <h3 className="font-body-lg text-body-lg text-text-primary font-bold truncate drop-shadow-md">{item.title}</h3>
              <div className="flex items-center justify-between mt-1">
                <span className="text-text-secondary text-sm">{item.release_year || ""}</span>
                <div className="flex items-center gap-1">
                  <span className="material-symbols-outlined text-rating-gold text-[16px]" style={{ fontVariationSettings: "'FILL' 1" }}>star</span>
                  <span className="text-text-primary text-sm font-bold">{item.imdb_rating || item.tmdb_rating || "N/A"}</span>
                </div>
              </div>
            </div>
          </Link>
        ))}
      </div>
    </section>
  );
};

export default async function Home() {
  let latestMovies: Movie[] = [];
  let latestSeries: Series[] = [];
  let categories: Category[] = [];

  try {
    const [moviesRes, seriesRes, catRes] = await Promise.all([
      fetchApi('/movies/latest?limit=10'),
      fetchApi('/series/latest?limit=10'),
      fetchApi('/categories')
    ]);
    latestMovies = moviesRes || [];
    latestSeries = seriesRes || [];
    categories = catRes || [];
  } catch (error) {
    console.error("Error fetching data for home page:", error);
  }

  const heroMovie = latestMovies.length > 0 ? latestMovies[0] : null;

  return (
    <>
      {/* Massive Hero Section */}
      <section className="relative w-full h-[870px] min-h-[600px] flex items-end pb-margin-desktop">
        {/* Featured Background */}
        <div className="absolute inset-0 w-full h-full">
          {heroMovie && heroMovie.poster_url ? (
            <Image 
              src={heroMovie.poster_url}
              alt={heroMovie.title}
              fill
              priority
              className="object-cover opacity-60"
            />
          ) : (
            <div className="absolute inset-0 bg-gradient-to-b from-surface-container to-background-obsidian"></div>
          )}
          {/* Smooth Dark Gradients */}
          <div className="absolute inset-0 bg-gradient-to-t from-background-obsidian via-background-obsidian/70 to-transparent"></div>
          <div className="absolute inset-0 bg-gradient-to-r from-background-obsidian via-background-obsidian/50 to-transparent"></div>
        </div>

        <div className="relative z-10 max-w-container-max mx-auto px-gutter w-full">
          <div className="max-w-3xl">
            {/* Badges */}
            <div className="flex flex-wrap items-center gap-2 sm:gap-3 mb-4">
              <span className="px-2 py-1 rounded bg-white/10 backdrop-blur-md text-text-primary font-label-caps text-[10px] sm:text-label-caps uppercase tracking-widest border border-white/10">
                {heroMovie?.genres || "Kino"}
              </span>
              <span className="px-2 py-1 rounded bg-primary-container text-white font-label-caps text-[10px] sm:text-label-caps font-bold">YANGI</span>
            </div>
            
            <h1 className="font-display-hero text-4xl sm:text-[48px] md:text-display-hero text-text-primary mb-4 drop-shadow-2xl tracking-tighter leading-tight">
              {heroMovie ? heroMovie.title : "KINOCHI PREMIUM"}
            </h1>
            
            <p className="font-body-lg text-body-lg text-text-secondary mb-8 max-w-2xl text-shadow-sm line-clamp-3">
              {heroMovie?.description || "Telegram tarmog'idagi eng katta va qulay kino bazasi. O'zingiz yoqtirgan filmlarni toping va bepul tomosha qiling."}
            </p>
            
            <div className="flex items-center gap-4">
              {heroMovie && (
                <Link 
                  href={`/movie/${heroMovie.code}`}
                  className="group flex items-center justify-center gap-2 px-8 py-4 bg-primary-container text-white rounded-full font-bold transition-all duration-300 hover:scale-105 shadow-[0_0_20px_rgba(229,9,20,0.4)] hover:shadow-[0_0_30px_rgba(229,9,20,0.7)]"
                >
                  <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>play_arrow</span>
                  Tomosha qilish
                </Link>
              )}
              <Link 
                href="/movies"
                className="flex items-center justify-center gap-2 px-8 py-4 bg-white/10 backdrop-blur-md border border-white/10 text-text-primary rounded-full font-bold transition-all duration-300 hover:bg-white/20 hover:scale-105"
              >
                <span className="material-symbols-outlined">movie</span>
                Barcha kinolar
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Horizontal Scrolling Rows */}
      <div className="space-y-margin-desktop py-margin-desktop -mt-20 relative z-20">
        <MovieRow title="Yangi kinolar" items={latestMovies} />
        <MovieRow title="So'nggi seriallar" items={latestSeries} isSeries={true} />
        
        {categories.slice(0, 3).map(cat => (
          <MovieRow key={cat.id} title={`${cat.name} turkumidagi kinolar`} items={latestMovies.slice().reverse()} />
        ))}
      </div>
    </>
  );
}
