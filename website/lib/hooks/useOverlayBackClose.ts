"use client";

import { useEffect, useRef } from "react";

/**
 * Intercepts browser / native OS Back (popstate) when an overlay (modal, drawer, onboarding)
 * is open, closing the overlay first instead of navigating away from the current page.
 */
export function useOverlayBackClose(isOpen: boolean, onClose: () => void) {
  const onCloseRef = useRef(onClose);
  onCloseRef.current = onClose;

  const pushedRef = useRef(false);

  useEffect(() => {
    if (typeof window === "undefined" || !isOpen) return;

    const token = `__overlay_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`;
    try {
      window.history.pushState(
        { ...(window.history.state || {}), __kinochiOverlayToken: token },
        ""
      );
      pushedRef.current = true;
    } catch {
      pushedRef.current = false;
    }

    const handlePopState = () => {
      if (pushedRef.current) {
        pushedRef.current = false;
        onCloseRef.current();
      }
    };

    window.addEventListener("popstate", handlePopState);
    return () => {
      window.removeEventListener("popstate", handlePopState);
      if (pushedRef.current) {
        pushedRef.current = false;
        try {
          if (window.history.state?.__kinochiOverlayToken === token) {
            window.history.back();
          }
        } catch {}
      }
    };
  }, [isOpen]);
}
