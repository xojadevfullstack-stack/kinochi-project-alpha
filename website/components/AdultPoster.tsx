"use client";

import { useState } from "react";
import Image from "next/image";

import { useAgeVerification } from "@/hooks/useAgeVerification";

interface AdultPosterProps {
  src: string;
  alt: string;
  is18Plus?: boolean;
  isDetailPage?: boolean;
  fill?: boolean;
  priority?: boolean;
  sizes?: string;
  className?: string;
  imageClassName?: string;
  showWarningBadge?: boolean;
}

export default function AdultPoster({
  src,
  alt,
  is18Plus = false,
  isDetailPage = false,
  fill = true,
  priority = false,
  sizes,
  className = "",
  imageClassName = "",
  showWarningBadge = true,
}: AdultPosterProps) {
  const { isMounted, isVerified } = useAgeVerification();
  const [hasError, setHasError] = useState(false);

  if (hasError || !src) {
    return (
      <div className={`w-full h-full flex flex-col items-center justify-center bg-surface-container-high text-gray-500 ${className}`}>
        <span className="material-symbols-outlined text-4xl mb-2 opacity-30">movie</span>
      </div>
    );
  }

  // If not 18+, render standard image
  if (!is18Plus) {
    return (
      <Image
        src={src}
        alt={alt}
        fill={fill}
        priority={priority}
        sizes={sizes}
        className={imageClassName || className}
        onError={() => setHasError(true)}
      />
    );
  }

  // Adult content:
  // On cards/listings (not detail page), ALWAYS keep blurred with 18+ indicator.
  // On movie/series detail page, keep blurred until user explicitly confirms age for that page.
  const shouldBlur = !isDetailPage ? true : (!isMounted || !isVerified);

  return (
    <>
      <Image
        src={src}
        alt={alt}
        fill={fill}
        priority={priority}
        sizes={sizes}
        className={`${imageClassName || className} transition-all duration-700 ease-out ${
          shouldBlur
            ? "blur-xl scale-110 brightness-75 select-none"
            : "blur-0 scale-100 brightness-100"
        }`}
        onError={() => setHasError(true)}
      />

      {shouldBlur && showWarningBadge && (
        <div
          className="absolute inset-0 z-20 flex flex-col items-center justify-center p-3 bg-black/60 backdrop-blur-xs select-none pointer-events-none"
        >
          <div className="flex flex-col items-center gap-1.5 text-center animate-in fade-in zoom-in-95 duration-300">
            <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-full bg-red-600/30 border-2 border-red-500/60 flex items-center justify-center shadow-lg shadow-red-950/60">
              <span className="text-xl sm:text-2xl">🔞</span>
            </div>
            <span className="px-2 py-0.5 rounded-full bg-red-600/85 text-white text-[10px] sm:text-[11px] font-black uppercase tracking-wider shadow-sm">
              18+ Kattalar uchun
            </span>
          </div>
        </div>
      )}
    </>
  );
}

