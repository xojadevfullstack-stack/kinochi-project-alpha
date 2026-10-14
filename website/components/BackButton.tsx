"use client";

import { useRouter } from "next/navigation";
import { triggerTelegramHaptic } from "@/lib/telegram";

interface BackButtonProps {
  fallbackUrl?: string;
  className?: string;
  size?: "sm" | "md" | "lg";
  ariaLabel?: string;
  title?: string;
}

export default function BackButton({
  fallbackUrl = "/",
  className = "",
  size = "md",
  ariaLabel = "Orqaga qaytish",
  title = "Orqaga",
}: BackButtonProps) {
  const router = useRouter();

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
      className={`group relative inline-flex items-center justify-center rounded-full bg-white/[0.08] hover:bg-white/[0.16] active:scale-90 border border-white/20 hover:border-white/40 shadow-lg shadow-black/40 backdrop-blur-xl transition-all duration-200 cursor-pointer text-white focus:outline-none focus:ring-2 focus:ring-primary-container/40 ${sizeClasses[size]} ${className}`}
      aria-label={ariaLabel}
      title={title}
    >
      <svg
        className={`${iconSizes[size]} -translate-x-0.5 text-white transition-transform duration-200 group-hover:-translate-x-1`}
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2.4"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <polyline points="15 18 9 12 15 6" />
      </svg>
    </button>
  );
}
