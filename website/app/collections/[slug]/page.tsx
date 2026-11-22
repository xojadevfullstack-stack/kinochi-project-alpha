import { fetchApi } from "@/lib/api";
import { notFound } from "next/navigation";
import Image from "next/image";
import { Metadata } from "next";
import CollectionTimelineView from "@/components/CollectionTimelineView";
import SubscribeButton from "@/components/SubscribeButton";

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
    <div className="min-h-screen bg-transparent text-slate-900 dark:text-text-primary pt-3 sm:pt-4 pb-20">
      {/* Hero Showcase Banner (Framed Hero Method matching HeroCarousel & Cinema Island) */}
      <div className="max-w-container-max mx-auto px-gutter mb-8 sm:mb-10">
        <div className="hero-stage preserve-white relative w-full rounded-2xl sm:rounded-3xl overflow-hidden border border-slate-900/15 dark:border-white/10 bg-[#0E0F13] shadow-xl">
          <div className="absolute inset-0 z-0 pointer-events-none">
            {collection.banner_url || collection.poster_url ? (
              <Image
                src={collection.banner_url || collection.poster_url}
                alt={collection.name}
                fill
                priority
                unoptimized
                className="object-cover opacity-65"
                style={{ objectPosition: "center 20%" }}
              />
            ) : null}
            <div className="absolute inset-0 bg-gradient-to-t from-[#0E0F13]/75 via-transparent to-transparent" />
            <div className="absolute inset-0 bg-gradient-to-r from-[#0E0F13]/85 via-[#0E0F13]/50 to-transparent" />
          </div>

          <div className="relative z-10 px-5 py-6 sm:px-10 sm:py-9 md:px-12 md:py-10 flex flex-col md:flex-row items-center md:items-end gap-6 sm:gap-8">
            {/* Poster Card */}
            {collection.poster_url && (
              <div className="w-36 sm:w-44 md:w-52 aspect-[2/3] rounded-2xl bg-surface-container-high overflow-hidden shadow-2xl border border-white/15 relative shrink-0">
                <Image
                  src={collection.poster_url}
                  alt={collection.name}
                  fill
                  priority
                  sizes="(max-width: 768px) 176px, 208px"
                  unoptimized
                  className="object-cover"
                />
              </div>
            )}

            {/* Info Details */}
            <div className="flex-1 text-center md:text-left min-w-0">
              <div className="flex flex-wrap items-center justify-center md:justify-start gap-2.5 mb-3">
                <span className="inline-flex items-center gap-1.5 text-xs font-bold text-white bg-[#E50914]/25 px-3 py-1.5 rounded-xl border border-[#E50914]/45">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#E50914]" />
                  <span>{collection.items?.length || 0} ta qism</span>
                </span>

                <SubscribeButton
                  targetType="collection"
                  targetId={collection.id}
                  title={collection.name}
                  className="px-3.5 py-1.5 rounded-xl text-xs"
                />
              </div>

              <h1 className="font-display-hero text-2xl sm:text-4xl md:text-5xl font-black text-white tracking-tight mb-3">
                {collection.name}
              </h1>

              <p className="text-slate-200 text-sm sm:text-base max-w-3xl leading-relaxed">
                {collection.description ||
                  "Ushbu koinotdagi barcha filmlar va ularning o'zaro bog'liqligi."}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Timeline View with Dual Toggle */}
      <div className="max-w-container-max mx-auto px-gutter">
        <CollectionTimelineView
          collectionId={collection.id}
          initialItems={collection.items || []}
          collectionName={collection.name}
          collectionSlug={collection.slug}
        />
      </div>
    </div>
  );
}
