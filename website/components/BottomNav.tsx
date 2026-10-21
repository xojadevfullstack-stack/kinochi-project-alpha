"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

export default function BottomNav() {
  const pathname = usePathname();
  const [searchTab, setSearchTab] = useState<string>("");

  useEffect(() => {
    const updateTab = () => {
      if (typeof window !== "undefined") {
        const params = new URLSearchParams(window.location.search);
        setSearchTab(params.get("tab") || "");
      }
    };
    updateTab();
    window.addEventListener("popstate", updateTab);
    return () => window.removeEventListener("popstate", updateTab);
  }, [pathname]);

  // Exactly 5 clean tabs:
  // 1. Bosh sahifa
  // 2. Obunalar (/profile?tab=subscriptions)
  // 3. Katalog (/catalog)
  // 4. Premyera (/movies)
  // 5. Profil (/profile)
  const navItems = [
    { label: "Bosh sahifa", href: "/", icon: "home" },
    { label: "Obunalar", href: "/profile?tab=subscriptions", icon: "loyalty" },
    { label: "Katalog", href: "/catalog", icon: "grid_view" },
    { label: "Premyera", href: "/movies", icon: "theaters" },
    { label: "Profil", href: "/profile", icon: "account_circle" },
  ];

  const handleNav = (href: string) => {
    if (href.includes("tab=subscriptions")) {
      setSearchTab("subscriptions");
    } else if (href === "/profile") {
      setSearchTab("");
    }
    if (pathname === href.split("?")[0] && typeof window !== "undefined") {
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  };

  const isSubTab = searchTab === "subscriptions";

  return (
    <nav
      className="xl:hidden fixed bottom-0 left-0 right-0 z-40 bg-background-obsidian/95 backdrop-blur-2xl border-t border-white/10 shadow-[0_-10px_30px_rgba(0,0,0,0.85)] pb-[env(safe-area-inset-bottom,0.5rem)]"
      aria-label="Mobil pastki navigatsiya"
    >
      <div className="max-w-md mx-auto px-2 sm:px-4 py-2 flex items-center justify-between">
        {navItems.map((item) => {
          const isActive =
            item.href === "/"
              ? pathname === "/"
              : item.href.includes("tab=subscriptions")
                ? pathname === "/profile" && isSubTab
                : item.href === "/profile"
                  ? pathname === "/profile" && !isSubTab
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
