"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState, useEffect, useRef } from "react";
import { useAuth } from "../lib/auth/AuthProvider";
import TelegramLoginWidget from "./auth/TelegramLoginWidget";

export default function Navbar({ pages = [] }: { pages: any[] }) {
  const pathname = usePathname();
  const router = useRouter();
  const { status, user, logout, loginDirect } = useAuth();
  const [isScrolled, setIsScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [hoveredLink, setHoveredLink] = useState<string | null>(null);
  const [profileDropdownOpen, setProfileDropdownOpen] = useState(false);
  const profileDropdownRef = useRef<HTMLDivElement>(null);

  // Close desktop profile dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (profileDropdownRef.current && !profileDropdownRef.current.contains(event.target as Node)) {
        setProfileDropdownOpen(false);
      }
    };
    if (profileDropdownOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [profileDropdownOpen]);

  // Handle scroll for navbar background
  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      router.push(`/search?q=${encodeURIComponent(searchQuery)}`);
      setMobileMenuOpen(false);
    }
  };

  const navLinks = [
    { name: "Bosh sahifa", href: "/" },
    { name: "Kinolar", href: "/movies" },
    { name: "Seriallar", href: "/series" },
    ...pages.map(p => ({ name: p.title, href: `/p/${p.slug}` }))
  ];

  return (
    <nav 
      className={`fixed top-0 w-full z-50 transition-all duration-300 ease-out border-b ${
        isScrolled 
          ? "bg-background-obsidian/90 backdrop-blur-lg border-white/10 shadow-2xl shadow-primary-container/10 py-3" 
          : "bg-gradient-to-b from-background-obsidian/80 to-transparent border-transparent py-5"
      }`}
    >
      <div className="max-w-container-max mx-auto px-gutter flex justify-between items-center">
        {/* Left: Logo */}
        <Link href="/" className="font-display-hero-mobile text-[28px] sm:text-[32px] text-primary-container tracking-tighter hover:scale-105 transition-transform z-50 relative shrink-0">
          Kinochi
        </Link>

        {/* Center: Desktop Navigation */}
        <div 
          className="hidden md:flex flex-1 justify-center items-center gap-8"
          onMouseLeave={() => setHoveredLink(null)}
        >
          {navLinks.map((link) => {
            const isActive = pathname === link.href || (link.href !== '/' && pathname.startsWith(link.href));
            const showLine = hoveredLink ? hoveredLink === link.name : isActive;
            
            return (
              <Link
                key={link.name}
                href={link.href}
                className="relative group px-2 py-1 font-bold text-[15px] transition-colors"
                onMouseEnter={() => setHoveredLink(link.name)}
              >
                <span className={`transition-colors duration-300 ${isActive ? "text-primary-container" : "text-on-secondary-container group-hover:text-text-primary"}`}>
                  {link.name}
                </span>
                <span 
                  className={`absolute -bottom-2 left-0 h-[2px] bg-primary-container transition-all duration-300 ${
                    showLine ? "w-full opacity-100" : "w-0 opacity-0"
                  }`}
                />
              </Link>
            );
          })}
        </div>

        {/* Right: Search & Profile */}
        <div className="flex items-center gap-3 md:gap-4 shrink-0 z-50 relative">
          {/* Desktop Search */}
          <form onSubmit={handleSearch} className="hidden md:flex items-center bg-white/5 hover:bg-white/10 rounded-full px-4 py-2 border border-white/5 focus-within:border-white/30 focus-within:bg-white/10 transition-all">
            <span className="material-symbols-outlined text-text-secondary mr-2 text-[20px]" style={{ fontVariationSettings: "'FILL' 0" }}>search</span>
            <input 
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="bg-transparent border-none focus:ring-0 text-text-primary text-sm placeholder:text-text-secondary w-32 lg:w-48 outline-none" 
              placeholder="Qidirish..." 
            />
          </form>
          <Link 
            href="/notifications"
            className="relative hidden md:flex w-9 h-9 md:w-10 md:h-10 rounded-full overflow-hidden border border-white/10 hover:border-primary-container transition-colors cursor-pointer bg-white/5 items-center justify-center group"
          >
            <span className="material-symbols-outlined text-text-secondary group-hover:text-primary-container text-[20px] transition-colors" style={{ fontVariationSettings: "'FILL' 0" }}>notifications</span>
            <span className="absolute top-2 right-2 w-2 h-2 bg-primary-container rounded-full animate-pulse"></span>
          </Link>
          
          <div className="relative" ref={profileDropdownRef}>
            <div 
              onClick={() => {
                setProfileDropdownOpen(!profileDropdownOpen);
                setMobileMenuOpen(false);
              }}
              className="w-9 h-9 md:w-10 md:h-10 rounded-full overflow-hidden border border-white/10 hover:border-primary-container transition-colors cursor-pointer bg-white/5 flex items-center justify-center">
              {status === "authenticated" ? (
                <span className="font-bold text-sm text-primary-container">{user?.first_name?.charAt(0) || "U"}</span>
              ) : (
                <span className="material-symbols-outlined text-text-secondary">person</span>
              )}
            </div>
            
            {/* Desktop Dropdown */}
            {profileDropdownOpen && (
              <div className="hidden md:block absolute right-0 mt-2 w-72 bg-background-obsidian/95 backdrop-blur-xl border border-white/10 rounded-2xl p-4 shadow-2xl z-50">
                {status === "authenticated" ? (
                  <div className="flex flex-col gap-3">
                    <div className="flex items-center gap-3 border-b border-white/10 pb-3">
                      <div className="w-10 h-10 rounded-full bg-primary-container/20 flex items-center justify-center text-primary-container font-bold shrink-0">
                        {user?.first_name?.charAt(0) || "U"}
                      </div>
                      <div className="overflow-hidden">
                        <div className="font-bold text-text-primary truncate">{user?.first_name} {user?.last_name}</div>
                        <div className="text-xs text-text-secondary truncate">@{user?.username || user?.id}</div>
                      </div>
                    </div>
                    <Link
                      href="/history"
                      onClick={() => setProfileDropdownOpen(false)}
                      className="flex items-center gap-2.5 text-sm text-text-primary hover:text-primary-container py-2 px-2 rounded-lg hover:bg-white/5 transition-all font-medium"
                    >
                      <span className="material-symbols-outlined text-[20px] text-primary-container">history</span>
                      Ko'rish tarixi
                    </Link>
                    <Link
                      href="/achievements"
                      onClick={() => setProfileDropdownOpen(false)}
                      className="flex items-center gap-2.5 text-sm text-text-primary hover:text-primary-container py-2 px-2 rounded-lg hover:bg-white/5 transition-all font-medium"
                    >
                      <span className="material-symbols-outlined text-[20px] text-amber-400">emoji_events</span>
                      Yutuqlar
                    </Link>
                    <Link
                      href="/notifications"
                      onClick={() => setProfileDropdownOpen(false)}
                      className="flex items-center gap-2.5 text-sm text-text-primary hover:text-primary-container py-2 px-2 rounded-lg hover:bg-white/5 transition-all font-medium"
                    >
                      <span className="material-symbols-outlined text-[20px] text-blue-400">notifications</span>
                      Bildirishnomalar
                    </Link>
                    <button 
                      onClick={() => {
                        logout();
                        setProfileDropdownOpen(false);
                      }}
                      className="text-left text-sm text-red-400 hover:text-red-300 font-medium py-1 px-2 transition-colors flex items-center gap-2 cursor-pointer"
                    >
                      <span className="material-symbols-outlined text-[18px]">logout</span>
                      Tizimdan chiqish
                    </button>
                  </div>
                ) : (
                  <div className="flex flex-col gap-3">
                    <div className="text-sm font-bold text-text-primary text-center">Tizimga kirish</div>
                    
                    {/* 1-Click Instant Login */}
                    <button
                      onClick={async () => {
                        try {
                          await loginDirect({ telegram_id: 1990156236, first_name: "XOJA" });
                          setProfileDropdownOpen(false);
                        } catch (err) {
                          console.error("Login failed:", err);
                        }
                      }}
                      className="w-full py-2.5 px-4 bg-primary-container hover:bg-primary-container/90 text-on-primary-container font-semibold rounded-lg text-sm transition-all flex items-center justify-center gap-2 shadow-lg shadow-primary-container/20 cursor-pointer"
                    >
                      <span className="material-symbols-outlined text-[20px]">bolt</span>
                      1-Bosishda Tezkor Kirish (XOJA)
                    </button>

                    <div className="relative flex py-1 items-center">
                      <div className="flex-grow border-t border-white/10"></div>
                      <span className="flex-shrink mx-2 text-[11px] text-text-secondary">yoki vidjet orqali</span>
                      <div className="flex-grow border-t border-white/10"></div>
                    </div>

                    <div className="flex justify-center">
                      <TelegramLoginWidget />
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Mobile Menu Toggle */}
          <div className="flex md:hidden items-center gap-2">
            <Link 
              href="/notifications"
              onClick={() => {
                setMobileMenuOpen(false);
                setProfileDropdownOpen(false);
              }}
              className="text-text-primary p-2 relative"
              aria-label="Bildirishnomalar"
            >
              <span className="material-symbols-outlined text-[24px]">notifications</span>
              <span className="absolute top-2 right-2 w-2 h-2 bg-primary-container rounded-full animate-pulse"></span>
            </Link>
            <button 
              className="text-text-primary p-2 flex items-center justify-center rounded-lg hover:bg-white/10 transition-colors cursor-pointer"
              onClick={() => {
                setMobileMenuOpen(true);
                setProfileDropdownOpen(false);
              }}
              aria-label="Menyu"
            >
              <span className="material-symbols-outlined text-3xl">menu</span>
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Navigation Drawer (Full-screen overlay, perfectly structured) */}
      {mobileMenuOpen && (
        <div className="md:hidden fixed inset-0 z-[100] bg-background-obsidian/98 backdrop-blur-2xl flex flex-col">
          {/* Drawer Top Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-white/10 shrink-0">
            <Link 
              href="/" 
              onClick={() => setMobileMenuOpen(false)} 
              className="font-display-hero-mobile text-[26px] text-primary-container tracking-tighter"
            >
              Kinochi
            </Link>
            <button 
              onClick={() => setMobileMenuOpen(false)}
              className="w-10 h-10 flex items-center justify-center rounded-full bg-white/10 text-text-primary hover:bg-white/20 transition-colors cursor-pointer"
              aria-label="Yopish"
            >
              <span className="material-symbols-outlined text-2xl">close</span>
            </button>
          </div>

          {/* Drawer Scrollable Content */}
          <div className="flex-1 overflow-y-auto px-6 py-5 flex flex-col gap-5">
            {/* Search Input */}
            <form onSubmit={handleSearch} className="flex w-full items-center bg-white/10 rounded-xl px-4 py-3 border border-white/10 focus-within:border-primary-container transition-all">
              <span className="material-symbols-outlined text-text-secondary mr-3 text-[22px]">search</span>
              <input 
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="bg-transparent border-none focus:ring-0 text-text-primary text-base w-full outline-none placeholder:text-text-secondary" 
                placeholder="Kino yoki serial qidirish..." 
              />
            </form>

            {/* Navigation Sections */}
            <div className="flex flex-col gap-1.5">
              <span className="text-[11px] font-bold uppercase tracking-wider text-text-secondary px-1 mb-1">Bo'limlar</span>
              {navLinks.map((link) => {
                const isActive = pathname === link.href || (link.href !== '/' && pathname.startsWith(link.href));
                return (
                  <Link
                    key={link.name}
                    href={link.href}
                    onClick={() => setMobileMenuOpen(false)}
                    className={`flex items-center px-4 py-3 rounded-xl text-lg font-bold tracking-wide transition-all ${
                      isActive 
                        ? "bg-primary-container text-white shadow-lg shadow-primary-container/20" 
                        : "text-text-secondary hover:text-text-primary hover:bg-white/5"
                    }`}
                  >
                    {link.name}
                  </Link>
                );
              })}
            </div>

            <div className="h-[1px] bg-white/10 w-full my-1"></div>

            {/* User Quick Links */}
            <div className="flex flex-col gap-1">
              <span className="text-[11px] font-bold uppercase tracking-wider text-text-secondary px-1 mb-1">Foydalanuvchi</span>
              <Link
                href="/notifications"
                onClick={() => setMobileMenuOpen(false)}
                className="flex items-center gap-3 px-4 py-2.5 rounded-xl text-base font-medium text-text-secondary hover:text-text-primary hover:bg-white/5 transition-all"
              >
                <span className="material-symbols-outlined text-[22px] text-blue-400">notifications</span>
                Bildirishnomalar
              </Link>
              <Link
                href="/history"
                onClick={() => setMobileMenuOpen(false)}
                className="flex items-center gap-3 px-4 py-2.5 rounded-xl text-base font-medium text-text-secondary hover:text-text-primary hover:bg-white/5 transition-all"
              >
                <span className="material-symbols-outlined text-[22px] text-primary-container">history</span>
                Ko'rish tarixi
              </Link>
              <Link
                href="/achievements"
                onClick={() => setMobileMenuOpen(false)}
                className="flex items-center gap-3 px-4 py-2.5 rounded-xl text-base font-medium text-text-secondary hover:text-text-primary hover:bg-white/5 transition-all"
              >
                <span className="material-symbols-outlined text-[22px] text-amber-400">emoji_events</span>
                Yutuqlar
              </Link>
            </div>

            {/* User Profile / Logout Section */}
            <div className="mt-auto pt-4 border-t border-white/10">
              {status === "authenticated" ? (
                <div className="flex items-center justify-between bg-white/5 p-3 rounded-xl">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-primary-container/20 flex items-center justify-center text-primary-container font-bold">
                      {user?.first_name?.charAt(0) || "U"}
                    </div>
                    <div className="overflow-hidden">
                      <div className="font-bold text-sm text-text-primary truncate">{user?.first_name}</div>
                      <div className="text-xs text-text-secondary truncate">@{user?.username || user?.id}</div>
                    </div>
                  </div>
                  <button 
                    onClick={() => {
                      logout();
                      setMobileMenuOpen(false);
                    }}
                    className="text-xs text-red-400 hover:text-red-300 font-semibold px-3 py-1.5 rounded-lg bg-white/5 cursor-pointer"
                  >
                    Chiqish
                  </button>
                </div>
              ) : (
                <button
                  onClick={async () => {
                    try {
                      await loginDirect({ telegram_id: 1990156236, first_name: "XOJA" });
                      setMobileMenuOpen(false);
                    } catch (err) {
                      console.error("Login failed:", err);
                    }
                  }}
                  className="w-full py-3 px-4 bg-primary-container hover:bg-primary-container/90 text-white font-bold rounded-xl text-sm flex items-center justify-center gap-2 shadow-lg shadow-primary-container/20 cursor-pointer"
                >
                  <span className="material-symbols-outlined text-[20px]">bolt</span>
                  1-Bosishda Kirish (XOJA)
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Mobile Profile Bottom Sheet Modal (Dedicated for Mobile / Telegram WebApp) */}
      {profileDropdownOpen && (
        <div className="md:hidden fixed inset-0 z-[110] flex flex-col justify-end">
          {/* Backdrop overlay */}
          <div 
            className="fixed inset-0 bg-black/80 backdrop-blur-md transition-opacity"
            onClick={() => setProfileDropdownOpen(false)}
          />

          {/* Bottom Sheet Drawer */}
          <div className="relative z-10 bg-background-obsidian/98 backdrop-blur-2xl border-t border-white/15 rounded-t-[32px] px-6 pt-4 pb-8 shadow-2xl flex flex-col gap-4 animate-in slide-in-from-bottom duration-300 max-h-[85vh] overflow-y-auto">
            {/* Drag Handle Bar */}
            <div className="w-12 h-1.5 bg-white/25 rounded-full mx-auto mb-1 shrink-0" />

            {/* Header */}
            <div className="flex items-center justify-between pb-3 border-b border-white/10 shrink-0">
              <span className="text-lg font-bold text-text-primary tracking-wide">
                {status === "authenticated" ? "Mening Profilim" : "Tizimga kirish"}
              </span>
              <button 
                onClick={() => setProfileDropdownOpen(false)}
                className="w-9 h-9 rounded-full bg-white/10 hover:bg-white/20 text-text-primary flex items-center justify-center transition-colors cursor-pointer"
                aria-label="Yopish"
              >
                <span className="material-symbols-outlined text-2xl">close</span>
              </button>
            </div>

            {status === "authenticated" ? (
              <div className="flex flex-col gap-4">
                {/* User Info Card */}
                <div className="flex items-center gap-3.5 p-4 bg-white/5 rounded-2xl border border-white/10">
                  <div className="w-13 h-13 rounded-full bg-primary-container/20 border-2 border-primary-container/40 flex items-center justify-center text-primary-container text-xl font-bold shrink-0">
                    {user?.first_name?.charAt(0) || "U"}
                  </div>
                  <div className="overflow-hidden">
                    <div className="font-bold text-lg text-text-primary truncate">
                      {user?.first_name} {user?.last_name || ""}
                    </div>
                    <div className="text-xs text-text-secondary truncate mt-0.5">
                      {user?.username ? `@${user.username}` : `ID: ${user?.id}`}
                    </div>
                  </div>
                </div>

                {/* Actions List */}
                <div className="flex flex-col gap-2.5">
                  <Link
                    href="/history"
                    onClick={() => setProfileDropdownOpen(false)}
                    className="flex items-center justify-between p-3.5 rounded-2xl bg-white/5 hover:bg-white/10 border border-white/5 transition-all text-text-primary group"
                  >
                    <div className="flex items-center gap-3.5">
                      <div className="w-10 h-10 rounded-xl bg-primary-container/15 flex items-center justify-center text-primary-container">
                        <span className="material-symbols-outlined text-[24px]">history</span>
                      </div>
                      <span className="font-semibold text-base">Ko'rish tarixi</span>
                    </div>
                    <span className="material-symbols-outlined text-text-secondary group-hover:text-primary-container transition-colors text-[20px]">chevron_right</span>
                  </Link>

                  <Link
                    href="/achievements"
                    onClick={() => setProfileDropdownOpen(false)}
                    className="flex items-center justify-between p-3.5 rounded-2xl bg-white/5 hover:bg-white/10 border border-white/5 transition-all text-text-primary group"
                  >
                    <div className="flex items-center gap-3.5">
                      <div className="w-10 h-10 rounded-xl bg-amber-400/15 flex items-center justify-center text-amber-400">
                        <span className="material-symbols-outlined text-[24px]">emoji_events</span>
                      </div>
                      <span className="font-semibold text-base">Yutuqlar</span>
                    </div>
                    <span className="material-symbols-outlined text-text-secondary group-hover:text-amber-400 transition-colors text-[20px]">chevron_right</span>
                  </Link>

                  <Link
                    href="/notifications"
                    onClick={() => setProfileDropdownOpen(false)}
                    className="flex items-center justify-between p-3.5 rounded-2xl bg-white/5 hover:bg-white/10 border border-white/5 transition-all text-text-primary group"
                  >
                    <div className="flex items-center gap-3.5">
                      <div className="w-10 h-10 rounded-xl bg-blue-400/15 flex items-center justify-center text-blue-400">
                        <span className="material-symbols-outlined text-[24px]">notifications</span>
                      </div>
                      <span className="font-semibold text-base">Bildirishnomalar</span>
                    </div>
                    <span className="material-symbols-outlined text-text-secondary group-hover:text-blue-400 transition-colors text-[20px]">chevron_right</span>
                  </Link>
                </div>

                {/* Logout Button */}
                <button 
                  onClick={() => {
                    logout();
                    setProfileDropdownOpen(false);
                  }}
                  className="w-full flex items-center justify-center gap-2 py-3.5 px-4 rounded-2xl bg-red-500/10 hover:bg-red-500/20 text-red-400 font-bold text-sm transition-all border border-red-500/20 mt-1 cursor-pointer"
                >
                  <span className="material-symbols-outlined text-[20px]">logout</span>
                  Tizimdan chiqish
                </button>
              </div>
            ) : (
              <div className="flex flex-col gap-4 py-2">
                <p className="text-sm text-text-secondary text-center">
                  Ko'rish tarixi, yutuqlar va shaxsiy tavsiyalardan foydalanish uchun tizimga kiring:
                </p>
                <button
                  onClick={async () => {
                    try {
                      await loginDirect({ telegram_id: 1990156236, first_name: "XOJA" });
                      setProfileDropdownOpen(false);
                    } catch (err) {
                      console.error("Login failed:", err);
                    }
                  }}
                  className="w-full py-3.5 px-4 bg-primary-container hover:bg-primary-container/90 text-white font-bold rounded-2xl text-sm transition-all flex items-center justify-center gap-2 shadow-lg shadow-primary-container/20 cursor-pointer"
                >
                  <span className="material-symbols-outlined text-[20px]">bolt</span>
                  1-Bosishda Tezkor Kirish (XOJA)
                </button>

                <div className="relative flex py-1 items-center">
                  <div className="flex-grow border-t border-white/10"></div>
                  <span className="flex-shrink mx-3 text-xs text-text-secondary">yoki Telegram orqali</span>
                  <div className="flex-grow border-t border-white/10"></div>
                </div>

                <div className="flex justify-center pb-2">
                  <TelegramLoginWidget />
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </nav>
  );
}
