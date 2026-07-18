"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState, useEffect } from "react";

export default function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const [isScrolled, setIsScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [hoveredLink, setHoveredLink] = useState<string | null>(null);

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
          <div className="hidden md:flex w-9 h-9 md:w-10 md:h-10 rounded-full overflow-hidden border border-white/10 hover:border-primary-container transition-colors cursor-pointer bg-white/5 items-center justify-center">
            <span className="material-symbols-outlined text-text-secondary text-[20px]" style={{ fontVariationSettings: "'FILL' 0" }}>notifications</span>
          </div>
          
          <div className="w-9 h-9 md:w-10 md:h-10 rounded-full overflow-hidden border border-white/10 hover:border-primary-container transition-colors cursor-pointer bg-white/5 flex items-center justify-center">
            <span className="material-symbols-outlined text-text-secondary">person</span>
          </div>

          {/* Mobile Menu Toggle & Search */}
          <div className="flex md:hidden items-center">
            <Link 
              href="/search"
              className="text-text-primary p-2"
              onClick={() => setMobileMenuOpen(false)}
            >
              <span className="material-symbols-outlined text-[28px]">search</span>
            </Link>
            <button 
              className="text-text-primary p-2"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            >
              <span className="material-symbols-outlined text-3xl">
                {mobileMenuOpen ? "close" : "menu"}
              </span>
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Navigation Menu */}
      <div className={`md:hidden absolute top-0 left-0 w-full h-screen bg-background-obsidian/95 backdrop-blur-xl transition-transform duration-300 ease-in-out ${
        mobileMenuOpen ? "translate-y-0 opacity-100" : "-translate-y-full opacity-0"
      }`}>
        <div className="flex flex-col items-center justify-center h-full gap-8 px-6">
          {/* Mobile Search */}
          <form onSubmit={handleSearch} className="flex w-full max-w-sm items-center bg-white/10 rounded-full px-5 py-3 border border-white/10 focus-within:border-white/30 transition-all">
            <span className="material-symbols-outlined text-text-secondary mr-3 text-[24px]">search</span>
            <input 
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="bg-transparent border-none focus:ring-0 text-text-primary text-lg w-full outline-none placeholder:text-text-secondary" 
              placeholder="Qidirish..." 
            />
          </form>

          {navLinks.map((link) => {
            const isActive = pathname === link.href || (link.href !== '/' && pathname.startsWith(link.href));
            return (
              <Link
                key={link.name}
                href={link.href}
                onClick={() => setMobileMenuOpen(false)}
                className={`text-2xl font-bold tracking-wide transition-colors ${
                  isActive ? "text-primary-container" : "text-text-secondary"
                }`}
              >
                {link.name}
              </Link>
            );
          })}
        </div>
      </div>
    </nav>
  );
}
