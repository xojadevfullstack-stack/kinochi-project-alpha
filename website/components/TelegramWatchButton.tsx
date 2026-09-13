"use client";

import React from "react";
import { openTelegramUrl } from "@/lib/telegram";

interface TelegramWatchButtonProps {
  url: string;
  className?: string;
  children: React.ReactNode;
  title?: string;
  ariaLabel?: string;
}

export default function TelegramWatchButton({
  url,
  className,
  children,
  title,
  ariaLabel,
}: TelegramWatchButtonProps) {
  const handleClick = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    openTelegramUrl(url);
  };

  return (
    <button
      type="button"
      onClick={handleClick}
      className={className}
      title={title}
      aria-label={ariaLabel}
    >
      {children}
    </button>
  );
}