"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import AdultHeroBackground from "@/components/AdultHeroBackground";

interface HeroTrailerBackdropProps {
  posterUrl?: string | null;
  trailerUrl?: string | null;
  title: string;
  is18Plus?: boolean;
  children?: React.ReactNode;
}

export default function HeroTrailerBackdrop({
  posterUrl,
  trailerUrl,
  title,
  is18Plus = false,
  children,
}: HeroTrailerBackdropProps) {
  const [isMounted, setIsMounted] = useState(false);
  const [videoReady, setVideoReady] = useState(false);
  const [isDimmed, setIsDimmed] = useState(false);

  const iframeRef = useRef<HTMLIFrameElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const isHoveredRef = useRef(false);

  // Helper function to extract YouTube ID
  const getYoutubeId = (url: string) => {
    const regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|&v=)([^#&?]*).*/;
    const match = url.match(regExp);
    return match && match[2].length === 11 ? match[2] : null;
  };

  const cleanUrl = (trailerUrl || "").trim();
  const isYoutube = cleanUrl.includes("youtube.com") || cleanUrl.includes("youtu.be");
  const youtubeId = isYoutube ? getYoutubeId(cleanUrl) : null;
  const isDirectMp4 = cleanUrl.endsWith(".mp4") || cleanUrl.includes(".mp4?");
  const hasVideo = Boolean(youtubeId || isDirectMp4);
  const TOP_SCROLL_THRESHOLD = 50;

  // Timer to dim metadata after a few seconds of initial reading
  const startDimTimer = useCallback(() => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
    }
    if (!hasVideo) return;

    timerRef.current = setTimeout(() => {
      const currentScrollY = typeof window !== "undefined" ? window.scrollY : 0;
      if (!isHoveredRef.current && currentScrollY <= TOP_SCROLL_THRESHOLD) {
        setIsDimmed(true);
      }
    }, 3500);
  }, [hasVideo]);

  // Restore metadata when user scrolls or interacts
  const restoreDetails = useCallback(() => {
    setIsDimmed(false);
    const currentScrollY = typeof window !== "undefined" ? window.scrollY : 0;
    if (currentScrollY <= TOP_SCROLL_THRESHOLD) {
      startDimTimer();
    } else {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
    }
  }, [startDimTimer]);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  useEffect(() => {
    if (!hasVideo) return;

    // Start timer on page enter
    startDimTimer();

    // Scroll & touch listeners: restores details when user scrolls, and restarts dim timer when back at the top
    const handleScrollOrTouch = () => {
      const currentScrollY = typeof window !== "undefined" ? window.scrollY : 0;
      setIsDimmed(false);

      if (currentScrollY <= TOP_SCROLL_THRESHOLD) {
        // User is at or scrolled back to top default position: start 3.5s dim timer again
        startDimTimer();
      } else {
        // User is scrolled down browsing content: keep details 100% visible
        if (timerRef.current) {
          clearTimeout(timerRef.current);
        }
      }
    };

    window.addEventListener("scroll", handleScrollOrTouch, { passive: true });
    window.addEventListener("touchmove", handleScrollOrTouch, { passive: true });

    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
      window.removeEventListener("scroll", handleScrollOrTouch);
      window.removeEventListener("touchmove", handleScrollOrTouch);
    };
  }, [hasVideo, restoreDetails, startDimTimer]);

  return (
    <div className="relative w-full min-h-[100svh] md:min-h-[800px] flex flex-col justify-start md:justify-center items-center pt-24 sm:pt-28 md:pt-32 pb-12 overflow-hidden">
      {/* Background Media Layer: Seamless full-bleed fill from y=0 behind fixed navbar */}
      <div className="absolute inset-0 top-0 overflow-hidden pointer-events-none">
        {/* Base Layer: Instant LCP Poster Image with fill */}
        {posterUrl ? (
          <AdultHeroBackground
            src={posterUrl}
            alt={title}
            is18Plus={is18Plus}
            isDetailPage={true}
          />
        ) : (
          <div className="absolute inset-0 bg-gradient-to-b from-surface-container to-background-obsidian" />
        )}

        {/* Ambient / Clear Video Layer: True object-cover fill for YouTube */}
        {isMounted && hasVideo && (
          <div
            className={`absolute inset-0 w-full h-full overflow-hidden transition-all duration-1000 ${
              !videoReady
                ? "opacity-0"
                : isDimmed
                ? "opacity-100 scale-100"
                : "opacity-60 md:opacity-75"
            }`}
          >
            {youtubeId ? (
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 pointer-events-none flex items-center justify-center">
                <iframe
                  ref={iframeRef}
                  src={`https://www.youtube-nocookie.com/embed/${youtubeId}?autoplay=1&mute=1&controls=0&playsinline=1&rel=0&showinfo=0&modestbranding=1&enablejsapi=1&iv_load_policy=3&disablekb=1&fs=0`}
                  style={{
                    width: "1920px",
                    height: "1080px",
                    maxWidth: "none",
                    pointerEvents: "none",
                  }}
                  className="scale-[1.15] sm:scale-[1.2] md:scale-[1.25] lg:scale-[1.3] pointer-events-none select-none border-0"
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                  onLoad={() => {
                    setTimeout(() => setVideoReady(true), 2400);
                  }}
                  tabIndex={-1}
                />
              </div>
            ) : isDirectMp4 ? (
              <video
                ref={videoRef}
                autoPlay
                muted
                loop
                playsInline
                onCanPlay={() => setVideoReady(true)}
                className="w-full h-full object-cover pointer-events-none"
                src={cleanUrl}
              />
            ) : null}
          </div>
        )}

        {/* Vignette Gradients: soften when dimmed so the trailer is in 1st priority focus */}
        <div
          className={`absolute inset-0 bg-gradient-to-t from-background-obsidian via-background-obsidian/[0.70] to-transparent pointer-events-none transition-opacity duration-1000 ${
            isDimmed ? "opacity-30" : "opacity-90"
          }`}
        />
        <div
          className={`absolute inset-0 bg-gradient-to-r from-background-obsidian via-background-obsidian/[0.75] md:via-background-obsidian/[0.60] to-transparent/20 pointer-events-none transition-opacity duration-1000 ${
            isDimmed ? "opacity-25" : "opacity-90"
          }`}
        />
        <div
          className={`absolute inset-0 bg-black/25 pointer-events-none transition-opacity duration-1000 ${
            isDimmed ? "opacity-10" : "opacity-100"
          }`}
        />
      </div>

      {/* Foreground Content: stays present in 2nd priority when dimmed, instantly restores on hover, tap or scroll */}
      <div
        onClick={() => {
          if (isDimmed) {
            setIsDimmed(false);
            startDimTimer();
          }
        }}
        onMouseEnter={() => {
          isHoveredRef.current = true;
          setIsDimmed(false);
          if (timerRef.current) {
            clearTimeout(timerRef.current);
          }
        }}
        onMouseLeave={() => {
          isHoveredRef.current = false;
          if (window.scrollY <= TOP_SCROLL_THRESHOLD) {
            startDimTimer();
          }
        }}
        className={`relative z-10 w-full transition-all duration-1000 ease-in-out ${
          isDimmed
            ? "opacity-25 hover:opacity-100 cursor-pointer"
            : "opacity-100"
        }`}
      >
        {children}
      </div>
    </div>
  );
}
