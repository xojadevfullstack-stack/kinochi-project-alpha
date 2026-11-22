"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const SEGMENT_LABELS: Record<string, string> = {
  movies: "Kinolar",
  movie: "Film",
  series: "Seriallar",
  anime: "Animelar",
  doramas: "Doramalar",
  cartoons: "Multfilmlar",
  catalog: "Katalog & Bo'limlar",
  category: "Bo'lim",
  collections: "Xronologiyalar",
  requests: "Buyurtma berish",
  tv: "Jonli TV",
  premieres: "Premyeralar",
  top100: "TOP 100",
  subscriptions: "Obunalar",
  profile: "Profil",
  history: "Ko'rish tarixi",
  notifications: "Bildirishnomalar",
  actors: "Aktyorlar",
  achievements: "Yutuqlar",
  search: "Qidiruv",
  p: "Sahifa",
  "test-auth": "Kirish",
};

function formatSegmentLabel(segment: string, prevSegment?: string): string {
  if (SEGMENT_LABELS[segment]) return SEGMENT_LABELS[segment];
  try {
    const decoded = decodeURIComponent(segment);
    if (prevSegment === "movie") return `#${decoded}`;
    return decoded
      .replace(/[-_]+/g, " ")
      .replace(/\b\w/g, (ch) => ch.toUpperCase());
  } catch {
    return segment;
  }
}

export default function Breadcrumb() {
  const pathname = usePathname();

  if (!pathname || pathname === "/") {
    return null;
  }

  const segments = pathname.split("/").filter(Boolean);
  if (segments.length === 0) return null;

  const crumbs = segments.map((seg, idx) => {
    const href = "/" + segments.slice(0, idx + 1).join("/");
    // Avoid broken parent links for virtual prefixes (/movie/[code], /category/[id], /p/[slug])
    const resolvedHref =
      seg === "movie" || seg === "category" || seg === "p" ? "/catalog" : href;
    return {
      label: formatSegmentLabel(seg, segments[idx - 1]),
      href: resolvedHref,
      isLast: idx === segments.length - 1,
    };
  });

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
              <span className="font-semibold text-slate-900 dark:text-white truncate max-w-[200px] sm:max-w-xs">
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
