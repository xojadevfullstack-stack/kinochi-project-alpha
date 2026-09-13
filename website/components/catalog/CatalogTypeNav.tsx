import Link from "next/link";

interface PageItem {
  id: number | string;
  title: string;
  slug: string;
}

interface CatalogTypeNavProps {
  currentType: "movies" | "series" | string;
  pages?: PageItem[];
}

function getPageIcon(title: string) {
  const t = title.toLowerCase();
  if (t.includes("anime")) return "🎌";
  if (t.includes("dorama")) return "🎭";
  if (t.includes("mult")) return "🧸";
  return "📂";
}

export default function CatalogTypeNav({ currentType, pages = [] }: CatalogTypeNavProps) {
  const baseItems = [
    { label: "Kinolar", href: "/movies", icon: "🎬", key: "movies" },
    { label: "Seriallar", href: "/series", icon: "📺", key: "series" },
  ];

  return (
    <div className="relative w-full mb-4">
      <div className="flex items-center gap-2 overflow-x-auto pb-2 pt-1 hide-scrollbar scroll-smooth">
        {/* Core items: Kinolar & Seriallar */}
        {baseItems.map((item) => {
          const isActive = currentType === item.key;
          return (
            <Link
              key={item.key}
              href={item.href}
              className={`px-4 sm:px-5 py-2.5 rounded-xl text-xs sm:text-sm font-semibold transition-all shrink-0 flex items-center gap-2 border active:scale-95 ${
                isActive
                  ? "bg-white/20 text-white border-white/30 shadow-lg shadow-black/20 font-bold backdrop-blur-md"
                  : "bg-white/5 border-white/10 text-text-secondary hover:text-text-primary hover:bg-white/10"
              }`}
            >
              <span className="text-[15px]">{item.icon}</span>
              <span>{item.label}</span>
            </Link>
          );
        })}

        {/* Dynamic Pages: Anime, Dorama, etc. */}
        {pages.map((page) => {
          const isActive = currentType === page.slug;
          return (
            <Link
              key={page.slug}
              href={`/p/${page.slug}`}
              className={`px-4 sm:px-5 py-2.5 rounded-xl text-xs sm:text-sm font-semibold transition-all shrink-0 flex items-center gap-2 border active:scale-95 ${
                isActive
                  ? "bg-white/20 text-white border-white/30 shadow-lg shadow-black/20 font-bold backdrop-blur-md"
                  : "bg-white/5 border-white/10 text-text-secondary hover:text-text-primary hover:bg-white/10"
              }`}
            >
              <span className="text-[15px]">{getPageIcon(page.title)}</span>
              <span>{page.title}</span>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
