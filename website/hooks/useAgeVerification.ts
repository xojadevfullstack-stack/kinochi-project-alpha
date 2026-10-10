"use client";

import { useState, useEffect, useCallback } from "react";
import { usePathname } from "next/navigation";

// In-memory record of the currently verified pathname.
// Deliberately NOT stored in localStorage so each 18+ page prompts anew.
let activeVerifiedPath: string | null = null;

export function useAgeVerification() {
  const pathname = usePathname();
  const [isMounted, setIsMounted] = useState(false);
  const [isVerified, setIsVerified] = useState(false);

  useEffect(() => {
    setIsMounted(true);

    // Clean up any stale persistent storage from older implementations
    try {
      localStorage.removeItem("kinochi_age_verified_18");
    } catch {}

    const currentlyVerified = activeVerifiedPath !== null && activeVerifiedPath === pathname;
    setIsVerified(currentlyVerified);

    const handleEvent = (event: Event) => {
      const customEvent = event as CustomEvent<{ path?: string; verified?: boolean } | boolean>;
      if (typeof customEvent?.detail === "object" && customEvent.detail !== null) {
        if (customEvent.detail.path === pathname) {
          setIsVerified(!!customEvent.detail.verified);
        } else {
          setIsVerified(activeVerifiedPath !== null && activeVerifiedPath === pathname);
        }
      } else if (typeof customEvent?.detail === "boolean") {
        setIsVerified(customEvent.detail);
      } else {
        setIsVerified(activeVerifiedPath !== null && activeVerifiedPath === pathname);
      }
    };

    window.addEventListener("kinochi:age_verified", handleEvent);

    return () => {
      window.removeEventListener("kinochi:age_verified", handleEvent);
    };
  }, [pathname]);

  const verifyAge = useCallback(() => {
    activeVerifiedPath = pathname;
    setIsVerified(true);
    window.dispatchEvent(
      new CustomEvent("kinochi:age_verified", {
        detail: { path: pathname, verified: true },
      })
    );
  }, [pathname]);

  const openVerificationModal = useCallback(() => {
    window.dispatchEvent(new CustomEvent("kinochi:open_age_modal"));
  }, []);

  return {
    isMounted,
    isVerified,
    verifyAge,
    openVerificationModal,
  };
}

