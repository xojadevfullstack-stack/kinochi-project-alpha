import Link from "next/link";

interface PageItem {
  id: number | string;
  title: string;
  slug: string;
  is_active?: boolean;
}

interface CatalogTypeNavProps {
  currentType: "movies" | "series" | string;
  pages?: PageItem[];
}

function getPageIcon(title: string): string {
  const t = title.toLowerCase();
  if (t.includes("anime")) return "animation";
  if (t.includes("dorama") || t.includes("koreys")) return "theater_comedy";
  if (t.includes("mult") || t.includes("kartun") || t.includes("bolalar")) return "smart_toy";
  if (t.includes("marvel") || t.includes("dc") || t.includes("komiks")) return "shield";
  if (t.includes("turk")) return "language";
  if (t.includes("retro") || t.includes("klassik")) return "videocam";
  if (t.includes("top") || t.includes("hit") || t.includes("trend")) return "local_fire_department";
  if (t.includes("hujjatli") || t.includes("doc")) return "history_edu";
  if (t.includes("fantastik")) return "rocket_launch";
  if (t.includes("jangari") || t.includes("jang")) return "military_tech";
  if (t.includes("horror") || t.includes("qo'rqinchli")) return "skull";
  return "category";
}

export default function CatalogTypeNav({ currentType, pages = [] }: CatalogTypeNavProps) {
  const baseItems = [
    { label: "Kinolar", href: "/movies", icon: "movie", key: "movies" },
    { label: "Seriallar", href: "/series", icon: "tv", key: "series" },
  ];

  const activePages = pages.filter((p) => p.is_active !== false);

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
              className={`px-4 sm:px-5 py-2.5 rounded-xl text-xs sm:text-sm font-semibold transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5 active:scale-95 shrink-0 flex items-center gap-2 border ${
                isActive
                  ? "bg-white/20 text-white border-white/30 shadow-lg shadow-black/20 font-bold backdrop-blur-md"
                  : "bg-white/5 border-white/10 text-text-secondary hover:text-text-primary hover:bg-white/10"
              }`}
            >
              <span className="material-symbols-outlined text-[18px]">{item.icon}</span>
              <span>{item.label}</span>
            </Link>
          );
        })}

        {/* Dynamic Pages: Anime, Dorama, and any page added via Admin Panel */}
        {activePages.map((page) => {
          const isActive = currentType === page.slug;
          return (
            <Link
              key={page.slug}
              href={`/p/${page.slug}`}
              className={`px-4 sm:px-5 py-2.5 rounded-xl text-xs sm:text-sm font-semibold transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5 active:scale-95 shrink-0 flex items-center gap-2 border ${
                isActive
                  ? "bg-white/20 text-white border-white/30 shadow-lg shadow-black/20 font-bold backdrop-blur-md"
                  : "bg-white/5 border-white/10 text-text-secondary hover:text-text-primary hover:bg-white/10"
              }`}
            >
              <span className="material-symbols-outlined text-[18px]">{getPageIcon(page.title)}</span>
              <span>{page.title}</span>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
