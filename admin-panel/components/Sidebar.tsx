"use client";

import Link from 'next/link';
import { useRouter, usePathname } from 'next/navigation';

const API_URL = "/api/v1";

export default function Sidebar() {
  const router = useRouter();
  const pathname = usePathname();

  const handleLogout = async () => {
    try {
      await fetch(`${API_URL}/auth/logout`, {
        method: "POST",
        credentials: "include",
      });
    } catch (e) {
      // Even if request fails, redirect to login
    }
    localStorage.removeItem("access_token");
    document.cookie = "access_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
    router.push("/login");
  };

  const navItems = [
    { name: "Dashboard", href: "/", icon: "dashboard" },
    { name: "Kinolar", href: "/movies", icon: "movie" },
    { name: "Seriallar", href: "/series", icon: "live_tv" },
    { name: "Kategoriyalar", href: "/categories", icon: "category" },
    { name: "Sahifalar", href: "/pages", icon: "pages" },
    { name: "Kanallar", href: "/channels", icon: "hub" },
    { name: "Manbalar", href: "/sources", icon: "source" },
    { name: "Xabarnomalar", href: "/broadcasts", icon: "podcasts" },
  ];

  return (
    <nav className="h-screen w-[280px] fixed left-0 top-0 bg-surface-container-lowest border-r border-white/5 flex flex-col z-40">
      {/* Brand / Header */}
      <div className="p-gutter border-b border-white/5 flex items-center gap-4">
        <div className="w-12 h-12 rounded-full overflow-hidden border-2 border-primary-container bg-surface-container-high flex justify-center items-center">
          <span className="material-symbols-outlined text-primary-container text-2xl">admin_panel_settings</span>
        </div>
        <div>
          <h1 className="font-headline-md text-xl text-primary-container">Kinochi Admin</h1>
          <p className="font-label-caps text-[10px] text-text-secondary mt-1 uppercase tracking-widest">System Controller</p>
        </div>
      </div>
      
      {/* Navigation Links */}
      <div className="flex-1 py-stack-md overflow-y-auto">
        <ul className="space-y-2">
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            return (
              <li key={item.name}>
                <Link 
                  href={item.href}
                  className={`flex items-center gap-4 p-4 font-label-caps text-sm uppercase tracking-wider transition-all ${
                    isActive 
                      ? 'bg-primary-container/10 text-primary-container border-l-4 border-primary-container active:scale-95' 
                      : 'text-on-secondary-container hover:bg-white/5 hover:text-text-primary border-l-4 border-transparent'
                  }`}
                >
                  <span className="material-symbols-outlined" style={{ fontVariationSettings: isActive ? "'FILL' 1" : "'FILL' 0" }}>
                    {item.icon}
                  </span>
                  <span>{item.name}</span>
                </Link>
              </li>
            );
          })}
        </ul>
      </div>
      
      {/* CTA / Logout */}
      <div className="p-gutter border-t border-white/5">
        <button 
          onClick={handleLogout}
          className="w-full bg-white/5 border border-white/10 hover:bg-red-500/20 hover:border-red-500/50 hover:text-red-500 text-on-secondary-container font-label-caps text-sm py-3 rounded-full hover:scale-105 transition-all duration-300 ease-out flex items-center justify-center gap-2"
        >
          <span className="material-symbols-outlined">logout</span>
          Chiqish
        </button>
      </div>
    </nav>
  );
}
