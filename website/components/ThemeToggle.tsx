"use client";

import { useEffect, useState } from "react";

export default function ThemeToggle({ className = "" }: { className?: string }) {
  const [theme, setTheme] = useState<"dark" | "light">("dark");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    try {
      const saved = localStorage.getItem("kinochi_theme") as "dark" | "light" | null;
      if (saved) {
        setTheme(saved);
        if (saved === "light") {
          document.documentElement.classList.remove("dark");
          document.documentElement.classList.add("light");
        } else {
          document.documentElement.classList.add("dark");
          document.documentElement.classList.remove("light");
        }
      } else {
        // Default to dark
        document.documentElement.classList.add("dark");
      }
    } catch {}
  }, []);

  const toggleTheme = () => {
    const nextTheme = theme === "dark" ? "light" : "dark";
    setTheme(nextTheme);
    try {
      localStorage.setItem("kinochi_theme", nextTheme);
      if (nextTheme === "light") {
        document.documentElement.classList.remove("dark");
        document.documentElement.classList.add("light");
      } else {
        document.documentElement.classList.add("dark");
        document.documentElement.classList.remove("light");
      }
    } catch {}
  };

  if (!mounted) {
    return (
      <div className={`w-9 h-9 sm:w-10 sm:h-10 rounded-full bg-white/5 border border-white/10 ${className}`} />
    );
  }

  return (
    <button
      onClick={toggleTheme}
      className={`relative w-9 h-9 sm:w-10 sm:h-10 rounded-full border border-white/10 hover:border-primary-container hover:text-primary-container transition-all duration-200 bg-white/5 hover:bg-white/10 flex items-center justify-center text-text-secondary cursor-pointer group active:scale-95 ${className}`}
      aria-label="Rejimni almashtirish"
      title={theme === "dark" ? "Kunduzgi rejim" : "Tungi rejim"}
    >
      <span className="material-symbols-outlined text-[20px] sm:text-[22px] text-text-secondary group-hover:text-primary-container transition-transform duration-300 group-hover:rotate-45">
        {theme === "dark" ? "light_mode" : "dark_mode"}
      </span>
    </button>
  );
}
