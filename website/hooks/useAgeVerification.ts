"use client";

import { useState, useEffect, useCallback } from "react";

const STORAGE_KEY = "kinochi_age_verified_18";

export function useAgeVerification() {
  const [isMounted, setIsMounted] = useState(false);
  const [isVerified, setIsVerified] = useState(false);

  useEffect(() => {
    setIsMounted(true);
    try {
      const stored = localStorage.getItem(STORAGE_KEY) === "true";
      setIsVerified(stored);
    } catch {
      setIsVerified(false);
    }

    const handleEvent = (event: Event) => {
      const customEvent = event as CustomEvent<boolean>;
      if (customEvent?.detail !== undefined) {
        setIsVerified(!!customEvent.detail);
      } else {
        try {
          setIsVerified(localStorage.getItem(STORAGE_KEY) === "true");
        } catch {
          setIsVerified(false);
        }
      }
    };

    window.addEventListener("kinochi:age_verified", handleEvent);
    window.addEventListener("storage", handleEvent);

    return () => {
      window.removeEventListener("kinochi:age_verified", handleEvent);
      window.removeEventListener("storage", handleEvent);
    };
  }, []);

  const verifyAge = useCallback(() => {
    try {
      localStorage.setItem(STORAGE_KEY, "true");
    } catch {}
    setIsVerified(true);
    window.dispatchEvent(new CustomEvent("kinochi:age_verified", { detail: true }));
  }, []);

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
