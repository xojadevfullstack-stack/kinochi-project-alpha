"use client";

import { useEffect, useState } from "react";

function applyThemeClasses(theme: "dark" | "light") {
  if (typeof document === "undefined") return;
  const html = document.documentElement;
  const body = document.body;
  if (theme === "light") {
    html.classList.remove("dark");
    html.classList.add("light");
    body?.classList.add("light-theme");
  } else {
    html.classList.add("dark");
    html.classList.remove("light");
    body?.classList.remove("light-theme");
  }
}

export default function ThemeToggle({ className = "" }: { className?: string }) {
  const [theme, setTheme] = useState<"dark" | "light">("dark");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    try {
      const saved = localStorage.getItem("kinochi_theme") as "dark" | "light" | null;
      const resolved: "dark" | "light" = saved === "light" ? "light" : "dark";
      setTheme(resolved);
      applyThemeClasses(resolved);
    } catch {
      applyThemeClasses("dark");
    }
  }, []);

  const toggleTheme = () => {
    const nextTheme: "dark" | "light" = theme === "dark" ? "light" : "dark";
    setTheme(nextTheme);
    try {
      localStorage.setItem("kinochi_theme", nextTheme);
    } catch {}
    applyThemeClasses(nextTheme);
  };

  if (!mounted) {
    return (
      <div className={`w-9 h-9 sm:w-10 sm:h-10 rounded-full bg-white/5 border border-white/10 ${className}`} />
    );
  }

  return (
    <button
      type="button"
      onClick={toggleTheme}
      className={`header-icon-btn relative w-9 h-9 sm:w-10 sm:h-10 rounded-full border border-slate-300/80 dark:border-white/10 bg-slate-100/80 dark:bg-white/5 text-slate-700 dark:text-text-secondary hover:bg-[#B80710] dark:hover:bg-[#E50914] hover:border-[#B80710] dark:hover:border-[#E50914] hover:text-white flex items-center justify-center transition-all duration-200 cursor-pointer group active:scale-95 ${className}`}
      aria-label="Rejimni almashtirish"
      title={theme === "dark" ? "Kunduzgi rejim" : "Tungi rejim"}
    >
      <span className="material-symbols-outlined text-[20px] sm:text-[22px] transition-transform duration-300 group-hover:rotate-45 group-hover:text-white">
        {theme === "dark" ? "light_mode" : "dark_mode"}
      </span>
    </button>
  );
}
