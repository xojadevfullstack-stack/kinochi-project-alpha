import { fetchApi } from "@/lib/api";
import { Metadata } from "next";
import CategoryFilter from "@/components/CategoryFilter";
import CatalogTypeNav from "@/components/catalog/CatalogTypeNav";
import CatalogGrid from "@/components/catalog/CatalogGrid";
import { CatalogItem } from "@/lib/api/catalog";

type Category = {
  id: number;
  name: string;
};

export async function generateMetadata({ params }: { params: { slug: string } }): Promise<Metadata> {
  try {
    const page = await fetchApi(`/pages/${params.slug}`);
    return {
      title: `${page.title} - Kinochi`,
      description: `${page.title} turidagi barcha kino va seriallar.`,
    };
  } catch (error) {
    return {
      title: "Sahifa - Kinochi",
    };
  }
}

export default async function DynamicPage({ params, searchParams }: { params: { slug: string }, searchParams: { category?: string } }) {
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

      const [moviesData, seriesData, categoriesData] = await Promise.all([
        fetchApi(moviesQuery),
        fetchApi(seriesQuery),
        fetchApi('/categories')
      ]);
      const movies: CatalogItem[] = (moviesData?.items || []).map((m: any) => ({ ...m, is_series: false }));
      const seriesList: CatalogItem[] = (seriesData?.items || []).map((s: any) => ({ ...s, is_series: true }));
      combinedItems = [...movies, ...seriesList].sort((a, b) => new Date(b.created_at || 0).getTime() - new Date(a.created_at || 0).getTime());
      total = (moviesData?.total || 0) + (seriesData?.total || 0);
      categories = categoriesData || [];
    }
  } catch (error) {
    console.error("Failed to fetch page data:", error);
  }

  if (!page) {
    return (
      <div className="min-h-screen pt-32 pb-margin-desktop px-gutter flex items-center justify-center">
        <h1 className="text-3xl font-bold text-text-primary">Sahifa topilmadi</h1>
      </div>
    );
  }

  return (
    <div className="min-h-screen pt-32 pb-margin-desktop px-gutter bg-gradient-to-b from-primary-container/[0.10] via-background-obsidian to-background-obsidian">
      <div className="max-w-container-max mx-auto">
        
        {/* Header */}
        <div className="mb-stack-lg">
          <div className="mb-stack-md text-center md:text-left">
            <h1 className="font-display-hero text-display-hero-mobile md:text-[56px] font-black text-text-primary mb-2 tracking-tighter">{page.title}</h1>
            <p className="text-text-secondary font-body-lg text-body-lg">Bizning maxsus to&apos;plamlarimiz.</p>
          </div>

          {/* Catalog Type Switcher (Kinolar / Seriallar / Anime / Dorama) */}
          <CatalogTypeNav currentType={params.slug} pages={allPages} />

          {/* Category Filter */}
          <CategoryFilter categories={categories} currentCategory={searchParams.category} baseUrl={`/p/${params.slug}`} />
        </div>

        <CatalogGrid 
          key={`page-${params.slug}-${searchParams.category || 'all'}`}
          initialItems={combinedItems}
          total={total}
          type="page"
          pageSlug={params.slug}
          pageId={page.id}
          categoryId={searchParams.category}
          pageSize={pageSize}
          emptyMessage="Hozircha ma'lumotlar mavjud emas."
        />
        
      </div>
    </div>
  );
}
