"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { API_URL } from "@/lib/api";
import { useAuth } from "@/lib/auth/AuthProvider";
import { openTelegramUrl, triggerTelegramHaptic } from "@/lib/telegram";

interface QuickMatch {
  id: number;
  title: string;
  code: string;
  short_code?: string | null;
  year?: number | null;
  poster_url?: string | null;
  imdb_rating?: number | null;
  type: "movie" | "series" | "collection";
}

export default function QuickCodePage() {
  const router = useRouter();
  const [rawCode, setRawCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [match, setMatch] = useState<QuickMatch | null>(null);

  const { botUsername } = useAuth();
  const cleanedCode = rawCode.replace(/^[#№\s]+/, "").trim();

  useEffect(() => {
    if (!cleanedCode || cleanedCode.length < 2) {
      setMatch(null);
      setErrorMsg(null);
      return;
    }

    const controller = new AbortController();
    const timer = setTimeout(async () => {
      try {
        const res = await fetch(
          `${API_URL}/search/live?q=${encodeURIComponent(cleanedCode)}&limit=3`,
          { signal: controller.signal }
        );
        if (!res.ok) return;
        const data = await res.json();
        const firstMovie = (data.results || []).find(
          (item: QuickMatch) =>
            item.type === "movie" &&
            (item.short_code === cleanedCode || item.code.toLowerCase() === cleanedCode.toLowerCase())
        );
        setMatch(firstMovie || (data.results?.[0] ?? null));
      } catch {
        // Ignore aborted or transient live-lookup errors
      }
    }, 220);

    return () => {
      controller.abort();
      clearTimeout(timer);
    };
  }, [cleanedCode]);

  const handleOpenCode = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!cleanedCode) {
      setErrorMsg("Kino kodini kiriting (masalan: 1001)");
      return;
    }
    triggerTelegramHaptic("light");
    setLoading(true);
    setErrorMsg(null);

    try {
      const res = await fetch(`${API_URL}/movies/code/${encodeURIComponent(cleanedCode)}`);
      if (res.ok) {
        const movie = await res.json();
        router.push(`/movie/${encodeURIComponent(movie.short_code || movie.code)}`);
        return;
      }
      const epRes = await fetch(`${API_URL}/series/episodes/code/${encodeURIComponent(cleanedCode)}`);
      if (epRes.ok) {
        const ep = await epRes.json();
        if (ep?.series_id) {
          router.push(`/series/${ep.series_id}`);
          return;
        }
      }
      if (match) {
        if (match.type === "series") {
          router.push(`/series/${match.id}`);
          return;
        }
        if (match.type === "collection") {
          router.push(`/collections/${encodeURIComponent(match.code)}`);
          return;
        }
        router.push(`/movie/${encodeURIComponent(match.short_code || match.code)}`);
        return;
      }
      setErrorMsg("Bunday kodli kino topilmadi. Kodni tekshiring yoki nomi bilan qidiring.");
    } catch {
      router.push(`/movie/${encodeURIComponent(cleanedCode)}`);
    } finally {
      setLoading(false);
    }
  };

  const telegramUrl = cleanedCode
    ? `https://t.me/${botUsername}?start=${encodeURIComponent(cleanedCode)}`
    : `https://t.me/${botUsername}`;

  return (
    <div className="min-h-[calc(100vh-200px)] flex items-center justify-center px-4 py-10">
      <div className="glass-panel w-full max-w-md rounded-[22px] p-6 sm:p-8 border border-white/10 bg-[#12151E]/85 backdrop-blur-xl shadow-2xl">
        <div className="flex flex-col items-center text-center mb-6">
          <div className="w-12 h-12 rounded-2xl bg-[#E50914]/15 border border-[#E50914]/35 flex items-center justify-center mb-3">
            <span className="material-symbols-outlined text-[26px] text-[#E50914]">
              pin
            </span>
          </div>
          <h1 className="text-xl sm:text-2xl font-extrabold tracking-tight text-white">
            Kino kodi bo&apos;yicha ochish
          </h1>
          <p className="text-xs sm:text-sm text-text-secondary mt-1.5">
            Instagram, TikTok yoki YouTube videoda ko&apos;rgan kodingizni kiriting
          </p>
        </div>

        <form onSubmit={handleOpenCode} className="space-y-4">
          <div className="relative">
            <span className="absolute left-4 top-1/2 -translate-y-1/2 text-lg font-bold text-[#E50914] select-none">
              #
            </span>
            <input
              type="text"
              inputMode="numeric"
              autoFocus
              value={rawCode}
              onChange={(e) => {
                setRawCode(e.target.value);
                setErrorMsg(null);
              }}
              placeholder="1001"
              aria-label="Kino kodi"
              className="w-full pl-10 pr-4 py-3.5 rounded-xl bg-white/[0.06] border border-white/15 focus:border-[#E50914] focus:outline-none text-center text-xl font-extrabold tracking-widest text-white placeholder:text-text-secondary/50 transition-colors"
            />
          </div>

          {errorMsg && (
            <div className="text-xs text-[#FF6B6B] bg-[#E50914]/10 border border-[#E50914]/30 rounded-xl px-3.5 py-2.5 text-center">
              {errorMsg}
            </div>
          )}

          {match && (
            <Link
              href={
                match.type === "series"
                  ? `/series/${match.id}`
                  : match.type === "collection"
                  ? `/collections/${encodeURIComponent(match.code)}`
                  : `/movie/${encodeURIComponent(match.short_code || match.code)}`
              }
              className="flex items-center gap-3 p-2.5 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 hover:border-[#E50914]/50 transition-all"
            >
              {match.poster_url ? (
                <img
                  src={match.poster_url}
                  alt={match.title}
                  className="w-11 h-16 object-cover rounded-lg flex-shrink-0"
                  decoding="async"
                />
              ) : (
                <div className="w-11 h-16 rounded-lg bg-white/10 flex items-center justify-center flex-shrink-0">
                  <span className="material-symbols-outlined text-white/40">movie</span>
                </div>
              )}
              <div className="min-w-0 flex-1 text-left">
                <p className="text-sm font-bold text-white truncate">{match.title}</p>
                <div className="flex items-center gap-2 text-xs text-text-secondary mt-0.5">
                  {match.year && <span>{match.year}</span>}
                  {match.imdb_rating && (
                    <span className="text-rating-gold font-semibold">★ {match.imdb_rating.toFixed(1)}</span>
                  )}
                  <span className="text-[#E50914] font-bold">
                    #{match.short_code || match.code}
                  </span>
                </div>
              </div>
              <span className="material-symbols-outlined text-[#E50914]">arrow_forward</span>
            </Link>
          )}

          <button
            type="submit"
            disabled={loading}
            className="preserve-white w-full py-3.5 rounded-xl bg-[#E50914] hover:bg-[#B80710] active:scale-[0.99] disabled:opacity-60 text-white font-bold text-sm uppercase tracking-wider shadow-lg shadow-[#E50914]/25 transition-all cursor-pointer"
          >
            {loading ? "Qidirilmoqda..." : "Kinoni ochish"}
          </button>
        </form>

        <div className="mt-4 pt-4 border-t border-white/10 flex flex-col gap-2.5">
          <button
            type="button"
            onClick={() => {
              triggerTelegramHaptic("light");
              openTelegramUrl(telegramUrl);
            }}
            className="w-full py-3 rounded-xl bg-white/[0.06] hover:bg-[#E50914] text-white hover:!text-white border border-white/15 hover:border-[#E50914] text-xs sm:text-sm font-semibold flex items-center justify-center gap-2 transition-all cursor-pointer"
          >
            <span className="material-symbols-outlined text-[18px]">send</span>
            <span>
              {cleanedCode
                ? `Telegram botda ochish (#${cleanedCode})`
                : `Telegram botga o'tish (@${botUsername})`}
            </span>
          </button>

          <Link
            href="/search"
            className="text-center text-xs text-text-secondary hover:text-[#E50914] transition-colors py-1"
          >
            Kod yodingizdan chiqdimi? Nomi bo&apos;yicha qidirish →
          </Link>
        </div>
      </div>
    </div>
  );
}
