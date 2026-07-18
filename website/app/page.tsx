import { fetchApi } from "@/lib/api";
import Link from "next/link";
import Image from "next/image";
import ShareButton from "@/components/ShareButton";

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
            className="w-[160px] md:w-[240px] shrink-0 snap-start group relative aspect-[2/3] rounded-xl overflow-hidden cursor-pointer bg-surface-container hover:scale-105 transition-transform duration-300 shadow-lg hover:shadow-[0_0_20px_rgba(229,9,20,0.3)] ring-1 ring-white/5 hover:ring-primary-container"
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
              <span className="font-label-caps text-xs font-bold">{item.imdb_rating || item.tmdb_rating || "N/A"}</span>
            </div>
            
            <div className="absolute bottom-0 left-0 w-full p-4 transform translate-y-2 group-hover:translate-y-0 transition-transform">
              <div className="flex gap-1 mb-1">
                <span className="px-1.5 py-0.5 bg-white/10 backdrop-blur-sm rounded text-[10px] font-bold text-text-secondary uppercase tracking-wider">{isSeries ? item.categories?.[0]?.name || "Serial" : item.genres?.split(',')[0] || "Kino"}</span>
                {item.release_year && <span className="px-1.5 py-0.5 bg-white/10 backdrop-blur-sm rounded text-[10px] font-bold text-text-secondary uppercase tracking-wider">{item.release_year}</span>}
              </div>
              <h3 className="font-body-lg text-text-primary font-bold line-clamp-2 drop-shadow-md">{item.title}</h3>
            </div>
          </Link>
        ))}
      </div>
    </section>
  );
};

