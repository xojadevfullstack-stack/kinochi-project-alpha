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
  const [hasUnread, setHasUnread] = useState(false);
  const profileDropdownRef = useRef<HTMLDivElement>(null);

  // Synchronize unread notification status
  useEffect(() => {
    const updateUnreadStatus = () => {
      try {
        const val = localStorage.getItem("kinochi_has_unread");
        setHasUnread(val === "true");
      } catch (e) {
        setHasUnread(false);
      }
    };

    updateUnreadStatus();
    window.addEventListener("kinochi_notifications_updated", updateUnreadStatus);
    window.addEventListener("storage", updateUnreadStatus);

    const handleToggleProfile = () => {
      setProfileDropdownOpen(prev => !prev);
      setMobileMenuOpen(false);
    };
    window.addEventListener("kinochi_toggle_profile", handleToggleProfile);

    return () => {
      window.removeEventListener("kinochi_notifications_updated", updateUnreadStatus);
      window.removeEventListener("storage", updateUnreadStatus);
      window.removeEventListener("kinochi_toggle_profile", handleToggleProfile);
    };
  }, []);

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

  // Prevent background scrolling when mobile menu or mobile profile modal is open
  useEffect(() => {
    const isMobile = typeof window !== "undefined" && window.innerWidth < 1280;
    const shouldLock = mobileMenuOpen || (profileDropdownOpen && isMobile);

    if (shouldLock) {
      const prevOverflow = document.body.style.overflow;
      document.body.style.overflow = "hidden";
      return () => {
        document.body.style.overflow = prevOverflow;
      };
    }
  }, [mobileMenuOpen, profileDropdownOpen]);

  // Close menus on route change
  useEffect(() => {
    setMobileMenuOpen(false);
    setProfileDropdownOpen(false);
  }, [pathname]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      router.push(`/search?q=${encodeURIComponent(searchQuery)}`);
      setMobileMenuOpen(false);
    }
  };

  const handleLinkClick = (href: string) => {
    if (pathname === href) {
      setMobileMenuOpen(false);
      setProfileDropdownOpen(false);
    }
  };

  const navLinks = [
    { name: "Bosh sahifa", href: "/" },
    { name: "Kinolar", href: "/movies" },
    { name: "Seriallar", href: "/series" },
    ...pages.map(p => ({ name: p.title, href: `/p/${p.slug}` }))
  ];

  return (
    <>
      <nav 
        className={`fixed top-0 w-full z-50 transition-all duration-300 ease-out border-b ${
        isScrolled 
          ? "bg-background-obsidian/90 backdrop-blur-lg border-white/10 shadow-2xl shadow-primary-container/10 py-3" 
          : "bg-gradient-to-b from-background-obsidian/80 to-transparent border-transparent py-5"
      }`}
      >
        <div className="max-w-container-max mx-auto px-gutter flex items-center justify-between">
          
          {/* Left: Logo */}
          <Link href="/" className="flex items-center gap-2 group z-50">
            <span className="font-display-hero text-2xl sm:text-3xl font-black tracking-wider text-primary-container group-hover:opacity-90 transition-opacity">
              Kinochi
            </span>
          </Link>

          {/* Center: Desktop Navigation Links (Classic Animated Line Hover) */}
          <div 
            className="hidden md:flex items-center gap-6 lg:gap-8"
            onMouseLeave={() => setHoveredLink(null)}
          >
            {navLinks.map((link) => {
              const isActive = pathname === link.href || (link.href !== '/' && pathname.startsWith(link.href));
              const showLine = hoveredLink ? hoveredLink === link.href : isActive;

              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className="relative group py-1 font-semibold text-sm xl:text-[15px] transition-colors cursor-pointer"
                  onMouseEnter={() => setHoveredLink(link.href)}
                >
                  <span className={`transition-colors duration-200 ${isActive ? "text-primary-container font-bold" : "text-text-secondary group-hover:text-text-primary"}`}>
                    {link.name}
                  </span>
                  <span 
                    className={`absolute -bottom-1.5 left-0 h-[2px] bg-primary-container transition-all duration-200 ${
                      showLine ? "w-full opacity-100" : "w-0 opacity-0"
                    }`}
                  />
                </Link>
              );
            })}
          </div>

          {/* Right: Search & Profile */}
          <div className="flex items-center gap-2 sm:gap-3 shrink-0 z-50 relative">
            {/* Desktop/Tablet Search */}
            <form onSubmit={handleSearch} className="hidden md:flex items-center bg-white/5 hover:bg-white/10 rounded-full px-3.5 py-1.5 xl:px-4 xl:py-2 border border-white/5 focus-within:border-white/30 focus-within:bg-white/10 transition-all">
              <span className="material-symbols-outlined text-text-secondary mr-2 text-[18px] xl:text-[20px]" style={{ fontVariationSettings: "'FILL' 0" }}>search</span>
              <input 
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="bg-transparent border-none focus:ring-0 text-text-primary text-sm placeholder:text-text-secondary w-24 lg:w-40 xl:w-56 outline-none" 
                placeholder="Qidirish..." 
              />
            </form>

            {/* Desktop/Tablet Notifications */}
            <Link 
              href="/notifications"
              className="relative hidden md:flex w-10 h-10 rounded-full border border-white/10 hover:border-primary-container hover:text-primary-container transition-colors bg-white/5 items-center justify-center text-text-secondary hover:bg-white/10 cursor-pointer group"
              aria-label="Bildirishnomalar"
            >
              <span className="material-symbols-outlined text-[22px] text-text-secondary group-hover:text-primary-container transition-colors">notifications</span>
              {hasUnread && (
                <span className="absolute top-2.5 right-2.5 w-2 h-2 bg-primary-container rounded-full animate-pulse"></span>
              )}
            </Link>
            
            {/* Profile Avatar Button (Desktop-only; on mobile BottomNav has dedicated Profil tab) */}
            <div className="relative hidden xl:block" ref={profileDropdownRef}>
              <div 
                onClick={() => {
                  setProfileDropdownOpen(prev => !prev);
                  setMobileMenuOpen(false);
                }}
                className="w-10 h-10 rounded-full border border-white/10 hover:border-primary-container hover:text-primary-container transition-colors bg-white/5 flex items-center justify-center text-text-secondary hover:bg-white/10 cursor-pointer group"
                aria-label="Profil"
              >
                {status === "authenticated" ? (
                  <span className="font-bold text-sm text-text-secondary group-hover:text-primary-container transition-colors">
                    {user?.first_name?.charAt(0) || "U"}
                  </span>
                ) : (
                  <span className="material-symbols-outlined text-[22px] text-text-secondary group-hover:text-primary-container transition-colors">
                    person
                  </span>
                )}
              </div>
              
              {/* Desktop Dropdown */}
              {profileDropdownOpen && (
                <div className="hidden xl:block absolute right-0 mt-2 w-72 bg-background-obsidian/95 backdrop-blur-xl border border-white/10 rounded-2xl p-4 shadow-2xl z-50">
                  {status === "authenticated" ? (
                    <div className="flex flex-col gap-3">
                      <div className="flex items-center gap-3 border-b border-white/10 pb-3">
                        <div className="w-10 h-10 rounded-full bg-white/10 border border-white/20 flex items-center justify-center text-white font-bold shrink-0">
                          {user?.first_name?.charAt(0) || "U"}
                        </div>
                        <div className="overflow-hidden">
                          <div className="font-bold text-text-primary truncate">{user?.first_name} {user?.last_name}</div>
                          <div className="text-xs text-text-secondary truncate">@{user?.username || user?.id}</div>
                        </div>
                      </div>
                      <Link
                        href="/history"
                        onClick={() => handleLinkClick("/history")}
                        className="flex items-center gap-2.5 text-sm text-text-primary hover:text-white py-2 px-2.5 rounded-xl hover:bg-white/5 transition-all font-medium group"
                      >
                        <span className="material-symbols-outlined text-[20px] text-sky-400">history</span>
                        <span>Ko'rish tarixi</span>
                      </Link>
                      <Link
                        href="/achievements"
                        onClick={() => handleLinkClick("/achievements")}
                        className="flex items-center gap-2.5 text-sm text-text-primary hover:text-white py-2 px-2.5 rounded-xl hover:bg-white/5 transition-all font-medium group"
                      >
                        <span className="material-symbols-outlined text-[20px] text-amber-400">emoji_events</span>
                        <span>Yutuqlar</span>
                      </Link>
                      <button
                        onClick={() => {
                          logout();
                          setProfileDropdownOpen(false);
                        }}
                        className="flex items-center gap-2.5 text-sm text-red-400 hover:text-red-300 py-2 px-2.5 rounded-xl hover:bg-red-500/10 transition-all font-medium text-left cursor-pointer border-t border-white/5 pt-3"
                      >
                        <span className="material-symbols-outlined text-[20px]">logout</span>
                        <span>Chiqish</span>
                      </button>
                    </div>
                  ) : (
                    <div className="flex flex-col gap-3">
                      <p className="text-xs text-text-secondary text-center">
                        Tizimga kiring:
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
                        className="w-full py-2.5 px-3 bg-primary-container hover:bg-primary-container/90 text-white font-bold rounded-xl text-xs flex items-center justify-center gap-2 shadow-md shadow-primary-container/20 cursor-pointer"
                      >
                        <span className="material-symbols-outlined text-[18px]">bolt</span>
                        1-Bosishda Kirish (XOJA)
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

          {/* Mobile & Tablet Notification & Menu Buttons (< xl) */}
          <div className="flex xl:hidden items-center gap-2.5">
            <Link 
              href="/notifications"
              onClick={() => handleLinkClick("/notifications")}
              className="w-10 h-10 rounded-full border border-white/10 hover:border-primary-container hover:text-primary-container transition-colors bg-white/5 flex items-center justify-center relative text-text-secondary hover:bg-white/10 cursor-pointer group"
              aria-label="Bildirishnomalar"
            >
              <span className="material-symbols-outlined text-[22px] text-text-secondary group-hover:text-primary-container transition-colors">notifications</span>
              {hasUnread && (
                <span className="absolute top-2.5 right-2.5 w-2 h-2 bg-primary-container rounded-full animate-pulse"></span>
              )}
            </Link>
            <button 
              className="w-10 h-10 rounded-full border border-white/10 hover:border-primary-container hover:text-primary-container transition-colors bg-white/5 flex items-center justify-center text-text-secondary hover:bg-white/10 cursor-pointer group"
              onClick={() => {
                setMobileMenuOpen(true);
                setProfileDropdownOpen(false);
              }}
              aria-label="Menyu"
            >
              <span className="material-symbols-outlined text-[22px] text-text-secondary group-hover:text-primary-container transition-colors">menu</span>
            </button>
          </div>
        </div>
      </div>
    </nav>

      {/* Mobile Navigation Drawer (Full-screen overlay, perfectly structured) */}
      {mobileMenuOpen && (
        <div className="xl:hidden fixed inset-0 z-[100] bg-background-obsidian/98 backdrop-blur-2xl flex flex-col overscroll-contain">
          {/* Drawer Top Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-white/10 shrink-0">
            <Link 
              href="/" 
              onClick={() => handleLinkClick("/")} 
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
          <div className="flex-1 overflow-y-auto overscroll-contain px-6 py-5 flex flex-col gap-5">
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
                    onClick={() => handleLinkClick(link.href)}
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
          </div>
        </div>
      )}

      {/* Mobile Profile Bottom Sheet Modal (Dedicated for Mobile / Telegram WebApp) */}
      {profileDropdownOpen && (
        <div className="xl:hidden fixed inset-0 z-[110] flex flex-col justify-end overscroll-contain">
          {/* Backdrop overlay */}
          <div 
            className="absolute inset-0 bg-black/80 backdrop-blur-md transition-opacity"
            onClick={() => setProfileDropdownOpen(false)}
          />

          {/* Bottom Sheet Drawer */}
          <div className="relative z-10 bg-background-obsidian/98 backdrop-blur-2xl border-t border-white/15 rounded-t-[32px] px-6 pt-4 pb-8 shadow-2xl flex flex-col gap-4 animate-in slide-in-from-bottom duration-300 max-h-[85vh] max-h-[85dvh] overflow-y-auto overscroll-contain">
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
                  <div className="w-12 h-12 rounded-full aspect-square bg-white/10 border border-white/20 flex items-center justify-center text-white text-lg font-bold shrink-0 shadow-inner">
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
                    href="/achievements"
                    onClick={() => handleLinkClick("/achievements")}
                    className="flex items-center justify-between p-3.5 rounded-2xl bg-white/5 hover:bg-white/10 border border-white/5 transition-all text-text-primary group cursor-pointer"
                  >
                    <div className="flex items-center gap-3.5">
                      <div className="w-10 h-10 rounded-xl bg-amber-400/15 border border-amber-400/20 flex items-center justify-center text-amber-400">
                        <span className="material-symbols-outlined text-[24px]">emoji_events</span>
                      </div>
                      <span className="font-semibold text-base">Yutuqlar</span>
                    </div>
                    <span className="material-symbols-outlined text-text-secondary group-hover:text-amber-400 transition-colors text-[20px]">chevron_right</span>
                  </Link>
                </div>

                {/* Logout Button */}
                <button 
                  onClick={() => {
                    logout();
                    setProfileDropdownOpen(false);
                  }}
                  className="w-full flex items-center justify-center gap-2 py-3 px-4 rounded-2xl bg-white/5 hover:bg-white/10 text-text-secondary hover:text-white font-semibold text-sm transition-all border border-white/10 hover:border-white/20 mt-1 cursor-pointer"
                >
                  <span className="material-symbols-outlined text-[20px]">logout</span>
                  <span>Tizimdan chiqish</span>
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
    </>
  );
}
