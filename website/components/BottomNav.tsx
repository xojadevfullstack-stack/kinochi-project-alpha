"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export default function BottomNav() {
  const pathname = usePathname();

  // Exactly 5 clean tabs:
  // 1. Bosh sahifa
  // 2. Obunalar (/subscriptions)
  // 3. Katalog (/catalog)
  // 4. Premyera (/premieres)
  // 5. Profil (/profile)
  const navItems = [
    { label: "Bosh sahifa", href: "/", icon: "home" },
    { label: "Obunalar", href: "/subscriptions", icon: "loyalty" },
    { label: "Katalog", href: "/catalog", icon: "grid_view" },
    { label: "Premyera", href: "/premieres", icon: "theaters" },
    { label: "Profil", href: "/profile", icon: "account_circle" },
  ];

  const handleNav = (href: string) => {
    if (pathname === href && typeof window !== "undefined") {
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  };

  return (
    <nav
      className="xl:hidden fixed bottom-[calc(12px+env(safe-area-inset-bottom,0px))] left-3 right-3 max-w-[440px] mx-auto z-40 rounded-[26px] bg-white/85 dark:bg-[#12141C]/80 backdrop-blur-2xl backdrop-saturate-[180%] border border-slate-900/10 dark:border-white/15 shadow-[inset_0_1px_0_rgba(255,255,255,0.9),0_12px_32px_rgba(15,23,42,0.12)] dark:shadow-[inset_0_1px_0_rgba(255,255,255,0.14),0_14px_38px_rgba(0,0,0,0.55)] px-2 py-1.5"
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
                  ? "text-primary-container font-semibold"
                  : "text-text-secondary hover:text-text-primary"
              }`}
            >
              <div className="relative flex items-center justify-center">
                <span
                  className={`material-symbols-outlined text-[22px] transition-colors ${
                    isActive
                      ? "text-primary-container"
                      : "text-text-secondary group-hover:text-text-primary"
                  }`}
                  style={{
                    fontVariationSettings: isActive ? "'FILL' 1" : "'FILL' 0",
                  }}
                >
                  {item.icon}
                </span>
                {isActive && (
                  <span className="absolute -bottom-1 w-1 h-1 bg-primary-container rounded-full" />
                )}
              </div>
              <span className="text-[10px] sm:text-[11px] tracking-tight leading-none truncate max-w-[64px]">
                {item.label}
              </span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
