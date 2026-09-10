import { Metadata } from "next";
import { getPages, getPageContent } from "@/lib/api/catalog";
import CategoryTabs from "@/components/catalog/CategoryTabs";
import CatalogGrid from "@/components/catalog/CatalogGrid";

export const dynamic = 'force-dynamic';

export const metadata: Metadata = {
  title: "Katalog - Kinochi",
  description: "Eng so'nggi va qiziqarli kinolar hamda seriallar katalogi.",
};

export default async function CatalogPage({ searchParams }: { searchParams: { page?: string } }) {
  // 1. Fetch available dynamic pages
  const pages = await getPages();
  
  // 2. Determine active page
  const activeSlug = searchParams.page || (pages.length > 0 ? pages[0].slug : "");
  
  // 3. Fetch content for active page (initial 20 items)
  const { items, total } = await getPageContent(activeSlug, 0, 20);

  return (
    <div className="min-h-screen pt-32 pb-margin-desktop px-gutter bg-gradient-to-b from-primary-container/[0.10] via-background-obsidian to-background-obsidian">
      <div className="max-w-container-max mx-auto">
        
        {/* Header Section */}
        <div className="mb-stack-lg">
          <div className="mb-stack-md text-center md:text-left">
            <h1 className="font-display-hero text-display-hero-mobile md:text-[56px] font-black text-text-primary mb-2 tracking-tighter">
              Katalog
            </h1>
            <p className="text-text-secondary font-body-lg text-body-lg">
              Bizning katta kino va seriallar kolleksiyamiz bilan tanishing.
            </p>
          </div>
          
          {/* Dynamic Tabs */}
          <CategoryTabs pages={pages} baseUrl="/movies" />
        </div>

        {/* Dynamic Grid with Load More */}
        <CatalogGrid initialItems={items} total={total} pageSlug={activeSlug} />
        
      </div>
    </div>
  );
}
