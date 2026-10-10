"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAgeVerification } from "@/hooks/useAgeVerification";

interface AgeVerificationModalProps {
  is18Plus?: boolean;
  allowDismissWithoutRedirect?: boolean;
  onVerifiedChange?: (verified: boolean) => void;
}

export default function AgeVerificationModal({
  is18Plus = false,
  allowDismissWithoutRedirect = false,
  onVerifiedChange,
}: AgeVerificationModalProps) {
  const router = useRouter();
  const { isMounted, isVerified, verifyAge } = useAgeVerification();
  const [manualOpen, setManualOpen] = useState(false);

  useEffect(() => {
    onVerifiedChange?.(isVerified);
  }, [isVerified, onVerifiedChange]);

  useEffect(() => {
    const handleOpenModal = () => {
      setManualOpen(true);
    };

    window.addEventListener("kinochi:open_age_modal", handleOpenModal);

    return () => {
      window.removeEventListener("kinochi:open_age_modal", handleOpenModal);
    };
  }, []);

  const handleConfirm = () => {
    verifyAge();
    setManualOpen(false);
    onVerifiedChange?.(true);
  };

  const handleDecline = () => {
    setManualOpen(false);
    if (allowDismissWithoutRedirect) {
      // Just close modal if dismissal without redirect is allowed
      return;
    }

    if (typeof window !== "undefined" && window.history.length > 1) {
      router.back();
    } else {
      router.push("/");
    }
  };

  if (!isMounted) {
    return null;
  }

  // Open if manually requested OR if current page is 18+ and user is not verified on this page
  const shouldShow = manualOpen || (is18Plus && !isVerified);
  if (!shouldShow) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-xl animate-in fade-in duration-300">
      <div className="relative w-full max-w-md bg-surface-container-high/95 border border-red-500/30 rounded-2xl p-6 sm:p-8 shadow-2xl shadow-red-950/50 text-center flex flex-col items-center">
        {/* Glow decoration */}
        <div className="absolute -top-12 w-28 h-28 bg-red-600/20 rounded-full blur-2xl pointer-events-none"></div>

        {/* 18+ Icon */}
        <div className="w-16 h-16 rounded-full bg-red-600/20 border-2 border-red-500/40 flex items-center justify-center mb-5 shadow-lg shadow-red-600/30 animate-pulse">
          <span className="text-3xl font-black text-red-400">🔞</span>
        </div>

        {/* Title */}
        <h2 className="font-display text-xl sm:text-2xl font-bold text-white mb-2 tracking-tight">
          18+ Yosh chegarasi
        </h2>

        {/* Subtitle / Notice */}
        <p className="text-text-secondary text-sm leading-relaxed mb-6">
          Ushbu film/serial faqat <b>18 yoshdan katta</b> foydalanuvchilar uchun mo&apos;ljallangan. 
          Davom etish orqali 18 yoshga to&apos;lganingizni tasdiqlaysiz.
        </p>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-3 w-full">
          <button
            type="button"
            onClick={handleConfirm}
            className="flex-1 bg-red-600 hover:bg-red-500 active:scale-95 text-white font-bold py-3.5 px-4 rounded-xl text-sm transition-all shadow-lg shadow-red-600/40 flex items-center justify-center gap-2 cursor-pointer"
          >
            <span className="material-symbols-outlined text-lg">check_circle</span>
            <span>Ha, 18 yoshdaman</span>
          </button>

          <button
            type="button"
            onClick={handleDecline}
            className="flex-1 bg-white/10 hover:bg-white/15 active:scale-95 text-white/80 hover:text-white font-medium py-3.5 px-4 rounded-xl text-sm border border-white/10 transition-all flex items-center justify-center gap-2 cursor-pointer"
          >
            <span className="material-symbols-outlined text-lg">arrow_back</span>
            <span>Ortga qaytish</span>
          </button>
        </div>
      </div>
    </div>
  );
}

