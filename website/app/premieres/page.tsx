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
  title: "Premyeralar - MediaPlus",
  description: "Eng so'nggi va sara premyeralarni tomosha qiling va saralang.",
};

type Category = {
  id: number;
  name: string;
};

export default async function PremieresPage({
  searchParams,
}: {
  searchParams: {
    category?: string;
    genre?: string;
    year?: string;
    search?: string;
    type?: string;
    page_id?: string;
  };
}) {
  let items: CatalogItem[] = [];
  let total = 0;
  let categories: Category[] = [];
  const pageSize = 36;

  try {
    const isSeriesSearch = searchParams.type === "series";
    const endpoint = isSeriesSearch ? "/series" : "/movies";
    let query = `${endpoint}?limit=${pageSize}`;

    if (searchParams.category) {
      query += `&category_id=${searchParams.category}`;
    }
    if (searchParams.genre) {
      query += `&genre=${encodeURIComponent(searchParams.genre)}`;
    }
    if (searchParams.year) {
      query += `&year=${searchParams.year}`;
    }
    if (searchParams.search) {
      query += `&search=${encodeURIComponent(searchParams.search)}`;
    }

    const [contentData, categoriesData] = await Promise.all([
      fetchApi(query).catch((e) => {
        console.error("fetch premieres failed:", e);
        return { items: [], total: 0 };
      }),
      fetchApi("/categories").catch((e) => {
        console.error("fetch categories failed:", e);
        return [];
      }),
    ]);

    const rawItems = contentData?.items || [];
    items = rawItems.map((m: any) => ({
      ...m,
      is_series: isSeriesSearch || !!m.is_series,
    }));
    total = contentData?.total ?? items.length;
    categories = Array.isArray(categoriesData) ? categoriesData : categoriesData?.items || [];
  } catch (error) {
    console.error("Failed to load premieres:", error);
  }

  const selectedYear = searchParams.year;
  const selectedCategory = searchParams.category;
  const selectedGenre = searchParams.genre;
  const selectedType = searchParams.type;

  const activeCategoryName = categories.find((c) => String(c.id) === String(selectedCategory))?.name;
  const activeTypeName = DEFAULT_MEDIA_TYPES.find((t) => t.id === selectedType)?.name;
  const activeGenreName = DEFAULT_GENRES.find((g) => g.id === selectedGenre)?.name;

  return (
    <div className="min-h-screen pt-24 sm:pt-28 pb-28 xl:pb-16 px-4 md:px-8 bg-gradient-to-b from-primary-container/[0.10] via-background-obsidian to-background-obsidian text-text-primary">
      <div className="max-w-container-max mx-auto space-y-6">
        {/* Smart Back Navigation & Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-white/10">
          <div className="flex items-center gap-3">
            <BackButton />
            <div>
              <h1 className="text-xl sm:text-2xl md:text-3xl font-black text-white font-headline-md tracking-tight flex items-center gap-2">
                <span>Premyeralar</span>
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              </h1>
              <p className="text-xs sm:text-sm text-text-secondary mt-0.5">
                Eng so&apos;nggi premyera qilingan filmlar va yangi fasllar.
              </p>
            </div>
          </div>

          <div className="w-full md:w-80">
            <LiveSearch placeholder="Premyeralardan qidirish..." className="w-full" />
          </div>
        </div>

        {/* Unified Filter Bar */}
        <section className="relative z-40 space-y-3 pt-1">
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
              baseUrl="/premieres"
              totalItems={total}
            />
          </Suspense>
        </section>

        {/* Premieres Results Section */}
        <div className="relative z-10 pt-4 border-t border-white/10">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base sm:text-lg font-bold text-text-primary font-headline-md flex items-center gap-2">
              <span className="w-1 h-5 bg-primary-container rounded-full block" />
              <span>
                {activeCategoryName
                  ? `${activeCategoryName} premyeralari`
                  : activeTypeName
                  ? `${activeTypeName} premyeralari`
                  : activeGenreName
                  ? `${activeGenreName} janridagi premyeralar`
                  : selectedYear
                  ? `${selectedYear} yili premyeralari`
                  : searchParams.search
                  ? `"${searchParams.search}" bo'yicha qidiruv`
                  : "Barcha yangi premyeralar"}
              </span>
            </h2>
            <span className="text-xs text-text-secondary">
              Topilgan premyeralar: <b className="text-white">{total} ta</b>
            </span>
          </div>

          <CatalogGrid
            initialItems={items}
            total={total}
            type="movies"
            year={selectedYear}
            genre={selectedGenre}
            categoryId={selectedCategory}
            search={searchParams.search}
            emptyMessage="Premyeralar hozircha mavjud emas"
          />
        </div>
      </div>
    </div>
  );
}
