"use client";

import Link from 'next/link';
import { useRouter, usePathname } from 'next/navigation';

const API_URL = "/api/v1";

interface SidebarProps {
  isOpen?: boolean;
  onClose?: () => void;
}

export default function Sidebar({ isOpen = false, onClose }: SidebarProps) {
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
    <aside 
      className={`fixed top-0 bottom-0 left-0 z-50 w-[280px] bg-surface-container-lowest border-r border-white/5 flex flex-col transition-transform duration-300 ease-in-out lg:translate-x-0 ${
        isOpen ? "translate-x-0 shadow-2xl" : "-translate-x-full"
      }`}
    >
      {/* Brand / Header */}
      <div className="p-4 sm:p-5 border-b border-white/5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full overflow-hidden border-2 border-primary-container bg-surface-container-high flex justify-center items-center shrink-0">
            <span className="material-symbols-outlined text-primary-container text-xl">admin_panel_settings</span>
          </div>
          <div>
            <h1 className="font-headline-md text-lg text-primary-container leading-none">MediaPlus Admin</h1>
            <p className="font-label-caps text-[9px] text-text-secondary mt-1 uppercase tracking-widest">System Controller</p>
          </div>
        </div>

        {/* Close Button on Mobile */}
        <button
          onClick={onClose}
          className="lg:hidden p-2 rounded-lg text-text-secondary hover:text-white hover:bg-white/5 transition-colors"
          aria-label="Menyuni yopish"
        >
          <span className="material-symbols-outlined text-2xl">close</span>
        </button>
      </div>
      
      {/* Navigation Links */}
      <div className="flex-1 py-3 overflow-y-auto px-2">
        <ul className="space-y-1">
          {navItems.map((item) => {
            const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
            return (
              <li key={item.name}>
                <Link 
                  href={item.href}
                  onClick={() => onClose?.()}
                  className={`flex items-center gap-3.5 px-3.5 py-3 rounded-xl font-label-caps text-xs uppercase tracking-wider transition-all min-h-[44px] ${
                    isActive 
                      ? 'bg-primary-container/15 text-primary-container font-bold border-l-4 border-primary-container' 
                      : 'text-on-secondary-container hover:bg-white/5 hover:text-text-primary border-l-4 border-transparent'
                  }`}
                >
                  <span 
                    className="material-symbols-outlined text-xl" 
                    style={{ fontVariationSettings: isActive ? "'FILL' 1" : "'FILL' 0" }}
                  >
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
      <div className="p-4 border-t border-white/5">
        <button 
          onClick={handleLogout}
          className="w-full bg-white/5 border border-white/10 hover:bg-red-500/20 hover:border-red-500/50 hover:text-red-400 text-on-secondary-container font-label-caps text-xs py-3 rounded-xl hover:scale-[1.02] active:scale-95 transition-all duration-200 ease-out flex items-center justify-center gap-2 min-h-[44px]"
        >
          <span className="material-symbols-outlined text-lg">logout</span>
          Chiqish
        </button>
      </div>
    </aside>
  );
}
