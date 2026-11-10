import { Suspense } from "react";
import { fetchApi } from "@/lib/api";
import { Metadata } from "next";
import Link from "next/link";
import CatalogGrid from "@/components/catalog/CatalogGrid";
import { CatalogItem } from "@/lib/api/catalog";
import BackButton from "@/components/BackButton";
import LiveSearch from "@/components/LiveSearch";
import UnifiedFilterBar from "@/components/catalog/UnifiedFilterBar";
import { DEFAULT_GENRES, DEFAULT_YEARS, DEFAULT_MEDIA_TYPES } from "@/lib/filterConstants";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Katalog - MediaPlus",
  description: "Barcha kinolar, seriallar, doramalar, anime va multfilmlar to'liq katalogi.",
};

const CATALOG_CATEGORIES = [
  {
    id: "top100",
    name: "Top 100",
    subtitle: "Eng sara 100 ta film va serial",
    href: "/top100",
    icon: "emoji_events",
    accent: "from-primary/20 to-transparent",
    iconColor: "text-primary",
  },
  {
    id: "movies",
    name: "Kinolar",
    subtitle: "To'liq metrajli filmlar",
    href: "/movies",
    icon: "movie",
    accent: "from-red-500/20 to-transparent",
    iconColor: "text-red-400",
  },
  {
    id: "series",
    name: "Seriallar",
    subtitle: "Ko'p qismli seriallar",
    href: "/series",
    icon: "live_tv",
    accent: "from-sky-500/20 to-transparent",
    iconColor: "text-sky-400",
  },
  {
    id: "doramas",
    name: "Doramalar",
    subtitle: "Koreya va Osiyo seriallari",
    href: "/doramas",
    icon: "spa",
    accent: "from-rose-500/20 to-transparent",
    iconColor: "text-rose-400",
  },
  {
    id: "anime",
    name: "Anime",
    subtitle: "Yapon animatsiyasi va seriallari",
    href: "/anime",
    icon: "auto_awesome",
    accent: "from-violet-500/20 to-transparent",
    iconColor: "text-violet-400",
  },
  {
    id: "cartoons",
    name: "Multfilmlar",
    subtitle: "Bolalar va oilaviy multfilmlar",
    href: "/cartoons",
    icon: "cruelty_free",
    accent: "from-emerald-500/20 to-transparent",
    iconColor: "text-emerald-400",
  },
];

