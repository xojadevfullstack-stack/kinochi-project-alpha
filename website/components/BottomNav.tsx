"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export default function BottomNav() {
  const pathname = usePathname();

  // 5 ta asosiy mobil pastki menyu:
  // 1. Bosh sahifa, 2. Obunalar, 3. Katalog (To'laqonli page!), 4. Premyeralar, 5. Profil (To'laqonli page!)
  const navItems = [
    { label: "Bosh sahifa", href: "/", icon: "home" },
    { label: "Obunalar", href: "/achievements", icon: "loyalty" },
    { label: "Katalog", href: "/catalog", icon: "grid_view" },
    { label: "Premyera", href: "/movies", icon: "theaters" },
    { label: "Profil", href: "/profile", icon: "person" },
  ];

  const handleNav = (href: string) => {
    if (pathname === href && typeof window !== "undefined") {
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  };

  return (
    <nav 
      className="xl:hidden fixed bottom-0 left-0 right-0 z-40 bg-background-obsidian/95 backdrop-blur-2xl border-t border-white/10 shadow-[0_-10px_30px_rgba(0,0,0,0.8)] pb-[env(safe-area-inset-bottom,0.5rem)]"
      aria-label="Mobil pastki navigatsiya"
    >
      <div className="max-w-md mx-auto px-2 sm:px-4 py-2 flex items-center justify-around">
        {navItems.map((item) => {
          const isKatalog = item.label === "Katalog";
          const isProfile = item.label === "Profil";
          const isPremyera = item.label === "Premyera";

          let isActive = false;
          if (item.href === "/") {
            isActive = pathname === "/";
          } else if (isKatalog) {
            isActive = pathname.startsWith("/catalog") || pathname.startsWith("/category/") || pathname.startsWith("/p/");
          } else if (isProfile) {
            isActive = pathname.startsWith("/profile") || pathname.startsWith("/history");
          } else if (isPremyera) {
            isActive = pathname.startsWith("/movies") || pathname.startsWith("/series");
          } else {
            isActive = pathname.startsWith(item.href);
          }

          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={() => handleNav(item.href)}
              className={`flex flex-col items-center justify-center gap-0.5 py-1 px-2.5 rounded-xl transition-all cursor-pointer relative group ${
                isActive ? "text-primary-container font-bold" : "text-text-secondary hover:text-text-primary"
              }`}
            >
              <div className="relative flex items-center justify-center">
                <span 
                  className={`material-symbols-outlined text-[23px] transition-colors ${
                    isActive ? "text-primary-container" : "text-text-secondary group-hover:text-text-primary"
                  }`}
                  style={{ fontVariationSettings: isActive ? "'FILL' 1" : "'FILL' 0" }}
                >
                  {item.icon}
                </span>
                {isActive && (
                  <span className="absolute -bottom-1 w-1 h-1 bg-primary-container rounded-full"></span>
                )}
              </div>
              <span className="text-[10px] sm:text-[11px] tracking-tight">{item.label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
