"use client";

import { useEffect, useRef } from "react";
import { usePathname, useRouter } from "next/navigation";
import {
  initTelegram,
  setupTelegramBackButton,
  hideTelegramBackButton,
  triggerTelegramHaptic,
} from "@/lib/telegram";

export default function TelegramInit() {
  const pathname = usePathname();
  const router = useRouter();
  const pathnameRef = useRef(pathname);
  pathnameRef.current = pathname;

  useEffect(() => {
    initTelegram();
  }, []);

  useEffect(() => {
    const isRoot = !pathname || pathname === "/";

    if (!isRoot) {
      const handleBack = () => {
        triggerTelegramHaptic("light");

        if (typeof window !== "undefined") {
          const hasHistory =
            window.history.length > 1 &&
            ((window.history.state && window.history.state.idx > 0) ||
              (document.referrer && document.referrer.includes(window.location.host)));

          if (hasHistory) {
            router.back();
            return;
          }

          const currentPath = pathnameRef.current || "";
          let fallback = "/";
          if (currentPath.startsWith("/movie/") || currentPath.startsWith("/category/")) {
            fallback = "/movies";
          } else if (currentPath.startsWith("/series/")) {
            fallback = "/series";
          } else if (currentPath.startsWith("/collections/")) {
            fallback = "/collections";
          }

          const tg = (window as any).Telegram?.WebApp;
          if (tg && tg.initData) {
            window.location.href = fallback;
            return;
          }
          router.push(fallback);
        }
      };

      const cleanup = setupTelegramBackButton(handleBack);
      return cleanup;
    } else {
      hideTelegramBackButton();
    }
  }, [pathname, router]);

  return null;
}