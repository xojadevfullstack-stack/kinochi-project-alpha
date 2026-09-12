"use client";

import { useState } from "react";

interface ShareButtonProps {
  title: string;
  text: string;
  url: string;
}

export default function ShareButton({ title, text, url }: ShareButtonProps) {
  const [copied, setCopied] = useState(false);

  const copyToClipboard = async () => {
    try {
      if (navigator.clipboard) {
        await navigator.clipboard.writeText(url);
      } else {
        const input = document.createElement("input");
        input.value = url;
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
  };

  const handleShare = async () => {
    // 1. Copy URL to clipboard immediately
    await copyToClipboard();

    // 2. Build Telegram share URL
    const tgShareUrl = `https://t.me/share/url?url=${encodeURIComponent(url)}&text=${encodeURIComponent(title + "\n" + (text || ""))}`;

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
        await navigator.share({ title, text, url });
        return;
      } catch (err) {
        // User cancelled or share failed
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
