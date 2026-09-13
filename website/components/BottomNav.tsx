"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "../lib/auth/AuthProvider";

export default function BottomNav() {
  const pathname = usePathname();
  const { status, user } = useAuth();

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
          const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
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
                  className={`material-symbols-outlined text-[23px] transition-transform ${
                    isActive ? "scale-110 drop-shadow-[0_0_8px_rgba(229,9,20,0.8)]" : "group-hover:scale-105"
                  }`}
                  style={{ fontVariationSettings: isActive ? "'FILL' 1" : "'FILL' 0" }}
                >
                  {item.icon}
                </span>
                {isActive && (
                  <span className="absolute -bottom-1 w-1 h-1 bg-primary-container rounded-full shadow-[0_0_6px_rgba(229,9,20,1)]"></span>
                )}
              </div>
              <span className="text-[11px] tracking-tight">{item.label}</span>
            </Link>
          );
        })}

        {/* Profile Button */}
        <button
          onClick={handleProfileClick}
          className="flex flex-col items-center justify-center gap-0.5 py-1 px-3 rounded-xl text-text-secondary hover:text-text-primary transition-all cursor-pointer group"
          aria-label="Profil"
        >
          <div className="w-6 h-6 rounded-full overflow-hidden border border-white/20 group-hover:border-primary-container transition-colors bg-white/10 flex items-center justify-center text-[11px] font-bold text-primary-container">
            {status === "authenticated" ? (
              user?.first_name?.charAt(0) || "U"
            ) : (
              <span className="material-symbols-outlined text-[16px] text-text-secondary group-hover:text-primary-container">person</span>
            )}
          </div>
          <span className="text-[11px] tracking-tight">Profil</span>
        </button>
      </div>
    </nav>
  );
}
