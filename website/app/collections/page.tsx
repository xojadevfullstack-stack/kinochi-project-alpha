import { fetchApi } from "@/lib/api";
import { Metadata } from "next";
import BackButton from "@/components/BackButton";
import CollectionsClientView from "@/components/CollectionsClientView";

export const metadata: Metadata = {
  title: "Kolleksiyalar & Film Olamlari - MediaPlus",
  description:
    "Marvel, DC, Garri Potter, O'rta Yer, Forsaj va boshqa kino to'plamlarini rasmiy voqealar xronologiyasi bo'yicha tartib bilan tomosha qiling.",
};

export const revalidate = 60;

interface Collection {
  id: number;
  name: string;
  slug: string;
  description?: string | null;
  poster_url?: string | null;
  banner_url?: string | null;
  is_franchise: boolean;
  category_type?: string;
  is_active: boolean;
  sort_order: number;
  items_count: number;
}

export default async function CollectionsPage() {
  let collections: Collection[] = [];
  try {
    const raw = await fetchApi("/collections");
    if (Array.isArray(raw)) {
      collections = raw.filter((c: Collection) => c.is_active && c.items_count > 0);
    } else {
      collections = [];
    }
  } catch (err) {
    collections = [];
  }

  return (
    <div className="min-h-screen bg-background-obsidian text-text-primary pt-24 sm:pt-28 md:pt-32 pb-16">
      {/* Hero Header */}
      <div className="max-w-container-max mx-auto px-gutter mb-8 sm:mb-12">
        {/* Smart Back Navigation */}
        <div className="mb-4 sm:mb-6">
          <BackButton fallbackUrl="/" />
        </div>

        <div className="relative rounded-3xl bg-gradient-to-r from-red-950/60 via-surface-container-high/60 to-black/80 border border-primary-container/20 p-6 sm:p-10 md:p-12 overflow-hidden shadow-2xl">
          <div className="absolute top-0 right-0 w-96 h-96 bg-primary-container/15 rounded-full blur-3xl pointer-events-none"></div>

          <div className="relative z-10 max-w-2xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary-container/20 border border-primary-container/40 text-primary-container font-extrabold text-xs uppercase tracking-widest mb-4">
              <span className="material-symbols-outlined text-[16px]">auto_awesome_motion</span>
              <span>Kino Kolleksiyalari & Franshizalar</span>
            </div>
            <h1 className="font-display-hero text-3xl sm:text-5xl font-black tracking-tight text-white mb-4 leading-tight">
              Film Olamlari & Kolleksiyalar
            </h1>
            <p className="text-text-secondary text-sm sm:text-base leading-relaxed">
              Dunyoning eng mashhur koinotlari (Marvel, DC, Garri Potter, Forsaj) hamda maxsus
              mavzuli to'plamlarni tomosha qiling va yangi qismlariga obuna bo'ling!
            </p>
          </div>
        </div>
      </div>

      {/* Filterable Collections View */}
      <div className="max-w-container-max mx-auto px-gutter">
        <CollectionsClientView initialCollections={collections} />
      </div>
    </div>
  );
}
