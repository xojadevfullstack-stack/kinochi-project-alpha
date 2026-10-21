import { fetchApi } from "@/lib/api";
import { Metadata } from "next";
import Link from "next/link";
import CatalogGrid from "@/components/catalog/CatalogGrid";
import { CatalogItem } from "@/lib/api/catalog";
import BackButton from "@/components/BackButton";
import LiveSearch from "@/components/LiveSearch";

export const revalidate = 60; // 60s ISR kesh

export const metadata: Metadata = {
  title: "Katalog - MediaPlus",
  description: "Barcha kinolar, seriallar, janrlar, yillar va to'plamlar to'liq katalogi.",
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
  searchParams: { category?: string; year?: string; genre?: string; sort?: string }
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

  return (
    <div className="min-h-screen pt-24 pb-28 xl:pb-16 px-4 md:px-8 bg-background-obsidian text-text-primary">
      <div className="max-w-container-max mx-auto space-y-6">
        
        {/* Header & Back Nav */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-white/10">
          <div className="flex items-center gap-3">
            <BackButton />
            <div>
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 rounded bg-primary-container text-white text-[10px] font-black uppercase">
                  Markazlashgan
                </span>
                <h1 className="text-xl sm:text-2xl font-black text-text-primary font-headline-md tracking-tight">
                  Kino Katalogi va Bo'limlar
                </h1>
              </div>
              <p className="text-xs text-text-secondary mt-0.5">
                Barcha toifalar, janrlar, yillar, kolleksiyalar va aktyorlar saralangan to'liq sahifa
              </p>
            </div>
          </div>

          <div className="w-full md:w-72">
            <LiveSearch placeholder="Katalogdan qidirish..." className="w-full" />
          </div>
        </div>

        {/* 1. ASOSIY BO'LIMLAR TABS */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs font-bold text-text-secondary uppercase tracking-wider">
            <span>Bo'limlar (Toifalar)</span>
            <Link href="/collections" className="text-primary-container hover:underline lowercase font-semibold">
              Kolleksiyalar &rarr;
            </Link>
          </div>
          <div className="flex items-center gap-2 overflow-x-auto pb-1 hide-scrollbar">
            <Link
              href="/catalog"
              className={`px-3.5 py-2 rounded-xl text-xs font-bold transition whitespace-nowrap ${
                !selectedCategory
                  ? "bg-primary-container text-white shadow-md shadow-black/40"
                  : "bg-surface-container hover:bg-surface-container-high text-text-secondary border border-white/5"
              }`}
            >
              Barcha Kinolar
            </Link>
            <Link
              href="/series"
              className="px-3.5 py-2 rounded-xl text-xs font-bold bg-surface-container hover:bg-surface-container-high text-text-secondary border border-white/5 transition whitespace-nowrap"
            >
              Seriallar
            </Link>
            {categories.map((cat) => (
              <Link
                key={cat.id}
                href={`/catalog?category=${cat.id}`}
                className={`px-3.5 py-2 rounded-xl text-xs font-bold transition whitespace-nowrap ${
                  selectedCategory === String(cat.id)
                    ? "bg-primary-container text-white shadow-md shadow-black/40"
                    : "bg-surface-container hover:bg-surface-container-high text-text-secondary border border-white/5"
                }`}
              >
                {cat.name}
              </Link>
            ))}
            {pages.map((p) => (
              <Link
                key={p.id}
                href={`/p/${p.slug}`}
                className="px-3.5 py-2 rounded-xl text-xs font-bold bg-surface-container hover:bg-surface-container-high text-text-secondary border border-white/5 transition whitespace-nowrap"
              >
                {p.title}
              </Link>
            ))}
            {/* Aktyorlar Bo'lim ichida */}
            <Link
              href="/catalog?tab=actors"
              className="px-3.5 py-2 rounded-xl text-xs font-bold bg-surface-container hover:bg-surface-container-high text-rating-gold border border-rating-gold/30 transition whitespace-nowrap flex items-center gap-1.5"
            >
              <span className="material-symbols-outlined text-sm">groups</span>
              Aktyorlar
            </Link>
          </div>
        </div>

        {/* 2. JANRLAR FILTRI (Bosh sahifadan bu yerga ko'chirilgan) */}
        <div className="bg-surface-container border border-white/10 rounded-2xl p-4 sm:p-5 space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-xs font-bold text-text-primary uppercase tracking-wider flex items-center gap-1.5">
              <span className="material-symbols-outlined text-base text-primary-container">theater_comedy</span>
              Janrlar bo'yicha saralash
            </h2>
            <span className="text-[11px] text-text-secondary">{GENRES.length} ta janr</span>
          </div>
          <div className="flex flex-wrap gap-2">
            <Link
              href="/catalog"
              className="px-3 py-1.5 rounded-lg bg-primary-container text-white text-xs font-bold shadow"
            >
              Barchasi
            </Link>
            {GENRES.map((g) => (
              <Link
                key={g.id}
                href={`/catalog?genre=${g.id}`}
                className="px-3 py-1.5 rounded-lg bg-surface-container-high hover:bg-white/10 text-text-secondary hover:text-white text-xs border border-white/5 transition flex items-center gap-1.5"
              >
                <span className="material-symbols-outlined text-sm text-text-secondary">{g.icon}</span>
                <span>{g.name}</span>
              </Link>
            ))}
          </div>
        </div>

        {/* 3. YILLAR FILTRI (Bosh sahifadan bu yerga ko'chirilgan) */}
        <div className="bg-surface-container border border-white/10 rounded-2xl p-4 sm:p-5 space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-xs font-bold text-text-primary uppercase tracking-wider flex items-center gap-1.5">
              <span className="material-symbols-outlined text-base text-primary-container">calendar_month</span>
              Yillar bo'yicha saralash
            </h2>
            {selectedYear && (
              <Link href="/catalog" className="text-[11px] text-primary-container hover:underline">
                Yil filtrini tozalash ✕
              </Link>
            )}
          </div>
          <div className="flex items-center gap-2 overflow-x-auto pb-1 text-xs hide-scrollbar">
            <Link
              href="/catalog"
              className={`px-3 py-1.5 rounded-lg font-bold transition whitespace-nowrap ${
                !selectedYear ? "bg-primary-container text-white shadow" : "bg-surface-container-high text-text-secondary border border-white/5 hover:text-white"
              }`}
            >
              Barcha yillar
            </Link>
            {YEARS.map((y) => (
              <Link
                key={y}
                href={`/catalog?year=${y}${selectedCategory ? `&category=${selectedCategory}` : ""}`}
                className={`px-3 py-1.5 rounded-lg font-bold transition whitespace-nowrap ${
                  selectedYear === String(y)
                    ? "bg-primary-container text-white shadow"
                    : "bg-surface-container-high text-text-secondary border border-white/5 hover:text-white hover:bg-white/10"
                }`}
              >
                {y}
              </Link>
            ))}
          </div>
        </div>

        {/* 4. KATALOG NATIJALARI (GRID) */}
        <div className="space-y-4 pt-2">
          <div className="flex items-center justify-between text-xs text-text-secondary">
            <span>
              Topilgan kinolar: <b className="text-white">{total} ta</b>
            </span>
            <div className="flex items-center gap-2">
              <span>Saralash:</span>
              <span className="font-bold text-white bg-surface-container px-2.5 py-1 rounded-lg border border-white/5">
                Eng yangilari
              </span>
            </div>
          </div>

          <CatalogGrid 
            initialItems={movies} 
            total={total} 
            type="movies" 
            categoryId={selectedCategory} 
          />
        </div>

      </div>
    </div>
  );
}
