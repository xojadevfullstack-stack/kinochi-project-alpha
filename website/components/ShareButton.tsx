"use client";

import { useState } from "react";

interface ShareButtonProps {
  title: string;
  text?: string;
  url?: string;
  code?: string;
  botUsername?: string;
}

export default function ShareButton({ title, text: _text, url = "", code, botUsername }: ShareButtonProps) {
  const [copied, setCopied] = useState(false);

  // Determine site base URL (prefer real window.location, fallback to Vercel production URL)
  const getFullWebUrl = () => {
    let siteBase = "https://kinochi-project-alpha.vercel.app";
    if (typeof window !== "undefined" && window.location.origin) {
      if (!window.location.origin.includes("localhost")) {
        siteBase = window.location.origin;
      }
    }
    let target = url || (typeof window !== "undefined" ? window.location.pathname : "");
    if (target.startsWith("https://kinochi.uz")) {
      target = target.replace("https://kinochi.uz", siteBase);
    } else if (target.startsWith("/")) {
      target = `${siteBase}${target}`;
    } else if (!target.startsWith("http")) {
      target = `${siteBase}/${target}`;
    }
    return target;
  };

  // Determine item code (movie code or series s_{id})
  const getItemCode = (fullUrl: string) => {
    if (code) return code;
    const movieMatch = fullUrl.match(/\/movie\/([A-Za-z0-9_-]+)/);
    if (movieMatch) return movieMatch[1];
    const seriesMatch = fullUrl.match(/\/series\/([0-9]+)/);
    if (seriesMatch) return `s_${seriesMatch[1]}`;
    return null;
  };

  const handleShare = async () => {
    const fullWebUrl = getFullWebUrl();
    const itemCode = getItemCode(fullWebUrl);
    const botUser = botUsername || process.env.NEXT_PUBLIC_BOT_USERNAME || "kinochi_uz_bot";
    const botLink = itemCode ? `https://t.me/${botUser}?start=${itemCode}` : `https://t.me/${botUser}`;

    // 1. Copy URL to clipboard immediately
    try {
      if (navigator.clipboard) {
        await navigator.clipboard.writeText(fullWebUrl);
      } else {
        const input = document.createElement("input");
        input.value = fullWebUrl;
        document.body.appendChild(input);
        input.select();
        document.execCommand("copy");
        document.body.removeChild(input);
      }
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    } catch (err) {
      console.error("Copy failed:", err);
    }

    // 2. Build Telegram share text with title, code, bot link and web link
    const shareLines = [
      `🎬 ${title}`,
      itemCode ? `🔑 Kod: ${itemCode}` : null,
      "",
      `🍿 Botda tomosha qilish: ${botLink}`,
    ].filter(line => line !== null).join("\n");

    const tgShareUrl = `https://t.me/share/url?url=${encodeURIComponent(fullWebUrl)}&text=${encodeURIComponent(shareLines)}`;

    // 3. Check if inside Telegram WebApp
    const tg = typeof window !== "undefined" ? (window as any).Telegram?.WebApp : null;
    if (tg?.openTelegramLink) {
      tg.openTelegramLink(tgShareUrl);
      return;
    }

    // 4. For mobile touch devices only, try native share if available
    const isMobile = typeof navigator !== "undefined" && /Mobi|Android|iPhone/i.test(navigator.userAgent);
    if (isMobile && navigator.share) {
      try {
        await navigator.share({
          title,
          text: shareLines,
          url: fullWebUrl
        });
        return;
      } catch (err) {
        // Fallback or user dismissed
      }
    }

    // 5. Desktop: open Telegram share directly in new tab
    window.open(tgShareUrl, "_blank", "noopener,noreferrer");
  };

  return (
    <div className="relative inline-block w-full sm:w-auto">
      <button 
        onClick={handleShare}
        className={`w-full sm:w-auto flex items-center justify-center gap-2 backdrop-blur-md border text-text-primary px-8 py-4 rounded-full font-label-caps text-xs uppercase tracking-widest transition-all duration-300 ease-out group font-bold ${
          copied 
            ? "bg-emerald-500/20 border-emerald-500/50 text-emerald-400" 
            : "bg-white/5 border-white/10 hover:bg-white/10 hover:border-white/30 hover:scale-105"
        }`}
      >
        <span className={`material-symbols-outlined text-[20px] transition-transform ${copied ? "text-emerald-400 scale-110" : "group-hover:rotate-45"}`}>
          {copied ? "check_circle" : "share"}
        </span>
        {copied ? "Havola nusxalandi!" : "ULASHISH"}
      </button>
    </div>
  );
}
