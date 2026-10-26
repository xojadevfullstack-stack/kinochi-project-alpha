import { fetchApi } from "@/lib/api";
import { Metadata } from "next";
import Link from "next/link";
import CatalogGrid from "@/components/catalog/CatalogGrid";
import { CatalogItem } from "@/lib/api/catalog";
import BackButton from "@/components/BackButton";
import LiveSearch from "@/components/LiveSearch";
import ThemedCollectionCard from "@/components/catalog/ThemedCollectionCard";
import UnifiedFilterBar, { DEFAULT_GENRES, DEFAULT_YEARS } from "@/components/catalog/UnifiedFilterBar";
import { CURATED_CATALOG_THEMES } from "@/lib/catalogThemes";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Katalog va To'plamlar - MediaPlus",
  description: "Barcha kinolar, seriallar, janrlar, yillar va qiziqarli mavzuli to'plamlar to'liq katalogi.",
};

export default async function FullCatalogPage({
  searchParams
}: {
  searchParams: { category?: string; year?: string; genre?: string; sort?: string; search?: string }
}) {
  let movies: CatalogItem[] = [];
  let total = 0;
  let categories: any[] = [];
  let pages: any[] = [];
  const pageSize = 36;

  try {
    let query = `/movies?limit=${pageSize}&exclude_paged=true`;
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

    const [moviesData, categoriesData, pagesData] = await Promise.all([
      fetchApi(query),
      fetchApi("/categories"),
      fetchApi("/pages/")
    ]);

    movies = (moviesData?.items || []).map((m: any) => ({ ...m, is_series: false }));
    total = moviesData?.total ?? movies.length;
    categories = categoriesData || [];
    pages = pagesData?.items || pagesData || [];
  } catch (error) {
    console.error("Failed to load catalog data:", error);
  }

  const selectedYear = searchParams.year;
  const selectedCategory = searchParams.category;
  const selectedGenre = searchParams.genre;
  const hasFilterActive = Boolean(selectedCategory || selectedYear || selectedGenre || searchParams.search);

  // Active filter label
  const activeCategoryName = categories.find((c) => String(c.id) === String(selectedCategory))?.name;
  const activeGenreName = DEFAULT_GENRES.find((g) => g.id === selectedGenre)?.name;

  return (
    <div className="min-h-screen pt-20 sm:pt-24 pb-28 xl:pb-16 px-4 md:px-8 bg-background-obsidian text-text-primary">
      <div className="max-w-container-max mx-auto space-y-8">
        
        {/* Header Bar */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-white/10">
          <div className="flex items-center gap-3">
            <BackButton />
            <div>
              <h1 className="text-xl sm:text-2xl font-black text-text-primary font-headline-md tracking-tight">
                Kino Katalogi va Mavzular
              </h1>
              <p className="text-xs text-text-secondary mt-0.5">
                Barcha janrlar, yillar, mavzuli to'plamlar va saralangan kinolar.
              </p>
            </div>
          </div>

          <div className="w-full md:w-80">
            <LiveSearch placeholder="Katalogdan qidirish..." className="w-full" />
          </div>
        </div>

        {/* 1. ASILMEDIA USLUBIDAGI QIZIQARLI MAVZULAR VA TO'PLAMLAR (Fanned 3-Poster Deck Grid) */}
        {!hasFilterActive && (
          <section className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg sm:text-xl font-black text-white font-headline-md flex items-center gap-2">
                  <span className="w-1.5 h-5 bg-rating-gold rounded-full block" />
                  <span>Qiziqarli mavzular</span>
                </h2>
                <p className="text-xs text-text-secondary mt-0.5">
                  Bitta mavzu atrofida jamlangan kinolar: o'zga sayyoraliklardan tortib qadimgi qahramonlargacha.
                </p>
              </div>

              <Link
                href="/collections"
                className="text-xs text-text-secondary hover:text-white font-semibold transition-colors flex items-center gap-1"
              >
                <span>Barcha to'plamlar</span>
                <span className="material-symbols-outlined text-sm">arrow_forward</span>
              </Link>
            </div>

            {/* Asilmedia Fanned 3-Poster Cards Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 sm:gap-6">
              {CURATED_CATALOG_THEMES.map((theme) => (
                <ThemedCollectionCard
                  key={theme.id}
                  title={theme.title}
                  count={theme.count}
                  href={theme.href}
                  posters={theme.posters}
                  description={theme.description}
                />
              ))}
            </div>
          </section>
        )}

        {/* 2. UNIFIED COMPACT FILTRLAR BAR (Combines Toifalar, Janrlar, Yillar into 1 expandable panel) */}
        <section className="space-y-3 pt-2">
          <UnifiedFilterBar
            categories={categories}
            genres={DEFAULT_GENRES}
            years={DEFAULT_YEARS}
            selectedCategory={selectedCategory}
            selectedGenre={selectedGenre}
            selectedYear={selectedYear}
            baseUrl="/catalog"
            totalItems={total}
          />
        </section>

        {/* 3. KATALOG GRID NATIJALARI */}
        <div className="pt-4 border-t border-white/10">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base sm:text-lg font-bold text-text-primary font-headline-md flex items-center gap-2">
              <span className="w-1 h-5 bg-rating-gold rounded-full block" />
              <span>
                {activeCategoryName
                  ? `${activeCategoryName} natijalari`
                  : activeGenreName
                  ? `${activeGenreName} janridagi filmlar`
                  : selectedYear
                  ? `${selectedYear} yili filmlari`
                  : searchParams.search
                  ? `"${searchParams.search}" bo'yicha qidiruv`
                  : "Barcha filmlar va seriallar"}
              </span>
            </h2>
            <span className="text-xs text-text-secondary">
              Topilgan kinolar: <strong className="text-white font-semibold">{total}</strong> ta
            </span>
          </div>

          <CatalogGrid
            initialItems={movies}
            total={total}
            categoryId={selectedCategory}
            genre={selectedGenre}
            year={selectedYear}
            search={searchParams.search}
            emptyMessage="Ushbu mezon bo'yicha hozircha filmlar topilmadi."
          />
        </div>

      </div>
    </div>
  );
}
