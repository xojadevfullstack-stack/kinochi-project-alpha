import { fetchApi } from "@/lib/api";
import { Metadata } from "next";
import { notFound } from "next/navigation";
import UnifiedFilterBar from "@/components/catalog/UnifiedFilterBar";
import CatalogGrid from "@/components/catalog/CatalogGrid";
import { CatalogItem } from "@/lib/api/catalog";
import BackButton from "@/components/BackButton";
import { DEFAULT_GENRES, DEFAULT_YEARS, DEFAULT_MEDIA_TYPES } from "@/lib/filterConstants";

type Category = {
  id: number;
  name: string;
};

export async function generateMetadata({ params }: { params: { slug: string } }): Promise<Metadata> {
  try {
    const page = await fetchApi(`/pages/${params.slug}`);
    return {
      title: `${page.title} - MediaPlus`,
      description: `${page.title} turidagi barcha kino va seriallar.`,
    };
  } catch (error) {
    return {
      title: "Sahifa - MediaPlus",
    };
  }
}

export default async function DynamicPage({
  params,
  searchParams = {}
}: {
  params: { slug: string };
  searchParams?: { category?: string; genre?: string; year?: string; sort?: string; search?: string };
}) {
  let page = null;
  let combinedItems: CatalogItem[] = [];
  let total = 0;
  let categories: Category[] = [];
  let allPages: any[] = [];
  const pageSize = 36;
  
  try {
    const [pageRes, allPagesRes] = await Promise.all([
      fetchApi(`/pages/${params.slug}`),
      fetchApi("/pages/")
    ]);
    page = pageRes;
    allPages = allPagesRes?.items || allPagesRes || [];

    if (page && page.id) {
      let moviesQuery = `/movies?limit=${pageSize}&page_id=${page.id}`;
      let seriesQuery = `/series?limit=${pageSize}&page_id=${page.id}`;
      
      if (searchParams.category) {
        moviesQuery += `&category_id=${searchParams.category}`;
        seriesQuery += `&category_id=${searchParams.category}`;
      }
      if (searchParams.genre) {
        moviesQuery += `&genre=${encodeURIComponent(searchParams.genre)}`;
        seriesQuery += `&genre=${encodeURIComponent(searchParams.genre)}`;
      }
      if (searchParams.year) {
        moviesQuery += `&year=${searchParams.year}`;
        seriesQuery += `&year=${searchParams.year}`;
      }
      if (searchParams.search) {
        moviesQuery += `&search=${encodeURIComponent(searchParams.search)}`;
        seriesQuery += `&search=${encodeURIComponent(searchParams.search)}`;
      }
      if (searchParams.sort) {
        moviesQuery += `&sort=${encodeURIComponent(searchParams.sort)}`;
        seriesQuery += `&sort=${encodeURIComponent(searchParams.sort)}`;
      }

      const [moviesData, seriesData, categoriesData] = await Promise.all([
        fetchApi(moviesQuery).catch(() => ({ items: [], total: 0 })),
        fetchApi(seriesQuery).catch(() => ({ items: [], total: 0 })),
        fetchApi('/categories').catch(() => [])
      ]);
      const movies: CatalogItem[] = (moviesData?.items || []).map((m: any) => ({ ...m, is_series: false }));
      const seriesList: CatalogItem[] = (seriesData?.items || []).map((s: any) => ({ ...s, is_series: true }));
      const unsorted = [...movies, ...seriesList];
      if (searchParams.sort === "rating" || searchParams.sort === "imdb") {
        combinedItems = unsorted.sort((a, b) => {
          const rA = Number(a.imdb_rating ?? 0);
          const rB = Number(b.imdb_rating ?? 0);
          if (rB !== rA) return rB - rA;
          const yA = Number(a.release_year ?? 0);
          const yB = Number(b.release_year ?? 0);
          if (yB !== yA) return yB - yA;
          return Number(b.id || 0) - Number(a.id || 0);
        });
      } else if (searchParams.sort === "latest") {
        combinedItems = unsorted.sort((a, b) => {
          const tA = new Date(a.updated_at || a.created_at || 0).getTime();
          const tB = new Date(b.updated_at || b.created_at || 0).getTime();
          if (tB !== tA) return tB - tA;
          return Number(b.id || 0) - Number(a.id || 0);
        });
      } else {
        combinedItems = unsorted.sort((a, b) => {
          const tA = new Date(a.updated_at || a.created_at || 0).getTime();
          const tB = new Date(b.updated_at || b.created_at || 0).getTime();
          if (tB !== tA) return tB - tA;
          return Number(b.id || 0) - Number(a.id || 0);
        });
      }
      total = (moviesData?.total || 0) + (seriesData?.total || 0);
      categories = categoriesData || [];
    }
  } catch (error) {
    console.error("Failed to fetch page data:", error);
  }

  if (!page) {
    notFound();
  }

  return (
    <div className="min-h-screen pt-32 pb-margin-desktop px-gutter bg-gradient-to-b from-primary-container/[0.10] via-background-obsidian to-background-obsidian">
      <div className="max-w-container-max mx-auto">
        
        {/* Smart Back Navigation */}
        <div className="mb-4 sm:mb-6">
          <BackButton fallbackUrl="/movies" />
        </div>

        {/* Header */}
        <div className="mb-stack-lg">
          <div className="mb-stack-md text-center md:text-left">
            <h1 className="font-display-hero text-display-hero-mobile md:text-[56px] font-black text-text-primary mb-2 tracking-tighter">{page.title}</h1>
            <p className="text-text-secondary font-body-lg text-body-lg">Bizning maxsus to&apos;plamlarimiz.</p>
          </div>

          {/* Unified Filter Bar replacing legacy CategoryFilter */}
          <div className="pt-2">
            <UnifiedFilterBar
              categories={categories}
              genres={DEFAULT_GENRES}
              years={DEFAULT_YEARS}
              types={DEFAULT_MEDIA_TYPES}
              selectedCategory={searchParams.category}
              selectedGenre={searchParams.genre}
              selectedYear={searchParams.year}
              selectedSort={searchParams.sort}
              baseUrl={`/p/${params.slug}`}
              totalItems={total}
            />
          </div>
        </div>

        <CatalogGrid 
          key={`page-${params.slug}-${searchParams.category || 'all'}-${searchParams.genre || 'all'}-${searchParams.year || 'all'}-${searchParams.sort || 'all'}`}
          initialItems={combinedItems}
          total={total}
          type="page"
          pageSlug={params.slug}
          pageId={page.id}
          categoryId={searchParams.category}
          genre={searchParams.genre}
          year={searchParams.year}
          search={searchParams.search}
          sort={searchParams.sort}
          pageSize={pageSize}
          emptyMessage="Hozircha ma'lumotlar mavjud emas."
        />
        
      </div>
    </div>
  );
}
