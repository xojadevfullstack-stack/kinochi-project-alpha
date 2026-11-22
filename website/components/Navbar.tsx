"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState, useEffect, useRef, useCallback } from "react";
import { useAuth } from "../lib/auth/AuthProvider";
import LiveSearch from "./LiveSearch";
import ThemeToggle from "./ThemeToggle";
import { fetchApi } from "../lib/api";
import { useOverlayBackClose } from "@/lib/hooks/useOverlayBackClose";

export default function Navbar({ pages = [] }: { pages: any[] }) {
  const pathname = usePathname();
  const router = useRouter();
  const { status, user } = useAuth();
  
  // Navbar scroll background
  const [isScrolled, setIsScrolled] = useState(false);
  
  // Mobile animated expanding search bar state
  const [isMobileSearchOpen, setIsMobileSearchOpen] = useState(false);
  
  // Dynamic Desktop Sidebar state (Opens ONLY when cursor approaches left edge)
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isPinned, setIsPinned] = useState(false);
  const isInitializedRef = useRef(false);
  
  const [hasUnread, setHasUnread] = useState(false);
  const closeTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Synchronize unread notification status
  useEffect(() => {
    let isCancelled = false;

    const checkFreshUnread = async () => {
      try {
        let readIds = new Set<string>();
        try {
          const saved = localStorage.getItem("kinochi_read_notification_ids");
          if (saved) {
            readIds = new Set(JSON.parse(saved));
          }
        } catch {}

        let hasNew = false;
        try {
          const bData: any = await fetchApi("/broadcasts/public?limit=5");
          if (bData && Array.isArray(bData.items) && bData.items.length > 0) {
            for (const b of bData.items) {
              if (!readIds.has(`sys-${b.id}`)) {
                hasNew = true;
                break;
              }
            }
          }
        } catch {}

        if (!hasNew && !readIds.has("sys-welcome")) {
          hasNew = true;
        }

        if (!isCancelled) {
          localStorage.setItem("kinochi_has_unread", hasNew ? "true" : "false");
          setHasUnread(hasNew);
        }
      } catch (e) {
        if (!isCancelled) {
          const val = localStorage.getItem("kinochi_has_unread");
          setHasUnread(val === "true");
        }
      }
    };

    const updateUnreadStatus = () => {
      try {
        const val = localStorage.getItem("kinochi_has_unread");
        setHasUnread(val === "true");
      } catch (e) {
        setHasUnread(false);
      }
    };

    updateUnreadStatus();
    checkFreshUnread();

    window.addEventListener("kinochi_notifications_updated", updateUnreadStatus);
    window.addEventListener("storage", updateUnreadStatus);
    window.addEventListener("focus", checkFreshUnread);

    const handleToggleProfile = () => {
      router.push("/profile");
    };
    window.addEventListener("kinochi_toggle_profile", handleToggleProfile);

    const interval = setInterval(checkFreshUnread, 60000);

    return () => {
      isCancelled = true;
      clearInterval(interval);
      window.removeEventListener("kinochi_notifications_updated", updateUnreadStatus);
      window.removeEventListener("storage", updateUnreadStatus);
      window.removeEventListener("focus", checkFreshUnread);
      window.removeEventListener("kinochi_toggle_profile", handleToggleProfile);
    };
  }, [status, router]);

  // Handle scroll for navbar background
  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  // Close dynamic sidebar and mobile search on route change
  useEffect(() => {
    if (!isPinned) {
      setSidebarOpen(false);
    }
    setIsMobileSearchOpen(false);
  }, [pathname, isPinned]);

  // Handle Escape key to dismiss mobile search
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isMobileSearchOpen) {
        setIsMobileSearchOpen(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isMobileSearchOpen]);

  // Initialize pin state from localStorage on desktop mount
  useEffect(() => {
    try {
      if (typeof window !== "undefined" && window.innerWidth >= 1280) {
        const saved = localStorage.getItem("kinochi_sidebar_pinned");
        if (saved === "true") {
          setIsPinned(true);
          setSidebarOpen(true);
          document.body.classList.add("sidebar-pinned");
        }
      }
    } catch {} finally {
      isInitializedRef.current = true;
    }
  }, []);

  // Synchronize document.body.sidebar-pinned class with isPinned state
  useEffect(() => {
    if (typeof window === "undefined" || !isInitializedRef.current) return;

    if (isPinned && window.innerWidth >= 1280) {
      document.body.classList.add("sidebar-pinned");
      try {
        localStorage.setItem("kinochi_sidebar_pinned", "true");
      } catch {}
    } else {
      document.body.classList.remove("sidebar-pinned");
      try {
        if (!isPinned) {
          localStorage.removeItem("kinochi_sidebar_pinned");
        }
      } catch {}
    }

    const handleResize = () => {
      if (window.innerWidth < 1280) {
        document.body.classList.remove("sidebar-pinned");
      } else if (isPinned) {
        document.body.classList.add("sidebar-pinned");
      }
    };

    window.addEventListener("resize", handleResize);
    return () => {
      window.removeEventListener("resize", handleResize);
      document.body.classList.remove("sidebar-pinned");
    };
  }, [isPinned]);

  // Dynamic Sidebar Hover Engine
  const openSidebarSmoothly = useCallback(() => {
    if (closeTimerRef.current) {
      clearTimeout(closeTimerRef.current);
      closeTimerRef.current = null;
    }
    setSidebarOpen(true);
  }, []);

  const closeSidebarSmoothly = useCallback(() => {
    if (isPinned) return;
    if (closeTimerRef.current) clearTimeout(closeTimerRef.current);
    closeTimerRef.current = setTimeout(() => {
      setSidebarOpen(false);
    }, 350); // 350ms grace period
  }, [isPinned]);

  const closeSidebarImmediate = useCallback(() => {
    if (closeTimerRef.current) clearTimeout(closeTimerRef.current);
    setIsPinned(false);
    setSidebarOpen(false);
  }, []);

  // Native OS Back (popstate) closes unpinned drawer or mobile search bar first
  useOverlayBackClose(sidebarOpen && !isPinned, closeSidebarImmediate);
  useOverlayBackClose(isMobileSearchOpen, () => setIsMobileSearchOpen(false));

  const togglePin = useCallback(() => {
    setIsPinned(prev => {
      const next = !prev;
      if (next) setSidebarOpen(true);
      return next;
    });
  }, []);

  // Lock background page scroll on mobile/tablet when overlay sidebar is open
  useEffect(() => {
    if (typeof window === "undefined") return;
    const shouldLock = sidebarOpen && !isPinned && window.innerWidth < 1280;
    if (shouldLock) {
      document.documentElement.style.overflow = "hidden";
      document.body.style.overflow = "hidden";
    } else {
      document.documentElement.style.overflow = "";
      document.body.style.overflow = "";
    }
    return () => {
      document.documentElement.style.overflow = "";
      document.body.style.overflow = "";
    };
  }, [sidebarOpen, isPinned]);

  // Proximity detection: if cursor approaches within 20px of left edge on desktop, open smoothly
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (typeof window === "undefined" || window.innerWidth < 1280 || isPinned) return;
      if (e.clientX <= 20) {
        openSidebarSmoothly();
      }
    };
    window.addEventListener("mousemove", handleMouseMove, { passive: true });
    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      if (closeTimerRef.current) clearTimeout(closeTimerRef.current);
    };
  }, [openSidebarSmoothly, isPinned]);

  return (
    <>
      {/* ========================================================
          1. PROXIMITY EDGE SENSOR (Invisible left trigger zone)
      ======================================================== */}
      <div
        onMouseEnter={openSidebarSmoothly}
        className={`hidden xl:block fixed top-0 left-0 bottom-0 w-6 z-40 cursor-pointer select-none ${
          isPinned ? "pointer-events-none" : "pointer-events-auto"
        }`}
        aria-hidden="true"
        title="Sichqonchani yaqinlashtirsangiz saydbar ochiladi"
      />

      {/* ========================================================
          2. MINIMALIST DYNAMIC DESKTOP SIDEBAR
      ======================================================== */}
      <aside
        id="mainSidebar"
        onMouseEnter={openSidebarSmoothly}
        onMouseLeave={closeSidebarSmoothly}
        className={`flex fixed top-0 left-0 bottom-0 h-[100dvh] overscroll-contain w-72 z-[60] bg-white/95 dark:bg-[#0c0d10]/95 backdrop-blur-2xl border-r border-slate-900/10 dark:border-white/10 ${
          isPinned ? "shadow-none" : "shadow-[20px_0_50px_rgba(0,0,0,0.22)] dark:shadow-[20px_0_50px_rgba(0,0,0,0.85)]"
        } flex-col justify-between select-none transition-transform duration-300 ease-[cubic-bezier(0.16,1,0.3,1)] ${
          (sidebarOpen || isPinned) ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="p-4 space-y-4 overflow-y-auto overscroll-contain touch-pan-y hide-scrollbar flex-1">
          {/* Sidebar Top Header & Pin Action */}
          <div className="flex items-center justify-between pb-3 border-b border-slate-200 dark:border-white/10">
            <Link href="/" className="flex items-center gap-2 group">
              <img
                src="/logo-mediaplus-icon.png"
                alt="MediaPlus"
                decoding="async"
                className="w-7 h-7 rounded-lg object-cover shrink-0 shadow-md shadow-brand-red/30"
              />
              <span className="font-heading font-black text-sm tracking-wider text-slate-900 dark:text-white">
                MEDIA<span className="text-primary-container">PLUS</span>
              </span>
            </Link>

            <div className="flex items-center gap-1">
              <button
                onClick={togglePin}
                className={`w-7 h-7 rounded-lg flex items-center justify-center transition-colors ${
                  isPinned
                    ? "bg-primary-container text-white border border-primary-container"
                    : "text-slate-600 dark:text-text-secondary hover:text-white hover:bg-[#B80710] dark:hover:bg-[#E50914]"
                }`}
                title={isPinned ? "Mahkamlangan (Yonma-yon)" : "Ekranga mahkamlash (Yonma-yon)"}
              >
                <span
                  className="material-symbols-outlined text-[16px]"
                  style={{ fontVariationSettings: isPinned ? "'FILL' 1" : "'FILL' 0" }}
                >
                  push_pin
                </span>
              </button>
              <button
                onClick={closeSidebarImmediate}
                className="w-7 h-7 rounded-lg text-slate-600 dark:text-text-secondary hover:text-white flex items-center justify-center hover:bg-[#B80710] dark:hover:bg-[#E50914] transition-colors"
                title="Yopish"
              >
                <span className="material-symbols-outlined text-[18px]">close</span>
              </button>
            </div>
          </div>

          {/* User Profile Card (Minimalist Dark Glass) */}
          <Link
            href="/profile"
            className="block p-3 bg-white/5 hover:bg-white/10 rounded-xl border border-white/10 transition-all shadow-sm group cursor-pointer"
          >
            <div className="flex items-center gap-3">
              <div className="relative">
                <div className="w-10 h-10 rounded-full bg-white/10 border border-white/15 flex items-center justify-center font-bold text-xs text-white">
                  {status === "authenticated" && user?.first_name ? user.first_name.charAt(0) : "U"}
                </div>
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-xs font-bold text-white truncate group-hover:text-white transition-colors">
                  {status === "authenticated" && user ? `${user.first_name} ${user.last_name || ""}` : "Mehmon (Kiring)"}
                </div>
                <div className="text-[10px] text-text-secondary font-medium flex items-center gap-1 mt-0.5">
                  <span className="material-symbols-outlined text-[12px] text-primary">verified</span>
                  <span>{status === "authenticated" ? "VIP Foydalanuvchi" : "Standart tarif"}</span>
                </div>
              </div>
            </div>

            <div className="mt-2.5 pt-2 border-t border-white/5 flex items-center justify-between text-xs text-text-secondary">
              <div className="flex items-center gap-1.5 group-hover:text-text-primary">
                <span className="material-symbols-outlined text-[15px]">notifications</span>
                <span>Bildirishnomalar</span>
              </div>
              {hasUnread ? (
                <span className="w-2 h-2 bg-primary-container rounded-full animate-pulse" />
              ) : (
                <span className="text-[10px] text-text-secondary">0</span>
              )}
            </div>
          </Link>

          {/* Full Prototype Navigation Links */}
          <nav className="space-y-1 text-xs font-medium">
            {[
              { label: "Bosh sahifa", href: "/", icon: "home", exact: true },
              { label: "Barchasi (Katalog)", href: "/catalog", icon: "apps" },
              { label: "Kinolar", href: "/movies", icon: "movie" },
              { label: "Seriallar", href: "/series", icon: "tv" },
              { label: "Animelar", href: "/anime", icon: "animation" },
              { label: "Doramalar", href: "/doramas", icon: "theater_comedy" },
              { label: "Multfilmlar", href: "/cartoons", icon: "child_care" },
              { label: "Jonli TV", href: "/tv", icon: "live_tv" },
              { label: "Premyeralar", href: "/premieres", icon: "theaters" },
              { label: "To'plamlar & Xronologiyalar", href: "/collections", icon: "auto_awesome_motion" },
              { label: "Aktyorlar", href: "/actors", icon: "groups" },
              { label: "TOP 100", href: "/top100", icon: "emoji_events" },
              { label: "Obunalar (Sevimlilar)", href: "/subscriptions", icon: "bookmark" },
              { label: "Ko'rish tarixi", href: "/history", icon: "history" },
              { label: "Buyurtma berish", href: "/requests", icon: "add_box" },
            ].map((item) => {
              const active = item.exact
                ? pathname === item.href
                : pathname === item.href || pathname.startsWith(`${item.href}/`);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-2.5 px-3 py-2 rounded-xl transition-all ${
                    active
                      ? "bg-[#D20A13] dark:bg-[#E50914] text-white font-semibold shadow-sm"
                      : "text-slate-700 dark:text-gray-300 hover:bg-slate-100 dark:hover:bg-white/5 hover:text-slate-900 dark:hover:text-white"
                  }`}
                >
                  <span
                    className="material-symbols-outlined text-[17px]"
                    style={{ fontVariationSettings: active ? "'FILL' 1" : "'FILL' 0" }}
                  >
                    {item.icon}
                  </span>
                  <span className="truncate">{item.label}</span>
                </Link>
              );
            })}

            <div className="pt-2 my-2 border-t border-slate-200 dark:border-white/10" />

            <Link
              href="/notifications"
              className={`flex items-center gap-2.5 px-3 py-2 rounded-xl transition-all ${
                pathname.startsWith("/notifications")
                  ? "bg-[#D20A13] dark:bg-[#E50914] text-white font-semibold shadow-sm"
                  : "text-slate-700 dark:text-gray-300 hover:bg-slate-100 dark:hover:bg-white/5 hover:text-slate-900 dark:hover:text-white"
              }`}
            >
              <span className="material-symbols-outlined text-[17px]">notifications</span>
              <span>Bildirishnomalar</span>
              {hasUnread && <span className="ml-auto w-2 h-2 rounded-full bg-[#E50914]" />}
            </Link>

            <Link
              href="/profile"
              className={`flex items-center gap-2.5 px-3 py-2 rounded-xl transition-all ${
                pathname.startsWith("/profile")
                  ? "bg-[#D20A13] dark:bg-[#E50914] text-white font-semibold shadow-sm"
                  : "text-slate-700 dark:text-gray-300 hover:bg-slate-100 dark:hover:bg-white/5 hover:text-slate-900 dark:hover:text-white"
              }`}
            >
              <span className="material-symbols-outlined text-[17px]">account_circle</span>
              <span>Mening profilim</span>
            </Link>
          </nav>
        </div>

        {/* Sidebar Bottom: Qo'llanma & Telegram Bot CTA */}
        <div className="p-3 border-t border-slate-200 dark:border-white/10 text-xs text-slate-700 dark:text-text-secondary space-y-2">
          {(pathname === "/" ||
            pathname === "/requests" ||
            pathname.startsWith("/series/") ||
            pathname.startsWith("/collections/")) && (
            <button
              type="button"
              onClick={() => {
                closeSidebarImmediate();
                window.dispatchEvent(new Event("mediaplus:start_onboarding"));
              }}
              className="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl hover:bg-slate-100 dark:hover:bg-white/5 hover:text-slate-900 dark:hover:text-white transition-all cursor-pointer text-left"
            >
              <span className="material-symbols-outlined text-[17px] text-[#E50914]">auto_awesome</span>
              <span>Qo&apos;llanma (Qanday ishlaydi?)</span>
            </button>
          )}
          <a
            href={`https://t.me/${process.env.NEXT_PUBLIC_BOT_USERNAME || "MediaPlusOfficialBot"}`}
            target="_blank"
            rel="noopener noreferrer"
            className="w-full bg-[#D20A13] dark:bg-[#E50914] hover:bg-[#B80710] text-white py-2.5 rounded-xl text-xs font-bold transition flex items-center justify-center gap-1.5 shadow"
          >
            <span className="material-symbols-outlined text-[15px]">send</span>
            <span>Telegram Botimiz</span>
          </a>
        </div>
      </aside>

      {/* Subtle overlay when sidebar is open on desktop and NOT pinned */}
      {sidebarOpen && !isPinned && (
        <div
          onClick={closeSidebarImmediate}
          className="fixed inset-0 z-50 bg-black/60 backdrop-blur-[2px] touch-none overscroll-none transition-opacity duration-300 cursor-pointer"
          aria-hidden="true"
        />
      )}

      {/* ========================================================
          3. MAIN TOP NAVBAR (Desktop & Mobile)
          Clean minimalist header without duplicate hamburger button
      ======================================================== */}
      <nav
        className={`site-top-nav fixed top-0 left-0 w-full z-50 transition-all duration-300 ease-[cubic-bezier(0.16,1,0.3,1)] border-b ${
          isScrolled
            ? "bg-white/80 dark:bg-[#0c0e14]/75 backdrop-blur-xl border-slate-900/10 dark:border-white/10 shadow-lg shadow-slate-900/5 dark:shadow-2xl dark:shadow-black/80 py-3"
            : "bg-white/75 dark:bg-[#0c0e14]/65 backdrop-blur-md border-slate-900/5 dark:border-white/5 py-3.5"
        }`}
      >
        <div className="max-w-container-max mx-auto px-2.5 sm:px-gutter flex items-center justify-between gap-1.5 sm:gap-4 relative">
          
          {/* Left: Back (on inner pages) + Hamburger Menu Button + Logo */}
          <div
            className={`flex items-center gap-1 sm:gap-2.5 shrink-0 min-w-0 transition-all duration-300 ease-[cubic-bezier(0.16,1,0.3,1)] ${
              isMobileSearchOpen
                ? "opacity-0 -translate-x-4 pointer-events-none scale-95 sm:opacity-100 sm:translate-x-0 sm:pointer-events-auto sm:scale-100"
                : "opacity-100 translate-x-0 scale-100"
            }`}
          >
            {pathname && pathname !== "/" && (
              <button
                type="button"
                onClick={() => {
                  const hasHistory =
                    typeof window !== "undefined" &&
                    window.history.length > 1 &&
                    ((window.history.state && window.history.state.idx > 0) ||
                      (document.referrer && document.referrer.includes(window.location.host)));
                  if (hasHistory) {
                    router.back();
                  } else {
                    router.push("/");
                  }
                }}
                className="back-btn header-icon-btn w-8 h-8 sm:w-10 sm:h-10 rounded-full bg-slate-100/80 dark:bg-white/5 hover:bg-[#B80710] dark:hover:bg-[#E50914] active:scale-95 border border-slate-300/80 dark:border-white/10 hover:border-[#B80710] dark:hover:border-[#E50914] flex items-center justify-center text-slate-700 dark:text-text-secondary hover:text-white transition-all cursor-pointer group shrink-0"
                title="Orqaga"
                aria-label="Orqaga qaytish"
              >
                <span className="material-symbols-outlined text-[18px] sm:text-[22px] group-hover:text-white">
                  arrow_back
                </span>
              </button>
            )}
            <button
              type="button"
              onClick={() => {
                if (sidebarOpen) {
                  closeSidebarImmediate();
                } else {
                  openSidebarSmoothly();
                }
              }}
              className="header-icon-btn w-8 h-8 sm:w-10 sm:h-10 rounded-full bg-slate-100/80 dark:bg-white/5 hover:bg-[#B80710] dark:hover:bg-[#E50914] active:scale-95 border border-slate-300/80 dark:border-white/10 hover:border-[#B80710] dark:hover:border-[#E50914] flex items-center justify-center text-slate-700 dark:text-text-secondary hover:text-white transition-all cursor-pointer group shrink-0"
              title="Menyu"
              aria-label="Menyuni ochish"
            >
              <span className="material-symbols-outlined text-[18px] sm:text-[22px] group-hover:text-white">
                {sidebarOpen ? "close" : "menu"}
              </span>
            </button>
            <Link href="/" className="flex items-center gap-1.5 sm:gap-2 group min-w-0">
              <img
                src="/logo-mediaplus-icon.png"
                alt="MediaPlus"
                decoding="async"
                className="w-6 h-6 sm:w-9 sm:h-9 rounded-lg object-cover shrink-0 shadow-lg shadow-brand-red/30"
              />
              <span className="font-display-hero text-base xs:text-lg sm:text-3xl font-black tracking-wide sm:tracking-wider text-slate-900 dark:text-white group-hover:opacity-95 transition-opacity truncate">
                MEDIA<span className="text-primary-container">PLUS</span>
              </span>
            </Link>
          </div>

          {/* Center: Wide LiveSearch Input (Desktop) */}
          <div className="flex-1 max-w-xl mx-2 hidden sm:block">
            <LiveSearch
              className="w-full"
              placeholder="Qidiruv: film nomi, aktyor, janr yoki #kod..."
            />
          </div>

          {/* Right Corner Controls: [Search (Mobile only), 1. Theme, 2. Notifications, 3. Profile] */}
          <div
            className={`flex items-center gap-1 sm:gap-2.5 shrink-0 transition-all duration-300 ease-[cubic-bezier(0.16,1,0.3,1)] ${
              isMobileSearchOpen
                ? "opacity-0 translate-x-4 pointer-events-none scale-95 sm:opacity-100 sm:translate-x-0 sm:pointer-events-auto sm:scale-100"
                : "opacity-100 translate-x-0 scale-100"
            }`}
          >
            {/* Mobile Search Button (Tap to expand search bar & animate logo out) */}
            <button
              type="button"
              onClick={() => setIsMobileSearchOpen(true)}
              className="header-icon-btn sm:hidden w-8 h-8 rounded-full border border-slate-300/80 dark:border-white/10 hover:border-[#B80710] dark:hover:border-[#E50914] transition-all duration-200 bg-slate-100/80 dark:bg-white/5 hover:bg-[#B80710] dark:hover:bg-[#E50914] flex items-center justify-center text-slate-700 dark:text-text-secondary hover:text-white cursor-pointer group active:scale-95 shrink-0"
              aria-label="Qidiruv"
              title="Qidiruvni ochish"
            >
              <span className="material-symbols-outlined text-[18px] group-hover:text-white">
                search
              </span>
            </button>

            {/* 1. Dark / Light Mode Toggle */}
            <ThemeToggle />

            {/* 2. Notifications Button */}
            <Link
              href="/notifications"
              className="header-icon-btn relative w-8 h-8 sm:w-10 sm:h-10 rounded-full border border-slate-300/80 dark:border-white/10 hover:border-[#B80710] dark:hover:border-[#E50914] transition-all duration-200 bg-slate-100/80 dark:bg-white/5 hover:bg-[#B80710] dark:hover:bg-[#E50914] flex items-center justify-center text-slate-700 dark:text-text-secondary hover:text-white cursor-pointer group active:scale-95 shrink-0"
              aria-label="Bildirishnomalar"
              title="Bildirishnomalar"
            >
              <span className="material-symbols-outlined text-[18px] sm:text-[22px] group-hover:text-white">
                notifications
              </span>
              {hasUnread && (
                <span className="absolute top-1.5 right-1.5 sm:top-2 sm:right-2 w-1.5 h-1.5 sm:w-2 sm:h-2 bg-primary-container group-hover:bg-white rounded-full animate-pulse shadow-sm shadow-primary-container" />
              )}
            </Link>

            {/* 3. Profile Avatar / Button */}
            <Link
              href="/profile"
              className="header-icon-btn relative w-8 h-8 sm:w-10 sm:h-10 rounded-full border border-slate-300/80 dark:border-white/10 hover:border-[#B80710] dark:hover:border-[#E50914] transition-all duration-200 bg-slate-100/80 dark:bg-white/5 hover:bg-[#B80710] dark:hover:bg-[#E50914] flex items-center justify-center text-slate-700 dark:text-text-secondary hover:text-white cursor-pointer group active:scale-95 overflow-hidden shrink-0"
              aria-label="Mening Profilim"
              title="Profil sahifasi"
            >
              {status === "authenticated" && user?.first_name ? (
                <span className="font-bold text-xs sm:text-sm text-slate-900 dark:text-text-primary group-hover:text-white">
                  {user.first_name.charAt(0)}
                </span>
              ) : (
                <span className="material-symbols-outlined text-[18px] sm:text-[22px] group-hover:text-white">
                  person
                </span>
              )}
            </Link>
          </div>

          {/* ========================================================
              Mobile Expanding Search Bar Layer
              Animates in to replace the Logo and action controls
          ======================================================== */}
          <div
            className={`sm:hidden absolute inset-0 px-gutter flex items-center gap-2 transition-all duration-300 ease-[cubic-bezier(0.16,1,0.3,1)] z-20 ${
              isMobileSearchOpen
                ? "opacity-100 translate-x-0 pointer-events-auto"
                : "opacity-0 translate-x-4 pointer-events-none"
            }`}
          >
            {/* Back button to dismiss search and restore Logo */}
            <button
              type="button"
              onClick={() => setIsMobileSearchOpen(false)}
              className="header-icon-btn w-9 h-9 rounded-full bg-slate-100/80 dark:bg-white/5 hover:bg-[#B80710] dark:hover:bg-[#E50914] active:scale-95 border border-slate-300/80 dark:border-white/10 hover:border-[#B80710] dark:hover:border-[#E50914] flex items-center justify-center text-slate-700 dark:text-text-secondary hover:text-white transition-all shrink-0 cursor-pointer group"
              aria-label="Qidiruvni yopish"
              title="Qidiruvni yopish"
            >
              <span className="material-symbols-outlined text-[20px] group-hover:text-white">
                arrow_back
              </span>
            </button>

            {/* Full-width LiveSearch input in mobile bar mode */}
            <div className="flex-1 min-w-0">
              <LiveSearch
                autoFocus={isMobileSearchOpen}
                isMobileBar={true}
                className="w-full"
                placeholder="Film, serial, aktyor yoki #kod..."
                onClose={() => setIsMobileSearchOpen(false)}
                onNavigate={() => setIsMobileSearchOpen(false)}
              />
            </div>
          </div>
        </div>
      </nav>

      {/* Mobile search backdrop overlay (Dismisses search when tapping outside) */}
      {isMobileSearchOpen && (
        <div
          onClick={() => setIsMobileSearchOpen(false)}
          className="sm:hidden fixed inset-0 top-[56px] z-40 bg-black/60 backdrop-blur-sm transition-opacity duration-300"
          aria-hidden="true"
        />
      )}
    </>
  );
}
