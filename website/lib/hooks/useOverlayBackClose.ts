"use client";

import { useEffect, useRef } from "react";

let suppressBackUntil = 0;

/**
 * Call immediately before programmatic navigation (router.push / Link navigation)
 * triggered from inside an overlay so closing the overlay does not call history.back()
 * and abort the in-flight navigation.
 */
export function suppressOverlayHistoryBack(durationMs = 1500) {
  suppressBackUntil = Date.now() + durationMs;
}

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

    const openedHref = window.location.href;
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
        const isSuppressed = Date.now() < suppressBackUntil;
        const urlChanged = window.location.href !== openedHref;
        try {
          if (window.history.state?.__kinochiOverlayToken === token) {
            if (isSuppressed || urlChanged) {
              // Scrub token in-place without calling history.back(), preserving the active navigation
              const nextState = { ...(window.history.state || {}) };
              delete nextState.__kinochiOverlayToken;
              window.history.replaceState(nextState, "");
            } else {
              window.history.back();
            }
          }
        } catch {}
      }
    };
  }, [isOpen]);
}
