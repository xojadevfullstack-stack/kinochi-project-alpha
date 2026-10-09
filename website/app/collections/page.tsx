import { fetchApi } from "@/lib/api";
import Link from "next/link";
import Image from "next/image";
import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Kinoxronologiyalar & Franchisalar - MediaPlus",
  description:
    "Marvel, DC, Garri Potter, O'rta Yer, Transformerlar va boshqa film olamlarini rasmiy voqealar xronologiyasi bo'yicha tartib bilan tomosha qiling.",
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
  is_active: boolean;
  sort_order: number;
  items_count: number;
}

export default async function CollectionsPage() {
  let collections: Collection[] = [];
  try {
    collections = await fetchApi("/collections");
  } catch (err) {
    collections = [];
  }

  return (
    <div className="min-h-screen bg-background-obsidian text-text-primary pt-24 sm:pt-28 md:pt-32 pb-16">
      {/* Hero Header */}
      <div className="max-w-container-max mx-auto px-gutter mb-10 sm:mb-14">
        <div className="relative rounded-3xl bg-gradient-to-r from-red-950/60 via-surface-container-high/60 to-black/80 border border-primary-container/20 p-6 sm:p-10 md:p-12 overflow-hidden shadow-2xl">
          <div className="absolute top-0 right-0 w-96 h-96 bg-primary-container/15 rounded-full blur-3xl pointer-events-none"></div>

          <div className="relative z-10 max-w-2xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary-container/20 border border-primary-container/40 text-primary-container font-extrabold text-xs uppercase tracking-widest mb-4">
              <span className="material-symbols-outlined text-[16px]">auto_awesome_motion</span>
              <span>Rasmiy Kinoxronologiyalar</span>
            </div>
            <h1 className="font-display-hero text-3xl sm:text-5xl font-black tracking-tight text-white mb-4 leading-tight">
              Film Olamlari & Kinoxronologiyalar
            </h1>
            <p className="text-text-secondary text-sm sm:text-base leading-relaxed">
              Dunyoning eng mashhur koinotlari (Marvel, DC, Garri Potter, Tolkien O'rta Yeri,
              Forsaj)ni qanday tartibda ko'rishni bilmayapsizmi? Rasmiy voqealar xronologiyasi va
              chiqarilgan yillari bo'yicha birma-bir tomosha qiling!
            </p>
          </div>
        </div>
      </div>

      {/* Franchises Grid */}
      <div className="max-w-container-max mx-auto px-gutter">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 sm:gap-8">
          {collections.map((col) => (
            <Link
              key={col.id}
              href={`/collections/${col.slug}`}
              className="group flex flex-col bg-surface-container-lowest/80 hover:bg-surface-container-low/90 border border-white/10 hover:border-primary-container/50 rounded-2xl overflow-hidden transition-all duration-300 hover:scale-[1.02] hover:shadow-2xl hover:shadow-primary-container/10"
            >
              {/* Banner / Poster Section */}
              <div className="relative aspect-[16/9] w-full bg-surface-container overflow-hidden">
                {col.banner_url || col.poster_url ? (
                  <Image
                    src={col.banner_url || col.poster_url || ""}
                    alt={col.name}
                    fill
                    sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
                    className="object-cover group-hover:scale-105 transition-transform duration-500"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-white/20">
                    <span className="material-symbols-outlined text-5xl">auto_awesome_motion</span>
                  </div>
                )}
                <div className="absolute inset-0 bg-gradient-to-t from-background-obsidian via-background-obsidian/40 to-transparent"></div>

                {/* Items Count Badge */}
                <div className="absolute top-3 right-3 px-2.5 py-1 rounded-lg bg-black/75 backdrop-blur-md border border-white/15 text-white text-xs font-bold flex items-center gap-1.5 shadow-lg">
                  <span className="material-symbols-outlined text-[14px] text-primary-container">
                    movie
                  </span>
                  <span>{col.items_count} ta qism</span>
                </div>

                {/* Franchise Badge */}
                {col.is_franchise && (
                  <div className="absolute top-3 left-3 px-2.5 py-1 rounded-lg bg-primary-container/80 backdrop-blur-md text-white text-[10px] font-extrabold uppercase tracking-wider shadow-lg">
                    Franchisa
                  </div>
                )}
              </div>

              {/* Content Body */}
              <div className="p-5 flex-1 flex flex-col justify-between">
                <div>
                  <h2 className="font-bold text-lg sm:text-xl text-white group-hover:text-primary-container transition-colors line-clamp-1 mb-2">
                    {col.name}
                  </h2>
                  <p className="text-xs sm:text-sm text-text-secondary line-clamp-2 leading-relaxed mb-4">
                    {col.description || "Ushbu to'plamdagi barcha qismlar va voqealar zanjiri."}
                  </p>
                </div>

                <div className="pt-3 border-t border-white/5 flex items-center justify-between text-xs font-bold text-primary-container">
                  <span>Xronologiyani ko'rish</span>
                  <span className="material-symbols-outlined text-base group-hover:translate-x-1.5 transition-transform">
                    arrow_forward
                  </span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
