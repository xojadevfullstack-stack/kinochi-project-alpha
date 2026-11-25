import React from "react";
import Image from "next/image";

interface MediaLoaderProps {
  variant?: "spinner" | "cardGrid" | "detail" | "inline";
  label?: string;
  count?: number;
  className?: string;
}

/**
 * Unified MediaPlus loading indicator & skeleton system.
 * Uses Primary Red (#E50914) accents and respects low-end reduced motion.
 */
export default function MediaLoader({
  variant = "spinner",
  label = "Yuklanmoqda...",
  count = 12,
  className = "",
}: MediaLoaderProps) {
  if (variant === "inline") {
    return (
      <span className={`inline-flex items-center gap-2 ${className}`}>
        <span
          className="w-4 h-4 rounded-full border-2 border-[#E50914] border-t-transparent animate-spin shrink-0"
          aria-hidden="true"
        />
        {label ? <span className="text-xs font-medium">{label}</span> : null}
      </span>
    );
  }

  if (variant === "cardGrid") {
    return (
      <div
        className={`max-w-container-max mx-auto px-gutter py-6 sm:py-8 ${className}`}
        aria-busy="true"
        aria-label={label}
      >
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-2.5">
            <span className="w-1.5 h-6 rounded-full bg-[#E50914]/80" />
            <div className="h-6 w-44 rounded-lg bg-slate-200 dark:bg-white/10 animate-pulse" />
          </div>
          <div className="h-8 w-24 rounded-full bg-slate-200/80 dark:bg-white/5 animate-pulse" />
        </div>
        <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 gap-3 sm:gap-4">
          {Array.from({ length: count }).map((_, idx) => (
            <div key={idx} className="flex flex-col gap-2">
              <div className="aspect-[2/3] w-full rounded-2xl bg-slate-200/80 dark:bg-white/[0.06] border border-slate-200 dark:border-white/5 animate-pulse" />
              <div className="h-3.5 w-4/5 rounded bg-slate-200/80 dark:bg-white/[0.06] animate-pulse" />
              <div className="h-2.5 w-1/2 rounded bg-slate-200/60 dark:bg-white/[0.04] animate-pulse" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (variant === "detail") {
    return (
      <div
        className={`max-w-7xl mx-auto px-3 sm:px-6 py-6 ${className}`}
        aria-busy="true"
        aria-label={label}
      >
        <div className="rounded-3xl border border-slate-200 dark:border-white/10 bg-white dark:bg-[#0E1117]/80 p-5 sm:p-10 flex flex-col md:flex-row gap-6 sm:gap-8 items-center">
          <div className="w-40 sm:w-56 md:w-68 aspect-[2/3] rounded-2xl bg-slate-200 dark:bg-white/[0.07] animate-pulse shrink-0" />
          <div className="flex-1 w-full space-y-4">
            <div className="flex items-center gap-2">
              <span className="w-5 h-5 rounded-full border-2 border-[#E50914] border-t-transparent animate-spin" />
              <span className="text-xs font-semibold text-slate-500 dark:text-gray-400">{label}</span>
            </div>
            <div className="h-9 w-3/4 rounded-xl bg-slate-200 dark:bg-white/[0.08] animate-pulse" />
            <div className="h-4 w-1/2 rounded-lg bg-slate-200/70 dark:bg-white/[0.05] animate-pulse" />
            <div className="flex gap-2 pt-2">
              <div className="h-11 w-40 rounded-full bg-[#E50914]/30 animate-pulse" />
              <div className="h-11 w-32 rounded-full bg-slate-200 dark:bg-white/[0.07] animate-pulse" />
            </div>
            <div className="h-20 w-full rounded-xl bg-slate-200/60 dark:bg-white/[0.04] animate-pulse" />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      className={`flex flex-col items-center justify-center gap-3 py-12 px-4 text-center ${className}`}
      role="status"
      aria-live="polite"
    >
      <div className="relative flex items-center justify-center w-14 h-14">
        <span className="absolute inset-0 rounded-full border-[3px] border-slate-200 dark:border-white/10" />
        <span className="absolute inset-0 rounded-full border-[3px] border-[#E50914] border-t-transparent animate-spin" />
        <Image
          src="/logo-mediaplus-icon.png"
          alt="MediaPlus"
          width={28}
          height={28}
          unoptimized
          className="w-7 h-7 rounded-lg object-cover"
        />
      </div>
      {label ? (
        <p className="text-xs sm:text-sm font-medium text-text-secondary">{label}</p>
      ) : null}
    </div>
  );
}
