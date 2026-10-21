import { fetchApi } from "@/lib/api";
import { Metadata } from "next";
import Link from "next/link";
import CatalogGrid from "@/components/catalog/CatalogGrid";
import { CatalogItem } from "@/lib/api/catalog";
import BackButton from "@/components/BackButton";
import LiveSearch from "@/components/LiveSearch";
import ThemedCollectionCard from "@/components/catalog/ThemedCollectionCard";
import { CURATED_CATALOG_THEMES } from "@/lib/catalogThemes";

export const revalidate = 60; // 60s ISR kesh

export const metadata: Metadata = {
  title: "Katalog va To'plamlar - MediaPlus",
  description: "Barcha kinolar, seriallar, janrlar, yillar va qiziqarli mavzuli to'plamlar to'liq katalogi.",
};

const GENRES = [
  { id: "action", name: "Jangari", icon: "swords" },
  { id: "comedy", name: "Komediya", icon: "sentiment_very_satisfied" },
  { id: "scifi", name: "Fantastika", icon: "rocket_launch" },
  { id: "thriller", name: "Triller", icon: "visibility" },
  { id: "drama", name: "Drama", icon: "theater_comedy" },
  { id: "horror", name: "Qo'rqinchli", icon: "skull" },
  { id: "romance", name: "Melodrama", icon: "favorite" },
  { id: "detective", name: "Detektiv", icon: "search" },
  { id: "animation", name: "Multfilm", icon: "animation" },
  { id: "history", name: "Tarixiy", icon: "history_edu" },
  { id: "adventure", name: "Sarguzasht", icon: "explore" },
  { id: "crime", name: "Jinoyat", icon: "local_police" },
  { id: "military", name: "Harbiy", icon: "shield" }
];

