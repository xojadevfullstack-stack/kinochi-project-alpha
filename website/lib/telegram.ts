// Telegram WebApp Utilities and Helpers

export function getTelegramWebApp() {
  if (typeof window === "undefined") return null;
  return (window as any).Telegram?.WebApp || null;
}

export function initTelegram() {
  if (typeof window === "undefined") return;
  const tg = (window as any).Telegram?.WebApp;
  if (tg) {
    try {
      if (typeof tg.ready === "function") {
        tg.ready();
      }
      if (typeof tg.expand === "function") {
        tg.expand();
      }
      // Set theme colors only if supported by Telegram WebApp version (>= 6.1)
      const isAtLeast61 = typeof tg.isVersionAtLeast === "function" ? tg.isVersionAtLeast("6.1") : false;
      if (isAtLeast61) {
        if (typeof tg.setHeaderColor === "function") {
          tg.setHeaderColor("#0d0d12");
        }
        if (typeof tg.setBackgroundColor === "function") {
          tg.setBackgroundColor("#0d0d12");
        }
      }
    } catch (e) {
      console.warn("Telegram WebApp initialization error:", e);
    }
  }
}

export function openTelegramUrl(url: string) {
  if (typeof window === "undefined") return;
  
  const tg = (window as any).Telegram?.WebApp;
  const isTgLink = url.startsWith("https://t.me") || url.startsWith("tg://");

  // 1. Inside Telegram WebApp with openTelegramLink
  if (tg && isTgLink && typeof tg.openTelegramLink === "function") {
    try {
      tg.openTelegramLink(url);
      return;
    } catch (e) {
      console.warn("tg.openTelegramLink failed, trying fallback:", e);
    }
  }

  // 2. Inside Telegram WebApp with non-telegram link
  if (tg && !isTgLink && typeof tg.openLink === "function") {
    try {
      tg.openLink(url);
      return;
    } catch (e) {
      console.warn("tg.openLink failed, trying fallback:", e);
    }
  }

  // 3. Mobile touch device (in-app browser or mobile browser)
  const isMobile = /Mobi|Android|iPhone|iPad|iPod/i.test(navigator.userAgent);
  if (isMobile) {
    window.location.href = url;
    return;
  }

  // 4. Desktop browser
  window.open(url, "_blank", "noopener,noreferrer");
}