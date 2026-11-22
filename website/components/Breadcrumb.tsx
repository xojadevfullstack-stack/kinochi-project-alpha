"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { buildBreadcrumbs } from "@/lib/breadcrumbHelpers.mjs";
import { useBreadcrumbOverrides } from "@/components/BreadcrumbContext";

export default function Breadcrumb() {
  const pathname = usePathname();
  const overrides = useBreadcrumbOverrides();

  if (!pathname || pathname === "/") {
    return null;
  }

  const crumbs = buildBreadcrumbs(pathname, overrides);
  if (crumbs.length === 0) return null;

  return (
    <nav
      aria-label="Sahifa manzili"
      className="universal-breadcrumb w-full bg-transparent py-1.5"
    >
      <div className="max-w-container-max mx-auto px-gutter flex items-center gap-1.5 text-xs overflow-x-auto hide-scrollbar whitespace-nowrap">
        <Link
          href="/"
          className="inline-flex items-center gap-1 text-slate-500 dark:text-gray-400 hover:text-[#D20A13] dark:hover:text-[#E50914] transition-colors shrink-0"
        >
          <span className="material-symbols-outlined text-[15px]">home</span>
          <span>Bosh sahifa</span>
        </Link>

        {crumbs.map((crumb) => (
          <div key={crumb.href + crumb.label} className="inline-flex items-center gap-1.5 shrink-0">
            <span className="text-slate-400 dark:text-gray-600 select-none">/</span>
            {crumb.isLast ? (
              <span className="font-semibold text-slate-900 dark:text-white truncate max-w-[200px] sm:max-w-md">
                {crumb.label}
              </span>
            ) : (
              <Link
                href={crumb.href}
                className="text-slate-500 dark:text-gray-400 hover:text-[#D20A13] dark:hover:text-[#E50914] transition-colors"
              >
                {crumb.label}
              </Link>
            )}
          </div>
        ))}
      </div>
    </nav>
  );
}
