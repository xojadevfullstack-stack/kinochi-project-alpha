import { fetchApi } from "@/lib/api";
import Link from "next/link";
import Image from "next/image";
import { Metadata } from "next";

export const revalidate = 60;

export const metadata: Metadata = {
  title: "Seriallar - Kinochi",
  description: "Eng so'nggi va qiziqarli seriallarni tomosha qiling.",
};

type Series = {
  id: number;
  title: string;
  description: string | null;
  poster_url: string | null;
};

type Category = {
  id: number;
  name: string;
};


export default async function SeriesListPage({ searchParams }: { searchParams: { category?: string } }) {
  let seriesList: Series[] = [];
  let categories: Category[] = [];
  
  try {
    const query = searchParams.category ? `/series?limit=50&category_id=${searchParams.category}&exclude_paged=true` : "/series?limit=50&exclude_paged=true";
    const [seriesData, categoriesData] = await Promise.all([
      fetchApi(query),
      fetchApi("/categories")
    ]);
    seriesList = seriesData.items || [];
    categories = categoriesData || [];
  } catch (error) {
    console.error("Failed to fetch series or categories:", error);
  }

  return (
    <div className="min-h-screen pt-32 pb-margin-desktop px-gutter bg-gradient-to-b from-primary-container/[0.10] via-background-obsidian to-background-obsidian">
      <div className="max-w-container-max mx-auto">
        
        {/* Header & Categories */}
        <div className="mb-stack-lg">
          <div className="mb-stack-md">
            <h1 className="font-display-hero text-display-hero-mobile md:text-[56px] font-black text-text-primary mb-2 tracking-tighter">Barcha Seriallar</h1>
            <p className="text-text-secondary font-body-lg text-body-lg">Bizning katta seriallar kolleksiyamiz bilan tanishing.</p>
          </div>
          <div className="flex gap-2 overflow-x-auto pb-2 hide-scrollbar">
            <Link href="/series" className={`px-6 py-2 rounded-full font-label-caps text-xs uppercase tracking-widest font-bold whitespace-nowrap transition-colors ${!searchParams.category ? "bg-primary-container text-white shadow-[0_0_15px_rgba(229,9,20,0.5)]" : "bg-white/5 border border-white/10 text-text-secondary hover:text-text-primary hover:bg-white/10"}`}>Barchasi</Link>
            {categories.map(cat => {
              const isActive = searchParams.category === String(cat.id);
              return (
                <Link 
                  key={cat.id} 
                  href={`/series?category=${cat.id}`}
                  className={`px-6 py-2 rounded-full font-label-caps text-xs uppercase tracking-widest font-bold whitespace-nowrap transition-colors ${isActive ? "bg-primary-container text-white shadow-[0_0_15px_rgba(229,9,20,0.5)]" : "bg-white/5 border border-white/10 text-text-secondary hover:text-text-primary hover:bg-white/10"}`}
                >
                  {cat.name}
                </Link>
              );
            })}
          </div>
        </div>

        {seriesList.length === 0 ? (
          <div className="text-center py-20 text-text-secondary">
            <span className="material-symbols-outlined text-6xl mb-4 opacity-50">live_tv</span>
            <p>Hozircha seriallar mavjud emas.</p>
          </div>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4 md:gap-6">
            {seriesList.map(series => (
              <Link 
                href={`/series/${series.id}`} 
                key={series.id} 
                className="group relative aspect-[2/3] rounded-xl overflow-hidden cursor-pointer bg-surface-container hover:scale-105 transition-transform duration-300 shadow-lg hover:shadow-[0_0_20px_rgba(229,9,20,0.3)] ring-1 ring-white/5 hover:ring-primary-container"
              >
                {series.poster_url ? (
                  <Image 
                    src={series.poster_url} 
                    alt={series.title}
                    fill
                    sizes="(max-width: 768px) 50vw, (max-width: 1024px) 33vw, 16vw"
                    className="object-cover"
                  />
                ) : (
                  <div className="absolute inset-0 flex flex-col items-center justify-center bg-surface-container-high text-gray-500">
                    <span className="material-symbols-outlined text-4xl mb-2 opacity-30">live_tv</span>
                  </div>
                )}
                
                <div className="absolute inset-0 bg-gradient-to-t from-background-obsidian via-background-obsidian/50 to-transparent opacity-80 group-hover:opacity-100 transition-opacity"></div>
                
                <div className="absolute top-2 right-2 px-2 py-1 bg-black/60 backdrop-blur-sm rounded text-rating-gold flex items-center gap-1 border border-white/10">
                  <span className="material-symbols-outlined text-[14px]" style={{ fontVariationSettings: "'FILL' 1" }}>star</span>
                  <span className="font-label-caps text-xs font-bold">{(series as any).imdb_rating || "N/A"}</span>
                </div>
                
                <div className="absolute bottom-0 left-0 w-full p-4 transform translate-y-2 group-hover:translate-y-0 transition-transform">
                  <div className="flex gap-1 mb-1">
                    <span className="px-1.5 py-0.5 bg-white/10 backdrop-blur-sm rounded text-[10px] font-bold text-text-secondary uppercase tracking-wider">{(series as any).categories?.[0]?.name || "Serial"}</span>
                    {(series as any).release_year && <span className="px-1.5 py-0.5 bg-white/10 backdrop-blur-sm rounded text-[10px] font-bold text-text-secondary uppercase tracking-wider">{(series as any).release_year}</span>}
                  </div>
                  <h3 className="font-display text-[18px] font-bold leading-tight text-white mb-1 group-hover:text-primary transition-colors line-clamp-2">
                    {series.title}
                  </h3>
                </div>
              </Link>
            ))}
          </div>
        )}
        
      </div>
    </div>
  );
}
