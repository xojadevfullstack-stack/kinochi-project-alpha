"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { detectEnvironment, Environment } from "./environment";
import { getToken, setToken, clearToken } from "./tokenStorage";
import { fetchApi } from "../api";

export interface User {
  id: number;
  telegram_id: number;
  first_name: string;
  last_name?: string;
  username?: string;
  role: string;
  is_active: boolean;
  language_code?: string;
}

export interface TelegramWidgetAuthData {
  id: number;
  first_name: string;
  last_name?: string;
  username?: string;
  photo_url?: string;
  auth_date: number;
  hash: string;
}

interface AuthContextValue {
  user: User | null;
  token: string | null;
  status: "loading" | "authenticated" | "unauthenticated" | "error";
  loginWithWidget: (widgetData: TelegramWidgetAuthData) => Promise<void>;
  loginDirect: (data?: { telegram_id?: number; first_name?: string; username?: string }) => Promise<void>;
  logout: () => void;
  resetAuthStatus: () => void;
  environment: Environment;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setTokenState] = useState<string | null>(null);
  const [status, setStatus] = useState<AuthContextValue["status"]>("loading");
  const [environment, setEnvironment] = useState<Environment>("browser");

  useEffect(() => {
    // Determine environment after mount to avoid hydration mismatch
    const env = detectEnvironment();
    setEnvironment(env);

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
            setUser(userData);
            setStatus("authenticated");
            window.history.replaceState({}, document.title, window.location.pathname);
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
          // Verify token by fetching user profile
          const userData = await fetchApi("/users/me");
          setTokenState(savedToken);
          setUser(userData);
          setStatus("authenticated");
          return; // Session successfully restored
        } catch (error) {
          console.error("Token verification failed:", error);
          clearToken(); // Invalid or expired token
        }
      }

      // If no valid token exists, handle based on environment
      if (env === "telegram_webapp" && window.Telegram?.WebApp?.initData) {
        try {
          const initData = window.Telegram.WebApp.initData;
          const authResponse = await fetchApi("/auth/telegram-webapp", {
            method: "POST",
            body: JSON.stringify({ initData }),
          });

          if (authResponse.access_token) {
            setToken(authResponse.access_token);
            setTokenState(authResponse.access_token);
            // Fetch user
            const userData = await fetchApi("/users/me");
            setUser(userData);
            setStatus("authenticated");
          } else {
            setStatus("unauthenticated");
          }
        } catch (error) {
          console.error("WebApp silent login failed:", error);
          setStatus("error"); // Use 'error' to show appropriate UI
        }
      } else {
        setStatus("unauthenticated");
      }
    };

    initAuth();

    // Listen for unauthorized events from api.ts interceptor
    const handleUnauthorized = () => {
      setTokenState(null);
      setUser(null);
      setStatus("unauthenticated");
    };

    window.addEventListener("auth:unauthorized", handleUnauthorized);
    return () => {
      window.removeEventListener("auth:unauthorized", handleUnauthorized);
    };
  }, []);

  const loginWithWidget = async (widgetData: TelegramWidgetAuthData) => {
    try {
      setStatus("loading");
      const authResponse = await fetchApi("/auth/telegram-login", {
        method: "POST",
        body: JSON.stringify(widgetData),
      });

      if (authResponse.access_token) {
        setToken(authResponse.access_token);
        setTokenState(authResponse.access_token);
        const userData = await fetchApi("/users/me");
        setUser(userData);
        setStatus("authenticated");
      } else {
        setStatus("unauthenticated");
      }
    } catch (error) {
      console.error("Widget login failed:", error);
      setStatus("error");
      throw error; // Let the component handle UI feedback
    }
  };

  const loginDirect = async (customData?: { telegram_id?: number; first_name?: string; username?: string }) => {
    try {
      setStatus("loading");
      const payload: Record<string, any> = {
        telegram_id: customData?.telegram_id || 123456789,
        first_name: customData?.first_name || "Kinochi Foydalanuvchi",
      };
      if (customData?.username) {
        payload.username = customData.username;
      }
      const authResponse = await fetchApi("/auth/dev-login", {
        method: "POST",
        body: JSON.stringify(payload),
      });

      if (authResponse.access_token) {
        setToken(authResponse.access_token);
        setTokenState(authResponse.access_token);
        const userData = await fetchApi("/users/me");
        setUser(userData);
        setStatus("authenticated");
      } else {
        setStatus("unauthenticated");
      }
    } catch (error) {
      console.error("Direct login failed:", error);
      setStatus("error");
      throw error;
    }
  };

  const resetAuthStatus = () => {
    setStatus("unauthenticated");
  };

  const logout = () => {
    clearToken();
    setTokenState(null);
    setUser(null);
    setStatus("unauthenticated");
  };

  return (
    <AuthContext.Provider
      value={{ user, token, status, loginWithWidget, loginDirect, logout, resetAuthStatus, environment }}
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
