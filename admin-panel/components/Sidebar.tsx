"use client";

import Link from 'next/link';
import { useRouter, usePathname } from 'next/navigation';

const API_URL = "/api/v1";

interface SidebarProps {
  isOpen?: boolean;
  onClose?: () => void;
}

interface NavItem {
  name: string;
  href: string;
  icon: string;
}

interface NavSection {
  title: string | null;
  items: NavItem[];
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

  const navSections: NavSection[] = [
    {
      title: null,
      items: [
        { name: "Dashboard", href: "/", icon: "dashboard" },
      ],
    },
    {
      title: "Media & Katalog",
      items: [
        { name: "Kinolar", href: "/movies", icon: "movie" },
        { name: "Seriallar", href: "/series", icon: "live_tv" },
        { name: "Xronologiyalar", href: "/collections", icon: "auto_awesome_motion" },
        { name: "Kategoriyalar", href: "/categories", icon: "category" },
        { name: "Sahifalar", href: "/pages", icon: "pages" },
      ],
    },
    {
      title: "Moderatsiya",
      items: [
        { name: "Kontent Auditi", href: "/audit", icon: "fact_check" },
        { name: "Rad Etilganlar", href: "/rejected", icon: "rule_folder" },
        { name: "Qora Ro'yxat", href: "/blacklist", icon: "block" },
        { name: "Shikoyatlar", href: "/reports", icon: "report_problem" },
      ],
    },
    {
      title: "Avtomatizatsiya",
      items: [
        { name: "Parser & Grabber", href: "/scraper", icon: "smart_toy" },
        { name: "Doner Kanallar", href: "/channels", icon: "hub" },
        { name: "Manbalar", href: "/sources", icon: "source" },
      ],
    },
    {
      title: "Aloqa",
      items: [
        { name: "Xabarnomalar", href: "/broadcasts", icon: "podcasts" },
      ],
    },
  ];

  return (
    <aside 
      className={`fixed top-0 bottom-0 left-0 z-50 w-[270px] bg-surface-container-lowest border-r border-white/5 flex flex-col transition-transform duration-300 ease-in-out lg:translate-x-0 ${
        isOpen ? "translate-x-0 shadow-2xl" : "-translate-x-full"
      }`}
    >
      {/* Brand / Header */}
      <div className="p-4 border-b border-white/5 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-full overflow-hidden border-2 border-primary-container bg-surface-container-high flex justify-center items-center shrink-0">
            <span className="material-symbols-outlined text-primary-container text-lg">admin_panel_settings</span>
          </div>
          <div>
            <h1 className="font-headline-md text-base text-primary-container leading-none font-bold">Kinochi Admin</h1>
            <p className="font-label-caps text-[9px] text-text-secondary mt-1 uppercase tracking-widest">Control Center</p>
          </div>
        </div>

        {/* Close Button on Mobile */}
        <button
          onClick={onClose}
          className="lg:hidden p-1.5 rounded-lg text-text-secondary hover:text-white hover:bg-white/5 transition-colors"
          aria-label="Menyuni yopish"
        >
          <span className="material-symbols-outlined text-xl">close</span>
        </button>
      </div>
      
      {/* Grouped Navigation Links */}
      <div className="flex-1 py-2 overflow-y-auto px-2 custom-scrollbar">
        {navSections.map((section, sIdx) => (
          <div key={section.title || `sec_${sIdx}`} className="mb-2">
            {section.title && (
              <div className="text-[10px] font-bold text-text-secondary/60 uppercase tracking-widest px-3 pt-2.5 pb-1 flex items-center justify-between">
                <span>{section.title}</span>
                <span className="w-8 h-[1px] bg-white/5"></span>
              </div>
            )}
            <ul className="space-y-0.5">
              {section.items.map((item) => {
                const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
                return (
                  <li key={item.name}>
                    <Link 
                      href={item.href}
                      onClick={() => onClose?.()}
                      className={`flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-medium tracking-wide transition-all ${
                        isActive 
                          ? 'bg-primary-container/15 text-primary-container font-bold border-l-[3px] border-primary-container shadow-sm' 
                          : 'text-on-secondary-container hover:bg-white/5 hover:text-text-primary border-l-[3px] border-transparent'
                      }`}
                    >
                      <span 
                        className="material-symbols-outlined text-lg shrink-0" 
                        style={{ fontVariationSettings: isActive ? "'FILL' 1" : "'FILL' 0" }}
                      >
                        {item.icon}
                      </span>
                      <span className="truncate">{item.name}</span>
                    </Link>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </div>
      
      {/* CTA / Logout */}
      <div className="p-3 border-t border-white/5 shrink-0">
        <button 
          onClick={handleLogout}
          className="w-full bg-white/5 border border-white/10 hover:bg-red-500/20 hover:border-red-500/40 hover:text-red-400 text-text-secondary text-xs font-semibold py-2.5 rounded-xl hover:scale-[1.01] active:scale-95 transition-all duration-150 flex items-center justify-center gap-2"
        >
          <span className="material-symbols-outlined text-base">logout</span>
          Chiqish
        </button>
      </div>
    </aside>
  );
}
