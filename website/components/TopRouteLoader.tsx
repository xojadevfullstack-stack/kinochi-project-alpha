"use client";

import { Suspense, useEffect, useRef, useState } from "react";
import { usePathname, useSearchParams } from "next/navigation";

function RouteProgressInner() {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [navigating, setNavigating] = useState(false);
  const [progress, setProgress] = useState(0);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const safetyRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const stopLoader = () => {
    if (timerRef.current) clearInterval(timerRef.current);
    if (safetyRef.current) clearTimeout(safetyRef.current);
    timerRef.current = null;
    safetyRef.current = null;
    setProgress(100);
    setTimeout(() => {
      setNavigating(false);
      setProgress(0);
    }, 180);
  };

  // Complete bar whenever route or search params finish updating
  useEffect(() => {
    if (navigating) {
      stopLoader();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pathname, searchParams]);

  useEffect(() => {
    const startLoader = () => {
      if (timerRef.current) clearInterval(timerRef.current);
      if (safetyRef.current) clearTimeout(safetyRef.current);
      setNavigating(true);
      setProgress(22);

      timerRef.current = setInterval(() => {
        setProgress((prev) => (prev < 88 ? Math.min(88, prev + (90 - prev) * 0.14) : prev));
      }, 180);

      // Guard against aborted / blocked navigations
      safetyRef.current = setTimeout(() => {
        stopLoader();
      }, 8000);
    };

    const handleClick = (e: MouseEvent) => {
      if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) {
        return;
      }
      const target = e.target as HTMLElement | null;
      const anchor = target?.closest?.("a[href]") as HTMLAnchorElement | null;
      if (!anchor) return;
      if (anchor.target === "_blank" || anchor.hasAttribute("download")) return;

      const rawHref = anchor.getAttribute("href") || "";
      if (!rawHref || rawHref.startsWith("#") || !rawHref.startsWith("/")) return;

      const currentUrl = `${window.location.pathname}${window.location.search}`;
      if (rawHref === currentUrl || rawHref === window.location.pathname) return;

      startLoader();
    };

    document.addEventListener("click", handleClick, true);
    return () => {
      document.removeEventListener("click", handleClick, true);
      if (timerRef.current) clearInterval(timerRef.current);
      if (safetyRef.current) clearTimeout(safetyRef.current);
    };
  }, []);

  if (!navigating) return null;

  return (
    <div
      className="fixed top-0 left-0 right-0 z-[200] h-[3px] pointer-events-none bg-transparent"
      role="progressbar"
      aria-valuenow={Math.round(progress)}
      aria-valuemin={0}
      aria-valuemax={100}
    >
      <div
        className="h-full bg-[#E50914] transition-all duration-200 ease-out"
        style={{ width: `${progress}%` }}
      />
    </div>
  );
}

/**
 * Global zero-delay top route progress bar for Vercel/SSR page transitions.
 */
export default function TopRouteLoader() {
  return (
    <Suspense fallback={null}>
      <RouteProgressInner />
    </Suspense>
  );
}
