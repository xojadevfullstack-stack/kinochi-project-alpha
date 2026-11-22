import { fetchApi } from "@/lib/api";
import Link from "next/link";
import { Metadata } from "next";
import CatalogGrid from "@/components/catalog/CatalogGrid";
import { CatalogItem } from "@/lib/api/catalog";
import BackButton from "@/components/BackButton";
import UnifiedFilterBar from "@/components/catalog/UnifiedFilterBar";
import { DEFAULT_GENRES, DEFAULT_YEARS, DEFAULT_MEDIA_TYPES } from "@/lib/filterConstants";

export const revalidate = 60;

type Category = {
  id: number;
  name: string;
};

// Generate metadata based on category name
export async function generateMetadata({ params }: { params: { id: string } }): Promise<Metadata> {
  try {
    const categories: Category[] = await fetchApi("/categories");
    const category = categories.find(c => String(c.id) === params.id);
    if (category) {
      return {
        title: `${category.name} kinolar - MediaPlus`,
        description: `${category.name} janridagi eng sara kinolar to'plami.`,
      };
    }
  } catch (error) {
    console.error("Error fetching categories for metadata:", error);
  }
  
  return {
    title: "Kategoriya - MediaPlus",
    description: "MediaPlus - Kategoriya bo'yicha kinolar",
  };
}

export default async function CategoryPage({
  params,
  searchParams = {}
}: {
  params: { id: string };
  searchParams?: { genre?: string; year?: string; sort?: string; search?: string };
}) {
  let movies: CatalogItem[] = [];
  let total = 0;
  let categories: Category[] = [];
  let categoryName = "Kategoriya";
  const pageSize = 36;
  
  try {
    let query = `/movies?limit=${pageSize}&category_id=${params.id}`;
    if (searchParams.genre) {
      query += `&genre=${encodeURIComponent(searchParams.genre)}`;
    }
    if (searchParams.year) {
      query += `&year=${searchParams.year}`;
    }
    if (searchParams.search) {
      query += `&search=${encodeURIComponent(searchParams.search)}`;
    }
    if (searchParams.sort) {
      query += `&sort=${encodeURIComponent(searchParams.sort)}`;
    }

    const [moviesData, categoriesData] = await Promise.all([
      fetchApi(query),
      fetchApi("/categories")
    ]);
    movies = (moviesData?.items || []).map((m: any) => ({ ...m, is_series: false }));
    total = moviesData?.total ?? movies.length;
    categories = categoriesData || [];
    
    const category = categories.find(c => String(c.id) === params.id);
    if (category) {
      categoryName = category.name;
    }
  } catch (error) {
    console.error("Failed to fetch data for category:", error);
  }

  return (
    <div className="min-h-screen pt-32 pb-margin-desktop px-gutter bg-gradient-to-b from-primary-container/[0.10] via-background-obsidian to-background-obsidian">
      <div className="max-w-container-max mx-auto">
        
        {/* Smart Back Navigation */}
        <div className="mb-4 sm:mb-6">
          <BackButton fallbackUrl="/movies" />
        </div>

        {/* Header & Categories */}
        <div className="mb-stack-lg">
          <div className="mb-stack-md">
            <h1 className="font-display-hero text-display-hero-mobile md:text-[56px] font-black text-text-primary mb-2 tracking-tighter">
              {categoryName}
            </h1>
            <p className="text-text-secondary font-body-lg text-body-lg">Bizning katta kino kolleksiyamiz bilan tanishing.</p>
          </div>
          
          {/* Unified Filter Bar */}
          <div className="pt-2">
            <UnifiedFilterBar
              categories={categories}
              genres={DEFAULT_GENRES}
              years={DEFAULT_YEARS}
              types={DEFAULT_MEDIA_TYPES}
              selectedCategory={params.id}
              selectedGenre={searchParams.genre}
              selectedYear={searchParams.year}
              selectedSort={searchParams.sort}
              baseUrl={`/category/${params.id}`}
              totalItems={total}
            />
          </div>
        </div>

        <CatalogGrid 
          key={`category-${params.id}-${searchParams.genre || 'all'}-${searchParams.year || 'all'}-${searchParams.sort || 'all'}`}
          initialItems={movies}
          total={total}
          type="movies"
          categoryId={params.id}
          genre={searchParams.genre}
          year={searchParams.year}
          sort={searchParams.sort}
          pageSize={pageSize}
          emptyMessage="Ushbu kategoriyada hozircha kinolar mavjud emas."
        />
        
      </div>
    </div>
  );
}
