import { fetchApi } from "@/lib/api";
import { notFound } from "next/navigation";
import Image from "next/image";
import Link from "next/link";
import { Metadata } from "next";
import CollectionTimelineView from "@/components/CollectionTimelineView";

type Props = {
  params: { slug: string };
};

export const revalidate = 60;

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  try {
    const col = await fetchApi(`/collections/${params.slug}`);
    return {
      title: `${col.name} - Voqealar Xronologiyasi | MediaPlus`,
      description:
        col.description ||
        `${col.name} film olami va uning barcha qismlari xronologik tartibda.`,
      openGraph: {
        title: `${col.name} - Voqealar Xronologiyasi`,
        description: col.description || `${col.name} kinoxronologiyasi.`,
        images: col.banner_url || col.poster_url ? [{ url: col.banner_url || col.poster_url }] : [],
      },
    };
  } catch (e) {
    return {
      title: "To'plam topilmadi - MediaPlus",
    };
  }
}

export default async function CollectionDetailPage({ params }: Props) {
  let collection;
  try {
    collection = await fetchApi(`/collections/${params.slug}`);
  } catch (err) {
    notFound();
  }

  return (
    <div className="min-h-screen bg-background-obsidian text-text-primary pt-20 sm:pt-24 md:pt-28 pb-20">
      {/* Hero Showcase Banner */}
      <div className="relative w-full overflow-hidden mb-8 sm:mb-12 border-b border-white/10">
        <div className="absolute inset-0 bg-background-obsidian">
          {collection.banner_url || collection.poster_url ? (
            <div
              className="absolute inset-0 bg-cover bg-center opacity-30 blur-md scale-105"
              style={{
                backgroundImage: `url('${collection.banner_url || collection.poster_url}')`,
              }}
            ></div>
          ) : null}
          <div className="absolute inset-0 bg-gradient-to-t from-background-obsidian via-background-obsidian/80 to-transparent"></div>
        </div>

        <div className="relative z-10 max-w-container-max mx-auto px-gutter py-12 sm:py-16 md:py-20 flex flex-col md:flex-row items-center md:items-end gap-6 sm:gap-8">
          {/* Poster Card */}
          {collection.poster_url && (
            <div className="w-36 sm:w-44 md:w-56 aspect-[2/3] rounded-2xl bg-surface-container-high overflow-hidden shadow-2xl border border-white/15 relative shrink-0">
              <Image
                src={collection.poster_url}
                alt={collection.name}
                fill
                priority
                sizes="(max-width: 768px) 180px, 224px"
                unoptimized
                className="object-cover"
              />
            </div>
          )}

          {/* Info Details */}
          <div className="flex-1 text-center md:text-left">
            <div className="flex flex-wrap items-center justify-center md:justify-start gap-2 mb-3">
              <Link
                href="/collections"
                className="inline-flex items-center gap-1 text-xs text-text-secondary hover:text-white bg-white/5 px-2.5 py-1 rounded-lg border border-white/10 transition-colors"
              >
                <span className="material-symbols-outlined text-[14px]">arrow_back</span>
                <span>Barcha Xronologiyalar</span>
              </Link>

              <span className="text-xs font-bold text-primary-container bg-primary-container/20 px-2.5 py-1 rounded-lg border border-primary-container/30">
                {collection.items?.length || 0} ta qism
              </span>
            </div>

            <h1 className="font-display-hero text-2xl sm:text-4xl md:text-5xl font-black text-white tracking-tight mb-3">
              {collection.name}
            </h1>

            <p className="text-text-secondary text-sm sm:text-base max-w-3xl leading-relaxed">
              {collection.description ||
                "Ushbu koinotdagi barcha filmlar va ularning o'zaro bog'liqligi."}
            </p>
          </div>
        </div>
      </div>

      {/* Main Timeline View with Dual Toggle */}
      <div className="max-w-container-max mx-auto px-gutter">
        <CollectionTimelineView
          initialItems={collection.items || []}
          collectionName={collection.name}
          collectionSlug={collection.slug}
        />
      </div>
    </div>
  );
}
