"use client";

import { useState, useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import Sidebar from "@/components/Sidebar";

const API_URL = "/api/v1";

export default function AdminShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  // Close mobile drawer whenever pathname changes
  useEffect(() => {
    setIsMobileMenuOpen(false);
  }, [pathname]);

  // Lock body scroll when mobile drawer is open
  useEffect(() => {
    if (isMobileMenuOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "auto";
    }
    return () => {
      document.body.style.overflow = "auto";
    };
  }, [isMobileMenuOpen]);

  // If on /login page, don't show admin sidebar or mobile header
  if (pathname === "/login") {
    return <main className="w-full min-h-screen">{children}</main>;
  }

  const handleLogout = async () => {
    try {
      await fetch(`${API_URL}/auth/logout`, {
        method: "POST",
        credentials: "include",
      });
    } catch (e) {
      // Ignore
    }
    localStorage.removeItem("access_token");
    document.cookie = "access_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
    router.push("/login");
  };

  // Derive human-friendly title from pathname
  const getPageTitle = () => {
    if (pathname === "/") return "Dashboard";
    if (pathname.startsWith("/movies")) return "Kinolar";
    if (pathname.startsWith("/series")) return "Seriallar";
    if (pathname.startsWith("/categories")) return "Kategoriyalar";
    if (pathname.startsWith("/pages")) return "Sahifalar";
    if (pathname.startsWith("/channels")) return "Kanallar";
    if (pathname.startsWith("/sources")) return "Manbalar";
    if (pathname.startsWith("/broadcasts")) return "Xabarnomalar";
    return "Admin";
  };

  return (
    <div className="min-h-screen flex flex-col lg:flex-row w-full bg-background-obsidian text-text-primary">
      {/* Mobile Top Bar (Sticky Header) */}
      <header className="lg:hidden sticky top-0 z-30 bg-surface-container-lowest/95 backdrop-blur-md border-b border-white/10 px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            onClick={() => setIsMobileMenuOpen(true)}
            className="p-2 -ml-1 rounded-xl bg-white/5 border border-white/10 text-text-primary hover:bg-white/10 active:scale-95 transition-all flex items-center justify-center min-h-[40px] min-w-[40px]"
            aria-label="Menyuni ochish"
          >
            <span className="material-symbols-outlined text-2xl">menu</span>
          </button>
          
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-primary-container animate-pulse"></span>
            <span className="font-display font-bold text-base text-text-primary tracking-tight">
              {getPageTitle()}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleLogout}
            className="p-2 rounded-xl bg-white/5 border border-white/10 text-text-secondary hover:text-red-400 hover:bg-red-500/10 active:scale-95 transition-all flex items-center justify-center min-h-[40px] min-w-[40px]"
            title="Chiqish"
            aria-label="Chiqish"
          >
            <span className="material-symbols-outlined text-xl">logout</span>
          </button>
        </div>
      </header>

      {/* Dimmed Backdrop for Mobile Drawer */}
      {isMobileMenuOpen && (
        <div
          onClick={() => setIsMobileMenuOpen(false)}
          className="fixed inset-0 bg-black/75 backdrop-blur-sm z-40 lg:hidden transition-opacity"
          aria-hidden="true"
        />
      )}

      {/* Sidebar (Desktop static & Mobile slide-over drawer) */}
      <Sidebar isOpen={isMobileMenuOpen} onClose={() => setIsMobileMenuOpen(false)} />

      {/* Main Content Area */}
      <main className="lg:ml-[280px] flex-1 min-h-[calc(100vh-60px)] lg:min-h-screen bg-background-obsidian relative overflow-y-auto w-full min-w-0">
        {/* Subtle Background Glow */}
        <div className="absolute top-0 left-1/4 w-[320px] sm:w-[500px] lg:w-[800px] h-[300px] sm:h-[400px] bg-primary-container/5 rounded-full blur-[100px] pointer-events-none -z-10" />
        
        {children}
      </main>
    </div>
  );
}
