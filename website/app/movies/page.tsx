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
  title: "Kinolar - MediaPlus",
  description: "Eng so'nggi va sara kinolarni tomosha qiling va saralang.",
};

type Category = {
  id: number;
  name: string;
};

export default async function MoviesListPage({
  searchParams
}: {
  searchParams: { category?: string; genre?: string; year?: string; search?: string; type?: string; page_id?: string }
}) {
  let movies: CatalogItem[] = [];
  let total = 0;
  let categories: Category[] = [];
  let pages: any[] = [];
  const pageSize = 36;
  
  try {
    let query = `/movies?limit=${pageSize}`;
    if (searchParams.page_id) {
      query += `&page_id=${searchParams.page_id}`;
    }
    if (searchParams.category) {
      query += `&category_id=${searchParams.category}`;
    } else if (searchParams.type === "anime") {
      query += `&category_id=2`;
    } else if (searchParams.type === "cartoon" || searchParams.type === "animation") {
      query += `&category_id=22`;
    }

    if (searchParams.genre) {
      query += `&genre=${encodeURIComponent(searchParams.genre)}`;
    } else {
      if (searchParams.type === "anime" && searchParams.category) {
        query += `&genre=anime`;
      } else if ((searchParams.type === "cartoon" || searchParams.type === "animation") && searchParams.category) {
        query += `&genre=animatsiya`;
      }
    }
    if (searchParams.year) {
      query += `&year=${searchParams.year}`;
    }
    if (searchParams.search) {
      query += `&search=${encodeURIComponent(searchParams.search)}`;
    }

    const [moviesData, categoriesData, pagesData] = await Promise.all([
      fetchApi(query).catch((e) => {
        console.error("fetch movies failed:", e);
        return { items: [], total: 0 };
      }),
      fetchApi("/categories").catch((e) => {
        console.error("fetch categories failed:", e);
        return [];
      }),
      fetchApi("/pages").catch((e) => {
        console.error("fetch pages failed:", e);
        return { items: [], total: 0 };
      })
    ]);
    movies = (moviesData?.items || []).map((m: any) => ({ ...m, is_series: false }));
    total = moviesData?.total ?? movies.length;
    categories = Array.isArray(categoriesData) ? categoriesData : (categoriesData?.items || []);
    pages = pagesData?.items || pagesData || [];
  } catch (error) {
    console.error("Failed to fetch movies, categories or pages:", error);
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
            <BackButton fallbackUrl="/" />
            <div>
              <h1 className="text-2xl sm:text-3xl font-black text-text-primary font-headline-md tracking-tight">
                Kinolar
              </h1>
              <p className="text-xs text-text-secondary mt-0.5">
                Bizning katta kinolar, seriallar va sara to&apos;plamlar kolleksiyamiz bilan tanishing.
              </p>
            </div>
          </div>

          <div className="w-full md:w-80">
            <LiveSearch placeholder="Kinolardan qidirish..." className="w-full" />
          </div>
        </div>

        {/* Unified Compact Filtrlar Bar (Bo'limlar, Turi, Janrlar, Yillar) */}
        <section className="space-y-3">
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
              baseUrl="/movies"
              totalItems={total}
            />
          </Suspense>
        </section>

        {/* Results Header & Grid */}
        <div className="pt-2">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base sm:text-lg font-bold text-text-primary font-headline-md flex items-center gap-2">
              <span className="w-1 h-5 bg-primary-container rounded-full block" />
              <span>
                {activeCategoryName
                  ? `${activeCategoryName} natijalari`
                  : activeTypeName
                  ? `${activeTypeName}`
                  : activeGenreName
                  ? `${activeGenreName} janridagi filmlar`
                  : selectedYear
                  ? `${selectedYear} yili filmlari`
                  : searchParams.search
                  ? `"${searchParams.search}" bo'yicha qidiruv`
                  : "Barcha kinolar"}
              </span>
            </h2>
            <span className="text-xs text-text-secondary">
              Topilgan kinolar: <strong className="text-white font-semibold">{total}</strong> ta
            </span>
          </div>

          <CatalogGrid 
            key={`movies-${selectedCategory || 'all'}-${selectedGenre || 'all'}-${selectedYear || 'all'}-${searchParams.search || ''}`}
            initialItems={movies}
            total={total}
            type="movies"
            categoryId={selectedCategory}
            genre={selectedGenre}
            year={selectedYear}
            search={searchParams.search}
            pageSize={pageSize}
            emptyMessage="Ushbu mezon bo'yicha hozircha kinolar topilmadi."
          />
        </div>
        
      </div>
    </div>
  );
}
