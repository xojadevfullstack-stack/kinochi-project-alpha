"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { PageResponse } from "@/lib/api/catalog";

type Props = {
  pages: PageResponse[];
  baseUrl: string;
};

export default function CategoryTabs({ pages, baseUrl }: Props) {
  const searchParams = useSearchParams();
  const currentSlug = searchParams.get("page") || (pages.length > 0 ? pages[0].slug : "");

  if (!pages || pages.length === 0) return null;

  return (
    <div className="w-full overflow-x-auto hide-scrollbar pb-2 mb-6 border-b border-white/10">
      <div className="flex items-center gap-2 md:gap-4 min-w-max">
        {pages.map((page) => {
          const isActive = page.slug === currentSlug;
          return (
            <Link
              key={page.id}
              href={`${baseUrl}?page=${page.slug}`}
              className={`px-4 sm:px-5 py-2.5 rounded-xl text-xs sm:text-sm font-semibold transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5 active:scale-95 shrink-0 flex items-center gap-2 border ${
                isActive
                  ? "bg-white/20 text-white border-white/30 shadow-md shadow-black/20 font-bold backdrop-blur-md"
                  : "bg-white/5 border-white/10 text-text-secondary hover:text-text-primary hover:bg-white/10"
              }`}
            >
              {page.title}
            </Link>
          );
        })}
      </div>
    </div>
  );
}
