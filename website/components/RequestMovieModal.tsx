"use client";

import { useState, useEffect } from "react";
import { createPortal } from "react-dom";
import Image from "next/image";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";

export interface RequestTargetItem {
  tmdb_id?: number | null;
  kinopoisk_id?: number | null;
  title: string;
  original_title?: string | null;
  media_type: "movie" | "series";
  release_year?: number | null;
  poster_url?: string | null;
  overview?: string | null;
  vote_average?: number | null;
}

interface RequestMovieModalProps {
  isOpen: boolean;
  onClose: () => void;
  item: RequestTargetItem | null;
  onSuccess?: () => void;
}

export default function RequestMovieModal({
  isOpen,
  onClose,
  item,
  onSuccess,
}: RequestMovieModalProps) {
  const [mounted, setMounted] = useState(false);
  const [preferredLang, setPreferredLang] = useState<string>("uz");
  const [userContact, setUserContact] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successInfo, setSuccessInfo] = useState<string | null>(null);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
      setErrorMsg(null);
      setSuccessInfo(null);
      setPreferredLang("uz");
      setUserContact("");
    } else {
      document.body.style.overflow = "unset";
    }
    return () => {
      document.body.style.overflow = "unset";
    };
  }, [isOpen]);

  if (!mounted || !isOpen || !item) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg(null);
    setSuccessInfo(null);

    try {
      const payload = {
        title: item.title,
        original_title: item.original_title,
        media_type: item.media_type,
        release_year: item.release_year,
        poster_url: item.poster_url,
        overview: item.overview,
        tmdb_id: item.tmdb_id,
        kinopoisk_id: item.kinopoisk_id,
        preferred_language: preferredLang,
        user_contact: userContact.trim() || null,
      };

      const res = await fetch(`${API_URL}/content-requests`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "So'rov yuborishda xatolik yuz berdi");
      }

      setSuccessInfo(
        data.message || "So'rovingiz qabul qilindi! Adminlarimiz uni tez orada platformaga qo'shishadi."
      );
      if (onSuccess) {
        onSuccess();
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Server bilan aloqada xatolik yuz berdi");
    } finally {
      setLoading(false);
    }
  };

  const modalContent = (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fade-in">
      <div 
        className="relative w-full max-w-lg bg-surface-container border border-white/10 rounded-2xl shadow-2xl overflow-hidden p-6 text-text-primary"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-text-secondary hover:text-white p-2 rounded-full hover:bg-white/10 transition-colors"
          title="Yopish"
        >
          <span className="material-symbols-outlined text-[20px]">close</span>
        </button>

        {successInfo ? (
          <div className="text-center py-6">
            <div className="w-16 h-16 bg-emerald-500/20 text-emerald-400 rounded-full flex items-center justify-center mx-auto mb-4 border border-emerald-500/30">
              <span className="material-symbols-outlined text-3xl">check_circle</span>
            </div>
            <h3 className="text-xl font-bold text-white mb-2">So&apos;rov qabul qilindi!</h3>
            <p className="text-sm text-text-secondary mb-6 leading-relaxed">
              {successInfo}
            </p>
            <button
              onClick={onClose}
              className="px-6 py-2.5 bg-rating-gold text-background-obsidian font-bold rounded-xl hover:brightness-110 transition-all shadow-lg text-sm"
            >
              Tushundim, rahmat!
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit}>
            <div className="flex items-center gap-2 mb-4 text-rating-gold text-xs font-bold uppercase tracking-wider">
              <span className="material-symbols-outlined text-[18px]">add_to_queue</span>
              <span>Kino / Serial qo&apos;shishni so&apos;rash</span>
            </div>

            {/* Media Preview Card */}
            <div className="flex gap-4 p-3.5 bg-white/5 rounded-xl border border-white/10 mb-5">
              <div className="relative w-16 h-24 rounded-lg overflow-hidden shrink-0 bg-white/10">
                {item.poster_url ? (
                  <Image
                    src={item.poster_url}
                    alt={item.title}
                    fill
                    sizes="64px"
                    className="object-cover"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-text-secondary">
                    <span className="material-symbols-outlined">movie</span>
                  </div>
                )}
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="px-2 py-0.5 bg-amber-500/20 text-amber-300 rounded text-[10px] font-bold uppercase">
                    {item.media_type === "series" ? "Serial" : "Kino"}
                  </span>
                  {item.release_year && (
                    <span className="text-xs text-text-secondary">{item.release_year}</span>
                  )}
                  {item.vote_average ? (
                    <span className="text-xs text-rating-gold font-bold flex items-center gap-0.5">
                      ★ {item.vote_average.toFixed(1)}
                    </span>
                  ) : null}
                </div>
                <h4 className="font-bold text-base text-white truncate">{item.title}</h4>
                {item.original_title && (
                  <p className="text-xs text-text-secondary truncate">{item.original_title}</p>
                )}
                {item.overview && (
                  <p className="text-xs text-text-secondary line-clamp-2 mt-1 opacity-80">
                    {item.overview}
                  </p>
                )}
              </div>
            </div>

            {/* Error Message */}
            {errorMsg && (
              <div className="mb-4 p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-xs">
                {errorMsg}
              </div>
            )}

            {/* Preferred Language */}
            <div className="mb-4">
              <label className="block text-xs font-bold text-text-secondary mb-2 uppercase tracking-wider">
                Qaysi tilda kutmoqdasiz?
              </label>
              <div className="grid grid-cols-2 gap-2">
                {[
                  { id: "uz", label: "🇺🇿 O'zbekcha ovoz", desc: "Professional dublyaj" },
                  { id: "ru", label: "🇷🇺 Ruscha ovoz", desc: "Original ruscha" },
                  { id: "sub", label: "💬 Subtitr bilan", desc: "Original til + subtitr" },
                  { id: "any", label: "✨ Farqi yo'q", desc: "Qaysi biri tez chiqsa" },
                ].map((opt) => (
                  <button
                    key={opt.id}
                    type="button"
                    onClick={() => setPreferredLang(opt.id)}
                    className={`p-2.5 rounded-xl border text-left transition-all ${
                      preferredLang === opt.id
                        ? "bg-rating-gold/15 border-rating-gold text-white shadow-sm"
                        : "bg-white/5 border-white/10 text-text-secondary hover:bg-white/10"
                    }`}
                  >
                    <div className="font-semibold text-xs text-white">{opt.label}</div>
                    <div className="text-[10px] text-text-secondary">{opt.desc}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Optional Contact info */}
            <div className="mb-6">
              <label className="block text-xs font-bold text-text-secondary mb-1 uppercase tracking-wider">
                Telegram @username yoki Telefon raqam (Ixtiyoriy)
              </label>
              <p className="text-[11px] text-text-secondary/80 mb-2">
                Kino joylanganda sizga birinchi bo&apos;lib xabar yuborishimiz uchun
              </p>
              <input
                type="text"
                value={userContact}
                onChange={(e) => setUserContact(e.target.value)}
                placeholder="@username yoki +998 90 123 45 67"
                className="w-full px-4 py-2.5 bg-white/5 border border-white/10 rounded-xl text-text-primary text-sm focus:outline-none focus:border-rating-gold/50 transition-colors"
              />
            </div>

            {/* Buttons */}
            <div className="flex gap-3">
              <button
                type="button"
                onClick={onClose}
                disabled={loading}
                className="flex-1 py-2.5 px-4 rounded-xl border border-white/10 text-text-secondary hover:text-white hover:bg-white/5 transition-colors text-sm font-semibold"
              >
                Bekor qilish
              </button>
              <button
                type="submit"
                disabled={loading}
                className="flex-1 py-2.5 px-4 rounded-xl bg-rating-gold text-background-obsidian font-bold hover:brightness-110 active:scale-95 transition-all text-sm flex items-center justify-center gap-2 shadow-lg disabled:opacity-50"
              >
                {loading ? (
                  <>
                    <span className="w-4 h-4 border-2 border-background-obsidian border-t-transparent rounded-full animate-spin"></span>
                    <span>Yuborilmoqda...</span>
                  </>
                ) : (
                  <>
                    <span className="material-symbols-outlined text-[18px]">send</span>
                    <span>So&apos;rov yuborish</span>
                  </>
                )}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );

  return createPortal(modalContent, document.body);
}
