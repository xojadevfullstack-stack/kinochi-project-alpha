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
        <section className="relative w-full min-h-[700px] flex items-center pt-[100px] pb-stack-lg overflow-hidden">
          {/* Background Blur & Gradient Overlays */}
          <div className="absolute inset-0 bg-background-obsidian">
            <div className="absolute inset-0 bg-cover bg-center opacity-30 blur-xl" 
                 style={{ backgroundImage: `url('${heroItem.poster_url || ''}')` }}></div>
          </div>
          <div className="absolute inset-0 bg-gradient-to-t from-background-obsidian via-background-obsidian/[0.85] to-transparent"></div>
          <div className="absolute inset-0 bg-gradient-to-r from-background-obsidian via-background-obsidian/[0.55] to-transparent hidden md:block"></div>
          
          {/* Content Container */}
          <div className="relative z-10 max-w-container-max mx-auto px-gutter w-full flex flex-col md:flex-row items-center md:items-end gap-margin-desktop">
            {/* Left: Poster */}
            <div className="w-full md:w-1/3 lg:w-[350px] shrink-0 mt-stack-lg md:mt-0 relative group perspective-1000">
              <div className="aspect-[2/3] rounded-xl overflow-hidden shadow-2xl shadow-primary-container/20 border border-white/10 transition-transform duration-500 ease-out group-hover:scale-[1.02] group-hover:shadow-primary-container/40 relative bg-surface-container-high">
                {heroItem.poster_url ? (
                  <Image 
                    src={heroItem.poster_url}
                    alt={heroItem.title}
                    fill
                    priority
                    className="object-cover"
                  />
                ) : (
                  <div className="absolute inset-0 flex items-center justify-center text-gray-500">
                     <span className="material-symbols-outlined text-6xl opacity-30">movie</span>
                  </div>
                )}
                <div className="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"></div>
              </div>
            </div>
            
            {/* Right: Movie Info */}
            <div className="flex-1 flex flex-col w-full md:pb-stack-lg">
              <h1 className="font-display-hero text-4xl sm:text-[48px] md:text-display-hero text-text-primary mb-stack-sm drop-shadow-lg text-center md:text-left tracking-tighter leading-tight">
                {heroItem.title}
              </h1>
              
              {/* Badges Row */}
              <div className="flex flex-wrap items-center justify-center md:justify-start gap-3 mb-stack-md font-label-caps text-label-caps tracking-widest uppercase text-xs">
                <div className="flex items-center gap-1 text-rating-gold bg-black/50 px-3 py-1.5 rounded backdrop-blur-sm border border-white/5">
                  <span className="material-symbols-outlined text-[16px]" style={{ fontVariationSettings: "'FILL' 1" }}>star</span>
                  <span>{heroItem.imdb_rating || heroItem.tmdb_rating || "N/A"}</span>
                </div>
                <span className="text-text-secondary bg-white/5 px-3 py-1.5 rounded border border-white/5">{heroItem.release_year || "2024"}</span>
                <span className="text-text-primary font-bold bg-white/10 px-3 py-1.5 rounded border border-white/20">PREMIUM</span>
                <span className="text-text-primary bg-white/5 px-3 py-1.5 rounded border border-white/5">{isHeroSeries ? "SERIAL" : "KINO"}</span>
              </div>
              
              {/* Description */}
              <p className="font-body-lg text-body-lg text-text-secondary mb-stack-lg max-w-3xl text-center md:text-left leading-relaxed line-clamp-4">
                {heroItem.description || "Ushbu ma'lumot kiritilmagan. Lekin bu sizni ajoyib premyerani tomosha qilishdan to'xtatib qolmasligi kerak!"}
              </p>
              
              {/* Action Buttons */}
              <div className="flex flex-col sm:flex-row gap-4 items-center justify-center md:justify-start">
                <a 
                  href={`https://t.me/${botUsername}?start=${isHeroSeries ? 's_' + heroItem.id : heroItem.code}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="w-full sm:w-auto flex items-center justify-center gap-2 bg-primary-container text-white px-8 py-4 rounded-full font-label-caps text-xs uppercase tracking-widest hover:bg-inverse-primary hover:scale-105 hover:shadow-[0_0_30px_rgba(229,9,20,0.4)] transition-all duration-300 ease-out group font-bold"
                >
                  <svg className="w-5 h-5 group-hover:scale-110 transition-transform" fill="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.896-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/>
                  </svg>
                  TELEGRAM ORQALI TOMOSHA QILISH
                </a>
                <ShareButton 
                  title={heroItem.title} 
                  text={`${heroItem.title} ni bepul tomosha qiling.`}
                  url={`https://kinochi.uz/${isHeroSeries ? 'series' : 'movie'}/${isHeroSeries ? heroItem.id : heroItem.code}`}
                />
              </div>
            </div>
          </div>
        </section>
      )}

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
