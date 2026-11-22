"use client";

import Image from "next/image";
import { useAgeVerification } from "@/hooks/useAgeVerification";

interface AdultHeroBackgroundProps {
  src: string;
  alt: string;
  is18Plus?: boolean;
  isDetailPage?: boolean;
  sharp?: boolean;
}

export default function AdultHeroBackground({
  src,
  alt,
  is18Plus = false,
  isDetailPage = false,
  sharp = false,
}: AdultHeroBackgroundProps) {
  const { isMounted, isVerified } = useAgeVerification();
  const shouldBlur = is18Plus && (!isDetailPage ? true : (!isMounted || !isVerified));

  return (
    <Image
      src={src}
      alt={alt}
      fill
      priority
      unoptimized
      className={`object-cover transition-all duration-700 ease-out ${
        shouldBlur
          ? "opacity-20 scale-125 blur-3xl"
          : sharp
          ? "opacity-65"
          : "opacity-50 sm:opacity-40 scale-105 blur-sm sm:blur-md"
      }`}
      style={{ objectPosition: "center 20%" }}
    />
  );
}

