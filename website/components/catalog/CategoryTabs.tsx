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
              className={`px-4 py-2 rounded-full font-label-caps text-xs md:text-sm tracking-wide font-bold transition-all duration-300 ${
                isActive
                  ? "bg-primary-container text-white shadow-[0_0_15px_rgba(229,9,20,0.3)]"
                  : "bg-surface-container/50 text-text-secondary hover:bg-surface-container hover:text-text-primary"
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
