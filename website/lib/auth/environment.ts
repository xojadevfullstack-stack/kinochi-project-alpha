export type Environment = "telegram_webapp" | "browser";

declare global {
  interface Window {
    Telegram?: {
      WebApp?: {
        initData?: string;
        [key: string]: any;
      };
    };
  }
}

export function detectEnvironment(): Environment {
  if (typeof window === "undefined") {
    // Should not be called during SSR, fallback to browser
    return "browser";
  }

  // Check if Telegram WebApp initData is present and non-empty
  if (
    window.Telegram &&
    window.Telegram.WebApp &&
    window.Telegram.WebApp.initData &&
    window.Telegram.WebApp.initData.trim() !== ""
  ) {
    return "telegram_webapp";
  }

  return "browser";
}
