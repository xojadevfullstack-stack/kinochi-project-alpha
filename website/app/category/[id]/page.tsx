import { fetchApi } from "@/lib/api";
import Link from "next/link";
import { Metadata } from "next";
import CatalogGrid from "@/components/catalog/CatalogGrid";
import { CatalogItem } from "@/lib/api/catalog";

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
        title: `${category.name} kinolar - Kinochi`,
        description: `${category.name} janridagi eng sara kinolar to'plami.`,
      };
    }
  } catch (error) {
    console.error("Error fetching categories for metadata:", error);
  }
  
  return {
    title: "Kategoriya - Kinochi",
    description: "Kinochi - Kategoriya bo'yicha kinolar",
  };
}

export default async function CategoryPage({ params }: { params: { id: string } }) {
  let movies: CatalogItem[] = [];
  let total = 0;
  let categories: Category[] = [];
  let categoryName = "Kategoriya";
  const pageSize = 36;
  
  try {
    const [moviesData, categoriesData] = await Promise.all([
      fetchApi(`/movies?limit=${pageSize}&category_id=${params.id}`),
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
        
        {/* Header & Categories */}
        <div className="mb-stack-lg">
          <div className="mb-stack-md">
            <h1 className="font-display-hero text-display-hero-mobile md:text-[56px] font-black text-text-primary mb-2 tracking-tighter">
              {categoryName}
            </h1>
            <p className="text-text-secondary font-body-lg text-body-lg">Bizning katta kino kolleksiyamiz bilan tanishing.</p>
          </div>
          <div className="flex items-center gap-2 overflow-x-auto pb-2 pt-1 hide-scrollbar scroll-smooth">
            <Link 
              href="/movies" 
              className="px-4 sm:px-5 py-2.5 rounded-xl text-xs sm:text-sm font-semibold transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5 active:scale-95 shrink-0 border bg-white/5 border-white/10 text-text-secondary hover:text-text-primary hover:bg-white/10"
            >
              Barchasi
            </Link>
            {categories.map(cat => {
              const isActive = String(cat.id) === params.id;
              return (
                <Link 
                  key={cat.id} 
                  href={`/category/${cat.id}`}
                  className={`px-4 sm:px-5 py-2.5 rounded-xl text-xs sm:text-sm font-semibold transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5 active:scale-95 shrink-0 border ${
                    isActive 
                      ? "bg-white/20 text-white border-white/30 shadow-lg shadow-black/20 font-bold backdrop-blur-md" 
                      : "bg-white/5 border-white/10 text-text-secondary hover:text-text-primary hover:bg-white/10"
                  }`}
                >
                  {cat.name}
                </Link>
              );
            })}
          </div>
        </div>

        <CatalogGrid 
          key={`category-${params.id}`}
          initialItems={movies}
          total={total}
          type="movies"
          categoryId={params.id}
          pageSize={pageSize}
          emptyMessage="Ushbu kategoriyada hozircha kinolar mavjud emas."
        />
        
      </div>
    </div>
  );
}
