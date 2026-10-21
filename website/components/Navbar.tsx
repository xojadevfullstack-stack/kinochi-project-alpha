"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState, useEffect, useRef } from "react";
import { useAuth } from "../lib/auth/AuthProvider";
import LiveSearch from "./LiveSearch";
import { fetchApi } from "../lib/api";
import ThemeToggle from "./ThemeToggle";

export default function Navbar({ pages = [] }: { pages: any[] }) {
  const pathname = usePathname();
  const router = useRouter();
  const { status, user, logout } = useAuth();
  const [isScrolled, setIsScrolled] = useState(false);
  const [hasUnread, setHasUnread] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarPinned, setSidebarPinned] = useState(false);
  const [sectionsExpanded, setSectionsExpanded] = useState(false);
  const [collectionsExpanded, setCollectionsExpanded] = useState(false);
  const sidebarHoverTimerRef = useRef<NodeJS.Timeout | null>(null);

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

    const interval = setInterval(checkFreshUnread, 60000);

    return () => {
      isCancelled = true;
      clearInterval(interval);
      window.removeEventListener("kinochi_notifications_updated", updateUnreadStatus);
      window.removeEventListener("storage", updateUnreadStatus);
      window.removeEventListener("focus", checkFreshUnread);
    };
  }, [status]);

  // Handle scroll for navbar background
  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  // Close dynamic sidebar on route change
  useEffect(() => {
    if (!sidebarPinned) {
      setSidebarOpen(false);
    }
  }, [pathname, sidebarPinned]);

  const handleSidebarMouseEnter = () => {
    if (sidebarHoverTimerRef.current) clearTimeout(sidebarHoverTimerRef.current);
    setSidebarOpen(true);
  };

  const handleSidebarMouseLeave = () => {
    if (!sidebarPinned) {
      sidebarHoverTimerRef.current = setTimeout(() => {
        setSidebarOpen(false);
      }, 300);
    }
  };

  return (
    <>
      {/* ===================== DESKTOP DYNAMIC SIDEBAR ===================== */}
      {/* Left Hover Trigger Zone: Invisible 16px hover sensor + slim launcher button on desktop */}
      <div 
        className="hidden xl:block fixed top-0 left-0 bottom-0 w-4 z-40"
        onMouseEnter={handleSidebarMouseEnter}
      />

      {/* Slim Floating Sidebar Trigger Pill (Hover on this opens sidebar immediately) */}
      <div 
        className="hidden xl:flex fixed top-24 left-2 z-40 bg-surface-container/90 hover:bg-surface-container-high border border-white/10 hover:border-primary-container text-text-secondary hover:text-white p-2 rounded-xl backdrop-blur-md shadow-2xl transition-all cursor-pointer items-center justify-center group"
        onMouseEnter={handleSidebarMouseEnter}
        onClick={() => setSidebarOpen(prev => !prev)}
        title="Menyuni ochish"
      >
        <span className="material-symbols-outlined text-[22px] group-hover:text-primary-container transition-colors">
          menu_open
        </span>
      </div>

      {/* Slide-out Dynamic Sidebar Container */}
      <aside
        onMouseEnter={handleSidebarMouseEnter}
        onMouseLeave={handleSidebarMouseLeave}
        className={`hidden xl:flex fixed top-0 left-0 bottom-0 w-72 z-50 bg-background-obsidian/95 backdrop-blur-2xl border-r border-white/10 shadow-[20px_0_50px_rgba(0,0,0,0.85)] flex-col justify-between transition-transform duration-300 ease-out select-none ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex-1 overflow-y-auto hide-scrollbar p-4 space-y-4">
          
          {/* Sidebar Top: Logo & Pin Button */}
          <div className="flex items-center justify-between pb-3 border-b border-white/10">
            <Link href="/" className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-primary-container flex items-center justify-center text-white font-black text-lg shadow-lg shadow-black/40">
                <span className="material-symbols-outlined text-xl">play_arrow</span>
              </div>
              <div>
                <span className="text-xl font-black tracking-wider text-white font-headline-md">
                  Media<span className="text-primary-container">Plus</span>
                </span>
                <span className="block text-[9px] uppercase tracking-widest text-text-secondary font-bold -mt-1">
                  Kinochi Portal
                </span>
              </div>
            </Link>

            <button
              onClick={() => setSidebarPinned(prev => !prev)}
              className={`w-7 h-7 rounded-lg flex items-center justify-center transition-colors ${
                sidebarPinned ? "bg-primary-container text-white" : "text-text-secondary hover:text-white hover:bg-white/10"
              }`}
              title={sidebarPinned ? "Avto-yopilishni yoqish" : "Ekranga mahkamlash"}
            >
              <span className="material-symbols-outlined text-base">push_pin</span>
            </button>
          </div>

          {/* User Profile Info Card in Sidebar */}
          <Link
            href="/profile"
            className="block p-3 rounded-xl bg-surface-container hover:bg-surface-container-high border border-white/10 transition group"
          >
            <div className="flex items-center gap-3">
              <div className="relative">
                <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-primary-container to-rating-gold p-0.5">
                  <div className="w-full h-full bg-background-obsidian rounded-full flex items-center justify-center font-bold text-xs text-white">
                    {user?.first_name?.charAt(0) || "U"}
                  </div>
                </div>
                <span className="absolute bottom-0 right-0 w-2.5 h-2.5 bg-primary-container border-2 border-surface-container rounded-full"></span>
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-xs font-bold text-text-primary truncate group-hover:text-primary-container transition-colors">
                  {user ? `${user.first_name || ""} ${user.last_name || ""}`.trim() : "Mening Profilim"}
                </div>
                <div className="text-[10px] text-rating-gold font-semibold flex items-center gap-1">
                  <span className="material-symbols-outlined text-xs">verified</span>
                  {status === "authenticated" ? "VIP Obunachi" : "Mehmon (Kirish)"}
                </div>
              </div>
            </div>

            {/* Quick Messages Link */}
            <div className="mt-2.5 pt-2 border-t border-white/5 flex items-center justify-between text-xs text-text-secondary">
              <span className="flex items-center gap-1.5">
                <span className="material-symbols-outlined text-sm text-primary-container">notifications</span>
                Habarlar
              </span>
              {hasUnread && (
                <span className="px-1.5 py-0.2 bg-primary-container text-white text-[9px] font-bold rounded-full">
                  yangi
                </span>
              )}
            </div>
          </Link>

          {/* Sidebar Nav Links */}
          <nav className="space-y-1 text-sm font-semibold">
            {/* 1. Bosh Sahifa */}
            <Link
              href="/"
              className={`flex items-center gap-3 px-3 py-2.5 rounded-xl transition ${
                pathname === "/"
                  ? "bg-primary-container/15 text-primary-container border-l-4 border-primary-container font-bold"
                  : "text-text-secondary hover:text-white hover:bg-white/5"
              }`}
            >
              <span className="material-symbols-outlined text-xl" style={{ fontVariationSettings: pathname === "/" ? "'FILL' 1" : "'FILL' 0" }}>
                home
              </span>
              <span>Bosh Sahifa</span>
            </Link>

            {/* 2. To'laqonli KATALOG sahifasi */}
            <Link
              href="/catalog"
              className={`flex items-center justify-between px-3 py-2.5 rounded-xl transition ${
                pathname.startsWith("/catalog")
                  ? "bg-primary-container/15 text-primary-container border-l-4 border-primary-container font-bold"
                  : "text-text-secondary hover:text-white hover:bg-white/5"
              }`}
            >
              <div className="flex items-center gap-3">
                <span className="material-symbols-outlined text-xl">grid_view</span>
                <span>Katalog</span>
              </div>
              <span className="text-[10px] bg-primary-container/20 text-primary-container px-1.5 py-0.5 rounded font-bold border border-primary-container/30">
                To'liq
              </span>
            </Link>

            {/* 3. Obunalar */}
            <Link
              href="/achievements"
              className={`flex items-center justify-between px-3 py-2.5 rounded-xl transition ${
                pathname.startsWith("/achievements")
                  ? "bg-primary-container/15 text-primary-container border-l-4 border-primary-container font-bold"
                  : "text-text-secondary hover:text-white hover:bg-white/5"
              }`}
            >
              <div className="flex items-center gap-3">
                <span className="material-symbols-outlined text-xl text-rating-gold">loyalty</span>
                <span>Obunalar</span>
              </div>
              <span className="text-[10px] bg-white/10 text-rating-gold px-1.5 py-0.5 rounded font-bold">VIP</span>
            </Link>

            {/* 4. Bo'limlar (Accordion: Aktyorlar ichida!) */}
            <div>
              <button
                onClick={() => setSectionsExpanded(prev => !prev)}
                className="w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-text-secondary hover:text-white hover:bg-white/5 transition"
              >
                <div className="flex items-center gap-3">
                  <span className="material-symbols-outlined text-xl">category</span>
                  <span>Bo'limlar</span>
                </div>
                <span className="material-symbols-outlined text-base">
                  {sectionsExpanded ? "expand_less" : "expand_more"}
                </span>
              </button>

              {sectionsExpanded && (
                <div className="pl-7 pr-2 py-1 space-y-0.5 text-xs text-text-secondary animate-in slide-in-from-top-1">
                  <Link href="/movies" className="block px-2.5 py-1.5 rounded-lg hover:text-white hover:bg-white/5">
                    🎬 Tarjima kinolar
                  </Link>
                  <Link href="/series" className="block px-2.5 py-1.5 rounded-lg hover:text-white hover:bg-white/5">
                    📺 Seriallar
                  </Link>
                  {pages.map(p => (
                    <Link key={p.id} href={`/p/${p.slug}`} className="block px-2.5 py-1.5 rounded-lg hover:text-white hover:bg-white/5">
                      ⭐ {p.title}
                    </Link>
                  ))}
                  {/* Aktyorlar bo'lim ichiga kirdi! */}
                  <Link
                    href="/catalog?tab=actors"
                    className="flex items-center justify-between px-2.5 py-1.5 rounded-lg bg-primary-container/10 text-primary-container font-bold border border-primary-container/20"
                  >
                    <span className="flex items-center gap-1.5">
                      <span className="material-symbols-outlined text-sm">groups</span>
                      Aktyorlar
                    </span>
                    <span className="text-[9px] bg-primary-container/20 text-white px-1 rounded">Bo'limda</span>
                  </Link>
                </div>
              )}
            </div>

            {/* 5. Kolleksiyalar */}
            <div>
              <button
                onClick={() => setCollectionsExpanded(prev => !prev)}
                className="w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-text-secondary hover:text-white hover:bg-white/5 transition"
              >
                <div className="flex items-center gap-3">
                  <span className="material-symbols-outlined text-xl text-rating-gold">collections_bookmark</span>
                  <span>Kolleksiyalar</span>
                </div>
                <span className="material-symbols-outlined text-base">
                  {collectionsExpanded ? "expand_less" : "expand_more"}
                </span>
              </button>

              {collectionsExpanded && (
                <div className="pl-7 pr-2 py-1 space-y-0.5 text-xs text-text-secondary animate-in slide-in-from-top-1">
                  <Link href="/collections" className="block px-2.5 py-1.5 rounded-lg hover:text-white hover:bg-white/5">
                    ✨ Barcha to'plamlar
                  </Link>
                  <Link href="/collections" className="block px-2.5 py-1.5 rounded-lg hover:text-white hover:bg-white/5">
                    💥 Marvel & DC Kinolari
                  </Link>
                  <Link href="/collections" className="block px-2.5 py-1.5 rounded-lg hover:text-white hover:bg-white/5">
                    🇺🇿 O'zbekcha Saralanganlar
                  </Link>
                </div>
              )}
            </div>

            {/* 6. Premyeralar */}
            <Link
              href="/movies"
              className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-text-secondary hover:text-white hover:bg-white/5 transition"
            >
              <span className="material-symbols-outlined text-xl">theaters</span>
              <span>Premyeralar</span>
            </Link>

            {/* 7. Profil sahifasi */}
            <Link
              href="/profile"
              className={`flex items-center gap-3 px-3 py-2.5 rounded-xl transition ${
                pathname.startsWith("/profile")
                  ? "bg-primary-container/15 text-primary-container border-l-4 border-primary-container font-bold"
                  : "text-text-secondary hover:text-white hover:bg-white/5"
              }`}
            >
              <span className="material-symbols-outlined text-xl text-sky-400">account_circle</span>
              <span>Profilim (Sahifa)</span>
            </Link>
          </nav>
        </div>

        {/* Sidebar Bottom: Theme & Contact */}
        <div className="p-3 border-t border-white/10 space-y-1 text-xs text-text-secondary">
          <div className="flex items-center justify-between px-3 py-2 rounded-xl bg-white/5">
            <span className="flex items-center gap-2">
              <span className="material-symbols-outlined text-base">brightness_6</span>
              Rejim
            </span>
            <ThemeToggle />
          </div>
          <a
            href="https://t.me/kinochi_uz_bot"
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-2 px-3 py-2 rounded-xl hover:bg-white/5 hover:text-white transition"
          >
            <span className="material-symbols-outlined text-base">mail</span>
            <span>Bog'lanish / Yordam</span>
          </a>
        </div>
      </aside>

      {/* ===================== TOP HEADER (NAVBAR) ===================== */}
      <nav 
        className={`fixed top-0 w-full z-40 transition-all duration-300 ease-out border-b ${
          isScrolled 
            ? "bg-background-obsidian/95 backdrop-blur-lg border-white/10 shadow-2xl shadow-black/60 py-2.5" 
            : "bg-gradient-to-b from-background-obsidian/90 to-transparent border-transparent py-3.5"
        }`}
      >
        <div className="max-w-container-max mx-auto px-gutter flex items-center justify-between gap-3 sm:gap-4">
          
          {/* Left: Logo & Sidebar Toggle */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen(prev => !prev)}
              className="hidden xl:flex w-9 h-9 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-text-secondary hover:text-white items-center justify-center transition cursor-pointer"
              title="Kinochi menyusi"
            >
              <span className="material-symbols-outlined text-xl">menu</span>
            </button>

            <Link href="/" className="flex items-center gap-2 group z-40">
              <span className="font-display-hero text-2xl sm:text-3xl font-black tracking-wider text-white group-hover:opacity-90 transition-opacity">
                Media<span className="text-primary-container">Plus</span>
              </span>
            </Link>
          </div>

          {/* Center: Wide LiveSearch on Desktop */}
          <div className="hidden md:flex flex-1 max-w-xl mx-4">
            <LiveSearch
              className="w-full"
              placeholder="Qidiruv: Kino, serial yoki #kod yozing..."
            />
          </div>

          {/* Right Header Controls (MOBILE VA DESKTOPDA O'NG BURCHAKDA) */}
          {/* USER TALABI: Mobileda tartib aniq -> 1. dark/lightmode, 2. notification, 3. profile */}
          <div className="flex items-center gap-2 sm:gap-2.5 shrink-0 z-40">
            
            {/* 1. Dark / Light Mode Toggle */}
            <ThemeToggle />

            {/* 2. Notification Button */}
            <Link 
              href="/notifications"
              className="relative w-9 h-9 sm:w-10 sm:h-10 rounded-full border border-white/10 hover:border-primary-container hover:text-primary-container transition-all duration-200 bg-white/5 hover:bg-white/10 flex items-center justify-center text-text-secondary cursor-pointer group active:scale-95"
              aria-label="Bildirishnomalar"
            >
              <span className="material-symbols-outlined text-[20px] sm:text-[22px] text-text-secondary group-hover:text-primary-container transition-colors">
                notifications
              </span>
              {hasUnread && (
                <span className="absolute top-2 right-2 w-2 h-2 bg-primary-container rounded-full animate-pulse"></span>
              )}
            </Link>

            {/* 3. Profile Button (Alohida Profil Sahifasiga olib boradi!) */}
            <Link
              href="/profile"
              className="w-9 h-9 sm:w-10 sm:h-10 rounded-full border border-white/10 hover:border-primary-container hover:text-primary-container transition-all duration-200 bg-white/5 hover:bg-white/10 flex items-center justify-center text-text-secondary cursor-pointer group active:scale-95 overflow-hidden"
              aria-label="Mening Profilim"
            >
              {status === "authenticated" ? (
                <span className="font-bold text-xs sm:text-sm text-text-primary group-hover:text-primary-container">
                  {user?.first_name?.charAt(0) || "U"}
                </span>
              ) : (
                <span className="material-symbols-outlined text-[20px] sm:text-[22px] text-text-secondary group-hover:text-primary-container">
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