const YEARS = [2026, 2025, 2024, 2023, 2022, 2021, 2020, 2019, 2018, 2017, 2016, 2015];

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
                Bitta mavzu atrofida jamlangan to'plamlar, janrlar va filmlar
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

        {/* 2. BO'LIMLAR (TOIFALAR) TABS */}
        <div className="space-y-2 pt-2 border-t border-white/10">
          <div className="flex items-center justify-between text-xs font-bold text-text-secondary uppercase tracking-wider">
            <span>Bo'limlar (Toifalar)</span>
            <Link href="/collections" className="text-text-secondary hover:text-white lowercase font-semibold transition-colors">
              Kolleksiyalar &rarr;
            </Link>
          </div>
          <div className="flex items-center gap-2 overflow-x-auto pb-1 hide-scrollbar">
            <Link
              href="/catalog"
              className={`px-3.5 py-2 rounded-xl text-xs transition-all whitespace-nowrap ${
                !selectedCategory
                  ? "bg-white/15 text-white font-bold border border-white/20 shadow-sm"
                  : "bg-white/5 hover:bg-white/10 text-text-secondary hover:text-white border border-white/5 font-medium"
              }`}
            >
              Barcha Kinolar
            </Link>
            {categories.map((cat) => {
              const active = String(selectedCategory) === String(cat.id);
              return (
                <Link
                  key={cat.id}
                  href={`/catalog?category=${cat.id}${selectedYear ? `&year=${selectedYear}` : ""}`}
                  className={`px-3.5 py-2 rounded-xl text-xs transition-all whitespace-nowrap ${
                    active
                      ? "bg-white/15 text-white font-bold border border-white/20 shadow-sm"
                      : "bg-white/5 hover:bg-white/10 text-text-secondary hover:text-white border border-white/5 font-medium"
                  }`}
                >
                  {cat.name}
                </Link>
              );
            })}
          </div>
        </div>

        {/* 3. JANRLAR FILTER ROW */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs font-bold text-text-secondary uppercase tracking-wider">
            <span>Janrlar bo'yicha saralash</span>
            <span className="text-[11px] text-text-secondary font-normal lowercase">{GENRES.length} ta janr</span>
          </div>
          <div className="flex items-center gap-2 overflow-x-auto pb-1 hide-scrollbar">
            <Link
              href={`/catalog${selectedCategory ? `?category=${selectedCategory}` : ""}${selectedYear ? `&year=${selectedYear}` : ""}`}
              className={`px-3 py-1.5 rounded-lg text-xs transition-all whitespace-nowrap border ${
                !selectedGenre
                  ? "bg-white/15 text-white font-bold border-white/20 shadow-sm"
                  : "bg-white/5 border-white/10 text-text-secondary hover:text-white hover:border-white/20 font-medium"
              }`}
            >
              Barchasi
            </Link>
            {GENRES.map((g) => {
              const active = selectedGenre === g.id;
              return (
                <Link
                  key={g.id}
                  href={`/catalog?genre=${g.id}${selectedCategory ? `&category=${selectedCategory}` : ""}${selectedYear ? `&year=${selectedYear}` : ""}`}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs whitespace-nowrap border transition-all ${
                    active
                      ? "bg-white/15 text-white font-bold border-white/20 shadow-sm"
                      : "bg-white/5 border-white/10 text-text-secondary hover:text-white hover:border-white/20 font-medium"
                  }`}
                >
                  <span className="material-symbols-outlined text-[15px] opacity-80">{g.icon}</span>
                  <span>{g.name}</span>
                </Link>
              );
            })}
          </div>
        </div>

        {/* 4. YILLAR FILTER ROW */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs font-bold text-text-secondary uppercase tracking-wider">
            <span>Chiqarilgan yili</span>
            {selectedYear && (
              <Link
                href={`/catalog${selectedCategory ? `?category=${selectedCategory}` : ""}`}
                className="text-xs text-text-secondary hover:text-white lowercase font-semibold transition-colors"
              >
                Filtrni tozalash ({selectedYear} ✕)
              </Link>
            )}
          </div>
          <div className="flex items-center gap-2 overflow-x-auto pb-1 hide-scrollbar">
            <Link
              href={`/catalog${selectedCategory ? `?category=${selectedCategory}` : ""}${selectedGenre ? `&genre=${selectedGenre}` : ""}`}
              className={`px-3 py-1.5 rounded-lg text-xs whitespace-nowrap border transition-all ${
                !selectedYear
                  ? "bg-white/15 text-white font-bold border-white/20 shadow-sm"
                  : "bg-white/5 border-white/10 text-text-secondary hover:text-white hover:border-white/20 font-medium"
              }`}
            >
              Barcha yillar
            </Link>
            {YEARS.map((y) => {
              const active = String(selectedYear) === String(y);
              return (
                <Link
                  key={y}
                  href={`/catalog?year=${y}${selectedCategory ? `&category=${selectedCategory}` : ""}${selectedGenre ? `&genre=${selectedGenre}` : ""}`}
                  className={`px-3 py-1.5 rounded-lg text-xs whitespace-nowrap border transition-all ${
                    active
                      ? "bg-white/15 text-white font-bold border-white/20 shadow-sm"
                      : "bg-white/5 border-white/10 text-text-secondary hover:text-white hover:border-white/20 font-medium"
                  }`}
                >
                  {y}
                </Link>
              );
            })}
          </div>
        </div>

        {/* 5. KATALOG GRID NATIJALARI */}
        <div className="pt-4 border-t border-white/10">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base sm:text-lg font-bold text-text-primary font-headline-md flex items-center gap-2">
              <span className="w-1 h-5 bg-rating-gold rounded-full block" />
              <span>
                {selectedCategory
                  ? categories.find(c => String(c.id) === String(selectedCategory))?.name || "Bo'lim natijalari"
                  : selectedYear
                  ? `${selectedYear} yili filmlari`
                  : selectedGenre
                  ? `${GENRES.find(g => g.id === selectedGenre)?.name || "Tanlangan janr"} filmlari`
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
            emptyMessage="Ushbu mezon bo'yicha hozircha filmlar topilmadi."
          />
        </div>

      </div>
    </div>
  );
}
