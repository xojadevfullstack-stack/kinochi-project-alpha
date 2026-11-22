"use client";

import Image from "next/image";
import { useAgeVerification } from "@/hooks/useAgeVerification";

interface AdultHeroBackgroundProps {
  src: string;
  alt: string;
  is18Plus?: boolean;
  isDetailPage?: boolean;
  sharp?: boolean;
  hidden?: boolean;
}

export default function AdultHeroBackground({
  src,
  alt,
  is18Plus = false,
  isDetailPage = false,
  sharp = false,
  hidden = false,
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
          : hidden
          ? "opacity-0 scale-105 blur-md"
          : sharp
          ? "opacity-65"
          : "opacity-40 sm:opacity-35 scale-105 blur-md sm:blur-lg"
      }`}
      style={{ objectPosition: "center 20%" }}
    />
  );
}

