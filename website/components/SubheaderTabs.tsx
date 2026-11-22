"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useRef } from "react";

const QUICK_TABS = [
  { label: "Kinolar", href: "/movies", icon: "movie" },
  { label: "Seriallar", href: "/series", icon: "tv" },
  { label: "Animelar", href: "/anime", icon: "animation" },
  { label: "Doramalar", href: "/doramas", icon: "theater_comedy" },
  { label: "Multfilmlar", href: "/cartoons", icon: "child_care" },
  { label: "Bo'limlar", href: "/catalog", icon: "category" },
  { label: "Buyurtma berish", href: "/requests", icon: "add_box" },
  { label: "Xronologiyalar", href: "/collections", icon: "timeline" },
  { label: "Jonli TV", href: "/tv", icon: "live_tv" },
];

export default function SubheaderTabs() {
  const pathname = usePathname();
  const scrollRef = useRef<HTMLDivElement>(null);

  const scrollTabs = (dir: -1 | 1) => {
    scrollRef.current?.scrollBy({ left: dir * 240, behavior: "smooth" });
  };

  return (
    <div className="master-subheader-bar w-full bg-transparent pt-[72px] sm:pt-[82px] pb-1.5">
      <div className="max-w-container-max mx-auto px-gutter flex items-center justify-between gap-2">
        <div
          ref={scrollRef}
          className="flex items-center gap-1.5 overflow-x-auto hide-scrollbar scroll-smooth flex-1 py-0.5"
        >
          {QUICK_TABS.map((tab) => {
            const isActive =
              pathname === tab.href ||
              (tab.href !== "/" && pathname?.startsWith(`${tab.href}/`));

            return (
              <Link
                key={tab.href}
                href={tab.href}
                className={`nav-tab flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-medium shrink-0 border transition-all duration-200 ${
                  isActive
                    ? "bg-[#D20A13] dark:bg-[#E50914] border-[#D20A13] dark:border-[#E50914] text-white shadow-md shadow-primary/25 font-semibold"
                    : "bg-white/85 dark:bg-[#1A1C24]/90 border-slate-300/80 dark:border-white/10 text-slate-700 dark:text-gray-300 hover:bg-[#B80710] dark:hover:bg-[#E50914] hover:border-[#B80710] dark:hover:border-[#E50914] hover:text-white"
                }`}
              >
                <span className="material-symbols-outlined text-[15px]">
                  {tab.icon}
                </span>
                <span>{tab.label}</span>
              </Link>
            );
          })}
        </div>

        {/* Desktop horizontal scroll controls */}
        <div className="hidden lg:flex items-center gap-1 shrink-0 pl-2">
          <button
            type="button"
            onClick={() => scrollTabs(-1)}
            className="w-7 h-7 rounded-full bg-white/85 dark:bg-[#141722] border border-slate-300/80 dark:border-white/10 text-slate-700 dark:text-gray-300 hover:bg-[#B80710] dark:hover:bg-[#E50914] hover:border-[#B80710] dark:hover:border-[#E50914] hover:text-white flex items-center justify-center transition cursor-pointer"
            aria-label="Chapga surish"
            title="Chapga"
          >
            <span className="material-symbols-outlined text-[16px]">
              chevron_left
            </span>
          </button>
          <button
            type="button"
            onClick={() => scrollTabs(1)}
            className="w-7 h-7 rounded-full bg-white/85 dark:bg-[#141722] border border-slate-300/80 dark:border-white/10 text-slate-700 dark:text-gray-300 hover:bg-[#B80710] dark:hover:bg-[#E50914] hover:border-[#B80710] dark:hover:border-[#E50914] hover:text-white flex items-center justify-center transition cursor-pointer"
            aria-label="O'ngga surish"
            title="O'ngga"
          >
            <span className="material-symbols-outlined text-[16px]">
              chevron_right
            </span>
          </button>
        </div>
      </div>
    </div>
  );
}
