"use client";

import { useRef } from "react";
import Link from "next/link";
import Image from "next/image";

interface HomeCollection {
  id: number;
  name: string;
  slug: string;
  poster_url?: string | null;
  banner_url?: string | null;
  posters?: string[];
  items_count?: number;
  is_active?: boolean;
}

export default function HomeCollectionsRow({
  collections = [],
}: {
  collections: HomeCollection[];
}) {
  const rowRef = useRef<HTMLDivElement>(null);

  const activeCollections = (collections || []).filter(
    (c) => c.is_active !== false && (c.items_count === undefined || c.items_count > 0)
  );

  if (activeCollections.length === 0) return null;

  const visible = activeCollections.slice(0, 8);

  const scrollRow = (dir: -1 | 1) => {
    rowRef.current?.scrollBy({ left: dir * 420, behavior: "smooth" });
  };

  return (
    <section className="max-w-container-max mx-auto px-gutter my-6 sm:my-10 cv-auto">
      <div className="flex items-center justify-between mb-3">
        <h2 className="font-headline-md text-base sm:text-xl text-slate-900 dark:text-white flex items-center gap-2 font-bold">
          <span className="w-1.5 h-5 bg-[#E50914] rounded-full block shrink-0" />
          <span>To&apos;plamlar</span>
        </h2>

        <div className="flex items-center gap-2">
          <div className="hidden sm:flex items-center gap-1">
            <button
              type="button"
              onClick={() => scrollRow(-1)}
              aria-label="Chapga"
              className="w-7 h-7 rounded-full bg-white dark:bg-[#121317] hover:bg-[#E50914] text-slate-700 dark:text-gray-300 hover:text-white flex items-center justify-center transition border border-slate-200 dark:border-white/10 cursor-pointer"
            >
              <span className="material-symbols-outlined text-[16px]">chevron_left</span>
            </button>
            <button
              type="button"
              onClick={() => scrollRow(1)}
              aria-label="O'ngga"
              className="w-7 h-7 rounded-full bg-white dark:bg-[#121317] hover:bg-[#E50914] text-slate-700 dark:text-gray-300 hover:text-white flex items-center justify-center transition border border-slate-200 dark:border-white/10 cursor-pointer"
            >
              <span className="material-symbols-outlined text-[16px]">chevron_right</span>
            </button>
          </div>
          <Link
            href="/collections"
            className="text-xs text-slate-600 dark:text-gray-400 hover:text-[#D20A13] dark:hover:text-[#E50914] transition flex items-center gap-0.5 ml-1 font-semibold"
          >
            <span>Barchasi</span>
            <span className="material-symbols-outlined text-[14px]">chevron_right</span>
          </Link>
        </div>
      </div>

      <div
        ref={rowRef}
        className="flex items-stretch gap-3 sm:gap-4 overflow-x-auto hide-scrollbar snap-x pb-3 pt-1"
      >
        {visible.map((col) => {
          const fallbackImg = col.poster_url || col.banner_url || "/logo-mediaplus-icon.png";
          const posters = col.posters && col.posters.length > 0 ? col.posters : [fallbackImg];
          const pLeft = posters[0] || fallbackImg;
          const pRight = posters[2] || posters[1] || fallbackImg;
          const pCenter = posters[1] || posters[0] || fallbackImg;

          return (
            <Link
              key={col.id}
              href={`/collections/${col.slug}`}
              className="shrink-0 snap-start w-56 sm:w-64 bg-white hover:bg-slate-50 dark:bg-[#0E1117] dark:hover:bg-[#141824] border border-slate-200 dark:border-white/10 hover:border-[#E50914] rounded-2xl p-4 transition duration-300 group cursor-pointer flex flex-col justify-between shadow-sm dark:shadow-xl"
            >
              <div className="fan-stack">
                <div className="fan-left bg-surface-container">
                  <Image
                    src={pLeft}
                    alt=""
                    fill
                    unoptimized
                    className="object-cover"
                  />
                </div>
                <div className="fan-right bg-surface-container">
                  <Image
                    src={pRight}
                    alt=""
                    fill
                    unoptimized
                    className="object-cover"
                  />
                </div>
                <div className="fan-center bg-surface-container-high">
                  <Image
                    src={pCenter}
                    alt={col.name}
                    fill
                    unoptimized
                    className="object-cover group-hover:scale-105 transition duration-300"
                  />
                </div>
              </div>

              <div className="mt-3 min-w-0">
                <h3 className="font-bold text-sm text-slate-900 dark:text-white group-hover:text-[#D20A13] dark:group-hover:text-[#E50914] transition truncate">
                  {col.name}
                </h3>
                {typeof col.items_count === "number" && (
                  <p className="text-xs text-slate-500 dark:text-gray-400 font-medium mt-0.5">
                    {col.items_count} ta qism
                  </p>
                )}
              </div>
            </Link>
          );
        })}

        <Link
          href="/collections"
          className="shrink-0 snap-start w-44 sm:w-60 bg-white dark:bg-[#0E1117]/70 hover:bg-slate-50 dark:hover:bg-[#141824] border-2 border-dashed border-slate-300 dark:border-[#E50914]/40 hover:border-[#E50914] rounded-2xl p-3 sm:p-4 flex flex-col items-center justify-center text-center transition duration-300 group cursor-pointer shadow-sm"
        >
          <span className="font-black text-3xl sm:text-5xl text-[#D20A13] dark:text-[#E50914] group-hover:scale-110 transition duration-300">
            {activeCollections.length}
          </span>
          <span className="text-[11px] sm:text-xs text-slate-500 dark:text-gray-400 font-medium mt-1 mb-2">
            kolleksiya
          </span>
          <div className="flex items-center gap-1 text-[11px] sm:text-xs font-bold text-[#D20A13] dark:text-[#E50914] group-hover:underline">
            <span>Barchasini ko&apos;rish</span>
            <span className="material-symbols-outlined text-[14px]">chevron_right</span>
          </div>
        </Link>
      </div>
    </section>
  );
}
