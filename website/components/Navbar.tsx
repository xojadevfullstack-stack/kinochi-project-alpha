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
  
  // Dynamic Desktop Sidebar state (Opens ONLY when cursor approaches left edge)
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isPinned, setIsPinned] = useState(false);
  const [bolimlarOpen, setBolimlarOpen] = useState(false);
  const [kolleksiyaOpen, setKolleksiyaOpen] = useState(false);
  
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

  // Close dynamic sidebar on route change if not pinned
  useEffect(() => {
    if (!isPinned) {
      setSidebarOpen(false);
    }
  }, [pathname, isPinned]);

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
      if (typeof window === "undefined" || window.innerWidth < 1280) return;
      if (e.clientX <= 20) {
        openSidebarSmoothly();
      }
    };
    window.addEventListener("mousemove", handleMouseMove, { passive: true });
    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      if (closeTimerRef.current) clearTimeout(closeTimerRef.current);
    };
  }, [openSidebarSmoothly]);

  return (
    <>
      {/* ========================================================
          1. PROXIMITY EDGE SENSOR (Invisible left trigger zone)
      ======================================================== */}
      <div
        onMouseEnter={openSidebarSmoothly}
        className="hidden xl:block fixed top-0 left-0 bottom-0 w-6 z-40 cursor-pointer pointer-events-auto select-none"
        aria-hidden="true"
        title="Sichqonchani yaqinlashtirsangiz saydbar ochiladi"
      />

      {/* ========================================================
          2. MINIMALIST DYNAMIC DESKTOP SIDEBAR
      ======================================================== */}
      <aside
        onMouseEnter={openSidebarSmoothly}
        onMouseLeave={closeSidebarSmoothly}
        className={`hidden xl:flex fixed top-0 left-0 bottom-0 w-72 z-50 bg-[#0c0d10]/98 backdrop-blur-2xl border-r border-white/10 shadow-[20px_0_50px_rgba(0,0,0,0.85)] flex-col justify-between select-none transition-transform duration-300 ease-[cubic-bezier(0.16,1,0.3,1)] ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
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
                title={isPinned ? "Mahkamlangan (Har doim ochiq)" : "Ekranga mahkamlash"}
              >
                <span className="material-symbols-outlined text-[16px]">
                  {isPinned ? "keep" : "push_pin"}
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

          {/* Minimalist Navigation Links (Consistent vector style) */}
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

            {/* 2. Katalog (Uniform styling - No contrast badge) */}
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

            {/* 3. Obunalar (Followed content / Subscriptions) */}
            <Link
              href="/subscriptions"
              className={`flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all ${
                pathname === "/subscriptions"
                  ? "bg-white/15 text-white font-bold border-l-2 border-primary-container"
                  : "text-text-secondary hover:bg-white/5 hover:text-white font-medium"
              }`}
            >
              <span className="material-symbols-outlined text-[18px]">loyalty</span>
              <span>Obunalar</span>
            </Link>

            {/* 4. Bo'limlar (Matching exact screenshot list) */}
            <div className="pt-1">
              <button
                onClick={() => setBolimlarOpen(prev => !prev)}
                className="w-full flex items-center justify-between px-3 py-2 rounded-xl text-text-secondary hover:bg-white/5 hover:text-white transition-all cursor-pointer font-medium"
              >
                <div className="flex items-center gap-3">
                  <span className="material-symbols-outlined text-[18px]">format_list_bulleted</span>
                  <span>Bo'limlar</span>
                </div>
                <span className="material-symbols-outlined text-[16px]">
                  {bolimlarOpen ? "expand_less" : "expand_more"}
                </span>
              </button>

              {bolimlarOpen && (
                <div className="pl-6 pr-1 py-1 space-y-0.5 text-text-secondary font-medium">
                  <Link
                    href="/movies"
                    className="flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg hover:text-white hover:bg-white/5 transition text-xs"
                  >
                    <span className="material-symbols-outlined text-[15px] opacity-70">movie</span>
                    <span>Tarjima kinolar</span>
                  </Link>
                  <Link
                    href="/catalog?category=hind"
                    className="flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg hover:text-white hover:bg-white/5 transition text-xs"
                  >
                    <span className="material-symbols-outlined text-[15px] opacity-70">language</span>
                    <span>Hind kinolari</span>
                  </Link>
                  <Link
                    href="/catalog?category=turk"
                    className="flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg hover:text-white hover:bg-white/5 transition text-xs"
                  >
                    <span className="material-symbols-outlined text-[15px] opacity-70">videocam</span>
                    <span>Turk kinolari</span>
                  </Link>
                  <Link
                    href="/series?category=turk"
                    className="flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg hover:text-white hover:bg-white/5 transition text-xs"
                  >
                    <span className="material-symbols-outlined text-[15px] opacity-70">tv</span>
                    <span>Turk seriali</span>
                  </Link>
                  <Link
                    href="/series"
                    className="flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg hover:text-white hover:bg-white/5 transition text-xs"
                  >
                    <span className="material-symbols-outlined text-[15px] opacity-70">live_tv</span>
                    <span>Seriallar</span>
                  </Link>
                  <Link
                    href="/catalog?genre=animation"
                    className="flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg hover:text-white hover:bg-white/5 transition text-xs"
                  >
                    <span className="material-symbols-outlined text-[15px] opacity-70">smart_toy</span>
                    <span>Multfilmlar</span>
                  </Link>
                  <Link
                    href="/catalog?category=treyler"
                    className="flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg hover:text-white hover:bg-white/5 transition text-xs"
                  >
                    <span className="material-symbols-outlined text-[15px] opacity-70">star</span>
                    <span>Treylerlar</span>
                  </Link>
                  <Link
                    href="/tv"
                    className="flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg hover:text-white hover:bg-white/5 transition text-xs"
                  >
                    <span className="material-symbols-outlined text-[15px] opacity-70">tv</span>
                    <span>Onlayn TV</span>
                  </Link>
                  <Link
                    href="/movies"
                    className="flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg hover:text-white hover:bg-white/5 transition text-xs"
                  >
                    <span className="material-symbols-outlined text-[15px] opacity-70">theaters</span>
                    <span>Premyeralar</span>
                  </Link>
                </div>
              )}
            </div>

            {/* 5. Kolleksiyalar (Matching exact screenshot list) */}
            <div className="pt-1">
              <button
                onClick={() => setKolleksiyaOpen(prev => !prev)}
                className="w-full flex items-center justify-between px-3 py-2 rounded-xl text-text-secondary hover:bg-white/5 hover:text-white transition-all cursor-pointer font-medium"
              >
                <div className="flex items-center gap-3">
                  <span className="material-symbols-outlined text-[18px]">explore</span>
                  <span>Kolleksiyalar</span>
                </div>
                <span className="material-symbols-outlined text-[16px]">
                  {kolleksiyaOpen ? "expand_less" : "expand_more"}
                </span>
              </button>

              {kolleksiyaOpen && (
                <div className="pl-6 pr-1 py-1 space-y-0.5 text-text-secondary font-medium">
                  <Link
                    href="/collections"
                    className="flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg hover:text-white hover:bg-white/5 transition text-xs"
                  >
                    <span className="material-symbols-outlined text-[15px] opacity-70">format_list_bulleted</span>
                    <span>Barchasi</span>
                  </Link>
                  <Link
                    href="/catalog?genre=action"
                    className="flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg hover:text-white hover:bg-white/5 transition text-xs"
                  >
                    <span className="material-symbols-outlined text-[15px] opacity-70">swords</span>
                    <span>Jangari</span>
                  </Link>
                  <Link
                    href="/catalog?genre=comedy"
                    className="flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg hover:text-white hover:bg-white/5 transition text-xs"
                  >
                    <span className="material-symbols-outlined text-[15px] opacity-70">sentiment_very_satisfied</span>
                    <span>Komediya</span>
                  </Link>
                  <Link
                    href="/catalog?genre=horror"
                    className="flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg hover:text-white hover:bg-white/5 transition text-xs"
                  >
                    <span className="material-symbols-outlined text-[15px] opacity-70">skull</span>
                    <span>Qo'rqinchli</span>
                  </Link>
                  <Link
                    href="/catalog?genre=scifi"
                    className="flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg hover:text-white hover:bg-white/5 transition text-xs"
                  >
                    <span className="material-symbols-outlined text-[15px] opacity-70">rocket_launch</span>
                    <span>Fantastika</span>
                  </Link>
                  <Link
                    href="/catalog?genre=drama"
                    className="flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg hover:text-white hover:bg-white/5 transition text-xs"
                  >
                    <span className="material-symbols-outlined text-[15px] opacity-70">theater_comedy</span>
                    <span>Drama</span>
                  </Link>
                  <Link
                    href="/catalog?genre=adventure"
                    className="flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg hover:text-white hover:bg-white/5 transition text-xs"
                  >
                    <span className="material-symbols-outlined text-[15px] opacity-70">flag</span>
                    <span>Sarguzasht</span>
                  </Link>
                  <Link
                    href="/catalog?genre=animation"
                    className="flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg hover:text-white hover:bg-white/5 transition text-xs"
                  >
                    <span className="material-symbols-outlined text-[15px] opacity-70">image</span>
                    <span>Multfilmlar (o'zbek tilida)</span>
                  </Link>
                  <Link
                    href="/series"
                    className="flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg hover:text-white hover:bg-white/5 transition text-xs"
                  >
                    <span className="material-symbols-outlined text-[15px] opacity-70">tv</span>
                    <span>Seriallar (o'zbek tilida)</span>
                  </Link>
                  <Link
                    href="/catalog?category=hind"
                    className="flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg hover:text-white hover:bg-white/5 transition text-xs"
                  >
                    <span className="material-symbols-outlined text-[15px] opacity-70">language</span>
                    <span>Hind kinolari</span>
                  </Link>
                </div>
              )}
            </div>

            {/* 6. Aktyorlar (Uniformly styled like main links - No contrast badge!) */}
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

            {/* 7. Premyeralar */}
            <Link
              href="/movies"
              className={`flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all ${
                pathname === "/movies"
                  ? "bg-white/15 text-white font-bold border-l-2 border-primary-container"
                  : "text-text-secondary hover:bg-white/5 hover:text-white font-medium"
              }`}
            >
              <span className="material-symbols-outlined text-[18px]">theaters</span>
              <span>Premyeralar</span>
            </Link>

            {/* 8. Profilim */}
            <Link
              href="/profile"
              className={`flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all ${
                pathname === "/profile"
                  ? "bg-white/15 text-white font-bold border-l-2 border-primary-container"
                  : "text-text-secondary hover:bg-white/5 hover:text-white font-medium"
              }`}
            >
              <span className="material-symbols-outlined text-[18px]">account_circle</span>
              <span>Profilim</span>
            </Link>
          </nav>
        </div>

        {/* Sidebar Bottom: Bog'lanish / Yordam (No duplicate dark/light toggle!) */}
        <div className="p-3 border-t border-white/10 text-xs text-text-secondary">
          <a
            href="https://t.me/kinochi_uz_bot"
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
          className="hidden xl:block fixed inset-0 z-40 bg-black/40 backdrop-blur-[2px] transition-opacity duration-300"
          aria-hidden="true"
        />
      )}

      {/* ========================================================
          3. MAIN TOP NAVBAR (Desktop & Mobile)
          Clean minimalist header without duplicate hamburger button
      ======================================================== */}
      <nav
        className={`fixed top-0 w-full z-30 transition-all duration-300 ease-out border-b ${
          isScrolled
            ? "bg-background-obsidian/95 backdrop-blur-xl border-white/10 shadow-2xl shadow-black/80 py-3"
            : "bg-gradient-to-b from-background-obsidian/95 via-background-obsidian/75 to-transparent border-transparent py-4"
        }`}
      >
        <div className="max-w-container-max mx-auto px-gutter flex items-center justify-between gap-3 sm:gap-4">
          
          {/* Left: Logo Only (No manual hamburger button - Sidebar opens purely dynamically via hover) */}
          <div className="flex items-center gap-2.5 shrink-0">
            <Link href="/" className="flex items-center gap-2 group">
              <span className="font-display-hero text-2xl sm:text-3xl font-black tracking-wider text-white group-hover:opacity-95 transition-opacity">
                Media<span className="text-primary-container">Plus</span>
              </span>
            </Link>
          </div>

          {/* Center: Wide LiveSearch Input */}
          <div className="flex-1 max-w-xl mx-2 hidden sm:block">
            <LiveSearch
              className="w-full"
              placeholder="Qidiruv: film nomi, aktyor, janr yoki #kod..."
            />
          </div>

          {/* Right Corner Controls: Strictly ordered [1. Dark/Light Mode, 2. Notifications, 3. Profile] */}
          <div className="flex items-center gap-2 sm:gap-3 shrink-0">
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
        </div>
      </nav>
    </>
  );
}
