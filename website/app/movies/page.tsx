import { fetchApi } from "@/lib/api";
import { Metadata } from "next";
import CategoryFilter from "@/components/CategoryFilter";
import CatalogTypeNav from "@/components/catalog/CatalogTypeNav";
import CatalogGrid from "@/components/catalog/CatalogGrid";
import { CatalogItem } from "@/lib/api/catalog";

export const dynamic = 'force-dynamic';

export const metadata: Metadata = {
  title: "Kinolar - MediaPlus",
  description: "Eng so'nggi va qiziqarli kinolarni tomosha qiling.",
};

type Category = {
  id: number;
  name: string;
};

export default async function MoviesListPage({ searchParams }: { searchParams: { category?: string } }) {
  let movies: CatalogItem[] = [];
  let total = 0;
  let categories: Category[] = [];
  let pages: any[] = [];
  const pageSize = 36;
  
  try {
    const query = searchParams.category 
      ? `/movies?limit=${pageSize}&category_id=${searchParams.category}` 
      : `/movies?limit=${pageSize}`;
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
    console.error("Failed to fetch movies, categories or pages:", error);
  }

  return (
    <div className="min-h-screen pt-32 pb-margin-desktop px-gutter bg-gradient-to-b from-primary-container/[0.10] via-background-obsidian to-background-obsidian">
      <div className="max-w-container-max mx-auto">
        
        {/* Header & Categories */}
        <div className="mb-stack-lg">
          <div className="mb-stack-md text-center md:text-left">
            <h1 className="font-display-hero text-display-hero-mobile md:text-[56px] font-black text-text-primary mb-2 tracking-tighter">
              Kinolar
            </h1>
            <p className="text-text-secondary font-body-lg text-body-lg">
              Bizning katta kinolar, seriallar va sara to&apos;plamlar kolleksiyamiz bilan tanishing.
            </p>
          </div>

          {/* Catalog Type Switcher (Kinolar / Seriallar / Anime / Dorama) */}
          <CatalogTypeNav currentType="movies" pages={pages} />

          {/* Category Filter */}
          <CategoryFilter categories={categories} currentCategory={searchParams.category} baseUrl="/movies" />
        </div>

        <CatalogGrid 
          key={`movies-${searchParams.category || 'all'}`}
          initialItems={movies}
          total={total}
          type="movies"
          categoryId={searchParams.category}
          pageSize={pageSize}
          emptyMessage="Hozircha kinolar mavjud emas."
        />
        
      </div>
    </div>
  );
}
