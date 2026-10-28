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
  title: "Doramalar - MediaPlus",
  description: "Eng sara Koreya va Osiyo seriallari to'liq katalogi.",
};

export default async function DoramasListPage({
  searchParams
}: {
  searchParams: { genre?: string; year?: string; search?: string }
}) {
  let doramas: CatalogItem[] = [];
  let total = 0;
  let categories: any[] = [];
  const pageSize = 36;

  try {
    let query = `/series?limit=${pageSize}&category_id=40`;
    if (searchParams.genre) {
      query += `&genre=${encodeURIComponent(searchParams.genre)}`;
    }
    if (searchParams.year) {
      query += `&year=${searchParams.year}`;
    }
    if (searchParams.search) {
      query += `&search=${encodeURIComponent(searchParams.search)}`;
    }

    const [seriesData, categoriesData] = await Promise.all([
      fetchApi(query).catch((e) => {
        console.error("fetch doramas failed:", e);
        return { items: [], total: 0 };
      }),
      fetchApi("/categories").catch(() => []),
    ]);

    doramas = (seriesData?.items || []).map((s: any) => ({ ...s, is_series: true }));
    total = seriesData?.total ?? doramas.length;
    categories = Array.isArray(categoriesData) ? categoriesData : (categoriesData?.items || []);
  } catch (err) {
    console.error("Failed to load doramas:", err);
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
                <span className="material-symbols-outlined text-rose-400 text-3xl">spa</span>
                <span>Doramalar</span>
              </h1>
              <p className="text-xs text-text-secondary mt-0.5">
                Koreya, Xitoy va Osiyo mamlakatlarining eng ommabop va sevimli seriallari.
              </p>
            </div>
          </div>

          <div className="w-full md:w-80">
            <LiveSearch placeholder="Doramalardan qidirish..." className="w-full" />
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
              baseUrl="/doramas"
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
                  ? `${activeGenreName} janridagi doramalar`
                  : selectedYear
                  ? `${selectedYear} yili doramalari`
                  : searchParams.search
                  ? `"${searchParams.search}" bo'yicha qidiruv`
                  : "Barcha doramalar"}
              </span>
            </h2>
            <span className="text-xs text-text-secondary">
              Topilgan doramalar: <strong className="text-white font-semibold">{total}</strong> ta
            </span>
          </div>

          <CatalogGrid
            initialItems={doramas}
            total={total}
            genre={selectedGenre}
            year={selectedYear}
            search={searchParams.search}
            emptyMessage="Ushbu mezon bo'yicha hozircha doramalar topilmadi."
          />
        </div>

      </div>
    </div>
  );
}
