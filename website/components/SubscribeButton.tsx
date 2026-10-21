"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "@/lib/auth/AuthProvider";
import { fetchApi } from "@/lib/api";
import TelegramLoginWidget from "@/components/auth/TelegramLoginWidget";

interface SubscribeButtonProps {
  targetType: "series" | "collection";
  targetId: number;
  title?: string;
  className?: string;
  showIconOnly?: boolean;
}

export default function SubscribeButton({
  targetType,
  targetId,
  title = "",
  className = "",
  showIconOnly = false,
}: SubscribeButtonProps) {
  const { user, status } = useAuth();
  const [isSubscribed, setIsSubscribed] = useState(false);
  const [loading, setLoading] = useState(false);
  const [checking, setChecking] = useState(true);
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // Check subscription status
  useEffect(() => {
    let isMounted = true;

    async function checkStatus() {
      if (!targetId) return;
      try {
        const query = user?.telegram_id ? `?telegram_user_id=${user.telegram_id}` : "";
        const endpoint =
          targetType === "series"
            ? `/series/${targetId}/subscription-status${query}`
            : `/collections/${targetId}/subscription-status${query}`;

        const data = await fetchApi(endpoint);
        if (isMounted) {
          setIsSubscribed(Boolean(data?.is_subscribed));
        }
      } catch (err) {
        // Guest or error -> fallback to unconfirmed
      } finally {
        if (isMounted) setChecking(false);
      }
    }

    checkStatus();

    const handleSync = () => checkStatus();
    window.addEventListener("subscription:change", handleSync);
    return () => {
      isMounted = false;
      window.removeEventListener("subscription:change", handleSync);
    };
  }, [targetId, targetType, user?.telegram_id, status]);

  const handleToggle = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();

    if (status !== "authenticated" || !user?.telegram_id) {
      setShowLoginModal(true);
      return;
    }

    setLoading(true);
    try {
      const endpoint =
        targetType === "series"
          ? `/series/${targetId}/subscribe`
          : `/collections/${targetId}/subscribe`;

      const res = await fetchApi(endpoint, {
        method: "POST",
        body: JSON.stringify({ telegram_user_id: user.telegram_id }),
      });

      const nextState = Boolean(res?.is_subscribed);
      setIsSubscribed(nextState);

      const msg = nextState
        ? "🔔 Obuna bo'ldingiz! Yangi qism chiqqanda Telegram botingizga xabar yuboriladi."
        : "🔕 Obuna bekor qilindi.";
      setToastMessage(msg);
      setTimeout(() => setToastMessage(null), 4000);

      window.dispatchEvent(new Event("subscription:change"));
    } catch (err: any) {
      setToastMessage("Xatolik: " + (err?.message || "Amalni bajarib bo'lmadi"));
      setTimeout(() => setToastMessage(null), 3000);
    } finally {
      setLoading(false);
    }
  };

  const botUsername = process.env.NEXT_PUBLIC_BOT_USERNAME || "kinochi_mvp_bot";
  const botDeepLink = `https://t.me/${botUsername}?start=sub_${targetType === "series" ? "series" : "col"}_${targetId}`;

  return (
    <>
      <button
        onClick={handleToggle}
        disabled={loading}
        title={isSubscribed ? "Obunani bekor qilish" : "Yangi qismlarga obuna bo'lish"}
        className={
          className ||
          `inline-flex items-center justify-center gap-2 px-5 py-3.5 rounded-xl font-label-caps text-xs sm:text-sm uppercase tracking-wider font-bold transition-all duration-200 cursor-pointer shadow-md active:scale-95 ${
            isSubscribed
              ? "bg-white/10 hover:bg-red-500/20 text-white hover:text-red-300 border border-white/20 hover:border-red-500/40"
              : "bg-red-600 hover:bg-red-700 text-white hover:scale-[1.02] shadow-red-950/50"
          }`
        }
      >
        <span
          className="material-symbols-outlined text-[18px]"
          style={isSubscribed ? { fontVariationSettings: "'FILL' 1" } : undefined}
        >
          {isSubscribed ? "notifications_active" : "notifications"}
        </span>
        {!showIconOnly && (
          <span>
            {checking
              ? "Yuklanmoqda..."
              : isSubscribed
              ? "Obunadasiz"
              : "Obuna bo'lish"}
          </span>
        )}
      </button>

      {/* Floating Feedback Toast */}
      {toastMessage && (
        <div className="fixed bottom-20 left-1/2 -translate-x-1/2 z-50 px-5 py-3 rounded-xl bg-neutral-900 border border-white/20 text-white text-xs sm:text-sm font-medium shadow-2xl backdrop-blur-md flex items-center gap-3 animate-in fade-in slide-in-from-bottom-3 duration-200">
          <span className="material-symbols-outlined text-rating-gold text-lg">info</span>
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Login Prompt Modal for Guests */}
      {showLoginModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-surface-container-high border border-white/15 rounded-2xl max-w-md w-full p-6 text-center space-y-5 shadow-2xl relative">
            <button
              onClick={() => setShowLoginModal(false)}
              className="absolute top-4 right-4 text-text-secondary hover:text-white p-1 rounded-lg hover:bg-white/10"
            >
              <span className="material-symbols-outlined text-xl">close</span>
            </button>

            <div className="w-14 h-14 mx-auto rounded-2xl bg-red-600/20 border border-red-500/30 flex items-center justify-center text-red-400">
              <span className="material-symbols-outlined text-3xl">notifications_active</span>
            </div>

            <div className="space-y-2">
              <h3 className="text-lg font-bold text-white">
                {title ? `"${title}" yangilanishlariga obuna bo'lish` : "Yangi qismlarga obuna bo'ling"}
              </h3>
              <p className="text-xs text-text-secondary leading-relaxed">
                Yangi qism chiqqanda Telegram botingizga video va xabar darhol yetib borishi uchun
                tizimga kiring yoki bot orqali 1-bosqichda obuna bo'ling.
              </p>
            </div>

            <div className="space-y-3 pt-2">
              <a
                href={botDeepLink}
                target="_blank"
                rel="noopener noreferrer"
                className="w-full py-3.5 px-4 rounded-xl bg-sky-500 hover:bg-sky-600 text-white font-bold text-xs uppercase tracking-wider flex items-center justify-center gap-2 shadow-lg transition-all"
              >
                <svg className="w-4 h-4 fill-current" viewBox="0 0 24 24">
                  <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.896-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/>
                </svg>
                <span>Telegram Bot orqali obuna bo'lish</span>
              </a>

              <div className="pt-2 border-t border-white/10">
                <p className="text-[11px] text-text-secondary mb-2">Yoki saytdagi profilingizga kiring:</p>
                <div className="flex justify-center">
                  <TelegramLoginWidget />
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
