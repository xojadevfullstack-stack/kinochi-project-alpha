import { fetchApi, getPublicConfig } from "@/lib/api";
import Link from "next/link";
import RecommendationsSection from "@/components/recommendations/RecommendationsSection";
import ContinueWatchingSection from "@/components/home/ContinueWatchingSection";
import Top10PodiumSection from "@/components/home/Top10PodiumSection";
import HomeCollectionsRow from "@/components/home/HomeCollectionsRow";
import MediaMarqueeSection from "@/components/home/MediaMarqueeSection";
import MovieCard from "@/components/catalog/MovieCard";
import { isAdultContent } from "@/lib/adult";
import OnboardingSpotlight from "@/components/OnboardingSpotlight";
import HeroCarousel from "@/components/home/HeroCarousel";

export const revalidate = 60; // 60s ISR kesh

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

const MovieRow = ({
  title,
  items,
  isSeries = false,
  isDynamicPage = false,
  pageSlug = ""
}: {
  title: string;
  items: any[];
  isSeries?: boolean;
  isDynamicPage?: boolean;
  pageSlug?: string;
}) => {
  if (!items || items.length === 0) return null;

  const viewAllHref = isDynamicPage ? `/p/${pageSlug}` : (isSeries ? "/series" : "/movies");

  return (
    <section className="max-w-container-max mx-auto px-gutter mb-14 sm:mb-16 cv-auto">
      <div className="mb-stack-md flex items-center justify-between">
        <h2 className="font-headline-md text-headline-md text-text-primary flex items-center gap-2">
          <span className="w-1 h-6 bg-primary rounded-full block" />
          <span>{title}</span>
        </h2>
        <Link
          href={viewAllHref}
          className="text-text-secondary hover:text-text-primary text-sm font-semibold transition-all duration-200 hover:scale-105 active:scale-95 flex items-center gap-1 group"
        >
          <span>Barchasi</span>
          <span className="material-symbols-outlined text-[16px] group-hover:translate-x-0.5 transition-transform">
            chevron_right
          </span>
        </Link>
      </div>
      <div className="flex gap-2 sm:gap-4 overflow-x-auto snap-x hide-scrollbar pb-6 pt-2">
        {items.map((item, idx) => {
          const itemIsSeries = isDynamicPage ? !!item.is_series : isSeries;
          const normalizedItem = {
            ...item,
            is_series: itemIsSeries,
          };
          return (
            <div
              key={itemIsSeries ? `s-${item.id}` : `m-${item.code || item.id}`}
              className={`${idx >= 6 ? "hidden sm:block " : ""}w-[calc((100%-16px)/3)] sm:w-[170px] md:w-[200px] shrink-0 snap-start`}
            >
              <MovieCard item={normalizedItem} />
            </div>
          );
        })}
        <Link
          href={viewAllHref}
          className="w-[calc((100%-16px)/3)] sm:w-[170px] md:w-[200px] aspect-[2/3] shrink-0 snap-start rounded-2xl border-2 border-dashed border-slate-300 dark:border-primary/35 hover:border-primary bg-white/95 dark:bg-[#0E1117]/75 hover:bg-slate-50 dark:hover:bg-[#141824] p-2.5 sm:p-4 flex flex-col items-center justify-center text-center transition-all duration-300 group shadow-sm hover:shadow-lg"
        >
          <span className="material-symbols-outlined text-primary text-3xl sm:text-4xl mb-1.5 group-hover:scale-110 transition-transform">
            grid_view
          </span>
          <span className="text-xs sm:text-sm font-semibold text-slate-600 dark:text-gray-300 line-clamp-1 mb-2">
            {title}
          </span>
          <span className="inline-flex items-center gap-0.5 text-[11px] sm:text-xs font-bold text-primary group-hover:underline">
            <span className="sm:hidden">Barchasi</span>
            <span className="hidden sm:inline">Barchasini ko&apos;rish</span>
            <span className="material-symbols-outlined text-[14px]">chevron_right</span>
          </span>
        </Link>
      </div>
    </section>
  );
};

