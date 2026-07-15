"use client";

import { useState } from "react";

interface ShareButtonProps {
  title: string;
  text: string;
  url: string;
}

export default function ShareButton({ title, text, url }: ShareButtonProps) {
  const [copied, setCopied] = useState(false);

  const handleShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title,
          text,
          url,
        });
      } catch (error) {
        console.error("Error sharing:", error);
      }
    } else {
      // Fallback: Copy to clipboard
      try {
        await navigator.clipboard.writeText(url);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      } catch (error) {
        console.error("Error copying to clipboard:", error);
      }
    }
  };

  return (
    <button 
      onClick={handleShare}
      className="w-full sm:w-auto flex items-center justify-center gap-2 bg-white/5 backdrop-blur-md border border-white/10 text-text-primary px-8 py-4 rounded-full font-label-caps text-xs uppercase tracking-widest hover:bg-white/10 hover:border-white/30 hover:scale-105 transition-all duration-300 ease-out group font-bold"
    >
      <span className="material-symbols-outlined text-[20px] group-hover:rotate-90 transition-transform">
        {copied ? "check" : "share"}
      </span>
      {copied ? "Nusxa olindi" : "ULASHISH"}
    </button>
  );
}
