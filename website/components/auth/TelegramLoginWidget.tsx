"use client";

import React, { useEffect, useRef } from "react";
import { useAuth, TelegramWidgetAuthData } from "../../lib/auth/AuthProvider";

export default function TelegramLoginWidget() {
  const { loginWithWidget, environment, status } = useAuth();
  const widgetRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Only render widget if environment is browser and we are not authenticated
    if (environment !== "browser" || status === "authenticated") {
      return;
    }

    const botUsername = process.env.NEXT_PUBLIC_BOT_USERNAME;
    if (!botUsername) {
      console.error("NEXT_PUBLIC_BOT_USERNAME is not defined in environment variables");
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
    // Add random param so the browser re-evaluates the script every time the dropdown opens
    script.src = `https://telegram.org/js/telegram-widget.js?22&r=${Math.random()}`;
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
      // Cleanup
      delete (window as any).onTelegramAuth;
      if (widgetRef.current) {
        widgetRef.current.innerHTML = "";
      }
    };
  }, [environment, loginWithWidget, status]);

  if (environment !== "browser") {
    return null; // Do not show in WebApp
  }

  if (status === "loading") {
    return <div className="text-gray-400">Loading Telegram Login...</div>;
  }
  
  if (status === "error") {
    return <div className="text-red-500 text-sm">Failed to login. Please try again.</div>;
  }

  return <div ref={widgetRef} className="flex justify-center my-4 min-h-[40px]" />;
}