export default async function Home() {
  const { bot_username: botUsername } = await getPublicConfig();
  let latestMovies: Movie[] = [];
  let latestSeries: Series[] = [];
  let globalMovies: Movie[] = [];
  let globalSeries: Series[] = [];
  let pagesData: any[] = [];
  let collectionsList: any[] = [];

  try {
    const [moviesRes, seriesRes, pagesRes, globalMoviesRes, globalSeriesRes, collectionsRes] = await Promise.all([
      fetchApi("/movies?limit=20&exclude_paged=true"),
      fetchApi("/series?limit=20&exclude_paged=true"),
      fetchApi("/pages"),
      fetchApi("/movies?limit=10"),
      fetchApi("/series?limit=10"),
      fetchApi("/collections").catch(() => [])
    ]);
    latestMovies = moviesRes?.items || [];
    latestSeries = seriesRes?.items || [];
    globalMovies = globalMoviesRes?.items || [];
    globalSeries = globalSeriesRes?.items || [];
    collectionsList = Array.isArray(collectionsRes) ? collectionsRes : (collectionsRes?.items || []);
    const rawPages = pagesRes?.items || pagesRes || [];
    const dynamicPages = rawPages.filter((page: any) => {
      const slug = (page.slug || "").toLowerCase().trim();
      const title = (page.title || "").toLowerCase().trim();
      return (
        slug !== "seriallar" &&
        slug !== "kinolar" &&
        slug !== "series" &&
        slug !== "movies" &&
        title !== "seriallar" &&
        title !== "kinolar"
      );
    });

    pagesData = await Promise.all(
      dynamicPages.map(async (page: any) => {
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

        combined.sort(
          (a, b) => new Date(b.updated_at || b.created_at || 0).getTime() - new Date(a.updated_at || a.created_at || 0).getTime()
        );

        return {
          ...page,
          items: combined.slice(0, 15)
        };
      })
    );
  } catch (error) {
    console.error("Error fetching data for home page:", error);
  }

  // Gather all recent items across global movies, global series, unpaged rows, and pages
  const rawRecentItems: any[] = [
    ...globalMovies.map((m) => ({ ...m, is_series: false })),
    ...globalSeries.map((s) => ({ ...s, is_series: true })),
    ...latestMovies.map((m) => ({ ...m, is_series: false })),
    ...latestSeries.map((s) => ({ ...s, is_series: true })),
    ...pagesData.flatMap((p) => p.items || [])
  ];

  // Deduplicate items across multiple categories/pages (e.g. Anime + Multfilm)
  const seenRecentKeys = new Set<string>();
  const allRecentItems: any[] = [];
  for (const item of rawRecentItems) {
    const key = item.is_series ? `series-${item.id}` : `movie-${item.code || item.id}`;
    if (!seenRecentKeys.has(key)) {
      seenRecentKeys.add(key);
      allRecentItems.push(item);
    }
  }

  allRecentItems.sort((a, b) => {
    const timeA = new Date(a.updated_at || a.created_at || 0).getTime();
    const timeB = new Date(b.updated_at || b.created_at || 0).getTime();
    if (timeB !== timeA) {
      return timeB - timeA;
    }
    return (b.id || 0) - (a.id || 0);
  });

  const heroSlides = allRecentItems.slice(0, 6);

  // Yagona birlashtirilgan "Eng so'nggi premyeralar va yangiliklar" ro'yxati (Hero ostidagi ixcham slayder)
  const unifiedRecentItems = allRecentItems.slice(1, 25);

  return (
    <>
      {/* 1. HERO CAROUSEL (#heroSlide) */}
      <HeroCarousel items={heroSlides} botUsername={botUsername} />

      {/* 1.5 TOP 10 EDITORIAL PODIUM */}
      <Top10PodiumSection items={allRecentItems} />

      {/* ========================================================
          2. YAGONA BIRLASHTIRILGAN PREMYERALAR VA YANGILIKLAR SLIDERI
          (Hero banner ostida, ixcham va minimalist kartochkalar)
      ======================================================== */}
      {unifiedRecentItems.length > 0 && (
        <section className="max-w-container-max mx-auto px-gutter mb-12 sm:mb-16 mt-4">
          <div className="flex items-center justify-between mb-4 gap-2">
            <h2 className="font-headline-md text-base sm:text-xl md:text-2xl text-text-primary flex items-center gap-2 font-bold whitespace-nowrap">
              <span className="w-1 h-5 sm:h-6 bg-primary rounded-full block shrink-0" />
              <span>Premyeralar va yangiliklar</span>
            </h2>
            <Link
              href="/catalog"
              className="text-text-secondary hover:text-primary text-xs sm:text-sm font-semibold transition-colors flex items-center gap-1 group shrink-0"
            >
              <span className="hidden sm:inline">Barchasi (Katalogda)</span>
              <span className="sm:hidden">Barchasi</span>
              <span className="material-symbols-outlined text-[16px] group-hover:translate-x-0.5 transition-transform">
                arrow_forward
              </span>
            </Link>
          </div>

          {/* Ixcham Scroll Slayder */}
          <div className="flex gap-2 sm:gap-4 overflow-x-auto snap-x hide-scrollbar pb-4 pt-1">
            {unifiedRecentItems.map((item, idx) => (
              <div
                key={item.is_series ? `rec-s-${item.id}` : `rec-m-${item.code || item.id}`}
                className={`${idx >= 6 ? "hidden sm:block " : ""}w-[calc((100%-16px)/3)] sm:w-[170px] md:w-[200px] shrink-0 snap-start`}
              >
                <MovieCard item={item} />
              </div>
            ))}
            <Link
              href="/catalog"
              className="w-[calc((100%-16px)/3)] sm:w-[170px] md:w-[200px] aspect-[2/3] shrink-0 snap-start rounded-2xl border-2 border-dashed border-slate-300 dark:border-primary/35 hover:border-primary bg-white/95 dark:bg-[#0E1117]/75 hover:bg-slate-50 dark:hover:bg-[#141824] p-2.5 sm:p-4 flex flex-col items-center justify-center text-center transition-all duration-300 group shadow-sm hover:shadow-lg"
            >
              <span className="material-symbols-outlined text-primary text-3xl sm:text-4xl mb-1.5 group-hover:scale-110 transition-transform">
                movie_filter
              </span>
              <span className="text-xs sm:text-sm font-semibold text-slate-600 dark:text-gray-300 mb-2">
                Katalog
              </span>
              <span className="inline-flex items-center gap-0.5 text-[11px] sm:text-xs font-bold text-primary group-hover:underline">
                <span className="sm:hidden">Barchasi</span>
                <span className="hidden sm:inline">Barchasini ko&apos;rish</span>
                <span className="material-symbols-outlined text-[14px]">chevron_right</span>
              </span>
            </Link>
          </div>
        </section>
      )}

      {/* Personalized Recommendations (Only visible if authenticated) */}
      <ContinueWatchingSection />

      {/* To'plamlar (3D Fan Stack Row) */}
      <HomeCollectionsRow collections={collectionsList} />

      <RecommendationsSection />

      {/* iTV Style Multi-Row Animated Marquee Section */}
      <MediaMarqueeSection items={allRecentItems} />


      {/* Horizontal Scrolling Rows for Bo'limlar */}
      <div className="space-y-margin-desktop py-4 relative z-20 bg-transparent">
        <MovieRow title="Kinolar" items={latestMovies} />
        <MovieRow title="Seriallar" items={latestSeries} isSeries={true} />

        {pagesData.map((page) => (
          <MovieRow
            key={page.id}
            title={page.title}
            items={page.items}
            isDynamicPage={true}
            pageSlug={page.slug}
          />
        ))}
      </div>
      {/* Interactive First-Time Spotlight Onboarding */}
      <OnboardingSpotlight />
    </>
  );
}