export default async function FullCatalogPage({
  searchParams
}: {
  searchParams: { category?: string; year?: string; genre?: string; sort?: string; search?: string; type?: string; page_id?: string }
}) {
  let movies: CatalogItem[] = [];
  let total = 0;
  let categories: any[] = [];
  const pageSize = 60;

  const selectedType = searchParams.type;
  const isAll = !selectedType || selectedType === "all";
  const isMovie = selectedType === "movie" || selectedType === "movies";
  const isSeries = selectedType === "series";
  const isDorama = selectedType === "dorama" || selectedType === "doramas";
  const isAnime = selectedType === "anime";
  const isCartoon = selectedType === "cartoon" || selectedType === "cartoons" || selectedType === "animation";

  const paramParts: string[] = [];
  if (searchParams.category) paramParts.push(`category_id=${searchParams.category}`);
  if (searchParams.page_id) paramParts.push(`page_id=${searchParams.page_id}`);
  if (searchParams.genre) paramParts.push(`genre=${encodeURIComponent(searchParams.genre)}`);
  if (searchParams.year) paramParts.push(`year=${searchParams.year}`);
  if (searchParams.search) paramParts.push(`search=${encodeURIComponent(searchParams.search)}`);
  if (searchParams.sort) paramParts.push(`sort=${encodeURIComponent(searchParams.sort)}`);
  const commonParams = paramParts.length > 0 ? `&${paramParts.join("&")}` : "";

  try {
    if (isMovie) {
      const [moviesData, categoriesData] = await Promise.all([
        fetchApi(`/movies?limit=${pageSize}${commonParams}`).catch(() => ({ items: [], total: 0 })),
        fetchApi("/categories").catch(() => []),
      ]);
      movies = (moviesData?.items || []).map((m: any) => ({ ...m, is_series: false }));
      total = moviesData?.total || movies.length;
      categories = Array.isArray(categoriesData) ? categoriesData : (categoriesData?.items || []);
    } else if (isSeries) {
      const [seriesData, categoriesData] = await Promise.all([
        fetchApi(`/series?limit=${pageSize}${commonParams}`).catch(() => ({ items: [], total: 0 })),
        fetchApi("/categories").catch(() => []),
      ]);
      movies = (seriesData?.items || []).map((s: any) => ({ ...s, is_series: true }));
      total = seriesData?.total || movies.length;
      categories = Array.isArray(categoriesData) ? categoriesData : (categoriesData?.items || []);
    } else if (isAnime) {
      const [seriesData, moviesData, categoriesData] = await Promise.all([
        fetchApi(`/series?limit=${pageSize}&category_id=2${commonParams}`).catch(() => ({ items: [], total: 0 })),
        fetchApi(`/movies?limit=${pageSize}&category_id=2${commonParams}`).catch(() => ({ items: [], total: 0 })),
        fetchApi("/categories").catch(() => []),
      ]);
      const seriesItems = (seriesData?.items || []).map((s: any) => ({ ...s, is_series: true }));
      const movieItems = (moviesData?.items || []).map((m: any) => ({ ...m, is_series: false }));
      movies = [...seriesItems, ...movieItems];
      total = (seriesData?.total || 0) + (moviesData?.total || 0);
      categories = Array.isArray(categoriesData) ? categoriesData : (categoriesData?.items || []);
    } else if (isCartoon) {
      const [moviesData, seriesData, categoriesData] = await Promise.all([
        fetchApi(`/movies?limit=${pageSize}&category_id=22${commonParams}`).catch(() => ({ items: [], total: 0 })),
        fetchApi(`/series?limit=${pageSize}&category_id=22${commonParams}`).catch(() => ({ items: [], total: 0 })),
        fetchApi("/categories").catch(() => []),
      ]);
      const movieItems = (moviesData?.items || []).map((m: any) => ({ ...m, is_series: false }));
      const seriesItems = (seriesData?.items || []).map((s: any) => ({ ...s, is_series: true }));
      movies = [...movieItems, ...seriesItems];
      total = (moviesData?.total || 0) + (seriesData?.total || 0);
      categories = Array.isArray(categoriesData) ? categoriesData : (categoriesData?.items || []);
    } else if (isDorama) {
      const [seriesData, moviesData, categoriesData] = await Promise.all([
        fetchApi(`/series?limit=${pageSize}&category_id=40${commonParams}`).catch(() => ({ items: [], total: 0 })),
        fetchApi(`/movies?limit=${pageSize}&category_id=40${commonParams}`).catch(() => ({ items: [], total: 0 })),
        fetchApi("/categories").catch(() => []),
      ]);
      const seriesItems = (seriesData?.items || []).map((s: any) => ({ ...s, is_series: true }));
      const movieItems = (moviesData?.items || []).map((m: any) => ({ ...m, is_series: false }));
      movies = [...seriesItems, ...movieItems];
      total = (seriesData?.total || 0) + (moviesData?.total || 0);
      categories = Array.isArray(categoriesData) ? categoriesData : (categoriesData?.items || []);
    } else {
      // Default: ALL (Fetch both movies and series combined)
      const [moviesData, seriesData, categoriesData] = await Promise.all([
        fetchApi(`/movies?limit=${pageSize}${commonParams}`).catch(() => ({ items: [], total: 0 })),
        fetchApi(`/series?limit=${pageSize}${commonParams}`).catch(() => ({ items: [], total: 0 })),
        fetchApi("/categories").catch(() => []),
      ]);

      const movieItems = (moviesData?.items || []).map((m: any) => ({ ...m, is_series: false }));
      const seriesItems = (seriesData?.items || []).map((s: any) => ({ ...s, is_series: true }));
      const combined = [...movieItems, ...seriesItems];

      if (searchParams.sort === "rating" || searchParams.sort === "imdb") {
        combined.sort((a, b) => Number(b.imdb_rating || b.rating || 0) - Number(a.imdb_rating || a.rating || 0));
      } else if (searchParams.sort === "year") {
        combined.sort((a, b) => Number(b.release_year || b.year || 0) - Number(a.release_year || a.year || 0));
      } else {
        combined.sort((a, b) => {
          const tA = a.created_at ? new Date(a.created_at).getTime() : 0;
          const tB = b.created_at ? new Date(b.created_at).getTime() : 0;
          if (tB !== tA) return tB - tA;
          return Number(b.id || 0) - Number(a.id || 0);
        });
      }

      movies = combined;
      total = (moviesData?.total || 0) + (seriesData?.total || 0);
      categories = Array.isArray(categoriesData) ? categoriesData : (categoriesData?.items || []);
    }
  } catch (error) {
    console.error("Failed to load catalog data:", error);
  }

  const selectedYear = searchParams.year;
  const selectedCategory = searchParams.category;
  const selectedGenre = searchParams.genre;
  const hasFilterActive = Boolean(
    selectedCategory ||
    selectedYear ||
    selectedGenre ||
    selectedType ||
    searchParams.search ||
    searchParams.sort
  );

  // Active filter label
  const activeCategoryName = categories.find((c) => String(c.id) === String(selectedCategory))?.name;
  const activeTypeName =
    isAll
      ? "Barcha filmlar va seriallar"
      : isDorama
      ? "Doramalar"
      : isAnime
      ? "Anime"
      : isCartoon
      ? "Multfilmlar"
      : isMovie
      ? "Kinolar"
      : isSeries
      ? "Seriallar"
      : DEFAULT_MEDIA_TYPES.find((t) => t.id === selectedType)?.name;
  const activeGenreName = DEFAULT_GENRES.find((g) => g.id === selectedGenre)?.name;

  return (
    <div className="min-h-screen pt-20 sm:pt-24 pb-28 xl:pb-16 px-4 md:px-8 bg-background-obsidian text-text-primary">
      <div className="max-w-container-max mx-auto space-y-6">
        
        {/* Header Bar */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-3 border-b border-white/10">
          <div className="flex items-center gap-3">
            <BackButton fallbackUrl="/" />
            <div>
              <h1 className="text-xl sm:text-2xl font-black text-text-primary font-headline-md tracking-tight flex items-center gap-2">
                <span className="material-symbols-outlined text-primary text-2xl">category</span>
                <span>Katalog</span>
              </h1>
              <p className="text-xs text-text-secondary mt-0.5">
                Kinolar, seriallar, doramalar, anime va multfilmlar bo&apos;limi.
              </p>
            </div>
          </div>

          <div className="w-full md:w-80">
            <LiveSearch placeholder="Katalogdan qidirish..." className="w-full" />
          </div>
        </div>

        {/* 1. UNIFIED COMPACT FILTRLAR BAR (Joylashuvi: Search va Bo'limlar oralig'ida) */}
        <section className="relative z-20 space-y-3">
          <Suspense fallback={<div className="h-14 w-full bg-white/5 animate-pulse rounded-2xl" />}>
            <UnifiedFilterBar
              categories={categories}
              genres={DEFAULT_GENRES}
              years={DEFAULT_YEARS}
              types={DEFAULT_MEDIA_TYPES}
              selectedCategory={selectedCategory}
              selectedGenre={selectedGenre}
              selectedYear={selectedYear}
              selectedType={selectedType}
              selectedSort={searchParams.sort}
              baseUrl="/catalog"
              totalItems={total}
            />
          </Suspense>
        </section>

        {/* 2. 6 TA ASOSIY KATALOG BO'LIMLARI (Faqat filtr faol bo'lmaganda ko'rinadi) */}
        {!hasFilterActive && (
          <section className="space-y-4 pt-2">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg sm:text-xl font-black text-white font-headline-md flex items-center gap-2">
                  <span className="w-1.5 h-5 bg-primary rounded-full block" />
                  <span>Katalog bo&apos;limlari</span>
                </h2>
                <p className="text-xs text-text-secondary mt-0.5">
                  O&apos;zingizga yoqqan yo&apos;nalishni tanlang: Top 100, kinolar, seriallar, doramalar, anime va multfilmlar.
                </p>
              </div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 sm:gap-4">
              {CATALOG_CATEGORIES.map((cat) => (
                <Link
                  key={cat.id}
                  href={cat.href}
                  className="group relative overflow-hidden rounded-2xl p-4 sm:p-5 flex flex-col justify-between border transition-all duration-300 min-h-[120px] sm:min-h-[140px] cursor-pointer bg-white/[0.03] hover:bg-white/[0.07] border-white/10 hover:border-primary/60 active:border-primary"
                >
                  {/* Subtle corner colored glow */}
                  <div
                    className={`absolute -right-6 -top-6 w-24 h-24 rounded-full bg-gradient-to-br ${cat.accent} blur-xl pointer-events-none opacity-60 group-hover:opacity-100 transition-opacity`}
                  />

                  {/* Top: Icon + Arrow */}
                  <div className="flex items-center justify-between mb-3 relative z-10">
                    <div
                      className={`w-10 h-10 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center transition-all ${cat.iconColor} group-hover:bg-primary/20 group-hover:text-primary group-hover:border-primary/30`}
                    >
                      <span className="material-symbols-outlined text-[22px]">
                        {cat.icon}
                      </span>
                    </div>

                    <span className="material-symbols-outlined text-sm text-white/30 group-hover:text-primary group-hover:translate-x-0.5 transition-all">
                      arrow_forward
                    </span>
                  </div>

                  {/* Bottom: Title & Subtitle */}
                  <div className="relative z-10">
                    <h3 className="font-black text-sm sm:text-base leading-tight transition-colors text-white group-hover:text-primary">
                      {cat.name}
                    </h3>
                    <p className="text-[11px] text-text-secondary mt-0.5 line-clamp-1">
                      {cat.subtitle}
                    </p>
                  </div>
                </Link>
              ))}
            </div>
          </section>
        )}

        {/* 3. KATALOG GRID NATIJALARI (Filtr tanlanganda darhol yuqoriga ko'tariladi) */}
        <div className="relative z-10 pt-2 border-t border-white/10">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base sm:text-lg font-bold text-text-primary font-headline-md flex items-center gap-2">
              <span className="w-1 h-5 bg-primary rounded-full block" />
              <span>
                {activeCategoryName
                  ? `${activeCategoryName} natijalari`
                  : activeTypeName
                  ? `${activeTypeName}`
                  : activeGenreName
                  ? `${activeGenreName} janridagi kontent`
                  : selectedYear
                  ? `${selectedYear} yili kontenti`
                  : searchParams.search
                  ? `"${searchParams.search}" bo'yicha qidiruv`
                  : "Barcha filmlar va seriallar"}
              </span>
            </h2>
            <span className="text-xs text-text-secondary">
              Topilgan kontent: <strong className="text-white font-semibold">{total}</strong> ta
            </span>
          </div>

          <CatalogGrid
            key={`catalog-${selectedType || 'all'}-${selectedCategory || 'all'}-${selectedGenre || 'all'}-${selectedYear || 'all'}-${searchParams.search || ''}-${searchParams.sort || ''}`}
            initialItems={movies}
            total={total}
            type={isSeries ? "series" : isMovie ? "movies" : "all"}
            categoryId={selectedCategory}
            genre={selectedGenre}
            year={selectedYear}
            search={searchParams.search}
            sort={searchParams.sort}
            emptyMessage="Ushbu mezon bo'yicha hozircha kontent topilmadi."
          />
        </div>

      </div>
    </div>
  );
}
