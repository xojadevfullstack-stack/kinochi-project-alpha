"use client";

import React, { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { API_URL } from "@/lib/api";
import { openTelegramUrl, triggerTelegramHaptic } from "@/lib/telegram";
import { useOverlayBackClose } from "@/lib/hooks/useOverlayBackClose";
import MediaLoader from "@/components/ui/MediaLoader";
import { buildStreamSignEndpoint, mapStreamErrorToUzbek } from "@/lib/streamHelpers.mjs";

export interface StreamTranslationItem {
  id: number;
  language: string;
  storage_channel_message_id: number;
}

interface WebVideoPlayerModalProps {
  isOpen: boolean;
  onClose: () => void;
  mediaType: "movie" | "episode";
  title: string;
  posterUrl?: string;
  translations: StreamTranslationItem[];
  telegramUrl: string;
}

export default function WebVideoPlayerModal({
  isOpen,
  onClose,
  mediaType,
  title,
  posterUrl,
  translations,
  telegramUrl,
}: WebVideoPlayerModalProps) {
  const [mounted, setMounted] = useState(false);
  const [selectedId, setSelectedId] = useState<number>(translations[0]?.id || 0);
  const [streamUrl, setStreamUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (translations.length > 0 && !translations.some((t) => t.id === selectedId)) {
      setSelectedId(translations[0].id);
    }
  }, [translations, selectedId]);

  useOverlayBackClose(isOpen, onClose);

  useEffect(() => {
    if (!isOpen) return;
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKeyDown);
    return () => {
      document.body.style.overflow = prevOverflow;
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [isOpen, onClose]);

  useEffect(() => {
    if (!isOpen || !selectedId) return;
    let cancelled = false;
    setLoading(true);
    setErrorMsg(null);
    setStreamUrl(null);

    const endpoint = `${API_URL}${buildStreamSignEndpoint(mediaType, selectedId)}`;
    fetch(endpoint, { cache: "no-store" })
      .then(async (res) => {
        if (!res.ok) {
          throw new Error(mapStreamErrorToUzbek(res.status));
        }
        return res.json();
      })
      .then((data) => {
        if (!cancelled) {
          if (data?.stream_url) {
            setStreamUrl(data.stream_url);
          } else {
            setErrorMsg(mapStreamErrorToUzbek("unknown"));
          }
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setErrorMsg(err?.message || mapStreamErrorToUzbek("unknown"));
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [isOpen, mediaType, selectedId]);

  if (!isOpen || !mounted) return null;

  return createPortal(
    <div
      className="fixed inset-0 z-[110] flex items-center justify-center p-2 sm:p-6 overflow-y-auto overscroll-contain preserve-white"
      role="dialog"
      aria-modal="true"
      aria-label={`${title} video player`}
    >
      <div
        className="fixed inset-0 bg-black/90 backdrop-blur-xl cursor-pointer"
        onClick={onClose}
      />

      <div
        className="relative z-10 w-full max-w-5xl rounded-2xl sm:rounded-3xl bg-[#0E0F13] border border-white/15 shadow-[0_25px_70px_rgba(0,0,0,0.95)] overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Top Bar */}
        <div className="flex flex-wrap items-center justify-between gap-2 px-4 py-3 border-b border-white/10 bg-black/40">
          <div className="flex items-center gap-2.5 min-w-0">
            <span className="w-2 h-2 rounded-full bg-[#E50914] shrink-0" />
            <h3 className="text-sm sm:text-base font-bold text-white truncate">{title}</h3>
          </div>

          <div className="flex items-center gap-2 ml-auto">
            {translations.length > 1 && (
              <div className="flex items-center gap-1.5 overflow-x-auto hide-scrollbar">
                {translations.map((tr) => {
                  const isActive = tr.id === selectedId;
                  return (
                    <button
                      key={tr.id}
                      type="button"
                      onClick={() => setSelectedId(tr.id)}
                      className={`px-2.5 py-1 rounded-full text-xs font-semibold whitespace-nowrap transition-all cursor-pointer border ${
                        isActive
                          ? "bg-[#E50914] text-white border-[#E50914] shadow-sm shadow-[#E50914]/30"
                          : "bg-white/10 text-slate-200 border-white/15 hover:bg-[#E50914]/80 hover:text-white"
                      }`}
                    >
                      {tr.language}
                    </button>
                  );
                })}
              </div>
            )}

            <button
              type="button"
              onClick={() => {
                triggerTelegramHaptic("light");
                openTelegramUrl(telegramUrl);
              }}
              className="px-2.5 py-1 rounded-full bg-white/10 hover:bg-[#229ED9] text-white text-xs font-semibold transition-colors cursor-pointer shrink-0 flex items-center gap-1"
              title="Telegram botda ochish"
            >
              <span className="material-symbols-outlined text-[14px]">send</span>
              <span className="hidden sm:inline">Telegram</span>
            </button>

            <button
              type="button"
              onClick={onClose}
              className="w-8 h-8 rounded-full bg-white/10 hover:bg-[#E50914] text-white flex items-center justify-center transition-colors cursor-pointer shrink-0"
              aria-label="Playerni yopish"
            >
              <span className="material-symbols-outlined text-[18px]">close</span>
            </button>
          </div>
        </div>

        {/* Video Stage */}
        <div className="relative w-full aspect-video bg-black flex items-center justify-center">
          {loading && <MediaLoader variant="spinner" label="Video oqimi tayyorlanmoqda..." />}

          {!loading && errorMsg && (
            <div className="p-6 max-w-md text-center flex flex-col items-center gap-4">
              <div className="w-12 h-12 rounded-2xl bg-[#E50914]/20 border border-[#E50914]/40 flex items-center justify-center text-[#E50914]">
                <span className="material-symbols-outlined text-2xl">error_outline</span>
              </div>
              <p className="text-xs sm:text-sm text-slate-200 leading-relaxed">{errorMsg}</p>
              <button
                type="button"
                onClick={() => {
                  triggerTelegramHaptic("medium");
                  openTelegramUrl(telegramUrl);
                }}
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-[#E50914] hover:bg-[#B80710] text-white text-xs sm:text-sm font-bold uppercase tracking-wider transition-all cursor-pointer shadow-lg shadow-[#E50914]/30"
              >
                <span className="material-symbols-outlined text-[18px]">send</span>
                <span>Telegram botda ko&apos;rish</span>
              </button>
            </div>
          )}

          {!loading && !errorMsg && streamUrl && (
            <video
              key={streamUrl}
              src={streamUrl}
              poster={posterUrl || undefined}
              controls
              autoPlay
              playsInline
              preload="metadata"
              onError={() => setErrorMsg(mapStreamErrorToUzbek("codec"))}
              className="w-full h-full object-contain bg-black"
            />
          )}
        </div>
      </div>
    </div>,
    document.body
  );
}
