"use client";

import { usePathname, useRouter } from "next/navigation";
import { triggerTelegramHaptic } from "@/lib/telegram";

export default function FloatingBackButton() {
  const pathname = usePathname();
  const router = useRouter();

  // Dual Back qoidasi: Bosh sahifada (/) orqaga tugmalari bo'lmasin
  if (!pathname || pathname === "/") {
    return null;
  }

  const handleBack = (e: React.MouseEvent<HTMLButtonElement>) => {
    e.preventDefault();
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

      router.push("/");
    }
  };

  return (
    <div className="fixed bottom-[86px] xl:bottom-6 right-4 z-40">
      <button
        type="button"
        onClick={handleBack}
        className="back-btn group relative inline-flex items-center justify-center w-11 h-11 rounded-2xl bg-white/90 backdrop-blur-xl border border-slate-300/80 text-slate-700 dark:bg-[#0E1117]/90 dark:border-white/15 dark:text-gray-200 hover:bg-[#B80710] dark:hover:bg-[#E50914] hover:border-[#B80710] dark:hover:border-[#E50914] hover:text-white active:scale-95 shadow-xl transition-all duration-200 cursor-pointer focus:outline-none focus:ring-2 focus:ring-primary/40"
        aria-label="Orqaga qaytish"
        title="Orqaga"
      >
        <span className="material-symbols-outlined text-[20px] text-slate-700 dark:text-gray-200 group-hover:text-white transition-colors duration-200">
          arrow_back
        </span>
      </button>
    </div>
  );
}
