import { fetchApi } from "@/lib/api";
import Link from "next/link";
import ShareButton from "@/components/ShareButton";
import RecommendationsSection from "@/components/recommendations/RecommendationsSection";
import RandomRecommendationWidget from "@/components/recommendations/RandomRecommendationWidget";
import { isAdultContent } from "@/lib/adult";
import AdultPoster from "@/components/AdultPoster";
import AdultHeroBackground from "@/components/AdultHeroBackground";

export const revalidate = 60; // 60s ISR kesh: Vercel CDN orqali Render trafigini 90% tejaydi 

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
  is_18_plus?: boolean;
  categories?: any[];
  created_at?: string;
  page_title?: string;
  page_slug?: string;
};

type Series = {
  id: number;
  title: string;
  description: string | null;
  poster_url: string | null;
  imdb_rating: number | null;
  release_year: number | null;
  is_18_plus?: boolean;
  categories?: any[];
  created_at?: string;
  page_title?: string;
  page_slug?: string;
};

const getHeroBadgeLabel = (item: any, isSeries: boolean): string => {
  const pageTitle = item?.page_title || item?.pages?.[0]?.title;
  if (pageTitle) {
    const trimmed = pageTitle.trim();
    const singular = trimmed.replace(/(lar|ler)$/i, "").toLowerCase();
    return `Eng so'nggi ${singular}`;
  }
  return isSeries ? "Eng so'nggi serial" : "Eng so'nggi kino";
};

const MovieRow = ({ 
  title, 
  items, 
  isSeries = false, 
  isDynamicPage = false, 
  pageSlug = "",
  badgeColor = "bg-primary-container"
}: { 
  title: string; 
  items: any[]; 
  isSeries?: boolean; 
  isDynamicPage?: boolean; 
  pageSlug?: string;
  badgeColor?: string;
}) => {
  if (!items || items.length === 0) return null;
  
  return (
    <section className="max-w-container-max mx-auto mb-10 sm:mb-14">
      <div className="px-gutter mb-3 sm:mb-4 flex items-center justify-between">
        <h2 className="font-headline-md text-lg sm:text-xl md:text-2xl text-text-primary flex items-center gap-2 font-bold tracking-tight">
          <span className={`w-1.5 h-5 sm:h-6 ${badgeColor} rounded-full block`}></span>
          {title}
        </h2>
        <Link 
          href={isDynamicPage ? `/p/${pageSlug}` : (isSeries ? "/series" : "/catalog")} 
          className="text-text-secondary hover:text-text-primary text-xs sm:text-sm font-semibold transition-all duration-200 hover:scale-105 active:scale-95 flex items-center gap-1 group"
        >
          <span>Barchasi</span>
          <span className="material-symbols-outlined text-[16px] group-hover:translate-x-0.5 transition-transform">chevron_right</span>
        </Link>
      </div>

      {/* Scroll Slide Row (Yetarlicha ko'rinadi, lekin ekranni to'ldirib yubormaydi) */}
      <div className="flex gap-3 sm:gap-4 overflow-x-auto snap-x hide-scrollbar px-gutter pb-4 pt-1">
        {items.map(item => {
          const itemIsSeries = isDynamicPage ? !!item.is_series : (item.is_series ?? isSeries);
          const itemIs18Plus = isAdultContent(item);
          return (
          <Link 
            href={itemIsSeries ? `/series/${item.id}` : `/movie/${item.code}`} 
            key={itemIsSeries ? `s-${item.id}` : `m-${item.code || item.id}`} 
            className="w-[140px] sm:w-[175px] md:w-[205px] shrink-0 snap-start group relative aspect-[2/3] rounded-xl overflow-hidden cursor-pointer bg-surface-container hover:scale-105 transition-transform duration-300 shadow-md ring-1 ring-white/10 hover:ring-white/25"
          >
            {item.poster_url ? (
              <AdultPoster 
                src={item.poster_url} 
                alt={item.title}
                is18Plus={itemIs18Plus}
                fill
                sizes="(max-width: 640px) 140px, (max-width: 768px) 175px, 205px"
                imageClassName="object-cover group-hover:scale-110 transition-transform duration-500 ease-out"
              />
            ) : (
              <div className="w-full h-full flex flex-col items-center justify-center bg-surface-container-high text-gray-500">
                <span className="material-symbols-outlined text-4xl mb-2 opacity-30">movie</span>
              </div>
            )}
            
            <div className="absolute inset-0 bg-gradient-to-t from-background-obsidian via-background-obsidian/40 to-transparent opacity-80 group-hover:opacity-100 transition-opacity pointer-events-none"></div>
            
            {/* Rating badge */}
            <div className="absolute top-2 right-2 z-10 px-1.5 py-0.5 bg-black/70 backdrop-blur-sm rounded text-rating-gold flex items-center gap-0.5 border border-white/10 pointer-events-none text-[10px] sm:text-xs">
              <span className="material-symbols-outlined text-[13px]" style={{ fontVariationSettings: "'FILL' 1" }}>star</span>
              <span className="font-bold">{item.imdb_rating || item.tmdb_rating || "N/A"}</span>
            </div>

            {/* Quality badge */}
            <div className="absolute top-2 left-2 z-10 flex flex-col gap-1 pointer-events-none">
              <span className="px-1.5 py-0.5 bg-primary-container text-white rounded text-[9px] font-black uppercase tracking-wider shadow">
                1080p
              </span>
              {itemIs18Plus && (
                <span className="px-1.5 py-0.5 bg-red-600/90 text-white rounded text-[9px] font-black uppercase tracking-wider">
                  🔞 18+
                </span>
              )}
            </div>
            
            <div className="absolute bottom-0 left-0 w-full p-2.5 sm:p-3 transform translate-y-1 group-hover:translate-y-0 transition-transform z-10 pointer-events-none">
              <div className="flex gap-1 mb-1">
                <span className="px-1.5 py-0.5 bg-white/15 backdrop-blur-sm rounded text-[9px] font-bold text-text-secondary uppercase tracking-wider">
                  {itemIsSeries ? item.categories?.[0]?.name || "Serial" : item.genres?.split(',')[0] || "Kino"}
                </span>
                {item.release_year && (
                  <span className="px-1.5 py-0.5 bg-white/15 backdrop-blur-sm rounded text-[9px] font-bold text-text-secondary uppercase tracking-wider">
                    {item.release_year}
                  </span>
                )}
              </div>
              <h3 className="text-xs sm:text-sm text-text-primary font-bold line-clamp-2 drop-shadow-md leading-tight">
                {item.title}
              </h3>
            </div>
          </Link>
        )})}
      </div>
    </section>
  );
};

