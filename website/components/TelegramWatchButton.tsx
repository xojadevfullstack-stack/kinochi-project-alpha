"use client";

import React, { useState, useEffect, useMemo } from "react";
import { createPortal } from "react-dom";
import { openTelegramUrl, triggerTelegramHaptic } from "@/lib/telegram";
import { useAuth } from "@/lib/auth/AuthProvider";
import { useOverlayBackClose } from "@/lib/hooks/useOverlayBackClose";

interface TelegramWatchButtonProps {
  url: string;
  mediaTitle?: string;
  mediaCode?: string | number;
  mediaId?: string | number;
  seriesId?: string | number;
  mediaType?: "movie" | "series" | "episode";
  posterUrl?: string;
  releaseYear?: number | null;
  imdbRating?: number | null;
  genres?: string | null;
  className?: string;
  children: React.ReactNode;
  title?: string;
  ariaLabel?: string;
}

export default function TelegramWatchButton({
  url,
  mediaTitle,
  mediaCode,
  mediaId,
  seriesId,
  mediaType = "movie",
  posterUrl,
  releaseYear,
  imdbRating,
  genres,
  className,
  children,
  title,
  ariaLabel,
}: TelegramWatchButtonProps) {
  const { botUsername: liveBotUsername } = useAuth();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isMounted, setIsMounted] = useState(false);

  const resolvedUrl = useMemo(() => {
    if (!url || !liveBotUsername) return url;
    return url.replace(/https:\/\/t\.me\/[^/?#]+/i, `https://t.me/${liveBotUsername}`);
  }, [url, liveBotUsername]);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  useOverlayBackClose(isModalOpen, () => setIsModalOpen(false));

  // Handle modal open: lock scroll, trigger haptic, setup escape & telegram back key
  useEffect(() => {
    if (!isModalOpen) return;

    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setIsModalOpen(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);

    // If inside Telegram WebApp, intercept back button to close modal first
    const tg = typeof window !== "undefined" && (window as any).Telegram?.WebApp;
    let cleanupTgBack: (() => void) | undefined;
    if (tg?.BackButton) {
      const handleTgBack = () => {
        triggerTelegramHaptic("light");
        setIsModalOpen(false);
      };
      tg.BackButton.show();
      tg.BackButton.onClick(handleTgBack);
      cleanupTgBack = () => {
        try {
          tg.BackButton.offClick(handleTgBack);
        } catch (e) {}
      };
    }

    return () => {
      document.body.style.overflow = prevOverflow;
      window.removeEventListener("keydown", handleKeyDown);
      if (cleanupTgBack) cleanupTgBack();
    };
  }, [isModalOpen]);

  const handleClick = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();

    // Persist continue watching state in local storage
    if (typeof window !== "undefined") {
      try {
        const rawCode = mediaCode && !String(mediaCode).startsWith("http") ? String(mediaCode) : undefined;
        const cleanSeriesId = seriesId || (mediaType === "series" ? mediaId : undefined);
        const cleanMovieId = mediaType === "movie" ? (mediaId || rawCode) : undefined;
        const resolvedId = cleanSeriesId || cleanMovieId || mediaId || rawCode;

        if (resolvedId) {
          const item = {
            id: resolvedId,
            code: rawCode,
            title: mediaTitle || "Noma'lum film",
            poster_url: posterUrl || null,
            is_series: mediaType === "series" || mediaType === "episode",
            release_year: releaseYear || null,
            imdb_rating: imdbRating || null,
            genres: genres || (mediaType === "series" || mediaType === "episode" ? "Serial" : "Kino"),
            last_watched_at: new Date().toISOString(),
            type: mediaType || "movie",
          };
          const raw = localStorage.getItem("mediaplus_continue_watching");
          let list = raw ? JSON.parse(raw) : [];
          if (!Array.isArray(list)) list = [];
          list = [item, ...list.filter((x: any) => String(x.id) !== String(item.id))].slice(0, 10);
          localStorage.setItem("mediaplus_continue_watching", JSON.stringify(list));
          window.dispatchEvent(new Event("mediaplus_continue_watching_updated"));
        }
      } catch (err) {
        console.error("Failed to save continue watching state:", err);
      }
    }

    // Trigger haptic feedback
    triggerTelegramHaptic("medium");

    // Open Telegram link
    openTelegramUrl(resolvedUrl);

    // Show confirmation modal with blurred background and back button
    setIsModalOpen(true);
  };

  const handleOpenBotDirectly = () => {
    triggerTelegramHaptic("light");
    openTelegramUrl(resolvedUrl);
    setIsModalOpen(false);
  };

  const typeName =
    mediaType === "series"
      ? "Serial"
      : mediaType === "episode"
      ? "Qism"
      : "Kino";

  const modalContent = isModalOpen && isMounted && (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center p-4 sm:p-6 overflow-y-auto overscroll-contain animate-in fade-in duration-200"
      role="dialog"
      aria-modal="true"
      aria-labelledby="telegram-modal-title"
    >
      {/* Apple Glass Blurred Backdrop */}
      <div
        className="fixed inset-0 bg-slate-900/55 dark:bg-black/80 backdrop-blur-xl transition-opacity cursor-pointer"
        onClick={() => setIsModalOpen(false)}
      />

      {/* Apple Glass + Cinematic Red Modal Card */}
      <div
        className="relative z-10 w-full max-w-md bg-white/95 dark:bg-[#11131B]/95 backdrop-blur-2xl border border-slate-200 dark:border-white/15 rounded-3xl p-5 sm:p-7 shadow-2xl shadow-slate-900/20 dark:shadow-[0_24px_64px_rgba(0,0,0,0.9)] flex flex-col items-center text-center animate-in zoom-in-95 duration-200 overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Subtle Cinematic Red Ambient Glows */}
        <div className="absolute -top-24 -right-24 w-52 h-52 bg-[#E50914]/15 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-24 -left-24 w-52 h-52 bg-[#E50914]/10 rounded-full blur-3xl pointer-events-none" />

        {/* Top Header Row with Unified Red-Hover Circular Back & Close Buttons */}
        <div className="w-full flex items-center justify-between mb-4 sm:mb-5 relative z-10">
          <button
            type="button"
            onClick={() => {
              triggerTelegramHaptic("light");
              setIsModalOpen(false);
            }}
            className="group relative inline-flex items-center justify-center w-9 h-9 sm:w-10 sm:h-10 rounded-full bg-slate-100 dark:bg-white/[0.08] hover:bg-[#B80710] dark:hover:bg-[#E50914] active:scale-90 border border-slate-200 dark:border-white/15 hover:border-[#B80710] dark:hover:border-[#E50914] shadow-sm transition-all duration-200 cursor-pointer text-slate-700 dark:text-white hover:text-white focus:outline-none"
            aria-label="Orqaga qaytish"
            title="Orqaga"
          >
            <svg
              className="w-5 h-5 -translate-x-0.5 transition-transform duration-200 group-hover:-translate-x-1"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.4"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <polyline points="15 18 9 12 15 6" />
            </svg>
          </button>

          <span className="inline-flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-widest text-slate-500 dark:text-slate-400">
            <span className="w-1.5 h-1.5 rounded-full bg-[#E50914]" />
            <span>MediaPlus Bot</span>
          </span>

          <button
            type="button"
            onClick={() => {
              triggerTelegramHaptic("light");
              setIsModalOpen(false);
            }}
            className="w-9 h-9 rounded-full bg-slate-100 dark:bg-white/[0.08] hover:bg-[#B80710] dark:hover:bg-[#E50914] active:scale-90 border border-slate-200 dark:border-white/15 hover:border-[#B80710] dark:hover:border-[#E50914] flex items-center justify-center text-slate-700 dark:text-slate-300 hover:text-white transition-all cursor-pointer"
            aria-label="Yopish"
          >
            <span className="material-symbols-outlined text-[20px]">close</span>
          </button>
        </div>

        {/* Hero Telegram Squircle Emblem */}
        <div className="relative mb-4">
          <div className="w-16 h-16 sm:w-20 sm:h-20 rounded-2xl sm:rounded-3xl bg-gradient-to-tr from-[#E50914]/15 to-red-500/5 border border-[#E50914]/30 flex items-center justify-center shadow-lg shadow-[#E50914]/15">
            <svg
              className="w-8 h-8 sm:w-10 sm:h-10 text-[#D20A13] dark:text-[#E50914] translate-x-0.5"
              viewBox="0 0 24 24"
              fill="currentColor"
            >
              <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.896-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z" />
            </svg>
          </div>
          <div className="absolute -bottom-1 -right-1 w-6 h-6 sm:w-7 sm:h-7 rounded-full bg-[#D20A13] dark:bg-[#E50914] border-2 border-white dark:border-[#11131B] flex items-center justify-center shadow-md">
            <span className="material-symbols-outlined text-[14px] sm:text-[15px] text-white font-bold">
              open_in_new
            </span>
          </div>
        </div>

        {/* Status Chip */}
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-red-50 dark:bg-[#E50914]/15 border border-red-200 dark:border-[#E50914]/35 text-[#D20A13] dark:text-[#ff4d57] text-[11px] font-bold tracking-wide uppercase mb-2">
          <span className="w-1.5 h-1.5 rounded-full bg-[#E50914] animate-pulse" />
          <span>Telegram bot ochilmoqda</span>
        </div>

        {/* Modal Title */}
        <h3
          id="telegram-modal-title"
          className="font-display-hero text-xl sm:text-2xl font-black text-slate-900 dark:text-white mb-2 tracking-tight"
        >
          Telegram botda davom eting
        </h3>

        {/* Informational Message */}
        <p className="text-slate-600 dark:text-slate-300 text-xs sm:text-sm leading-relaxed mb-4 max-w-sm">
          {mediaTitle ? `«${mediaTitle}» videosini` : "Videoni"} tomosha qilish uchun Telegram botga havola ochildi. Botda «Start» yoki «Boshlash» tugmasini bosing.
        </p>

        {/* Media Preview Box */}
        {mediaTitle && (
          <div className="w-full p-2.5 sm:p-3 rounded-2xl bg-slate-50 dark:bg-white/[0.04] border border-slate-200 dark:border-white/10 flex items-center gap-3.5 mb-5 text-left">
            {posterUrl ? (
              <div className="w-11 h-14 rounded-lg bg-slate-200 dark:bg-surface-container-high overflow-hidden shrink-0 relative border border-slate-200 dark:border-white/10">
                <img
                  src={posterUrl}
                  alt={mediaTitle}
                  className="w-full h-full object-cover"
                />
              </div>
            ) : (
              <div className="w-11 h-14 rounded-lg bg-slate-200 dark:bg-white/10 flex items-center justify-center shrink-0 text-slate-400 dark:text-white/50 border border-slate-200 dark:border-white/10">
                <span className="material-symbols-outlined text-xl">movie</span>
              </div>
            )}
            <div className="flex-1 overflow-hidden">
              <div className="font-bold text-sm text-slate-900 dark:text-white truncate">
                {mediaTitle}
              </div>
              {mediaCode && (
                <div className="inline-block mt-1 px-2 py-0.5 rounded-md bg-red-50 dark:bg-[#E50914]/15 text-[11px] font-mono font-bold text-[#D20A13] dark:text-[#ff4d57] border border-red-200 dark:border-[#E50914]/30">
                  #{mediaCode}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Actions (Cinematic Red Primary + Clean Secondary) */}
        <div className="w-full flex flex-col gap-2.5">
          <button
            type="button"
            onClick={handleOpenBotDirectly}
            className="w-full flex items-center justify-center gap-2 py-3.5 px-5 rounded-2xl bg-[#D20A13] dark:bg-[#E50914] hover:bg-[#B80710] active:scale-95 text-white font-bold text-sm shadow-lg shadow-[#E50914]/25 hover:shadow-[#E50914]/40 transition-all cursor-pointer"
          >
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
              <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.896-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z" />
            </svg>
            <span>Telegram botni ochish</span>
          </button>

          <button
            type="button"
            onClick={() => {
              triggerTelegramHaptic("light");
              setIsModalOpen(false);
            }}
            className="w-full flex items-center justify-center gap-1.5 py-3 px-5 rounded-2xl bg-slate-100 dark:bg-white/5 hover:bg-slate-200 dark:hover:bg-white/10 active:scale-95 border border-slate-200 dark:border-white/10 text-slate-700 dark:text-slate-200 hover:text-slate-900 dark:hover:text-white font-semibold text-xs transition-all cursor-pointer"
          >
            <span>Orqaga qaytish</span>
          </button>
        </div>
      </div>
    </div>
  );

  return (
    <>
      <button
        type="button"
        onClick={handleClick}
        className={className}
        title={title}
        aria-label={ariaLabel}
      >
        {children}
      </button>

      {isMounted && modalContent && createPortal(modalContent, document.body)}
    </>
  );
}