"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
export default function BottomNav() {
  const pathname = usePathname();

  const navItems = [
    { label: "Asosiy", href: "/", icon: "home" },
    { label: "Katalog", href: "/movies", icon: "movie" },
    { label: "Qidiruv", href: "/search", icon: "search" },
    { label: "Tarix", href: "/history", icon: "history" },
  ];

  const handleProfileClick = () => {
    if (typeof window !== "undefined") {
      window.dispatchEvent(new CustomEvent("kinochi_toggle_profile"));
    }
  };

  return (
    <nav 
      className="xl:hidden fixed bottom-0 left-0 right-0 z-40 bg-background-obsidian/95 backdrop-blur-2xl border-t border-white/10 shadow-[0_-10px_30px_rgba(0,0,0,0.8)] pb-[env(safe-area-inset-bottom,0.5rem)]"
      aria-label="Mobil pastki navigatsiya"
    >
      <div className="max-w-md mx-auto px-4 py-2 flex items-center justify-around">
        {navItems.map((item) => {
          const isKatalog = item.label === "Katalog";
          const isActive = isKatalog
            ? pathname.startsWith("/movies") || pathname.startsWith("/series") || pathname.startsWith("/p/") || pathname.startsWith("/category/") || pathname.startsWith("/catalog")
            : pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex flex-col items-center justify-center gap-0.5 py-1 px-3 rounded-xl transition-all cursor-pointer relative group ${
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
              <span className="text-[11px] tracking-tight">{item.label}</span>
            </Link>
          );
        })}

        {/* Profile Button - Standardized icon matching other 4 tabs */}
        <button
          onClick={handleProfileClick}
          className="flex flex-col items-center justify-center gap-0.5 py-1 px-3 rounded-xl text-text-secondary hover:text-text-primary transition-all cursor-pointer group"
          aria-label="Profil"
        >
          <div className="relative flex items-center justify-center">
            <span 
              className="material-symbols-outlined text-[23px] text-text-secondary group-hover:text-text-primary transition-colors"
              style={{ fontVariationSettings: "'FILL' 0" }}
            >
              person
            </span>
          </div>
          <span className="text-[11px] tracking-tight">Profil</span>
        </button>
      </div>
    </nav>
  );
}