export default async function Home() {
  const botUsername = process.env.NEXT_PUBLIC_BOT_USERNAME || "kinochi_uz_bot";
  let latestMovies: Movie[] = [];
  let latestSeries: Series[] = [];
  let pagesData: any[] = [];

  try {
    const [moviesRes, seriesRes, pagesRes] = await Promise.all([
      fetchApi('/movies?limit=24&exclude_paged=true'),
      fetchApi('/series?limit=24&exclude_paged=true'),
      fetchApi('/pages')
    ]);
    latestMovies = moviesRes?.items || [];
    latestSeries = seriesRes?.items || [];
    const dynamicPages = pagesRes?.items || pagesRes || [];

    pagesData = await Promise.all(dynamicPages.map(async (page: any) => {
      const [pageMovies, pageSeries] = await Promise.all([
        fetchApi(`/movies?limit=15&page_id=${page.id}`),
        fetchApi(`/series?limit=15&page_id=${page.id}`)
      ]);
      
      const combined = [
        ...(pageMovies?.items || []).map((m: any) => ({
          ...m,
          is_series: false,
          page_title: page.title,
          page_slug: page.slug
        })),
        ...(pageSeries?.items || []).map((s: any) => ({
          ...s,
          is_series: true,
          page_title: page.title,
          page_slug: page.slug
        }))
      ];
      
      combined.sort((a, b) => new Date(b.created_at || 0).getTime() - new Date(a.created_at || 0).getTime());
      
      return {
        ...page,
        items: combined.slice(0, 15)
      };
    }));

  } catch (error) {
    console.error("Error fetching data for home page:", error);
  }

  // Barcha so'nggi premyeralar jamlanmasi
  const allRecentItems: any[] = [
    ...latestMovies.map(m => ({ ...m, is_series: false })),
    ...latestSeries.map(s => ({ ...s, is_series: true })),
    ...pagesData.flatMap(p => p.items || [])
  ];

  allRecentItems.sort((a, b) => {
    const timeA = a.created_at ? new Date(a.created_at).getTime() : 0;
    const timeB = b.created_at ? new Date(b.created_at).getTime() : 0;
    if (timeB !== timeA) {
      return timeB - timeA;
    }
    return (b.id || 0) - (a.id || 0);
  });

  const heroItem = allRecentItems[0] || null;
  const isHeroSeries = heroItem ? (heroItem.is_series ?? !heroItem.code) : false;
  const isHero18Plus = isAdultContent(heroItem);

  return (
    <>
      {/* 1. HERO PREMYERA BANNER */}
      {heroItem && (
        <section className="relative w-full pt-20 pb-6 md:pt-28 md:pb-12 md:min-h-[80vh] md:flex md:items-center overflow-hidden">
          <div className="absolute inset-0 w-full h-full bg-background-obsidian pointer-events-none">
            {heroItem.poster_url && (
              <AdultHeroBackground 
                src={heroItem.poster_url} 
                alt={heroItem.title}
                is18Plus={isHero18Plus}
              />
            )}
            <div className="absolute inset-0 bg-gradient-to-b from-background-obsidian/90 via-background-obsidian/40 to-background-obsidian sm:hidden"></div>
            <div className="hidden sm:block absolute inset-0 bg-gradient-to-t from-background-obsidian via-background-obsidian/85 to-background-obsidian/30"></div>
          </div>
          
          <div className="relative z-10 max-w-container-max mx-auto px-gutter w-full flex flex-col md:flex-row items-center gap-6 md:gap-10 mt-2 md:mt-4">
            <div className="flex-1 w-full flex flex-col items-center md:items-start text-center md:text-left bg-white/[0.04] sm:bg-white/5 backdrop-blur-xl p-5 sm:p-8 md:p-10 rounded-2xl sm:rounded-3xl border border-white/10 shadow-2xl">
              <div className="mb-3 sm:mb-4 flex flex-col items-center md:items-start gap-2">
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary-container/15 border border-primary-container/30 text-primary-container font-label-caps text-[10px] sm:text-xs font-bold tracking-widest uppercase backdrop-blur-md">
                  <span className="w-1.5 h-1.5 rounded-full bg-primary-container animate-pulse"></span>
                  <span>{getHeroBadgeLabel(heroItem, isHeroSeries)}</span>
                </div>
                
                <h1 className="font-display-hero text-2xl sm:text-4xl md:text-5xl text-text-primary drop-shadow-2xl tracking-tight leading-tight">
                  {heroItem.title}
                </h1>
              </div>
              
              <div className="flex flex-wrap items-center justify-center md:justify-start gap-2 sm:gap-3 mb-3 sm:mb-5">
                <div className="flex items-center gap-1 text-rating-gold bg-black/50 px-2 py-0.5 rounded-lg backdrop-blur-sm border border-white/10 text-xs">
                  <span className="material-symbols-outlined text-[14px]" style={{ fontVariationSettings: "'FILL' 1" }}>star</span>
                  <span className="font-bold">{heroItem.imdb_rating || heroItem.tmdb_rating || "N/A"}</span>
                </div>
                {heroItem.release_year && (
                  <span className="text-text-secondary bg-white/10 backdrop-blur-sm px-2 py-0.5 rounded-lg border border-white/10 text-xs font-medium">
                    {heroItem.release_year}
                  </span>
                )}
                <span className="text-text-primary bg-white/10 backdrop-blur-sm px-2 py-0.5 rounded-lg border border-white/10 text-xs font-medium">
                  {heroItem.page_title || (isHeroSeries ? heroItem.categories?.[0]?.name || "Serial" : heroItem.genres?.split(',')[0] || "Kino")}
                </span>
                {isHero18Plus && (
                  <span className="inline-flex items-center gap-1 text-red-300 bg-red-600/25 px-2 py-0.5 rounded-lg border border-red-500/40 text-xs font-bold">
                    <span>🔞</span>
                    <span>18+</span>
                  </span>
                )}
              </div>
              
              <p className="text-xs sm:text-sm md:text-base text-text-secondary mb-5 leading-relaxed line-clamp-2">
                {heroItem.description || "Telegram tarmog'idagi eng katta va qulay kino bazasi. O'zingiz yoqtirgan filmlarni toping va bepul tomosha qiling."}
              </p>
              
              <div className="flex flex-col sm:flex-row gap-2.5 sm:gap-3 items-center w-full sm:w-auto">
                <Link 
                  href={isHeroSeries ? `/series/${heroItem.id}` : `/movie/${heroItem.code}`}
                  className="w-full sm:w-auto flex items-center justify-center gap-2 bg-primary-container text-white px-6 sm:px-7 py-3 rounded-xl font-label-caps text-xs sm:text-sm uppercase tracking-widest hover:bg-inverse-primary hover:scale-[1.02] shadow-lg shadow-black/40 transition-all font-bold active:scale-95 cursor-pointer"
                >
                  <span className="material-symbols-outlined text-[20px]" style={{ fontVariationSettings: "'FILL' 1" }}>play_circle</span>
                  <span>TOMOSHA QILISH</span>
                </Link>
                <ShareButton 
                  title={heroItem.title} 
                  text={`${heroItem.title} ni bepul tomosha qiling.`}
                  url={`/${isHeroSeries ? 'series' : 'movie'}/${isHeroSeries ? heroItem.id : heroItem.code}`}
                  code={isHeroSeries ? `s_${heroItem.id}` : heroItem.code}
                  botUsername={botUsername}
                  className="w-full sm:w-auto flex items-center justify-center gap-2 bg-white/10 hover:bg-white/15 text-white px-5 sm:px-6 py-3 rounded-xl font-label-caps text-xs sm:text-sm uppercase tracking-widest border border-white/15 transition-all font-bold active:scale-95 shadow-md cursor-pointer"
                />
              </div>
            </div>

            <div className="hidden md:block w-1/3 lg:w-[380px] shrink-0 relative perspective-1000">
              <div className="aspect-[2/3] w-full rounded-2xl overflow-hidden shadow-[0_20px_50px_rgba(0,0,0,0.5)] border-4 border-white/5 transform rotate-y-[-8deg] rotate-x-[4deg] hover:rotate-y-0 hover:rotate-x-0 transition-transform duration-700 ease-out group relative bg-surface-container-high">
                {heroItem.poster_url ? (
                  <AdultPoster 
                    src={heroItem.poster_url}
                    alt={heroItem.title}
                    is18Plus={isHero18Plus}
                    fill
                    priority
                    imageClassName="object-cover group-hover:scale-105 transition-transform duration-700"
                  />
                ) : (
                  <div className="absolute inset-0 flex items-center justify-center bg-surface-container-high text-gray-500">
                     <span className="material-symbols-outlined text-5xl opacity-30">movie</span>
                  </div>
                )}
                <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent opacity-50 group-hover:opacity-20 transition-opacity duration-700 pointer-events-none"></div>
              </div>
            </div>
          </div>
        </section>
      )}

      {/* 2. ENG SO'NGGI PREMYERALAR (PREMYERANING OSTIDA SCROLL SLIDE) */}
      <div className="pt-2 sm:pt-4 relative z-20 bg-background-obsidian">
        <MovieRow 
          title="Eng so'nggi premyeralar" 
          items={allRecentItems.slice(1, 16)} 
          badgeColor="bg-primary-container"
        />

        {/* 3. ENG SO'NGGI QO'SHILGANLAR (PREMYERANING TO'G'RIDAN-TO'G'RI OSTIDA SCROLL SLIDE) */}
        <MovieRow 
          title="Eng so'nggi qo'shilganlar" 
          items={latestMovies.slice(0, 16)} 
          badgeColor="bg-rating-gold"
        />

        {/* 4. TAVSIYALAR (Authenticated userlar uchun) */}
        <RecommendationsSection />

        {/* 5. TASODIFIY KINO TANLASH WIDGETI */}
        <RandomRecommendationWidget 
          movies={latestMovies} 
          series={latestSeries} 
          pages={pagesData} 
        />

        {/* 6. SERIALLAR & DYNAMIC SAHIFALAR */}
        <MovieRow 
          title="Ommabop seriallar" 
          items={latestSeries} 
          isSeries={true} 
          badgeColor="bg-sky-500"
        />
        
        {pagesData.map(page => (
          <MovieRow 
            key={page.id} 
            title={page.title} 
            items={page.items} 
            isDynamicPage={true} 
            pageSlug={page.slug} 
            badgeColor="bg-primary-container"
          />
        ))}
      </div>
    </>
  );
}
