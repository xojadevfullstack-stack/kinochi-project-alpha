"use client";

import React from "react";
import { useAuth } from "../../lib/auth/AuthProvider";

export default function TelegramLoginWidget() {
  const { environment, status, resetAuthStatus } = useAuth();
  const botUsername = process.env.NEXT_PUBLIC_BOT_USERNAME || "kinochi_uz_bot";

  if (environment !== "browser") {
    return null; // Do not show in WebApp
  }

  const telegramBotLoginUrl = `https://t.me/${botUsername}?start=login`;

  return (
    <div className="flex flex-col items-center justify-center my-1 w-full gap-2.5">
      {/* Telegram Bot orqali kirish */}
      <a
        href={telegramBotLoginUrl}
        target="_blank"
        rel="noopener noreferrer"
        className="w-full py-2.5 px-3 bg-[#229ED9] hover:bg-[#1e8cc0] text-white font-semibold rounded-xl text-xs sm:text-sm flex items-center justify-center gap-2 shadow-md shadow-[#229ED9]/20 transition-all cursor-pointer group active:scale-95"
      >
        <svg className="w-4 h-4 fill-current transition-transform group-hover:scale-110" viewBox="0 0 24 24">
          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.22-1.59.15-.15 2.71-2.48 2.76-2.69a.2.2 0 00-.05-.18c-.06-.05-.14-.03-.21-.02-.09.02-1.49.95-4.22 2.79-.4.27-.76.41-1.08.4-.36-.01-1.04-.2-1.55-.37-.63-.2-1.12-.31-1.08-.66.02-.18.27-.36.74-.55 2.92-1.27 4.86-2.11 5.83-2.51 2.78-1.16 3.35-1.36 3.73-1.36.08 0 .27.02.39.12.1.08.13.19.14.27-.01.06.01.24 0 .38z" />
        </svg>
        <span>Telegram Bot orqali kirish</span>
      </a>

      {status === "loading" && (
        <div className="text-xs text-text-secondary py-1 flex items-center justify-center gap-2">
          <span className="inline-block w-3.5 h-3.5 border-2 border-primary-container border-t-transparent rounded-full animate-spin"></span>
          <span>Tekshirilmoqda...</span>
        </div>
      )}

      {status === "error" && (
        <div className="flex flex-col items-center gap-1.5 py-1.5 px-3 rounded-xl bg-red-500/10 border border-red-500/20 w-full">
          <p className="text-red-400 text-xs font-medium">Kirishda xatolik yuz berdi</p>
          <button
            type="button"
            onClick={() => resetAuthStatus()}
            className="text-[11px] px-2.5 py-0.5 bg-white/10 hover:bg-white/20 text-white rounded-lg transition-colors font-medium cursor-pointer"
          >
            Qayta urinish
          </button>
        </div>
      )}
    </div>
  );
}