export default async function Home() {
  const botUsername = process.env.NEXT_PUBLIC_BOT_USERNAME || "kinochi_uz_bot";
  let latestMovies: Movie[] = [];
  let latestSeries: Series[] = [];
  let categories: Category[] = [];

  try {
    const [moviesRes, seriesRes, catRes] = await Promise.all([
      fetchApi('/movies?limit=10'),
      fetchApi('/series?limit=10'),
      fetchApi('/categories')
    ]);
    latestMovies = moviesRes?.items || [];
    latestSeries = seriesRes?.items || [];
    categories = catRes || [];
  } catch (error) {
    console.error("Error fetching data for home page:", error);
  }

  let heroItem: any = null;
  let isHeroSeries = false;
  
  if (latestMovies.length > 0) {
    heroItem = latestMovies[0];
  } else if (latestSeries.length > 0) {
    heroItem = latestSeries[0];
    isHeroSeries = true;
  }

  return (
    <>
      {heroItem && (
        <section className="relative w-full min-h-[100svh] md:min-h-[85vh] flex items-center pt-24 pb-16 overflow-hidden">
          {/* Main Background Image - slightly zoomed and blurred for a creative backdrop */}
          <div className="absolute inset-0 w-full h-full bg-background-obsidian">
            {heroItem.poster_url && (
              <Image 
                src={heroItem.poster_url}
                alt={heroItem.title}
                fill
                priority
                className="object-cover opacity-40 scale-110 blur-sm"
                style={{ objectPosition: 'center 20%' }}
              />
            )}
            <div className="absolute inset-0 bg-gradient-to-t from-background-obsidian via-background-obsidian/80 to-background-obsidian/30"></div>
          </div>
          
          <div className="relative z-10 max-w-container-max mx-auto px-gutter w-full flex flex-col md:flex-row items-center gap-12 mt-10">
            {/* Left: Glassmorphic Info Card */}
            <div className="flex-1 w-full flex flex-col items-center md:items-start text-center md:text-left bg-white/5 backdrop-blur-xl p-8 md:p-12 rounded-3xl border border-white/10 shadow-2xl">
              <div className="mb-6 flex flex-col items-center md:items-start gap-4">
                {/* Specific Label Requested by User */}
                <div className="inline-block px-4 py-1.5 rounded-full bg-primary-container/20 border border-primary-container/50 text-primary-container font-label-caps text-xs font-bold tracking-widest uppercase shadow-[0_0_15px_rgba(229,9,20,0.2)] animate-pulse">
                  {isHeroSeries ? "Eng so'nggi serial" : "Eng so'nggi kino"}
                </div>
                
                <h1 className="font-display-hero text-4xl sm:text-5xl md:text-6xl text-text-primary drop-shadow-2xl tracking-tight leading-tight">
                  {heroItem.title}
                </h1>
              </div>
              
              <div className="flex flex-wrap items-center justify-center md:justify-start gap-3 mb-6">
                <div className="flex items-center gap-1 text-rating-gold bg-black/40 px-3 py-1 rounded-md backdrop-blur-sm border border-white/10">
                  <span className="material-symbols-outlined text-[16px]" style={{ fontVariationSettings: "'FILL' 1" }}>star</span>
                  <span className="font-bold text-sm">{heroItem.imdb_rating || heroItem.tmdb_rating || "N/A"}</span>
                </div>
                {heroItem.release_year && (
                  <span className="text-text-secondary bg-white/10 backdrop-blur-sm px-3 py-1 rounded-md border border-white/10 text-sm font-medium">{heroItem.release_year}</span>
                )}
                <span className="text-text-primary bg-white/10 backdrop-blur-sm px-3 py-1 rounded-md border border-white/10 text-sm font-medium">
                  {isHeroSeries ? heroItem.categories?.[0]?.name || "Serial" : heroItem.genres?.split(',')[0] || "Kino"}
                </span>
              </div>
              
              <p className="font-body-lg text-lg text-text-secondary mb-8 leading-relaxed line-clamp-3">
                {heroItem.description || "Telegram tarmog'idagi eng katta va qulay kino bazasi. O'zingiz yoqtirgan filmlarni toping va bepul tomosha qiling."}
              </p>
              
              <div className="flex flex-col sm:flex-row gap-4 w-full sm:w-auto">
                <a 
                  href={`https://t.me/${botUsername}?start=${isHeroSeries ? 's_' + heroItem.id : heroItem.code}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center justify-center gap-3 bg-primary-container text-white px-8 py-4 rounded-xl font-label-caps text-sm uppercase tracking-widest hover:bg-inverse-primary hover:-translate-y-1 hover:shadow-[0_10px_30px_rgba(229,9,20,0.5)] transition-all duration-300 font-bold"
                >
                  <span className="material-symbols-outlined text-[24px]" style={{ fontVariationSettings: "'FILL' 1" }}>play_circle</span>
                  Tomosha qilish
                </a>
                <ShareButton 
                  title={heroItem.title} 
                  text={`${heroItem.title} ni bepul tomosha qiling.`}
                  url={`https://kinochi.uz/${isHeroSeries ? 'series' : 'movie'}/${isHeroSeries ? heroItem.id : heroItem.code}`}
                />
              </div>
            </div>

            {/* Right: Floating Poster Image (Different from Movie details page) */}
            <div className="hidden md:block w-1/3 lg:w-[450px] shrink-0 relative perspective-1000">
              <div className="aspect-[2/3] w-full rounded-2xl overflow-hidden shadow-[0_20px_50px_rgba(0,0,0,0.5)] border-4 border-white/5 transform rotate-y-[-10deg] rotate-x-[5deg] hover:rotate-y-0 hover:rotate-x-0 transition-transform duration-700 ease-out group">
                {heroItem.poster_url ? (
                  <Image 
                    src={heroItem.poster_url}
                    alt={heroItem.title}
                    fill
                    priority
                    className="object-cover group-hover:scale-105 transition-transform duration-700"
                  />
                ) : (
                  <div className="absolute inset-0 flex items-center justify-center bg-surface-container-high text-gray-500">
                     <span className="material-symbols-outlined text-6xl opacity-30">movie</span>
                  </div>
                )}
                <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent opacity-50 group-hover:opacity-20 transition-opacity duration-700"></div>
              </div>
            </div>
          </div>
        </section>
      )}

      {/* Horizontal Scrolling Rows */}
      <div className="space-y-margin-desktop py-margin-desktop relative z-20 bg-background-obsidian">
        <MovieRow title="Yangi kinolar" items={latestMovies} />
        <MovieRow title="So'nggi seriallar" items={latestSeries} isSeries={true} />
        
        {categories.slice(0, 3).map(cat => (
          <MovieRow key={cat.id} title={`${cat.name} turkumidagi kinolar`} items={latestMovies.slice().reverse()} />
        ))}
      </div>
    </>
  );
}
