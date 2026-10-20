"use client";

import { useState } from "react";

interface SourceBadgeProps {
  sourceType?: string | null;
  customSourceName?: string | null;
  customSourceLogo?: string | null;
  className?: string;
  size?: "sm" | "md";
}

export default function SourceBadge({
  sourceType,
  customSourceName,
  customSourceLogo,
  className = "",
  size = "md"
}: SourceBadgeProps) {
  const [imgError, setImgError] = useState(false);

  if (!sourceType || !["asilmedia", "uzmovi", "boshqa"].includes(sourceType)) {
    return null;
  }

  const isSm = size === "sm";
  const iconClass = isSm ? "w-3 h-3 rounded object-contain inline" : "w-4 h-4 rounded object-contain inline";

  return (
    <div
      className={className || "inline-flex items-center gap-1.5 h-7 sm:h-8 px-2.5 sm:px-3 rounded-lg bg-white/[0.08] backdrop-blur-md border border-white/15 text-xs font-bold shadow-sm"}
      title="Kontent manbasi"
    >
      {sourceType === "asilmedia" ? (
        <span className="text-amber-400 font-bold flex items-center gap-1.5">
          {!imgError && (
            <img
              src="https://asilmedia.org/favicon.svg"
              alt=""
              className={iconClass}
              onError={() => setImgError(true)}
            />
          )}
          <span>Asilmedia</span>
        </span>
      ) : sourceType === "uzmovi" ? (
        <span className="text-sky-400 font-bold flex items-center gap-1.5">
          {!imgError && (
            <img
              src="https://uzmovi.com/favicon.ico"
              alt=""
              className={isSm ? "w-3 h-3 rounded-full object-contain inline" : "w-4 h-4 rounded-full object-contain inline"}
              onError={() => setImgError(true)}
            />
          )}
          <span>Uzmovi</span>
        </span>
      ) : sourceType === "boshqa" ? (
        <span className="text-purple-300 font-bold flex items-center gap-1.5">
          {customSourceLogo && !imgError && (
            <img
              src={customSourceLogo}
              alt=""
              className={isSm ? "w-3 h-3 rounded object-cover inline" : "w-4 h-4 rounded object-cover inline"}
              onError={() => setImgError(true)}
            />
          )}
          <span>{customSourceName || "Boshqa"}</span>
        </span>
      ) : null}
    </div>
  );
}
