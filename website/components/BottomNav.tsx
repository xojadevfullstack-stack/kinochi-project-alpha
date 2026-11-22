"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export default function BottomNav() {
  const pathname = usePathname();

  // Prototipdagi 5 ta tezkor mobil bo'lim:
  // 1. Asosiy (/), 2. Sevimlilar (/subscriptions), 3. Premyera (/premieres), 4. Barchasi (/catalog), 5. To'plam (/collections)
  const navItems = [
    { label: "Asosiy", href: "/", icon: "home" },
    { label: "Sevimlilar", href: "/subscriptions", icon: "bookmark" },
    { label: "Premyera", href: "/premieres", icon: "theaters" },
    { label: "Barchasi", href: "/catalog", icon: "apps" },
    { label: "To'plam", href: "/collections", icon: "auto_awesome_motion" },
  ];

  const handleNav = (href: string) => {
    if (pathname === href && typeof window !== "undefined") {
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  };

  return (
    <nav
      className="xl:hidden fixed bottom-[calc(12px+env(safe-area-inset-bottom,0px))] left-1/2 -translate-x-1/2 w-[calc(100%-24px)] max-w-[440px] z-40 rounded-[26px] bg-white/90 dark:bg-[#12141C]/85 backdrop-blur-2xl backdrop-saturate-[180%] border border-slate-900/10 dark:border-white/15 shadow-[inset_0_1px_0_rgba(255,255,255,0.9),0_12px_32px_rgba(15,23,42,0.12)] dark:shadow-[inset_0_1px_0_rgba(255,255,255,0.14),0_14px_38px_rgba(0,0,0,0.55)] px-2 py-1.5"
      aria-label="Mobil pastki navigatsiya"
    >
      <div className="w-full flex items-center justify-between gap-1">
        {navItems.map((item) => {
          const isActive =
            item.href === "/"
              ? pathname === "/"
              : pathname.startsWith(item.href);

          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={() => handleNav(item.href)}
              className={`flex-1 flex flex-col items-center justify-center gap-1 py-1 px-1 rounded-xl transition-all cursor-pointer relative group ${
                isActive
                  ? "text-[#D20A13] dark:text-[#E50914] font-semibold"
                  : "text-slate-600 dark:text-text-secondary hover:text-slate-900 dark:hover:text-white"
              }`}
            >
              <div className="relative flex items-center justify-center">
                <span
                  className={`material-symbols-outlined text-[21px] transition-colors ${
                    isActive
                      ? "text-[#D20A13] dark:text-[#E50914]"
                      : "text-slate-600 dark:text-text-secondary group-hover:text-slate-900 dark:group-hover:text-white"
                  }`}
                  style={{
                    fontVariationSettings: isActive ? "'FILL' 1" : "'FILL' 0",
                  }}
                >
                  {item.icon}
                </span>
              </div>
              <span className="text-[10px] sm:text-[11px] tracking-tight leading-none truncate max-w-[68px]">
                {item.label}
              </span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
