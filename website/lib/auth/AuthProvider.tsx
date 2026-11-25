"use client";

import React, { createContext, useCallback, useContext, useEffect, useState } from "react";
import { detectEnvironment, Environment } from "./environment";
import { getToken, setToken, clearToken } from "./tokenStorage";
import { fetchApi, getPublicConfig } from "../api";

export interface User {
  id: number;
  telegram_id: number;
  first_name: string;
  last_name?: string;
  username?: string;
  role: string;
  is_active: boolean;
  language_code?: string;
  show_adult_content?: boolean;
}

interface AuthContextValue {
  user: User | null;
  token: string | null;
  status: "loading" | "authenticated" | "unauthenticated" | "error";
  logout: () => void;
  resetAuthStatus: () => void;
  triggerWebAppLogin: () => Promise<boolean>;
  environment: Environment;
  botUsername: string;
  streamEnabled: boolean;
  showAdultContent: boolean;
  updateAdultContent: (enabled: boolean) => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

const DEFAULT_BOT_USERNAME = (process.env.NEXT_PUBLIC_BOT_USERNAME || "MediaPlusOfficialBot")
  .trim()
  .replace(/^@+/, "");

async function waitForTelegramInitData(maxWaitMs = 2000): Promise<string | null> {
  if (typeof window === "undefined") return null;
  const started = Date.now();
  while (Date.now() - started < maxWaitMs) {
    const raw = window.Telegram?.WebApp?.initData;
    if (raw && raw.trim() !== "") {
      return raw;
    }
    await new Promise((resolve) => setTimeout(resolve, 150));
  }
  const finalRaw = window.Telegram?.WebApp?.initData;
  return finalRaw && finalRaw.trim() !== "" ? finalRaw : null;
}

export function AuthProvider({
  children,
  initialBotUsername,
  initialStreamEnabled = false,
}: {
  children: React.ReactNode;
  initialBotUsername?: string;
  initialStreamEnabled?: boolean;
}) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setTokenState] = useState<string | null>(null);
  const [status, setStatus] = useState<AuthContextValue["status"]>("loading");
  const [environment, setEnvironment] = useState<Environment>("browser");
  const [botUsername, setBotUsername] = useState<string>(
    (initialBotUsername || DEFAULT_BOT_USERNAME).replace(/^@+/, "")
  );
  const [streamEnabled, setStreamEnabled] = useState<boolean>(initialStreamEnabled);
  const [showAdultContent, setShowAdultContent] = useState<boolean>(false);

  const persistAdultPreference = useCallback((enabled: boolean) => {
    setShowAdultContent(enabled);
    if (typeof window !== "undefined") {
      try {
        localStorage.setItem("kinochi_show_adult", enabled ? "1" : "0");
      } catch {}
      document.cookie = `kinochi_show_adult=${enabled ? "1" : "0"}; Path=/; Max-Age=31536000; SameSite=Lax`;
    }
  }, []);

  const syncUserSession = useCallback(
    (userData: User) => {
      setUser(userData);
      setStatus("authenticated");
      persistAdultPreference(Boolean(userData?.show_adult_content));
    },
    [persistAdultPreference]
  );

  const updateAdultContent = useCallback(
    async (enabled: boolean) => {
      persistAdultPreference(enabled);
      if (getToken()) {
        try {
          const updated = await fetchApi("/users/me/settings", {
            method: "PATCH",
            body: JSON.stringify({ show_adult_content: enabled }),
          });
          if (updated) {
            setUser(updated);
            persistAdultPreference(Boolean(updated.show_adult_content));
          }
        } catch (err) {
          console.error("Failed to persist 18+ preference to backend:", err);
        }
      }
    },
    [persistAdultPreference]
  );

  const attemptWebAppLogin = useCallback(async (initData: string): Promise<boolean> => {
    for (let attempt = 0; attempt < 2; attempt++) {
      try {
        const authResponse = await fetchApi("/auth/telegram-webapp", {
          method: "POST",
          body: JSON.stringify({ initData }),
        });

        if (authResponse?.access_token) {
          setToken(authResponse.access_token);
          setTokenState(authResponse.access_token);
          const userData = await fetchApi("/users/me");
          syncUserSession(userData);
          return true;
        }
      } catch (error) {
        console.warn(`WebApp silent login attempt ${attempt + 1} failed:`, error);
        if (attempt === 0) {
          await new Promise((resolve) => setTimeout(resolve, 800));
        }
      }
    }
    return false;
  }, [syncUserSession]);

  const triggerWebAppLogin = useCallback(async (): Promise<boolean> => {
    const initData = await waitForTelegramInitData(1200);
    if (!initData) return false;
    setEnvironment("telegram_webapp");
    setStatus("loading");
    const ok = await attemptWebAppLogin(initData);
    if (!ok) setStatus("error");
    return ok;
  }, [attemptWebAppLogin]);

  useEffect(() => {
    let active = true;

    // Sync live public config (active bot username & stream availability) from backend
    getPublicConfig().then((cfg) => {
      if (!active) return;
      if (cfg.bot_username) setBotUsername(cfg.bot_username);
      setStreamEnabled(Boolean(cfg.stream_enabled));
    });

    // Determine initial environment & saved 18+ filter preference after mount
    const env = detectEnvironment();
    setEnvironment(env);
    if (typeof window !== "undefined") {
      try {
        const match = document.cookie.match(/(?:^|;\s*)kinochi_show_adult=([^;]*)/);
        const cookieAdult = match ? match[1] === "1" : localStorage.getItem("kinochi_show_adult") === "1";
        setShowAdultContent(cookieAdult);
      } catch {}
    }

    const initAuth = async () => {
      // 1. Check URL parameters for direct token login (e.g. ?auth_token=...)
      if (typeof window !== "undefined") {
        const urlParams = new URLSearchParams(window.location.search);
        const queryToken = urlParams.get("auth_token");
        if (queryToken) {
          try {
            setToken(queryToken);
            setTokenState(queryToken);
            const userData = await fetchApi("/users/me");
            if (!active) return;
            syncUserSession(userData);
            urlParams.delete("auth_token");
            const nextQs = urlParams.toString();
            const cleanUrl = nextQs ? `${window.location.pathname}?${nextQs}` : window.location.pathname;
            window.history.replaceState({}, document.title, cleanUrl);
            return;
          } catch (e) {
            console.error("URL auth_token verification failed:", e);
            clearToken();
          }
        }
      }

      const savedToken = getToken();

      if (savedToken) {
        try {
          const userData = await fetchApi("/users/me");
          if (!active) return;
          setTokenState(savedToken);
          syncUserSession(userData);
          return;
        } catch (error) {
          console.error("Token verification failed:", error);
          clearToken();
        }
      }

      // 2. Telegram WebApp automatic seamless login (waits briefly for late Telegram SDK initData)
      const immediateInitData = window.Telegram?.WebApp?.initData;
      const inTgWebApp =
        env === "telegram_webapp" ||
        Boolean(immediateInitData) ||
        Boolean(
          typeof window !== "undefined" &&
            window.Telegram?.WebApp?.platform &&
            window.Telegram.WebApp.platform !== "unknown"
        );

      const resolvedInitData = immediateInitData?.trim()
        ? immediateInitData
        : inTgWebApp
        ? await waitForTelegramInitData(2200)
        : null;

      if (!active) return;

      if (resolvedInitData) {
        setEnvironment("telegram_webapp");
        const ok = await attemptWebAppLogin(resolvedInitData);
        if (!active) return;
        if (!ok) setStatus("error");
      } else {
        setStatus("unauthenticated");
      }
    };

    initAuth();

    // Listen for unauthorized events from api.ts interceptor
    const handleUnauthorized = async () => {
      setTokenState(null);
      setUser(null);
      const tgData = window.Telegram?.WebApp?.initData;
      if (tgData && tgData.trim() !== "") {
        const ok = await attemptWebAppLogin(tgData);
        if (ok) return;
      }
      setStatus("unauthenticated");
    };

    window.addEventListener("auth:unauthorized", handleUnauthorized);
    return () => {
      active = false;
      window.removeEventListener("auth:unauthorized", handleUnauthorized);
    };
  }, [attemptWebAppLogin, syncUserSession]);

  const resetAuthStatus = () => {
    if (typeof window !== "undefined" && window.Telegram?.WebApp?.initData) {
      triggerWebAppLogin();
      return;
    }
    setStatus("unauthenticated");
  };

  const logout = () => {
    try {
      fetchApi("/auth/logout", { method: "POST" }).catch(() => {});
    } catch (e) {}
    if (typeof document !== "undefined") {
      document.cookie = "user_access_token=; path=/; max-age=0; expires=Thu, 01 Jan 1970 00:00:00 GMT";
      document.cookie = "access_token=; path=/; max-age=0; expires=Thu, 01 Jan 1970 00:00:00 GMT";
    }
    persistAdultPreference(false);
    clearToken();
    setTokenState(null);
    setUser(null);
    setStatus("unauthenticated");
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        status,
        logout,
        resetAuthStatus,
        triggerWebAppLogin,
        environment,
        botUsername,
        streamEnabled,
        showAdultContent,
        updateAdultContent,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
