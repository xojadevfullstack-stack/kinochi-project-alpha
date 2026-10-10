"use client";

import Image from "next/image";
import { useAgeVerification } from "@/hooks/useAgeVerification";

interface AdultPosterProps {
  src: string;
  alt: string;
  is18Plus?: boolean;
  fill?: boolean;
  priority?: boolean;
  sizes?: string;
  className?: string;
  imageClassName?: string;
  showWarningBadge?: boolean;
  onVerifyClick?: () => void;
}

export default function AdultPoster({
  src,
  alt,
  is18Plus = false,
  fill = true,
  priority = false,
  sizes,
  className = "",
  imageClassName = "",
  showWarningBadge = true,
  onVerifyClick,
}: AdultPosterProps) {
  const { isMounted, isVerified, openVerificationModal } = useAgeVerification();

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
      />
    );
  }

  // Adult content: before mount or if not verified, show heavy blur
  const shouldBlur = !isMounted || !isVerified;

  const handleVerifyClick = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (onVerifyClick) {
      onVerifyClick();
    } else {
      openVerificationModal();
    }
  };

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
      />

      {shouldBlur && (
        <div
          onClick={handleVerifyClick}
          className="absolute inset-0 z-20 flex flex-col items-center justify-center p-3 bg-black/50 backdrop-blur-xs select-none cursor-pointer transition-all hover:bg-black/60 group/blur"
          title="18+ Kontent. Yoshni tasdiqlash uchun bosing."
        >
          {showWarningBadge && (
            <div className="flex flex-col items-center gap-1.5 text-center animate-in fade-in zoom-in-95 duration-300">
              <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-full bg-red-600/30 border-2 border-red-500/60 flex items-center justify-center shadow-lg shadow-red-950/60 group-hover/blur:scale-110 transition-transform">
                <span className="text-xl sm:text-2xl">🔞</span>
              </div>
              <span className="px-2 py-0.5 rounded-full bg-red-600/80 text-white text-[10px] sm:text-[11px] font-black uppercase tracking-wider shadow-sm">
                18+ Kattalar uchun
              </span>
              <span className="text-[10px] text-white/80 group-hover/blur:text-white underline underline-offset-2 transition-colors">
                Tasdiqlash
              </span>
            </div>
          )}
        </div>
      )}
    </>
  );
}
