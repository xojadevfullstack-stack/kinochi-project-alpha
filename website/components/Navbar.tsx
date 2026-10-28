"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState, useEffect, useRef, useCallback } from "react";
import { useAuth } from "../lib/auth/AuthProvider";
import LiveSearch from "./LiveSearch";
import ThemeToggle from "./ThemeToggle";
import { fetchApi } from "../lib/api";

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
    window.addEventListener("scroll", handleScroll);
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

  const togglePin = useCallback(() => {
    setIsPinned(prev => {
      const next = !prev;
      if (next) setSidebarOpen(true);
      return next;
    });
  }, []);

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
        onMouseEnter={openSidebarSmoothly}
        onMouseLeave={closeSidebarSmoothly}
        className={`flex fixed top-0 left-0 bottom-0 w-72 z-[60] bg-[#0c0d10]/98 backdrop-blur-2xl border-r border-white/10 ${
          isPinned ? "shadow-none" : "shadow-[20px_0_50px_rgba(0,0,0,0.85)]"
        } flex-col justify-between select-none transition-transform duration-300 ease-[cubic-bezier(0.16,1,0.3,1)] ${
          (sidebarOpen || isPinned) ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="p-4 space-y-4 overflow-y-auto hide-scrollbar flex-1">
          {/* Sidebar Top Header & Pin Action */}
          <div className="flex items-center justify-between pb-3 border-b border-white/10">
            <Link href="/" className="flex items-center gap-2 group">
              <span className="font-heading font-black text-sm tracking-wider text-white">
                MEDIA<span className="text-primary-container">PLUS</span>
              </span>
            </Link>

            <div className="flex items-center gap-1">
              <button
                onClick={togglePin}
                className={`w-7 h-7 rounded-lg flex items-center justify-center transition-colors ${
                  isPinned
                    ? "bg-white/15 text-white border border-white/20"
                    : "text-text-secondary hover:text-white hover:bg-white/5"
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
                className="w-7 h-7 rounded-lg text-text-secondary hover:text-white flex items-center justify-center hover:bg-white/5 transition-colors"
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
                  <span className="material-symbols-outlined text-[12px] text-rating-gold">verified</span>
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

          {/* Minimalist & Clean Navigation Links */}
          <nav className="space-y-1 text-xs">
            {/* 1. Bosh Sahifa */}
            <Link
              href="/"
              className={`flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all ${
                pathname === "/"
                  ? "bg-white/15 text-white font-bold border-l-2 border-primary-container"
                  : "text-text-secondary hover:bg-white/5 hover:text-white font-medium"
              }`}
            >
              <span
                className="material-symbols-outlined text-[18px]"
                style={{ fontVariationSettings: pathname === "/" ? "'FILL' 1" : "'FILL' 0" }}
              >
                home
              </span>
              <span>Bosh Sahifa</span>
            </Link>

            {/* 2. Katalog */}
            <Link
              href="/catalog"
              className={`flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all ${
                pathname.startsWith("/catalog")
                  ? "bg-white/15 text-white font-bold border-l-2 border-primary-container"
                  : "text-text-secondary hover:bg-white/5 hover:text-white font-medium"
              }`}
            >
              <span className="material-symbols-outlined text-[18px]">grid_view</span>
              <span>Katalog</span>
            </Link>

            {/* 3. Seriallar */}
            <Link
              href="/series"
              className={`flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all ${
                pathname.startsWith("/series")
                  ? "bg-white/15 text-white font-bold border-l-2 border-primary-container"
                  : "text-text-secondary hover:bg-white/5 hover:text-white font-medium"
              }`}
            >
              <span className="material-symbols-outlined text-[18px]">live_tv</span>
              <span>Seriallar</span>
            </Link>

            {/* 4. Franshizalar & To'plamlar */}
            <Link
              href="/collections"
              className={`flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all ${
                pathname.startsWith("/collections")
                  ? "bg-white/15 text-white font-bold border-l-2 border-primary-container"
                  : "text-text-secondary hover:bg-white/5 hover:text-white font-medium"
              }`}
            >
              <span className="material-symbols-outlined text-[18px]">explore</span>
              <span>Franshizalar & To'plamlar</span>
            </Link>

            {/* 5. Premyeralar */}
            <Link
              href="/premieres"
              className={`flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all ${
                pathname === "/premieres"
                  ? "bg-white/15 text-white font-bold border-l-2 border-primary-container"
                  : "text-text-secondary hover:bg-white/5 hover:text-white font-medium"
              }`}
            >
              <span className="material-symbols-outlined text-[18px]">theaters</span>
              <span>Premyeralar</span>
            </Link>

            {/* 6. Aktyorlar */}
            <Link
              href="/actors"
              className={`flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all ${
                pathname === "/actors"
                  ? "bg-white/15 text-white font-bold border-l-2 border-primary-container"
                  : "text-text-secondary hover:bg-white/5 hover:text-white font-medium"
              }`}
            >
              <span className="material-symbols-outlined text-[18px]">groups</span>
              <span>Aktyorlar</span>
            </Link>

            {/* 7. Obunalar */}
            <Link
              href="/subscriptions"
              className={`flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all ${
                pathname.startsWith("/subscriptions")
                  ? "bg-white/15 text-white font-bold border-l-2 border-primary-container"
                  : "text-text-secondary hover:bg-white/5 hover:text-white font-medium"
              }`}
            >
              <span className="material-symbols-outlined text-[18px]">loyalty</span>
              <span>Obunalar</span>
            </Link>

            {/* 8. Kino buyurtma qilish */}
            <Link
              href="/requests"
              className={`flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all ${
                pathname === "/requests"
                  ? "bg-white/15 text-white font-bold border-l-2 border-primary-container"
                  : "text-text-secondary hover:bg-white/5 hover:text-white font-medium"
              }`}
            >
              <span className="material-symbols-outlined text-[18px]">add_to_queue</span>
              <span>Kino buyurtma qilish</span>
            </Link>          </nav>
        </div>

        {/* Sidebar Bottom: Bog'lanish / Yordam (No duplicate dark/light toggle!) */}
        <div className="p-3 border-t border-white/10 text-xs text-text-secondary">
          <a
            href={`https://t.me/${process.env.NEXT_PUBLIC_BOT_USERNAME || "kinochi_mvp_bot"}`}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2.5 px-3 py-2 rounded-xl hover:bg-white/5 hover:text-white transition-all cursor-pointer"
          >
            <span className="material-symbols-outlined text-[18px]">help_outline</span>
            <span>Bog'lanish / Yordam</span>
          </a>
        </div>
      </aside>

      {/* Subtle overlay when sidebar is open on desktop and NOT pinned */}
      {sidebarOpen && !isPinned && (
        <div
          onClick={closeSidebarImmediate}
          className="fixed inset-0 z-50 bg-black/60 backdrop-blur-[2px] transition-opacity duration-300 cursor-pointer"
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
            ? "bg-black/60 backdrop-blur-xl border-white/10 shadow-2xl shadow-black/80 py-3"
            : "bg-black/20 backdrop-blur-md border-white/5 py-4"
        }`}
      >
        <div className="max-w-container-max mx-auto px-gutter flex items-center justify-between gap-3 sm:gap-4 relative">
          
          {/* Left: Hamburger Menu Button + Logo (Animates smoothly out on mobile when search opens) */}
          <div
            className={`flex items-center gap-2 sm:gap-3 shrink-0 transition-all duration-300 ease-[cubic-bezier(0.16,1,0.3,1)] ${
              isMobileSearchOpen
                ? "opacity-0 -translate-x-4 pointer-events-none scale-95 sm:opacity-100 sm:translate-x-0 sm:pointer-events-auto sm:scale-100"
                : "opacity-100 translate-x-0 scale-100"
            }`}
          >
            <button
              type="button"
              onClick={() => {
                if (sidebarOpen) {
                  closeSidebarImmediate();
                } else {
                  openSidebarSmoothly();
                }
              }}
              className="w-9 h-9 sm:w-10 sm:h-10 rounded-xl bg-white/5 hover:bg-white/10 active:bg-white/15 border border-white/10 flex items-center justify-center text-text-secondary hover:text-white transition-all cursor-pointer"
              title="Menyu"
              aria-label="Menyuni ochish"
            >
              <span className="material-symbols-outlined text-[20px] sm:text-[22px]">
                {sidebarOpen ? "close" : "menu"}
              </span>
            </button>
            <Link href="/" className="flex items-center gap-2 group">
              <span className="font-display-hero text-2xl sm:text-3xl font-black tracking-wider text-white group-hover:opacity-95 transition-opacity">
                Media<span className="text-primary-container">Plus</span>
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
            className={`flex items-center gap-2 sm:gap-3 shrink-0 transition-all duration-300 ease-[cubic-bezier(0.16,1,0.3,1)] ${
              isMobileSearchOpen
                ? "opacity-0 translate-x-4 pointer-events-none scale-95 sm:opacity-100 sm:translate-x-0 sm:pointer-events-auto sm:scale-100"
                : "opacity-100 translate-x-0 scale-100"
            }`}
          >
            {/* Mobile Search Button (Tap to expand search bar & animate logo out) */}
            <button
              type="button"
              onClick={() => setIsMobileSearchOpen(true)}
              className="sm:hidden w-9 h-9 rounded-full border border-white/10 hover:border-white/20 transition-all duration-200 bg-white/5 hover:bg-white/10 flex items-center justify-center text-text-secondary hover:text-white cursor-pointer active:scale-95"
              aria-label="Qidiruv"
              title="Qidiruvni ochish"
            >
              <span className="material-symbols-outlined text-[20px]">
                search
              </span>
            </button>

            {/* 1. Dark / Light Mode Toggle */}
            <ThemeToggle />

            {/* 2. Notifications Button */}
            <Link
              href="/notifications"
              className="relative w-9 h-9 sm:w-10 sm:h-10 rounded-full border border-white/10 hover:border-white/20 transition-all duration-200 bg-white/5 hover:bg-white/10 flex items-center justify-center text-text-secondary hover:text-white cursor-pointer group active:scale-95"
              aria-label="Bildirishnomalar"
              title="Bildirishnomalar"
            >
              <span className="material-symbols-outlined text-[20px] sm:text-[22px]">
                notifications
              </span>
              {hasUnread && (
                <span className="absolute top-2 right-2 w-2 h-2 bg-primary-container rounded-full animate-pulse shadow-sm shadow-primary-container" />
              )}
            </Link>

            {/* 3. Profile Avatar / Button */}
            <Link
              href="/profile"
              className="relative w-9 h-9 sm:w-10 sm:h-10 rounded-full border border-white/10 hover:border-white/20 transition-all duration-200 bg-white/5 hover:bg-white/10 flex items-center justify-center text-text-secondary hover:text-white cursor-pointer group active:scale-95 overflow-hidden"
              aria-label="Mening Profilim"
              title="Profil sahifasi"
            >
              {status === "authenticated" && user?.first_name ? (
                <span className="font-bold text-xs sm:text-sm text-text-primary">
                  {user.first_name.charAt(0)}
                </span>
              ) : (
                <span className="material-symbols-outlined text-[20px] sm:text-[22px]">
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
              className="w-9 h-9 rounded-xl bg-white/5 hover:bg-white/10 active:bg-white/15 border border-white/10 flex items-center justify-center text-text-secondary hover:text-white transition-all shrink-0 cursor-pointer active:scale-95"
              aria-label="Qidiruvni yopish"
              title="Qidiruvni yopish"
            >
              <span className="material-symbols-outlined text-[20px]">
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
