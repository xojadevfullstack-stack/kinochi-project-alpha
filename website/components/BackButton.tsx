"use client";

import { useRouter } from "next/navigation";
import { triggerTelegramHaptic } from "@/lib/telegram";

interface BackButtonProps {
  fallbackUrl?: string;
  className?: string;
  size?: "sm" | "md" | "lg";
  ariaLabel?: string;
  title?: string;
  inline?: boolean;
}

export default function BackButton({
  fallbackUrl = "/",
  className = "",
  size = "md",
  ariaLabel = "Orqaga qaytish",
  title = "Orqaga",
  inline = false,
}: BackButtonProps) {
  const router = useRouter();

  // Dual Back Parity: Unified top header Back lives in Navbar.tsx and floating bottom-right in FloatingBackButton.tsx
  if (!inline) {
    return null;
  }

  const handleBack = (e: React.MouseEvent<HTMLButtonElement>) => {
    e.preventDefault();
    triggerTelegramHaptic("light");

    if (typeof window !== "undefined") {
      // 1. Check if user navigated internally within the same session
      const hasHistory =
        window.history.length > 1 &&
        ((window.history.state && window.history.state.idx > 0) ||
          (document.referrer && document.referrer.includes(window.location.host)));

      if (hasHistory) {
        router.back();
        return;
      }

      // 2. Direct entrance fallback (e.g. from deep link in Telegram)
      const tg = (window as any).Telegram?.WebApp;
      if (tg && tg.initData) {
        window.location.href = fallbackUrl;
        return;
      }

      router.push(fallbackUrl);
    }
  };

  const sizeClasses = {
    sm: "w-9 h-9",
    md: "w-10 h-10 sm:w-11 sm:h-11",
    lg: "w-12 h-12",
  };

  const iconSizes = {
    sm: "w-4 h-4",
    md: "w-5 h-5",
    lg: "w-6 h-6",
  };

  return (
    <button
      type="button"
      onClick={handleBack}
      className={`group relative inline-flex items-center justify-center rounded-xl bg-slate-100 border border-slate-200 text-slate-700 dark:bg-white/5 dark:border-white/10 dark:text-gray-300 hover:bg-primary hover:border-primary hover:text-white dark:hover:bg-primary dark:hover:border-primary dark:hover:text-white active:scale-95 transition-all duration-200 cursor-pointer focus:outline-none focus:ring-2 focus:ring-primary/40 ${sizeClasses[size]} ${className}`}
      aria-label={ariaLabel}
      title={title}
    >
      <svg
        className={`${iconSizes[size]} -translate-x-0.5 text-slate-700 dark:text-gray-300 group-hover:text-white transition-colors duration-200`}
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <polyline points="15 18 9 12 15 6" />
      </svg>
    </button>
  );
}
