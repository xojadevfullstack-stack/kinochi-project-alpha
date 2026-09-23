"use client";

import React, { useEffect, useRef } from "react";
import { useAuth, TelegramWidgetAuthData } from "../../lib/auth/AuthProvider";

export default function TelegramLoginWidget() {
  const { loginWithWidget, environment, status, resetAuthStatus } = useAuth();
  const widgetRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Only render widget if environment is browser and we are not authenticated
    if (environment !== "browser" || status === "authenticated" || status === "loading" || status === "error") {
      return;
    }

    const botUsername = process.env.NEXT_PUBLIC_BOT_USERNAME;
    if (!botUsername) {
      console.warn("NEXT_PUBLIC_BOT_USERNAME is not defined in environment variables");
      return;
    }

    // Define the global callback function that Telegram's script will call
    (window as any).onTelegramAuth = (user: TelegramWidgetAuthData) => {
      loginWithWidget(user).catch(console.error);
    };

    // Clean up any existing script to avoid duplicates on re-renders
    if (widgetRef.current) {
      widgetRef.current.innerHTML = "";
    }

    // Create the script element dynamically
    const script = document.createElement("script");
    script.src = "https://telegram.org/js/telegram-widget.js?22";
    script.async = true;
    script.setAttribute("data-telegram-login", botUsername);
    script.setAttribute("data-size", "large");
    script.setAttribute("data-radius", "8");
    script.setAttribute("data-onauth", "onTelegramAuth(user)");
    script.setAttribute("data-request-access", "write");

    if (widgetRef.current) {
      widgetRef.current.appendChild(script);
    }

    return () => {
      delete (window as any).onTelegramAuth;
      if (widgetRef.current) {
        widgetRef.current.innerHTML = "";
      }
    };
  }, [environment, loginWithWidget, status]);

  if (environment !== "browser") {
    return null; // Do not show in WebApp
  }

  return (
    <div className="flex flex-col items-center justify-center my-2 min-h-[44px] text-center w-full">
      {status === "loading" && (
        <div className="text-xs text-text-secondary py-2 flex items-center justify-center gap-2">
          <span className="inline-block w-4 h-4 border-2 border-primary-container border-t-transparent rounded-full animate-spin"></span>
          <span>Telegram Login yuklanmoqda...</span>
        </div>
      )}

      {status === "error" && (
        <div className="flex flex-col items-center gap-2 py-2 px-3 rounded-xl bg-red-500/10 border border-red-500/20 max-w-xs my-1">
          <p className="text-red-400 text-xs font-medium">Kirishda xatolik yuz berdi</p>
          <button
            type="button"
            onClick={() => resetAuthStatus()}
            className="text-xs px-3 py-1 bg-white/10 hover:bg-white/20 text-white rounded-lg transition-colors font-medium cursor-pointer"
          >
            Qayta urinish
          </button>
        </div>
      )}

      <div
        ref={widgetRef}
        className={`flex justify-center w-full ${status === "loading" || status === "error" ? "hidden" : ""}`}
      />
    </div>
  );
}
