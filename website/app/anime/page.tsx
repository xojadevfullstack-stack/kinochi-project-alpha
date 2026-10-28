import { Suspense } from "react";
import { fetchApi } from "@/lib/api";
import { Metadata } from "next";
import CatalogGrid from "@/components/catalog/CatalogGrid";
import { CatalogItem } from "@/lib/api/catalog";
import BackButton from "@/components/BackButton";
import LiveSearch from "@/components/LiveSearch";
import UnifiedFilterBar from "@/components/catalog/UnifiedFilterBar";
import { DEFAULT_GENRES, DEFAULT_YEARS, DEFAULT_MEDIA_TYPES } from "@/lib/filterConstants";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Anime - MediaPlus",
  description: "Eng sara yapon animatsiyasi, anime seriallari va filmlari katalogi.",
};

export default async function AnimeListPage({
  searchParams
}: {
  searchParams: { genre?: string; year?: string; search?: string }
}) {
  let animes: CatalogItem[] = [];
  let total = 0;
  let categories: any[] = [];
  const pageSize = 36;

  try {
    const genreParam = searchParams.genre ? `&genre=${encodeURIComponent(searchParams.genre)}` : "";
    const yearParam = searchParams.year ? `&year=${searchParams.year}` : "";
    const searchParam = searchParams.search ? `&search=${encodeURIComponent(searchParams.search)}` : "";

    const [seriesData, moviesData, categoriesData] = await Promise.all([
      fetchApi(`/series?limit=${pageSize}&category_id=2${genreParam}${yearParam}${searchParam}`).catch(() => ({ items: [], total: 0 })),
      fetchApi(`/movies?limit=12&category_id=2${genreParam}${yearParam}${searchParam}`).catch(() => ({ items: [], total: 0 })),
      fetchApi("/categories").catch(() => []),
    ]);

    const sItems = (seriesData?.items || []).map((s: any) => ({ ...s, is_series: true }));
    const mItems = (moviesData?.items || []).map((m: any) => ({ ...m, is_series: false }));

    animes = [...sItems, ...mItems];
    total = (seriesData?.total || 0) + (moviesData?.total || 0);
    categories = Array.isArray(categoriesData) ? categoriesData : (categoriesData?.items || []);
  } catch (err) {
    console.error("Failed to load anime:", err);
  }

  const selectedYear = searchParams.year;
  const selectedGenre = searchParams.genre;
  const activeGenreName = DEFAULT_GENRES.find((g) => g.id === selectedGenre)?.name;

  return (
    <div className="min-h-screen pt-24 sm:pt-28 pb-28 xl:pb-16 px-4 md:px-8 bg-background-obsidian text-text-primary">
      <div className="max-w-container-max mx-auto space-y-6">
        
        {/* Header Bar */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-white/10">
          <div className="flex items-center gap-3">
            <BackButton fallbackUrl="/catalog" />
            <div>
              <h1 className="text-2xl sm:text-3xl font-black text-text-primary font-headline-md tracking-tight flex items-center gap-2">
                <span className="material-symbols-outlined text-violet-400 text-3xl">auto_awesome</span>
                <span>Anime</span>
              </h1>
              <p className="text-xs text-text-secondary mt-0.5">
                Mashhur yapon anime seriallari va to&apos;liq metrajli animatsion filmlari.
              </p>
            </div>
          </div>

          <div className="w-full md:w-80">
            <LiveSearch placeholder="Animedan qidirish..." className="w-full" />
          </div>
        </div>

        {/* Filter Bar */}
        <section className="relative z-20 space-y-3">
          <Suspense fallback={<div className="h-14 w-full bg-white/5 animate-pulse rounded-2xl" />}>
            <UnifiedFilterBar
              categories={categories}
              genres={DEFAULT_GENRES}
              years={DEFAULT_YEARS}
              types={DEFAULT_MEDIA_TYPES}
              selectedGenre={selectedGenre}
              selectedYear={selectedYear}
              baseUrl="/anime"
              totalItems={total}
            />
          </Suspense>
        </section>

        {/* Results Header & Grid */}
        <div className="relative z-10 pt-2">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base sm:text-lg font-bold text-text-primary font-headline-md flex items-center gap-2">
              <span className="w-1 h-5 bg-primary rounded-full block" />
              <span>
                {activeGenreName
                  ? `${activeGenreName} janridagi animelar`
                  : selectedYear
                  ? `${selectedYear} yili animelari`
                  : searchParams.search
                  ? `"${searchParams.search}" bo'yicha qidiruv`
                  : "Barcha animelar"}
              </span>
            </h2>
            <span className="text-xs text-text-secondary">
              Topilgan animelar: <strong className="text-white font-semibold">{total}</strong> ta
            </span>
          </div>

          <CatalogGrid
            initialItems={animes}
            total={total}
            genre={selectedGenre}
            year={selectedYear}
            search={searchParams.search}
            emptyMessage="Ushbu mezon bo'yicha hozircha animelar topilmadi."
          />
        </div>

      </div>
    </div>
  );
}
