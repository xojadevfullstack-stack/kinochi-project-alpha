"use client";

import { useState, useRef, useEffect, useCallback } from "react";

export interface TranslationSource {
  id: number;
  language: string;
  stream_url?: string;
  storage_channel_message_id?: number;
  telegram_file_id?: string;
}

interface CinemaPlayerProps {
  title: string;
  mediaCode: string;
  mediaType?: "movie" | "episode";
  posterUrl?: string;
  translations?: TranslationSource[];
  directStreamUrl?: string;
  telegramDeepLink?: string;
  storageChannelUsername?: string;
  onNextEpisode?: () => void;
  hasNextEpisode?: boolean;
  episodeNumber?: number;
  seasonNumber?: number;
  seriesTitle?: string;
}

const SPEED_OPTIONS = [0.5, 0.75, 1, 1.25, 1.5, 2];

function formatTime(seconds: number): string {
  if (isNaN(seconds) || seconds < 0) return "00:00";
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);

  if (h > 0) {
    return `${h.toString().padStart(2, "0")}:${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  }
  return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
}

export default function CinemaPlayer({
  title,
  mediaCode,
  mediaType = "movie",
  posterUrl,
  translations = [],
  directStreamUrl,
  telegramDeepLink,
  storageChannelUsername,
  onNextEpisode,
  hasNextEpisode = false,
  episodeNumber,
  seasonNumber,
  seriesTitle,
}: CinemaPlayerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const progressBarRef = useRef<HTMLDivElement>(null);
  const controlsTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Player States
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [bufferedPercent, setBufferedPercent] = useState(0);
  const [volume, setVolume] = useState(1);
  const [isMuted, setIsMuted] = useState(false);
  const [playbackRate, setPlaybackRate] = useState(1);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [isTheaterMode, setIsTheaterMode] = useState(false);
  const [isControlsVisible, setIsControlsVisible] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [hasError, setHasError] = useState(false);

  // Menus
  const [isSpeedMenuOpen, setIsSpeedMenuOpen] = useState(false);
  const [isAudioMenuOpen, setIsAudioMenuOpen] = useState(false);

  // Hover Tooltip on Timeline
  const [hoverTime, setHoverTime] = useState<number | null>(null);
  const [hoverPosition, setHoverPosition] = useState<number>(0);

  // Double-tap Feedback for Mobile
  const [doubleTapFeedback, setDoubleTapFeedback] = useState<{
    type: "rewind" | "forward" | null;
  }>({ type: null });
  const lastTapRef = useRef<{ time: number; x: number }>({ time: 0, x: 0 });

  // Auto-Resume Toast State
  const [showResumeToast, setShowResumeToast] = useState(false);
  const [savedResumeTime, setSavedResumeTime] = useState(0);

  // Next Episode Countdown Modal
  const [showNextCountdown, setShowNextCountdown] = useState(false);
  const [countdownSeconds, setCountdownSeconds] = useState(5);

  // Selected Language / Translation
  const defaultLang = translations.length > 0 ? translations[0].language : "O'zbekcha";
  const [selectedLanguage, setSelectedLanguage] = useState<string>(defaultLang);

  // Active video source resolution
  const activeTranslation = translations.find((t) => t.language === selectedLanguage) || translations[0];

  const storageChannel =
    storageChannelUsername ||
    process.env.NEXT_PUBLIC_STORAGE_CHANNEL_USERNAME ||
    "mediaplusstorage";

  const tgEmbedUrl = activeTranslation?.storage_channel_message_id
    ? `https://t.me/${storageChannel}/${activeTranslation.storage_channel_message_id}?embed=1&autoplay=1`
    : null;

  // Decide player mode: default to 'telegram' when tgEmbedUrl is present (Option 2), otherwise 'cinema'
  const [playerMode, setPlayerMode] = useState<"cinema" | "telegram">(() => {
    if (directStreamUrl) return "cinema";
    if (activeTranslation?.storage_channel_message_id) return "telegram";
    return "cinema";
  });
  
  // Stream source URL logic
  const streamSrc =
    directStreamUrl ||
    (activeTranslation && activeTranslation.stream_url) ||
    `/api/v1/stream/${mediaType}/${mediaCode}?lang=${encodeURIComponent(selectedLanguage)}`;

  const localStorageKey = `kinochi_progress_${mediaType}_${mediaCode}`;

  // 1. Check saved watch progress on mount
  useEffect(() => {
    try {
      const saved = localStorage.getItem(localStorageKey);
      if (saved) {
        const time = parseFloat(saved);
        if (time > 15) {
          setSavedResumeTime(time);
          setShowResumeToast(true);
        }
      }
    } catch {
      // Ignore localStorage errors
    }
  }, [localStorageKey]);

  // 2. Hide controls automatically after idle
  const showControlsTemporarily = useCallback(() => {
    setIsControlsVisible(true);
    if (controlsTimeoutRef.current) {
      clearTimeout(controlsTimeoutRef.current);
    }
    controlsTimeoutRef.current = setTimeout(() => {
      if (videoRef.current && !videoRef.current.paused) {
        setIsControlsVisible(false);
        setIsSpeedMenuOpen(false);
        setIsAudioMenuOpen(false);
      }
    }, 3500);
  }, []);

  const handleMouseMove = () => {
    showControlsTemporarily();
  };

  // 3. Play / Pause Toggle
  const togglePlay = useCallback(() => {
    if (!videoRef.current) return;
    if (videoRef.current.paused) {
      videoRef.current
        .play()
        .then(() => setIsPlaying(true))
        .catch(() => setIsPlaying(false));
    } else {
      videoRef.current.pause();
      setIsPlaying(false);
    }
    showControlsTemporarily();
  }, [showControlsTemporarily]);

  // 4. Seek forward / backward
  const seekRelative = useCallback((seconds: number) => {
    if (!videoRef.current) return;
    const newTime = Math.max(0, Math.min(videoRef.current.duration || 0, videoRef.current.currentTime + seconds));
    videoRef.current.currentTime = newTime;
    setCurrentTime(newTime);
    showControlsTemporarily();
  }, [showControlsTemporarily]);

  // 5. Volume & Mute
  const handleVolumeChange = (newVolume: number) => {
    if (!videoRef.current) return;
    const clamped = Math.max(0, Math.min(1, newVolume));
    videoRef.current.volume = clamped;
    setVolume(clamped);
    setIsMuted(clamped === 0);
  };

  const toggleMute = useCallback(() => {
    if (!videoRef.current) return;
    if (isMuted) {
      videoRef.current.volume = volume > 0 ? volume : 0.5;
      setIsMuted(false);
    } else {
      videoRef.current.volume = 0;
      setIsMuted(true);
    }
  }, [isMuted, volume]);

  // 6. Playback Rate
  const handleRateChange = (rate: number) => {
    if (!videoRef.current) return;
    videoRef.current.playbackRate = rate;
    setPlaybackRate(rate);
    setIsSpeedMenuOpen(false);
    showControlsTemporarily();
  };

  // 7. Fullscreen Toggle
  const toggleFullscreen = async () => {
    if (!containerRef.current) return;
    try {
      if (!document.fullscreenElement) {
        await containerRef.current.requestFullscreen();
        setIsFullscreen(true);
      } else {
        await document.exitFullscreen();
        setIsFullscreen(false);
      }
    } catch (e) {
      console.warn("Fullscreen toggle error:", e);
    }
  };

  useEffect(() => {
    const onFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };
    document.addEventListener("fullscreenchange", onFullscreenChange);
    return () => document.removeEventListener("fullscreenchange", onFullscreenChange);
  }, []);

  // 8. Picture in Picture (PiP)
  const togglePiP = async () => {
    if (!videoRef.current) return;
    try {
      if (document.pictureInPictureElement) {
        await document.exitPictureInPicture();
      } else if (document.pictureInPictureEnabled) {
        await videoRef.current.requestPictureInPicture();
      }
    } catch (e) {
      console.warn("PiP error:", e);
    }
  };

  // 9. Keyboard Shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't intercept typing in input fields
      const target = e.target as HTMLElement;
      if (target && (target.tagName === "INPUT" || target.tagName === "TEXTAREA")) return;

      switch (e.key) {
        case " ":
        case "k":
        case "K":
          e.preventDefault();
          togglePlay();
          break;
        case "f":
        case "F":
          e.preventDefault();
          toggleFullscreen();
          break;
        case "m":
        case "M":
          e.preventDefault();
          toggleMute();
          break;
        case "ArrowLeft":
          e.preventDefault();
          seekRelative(-10);
          break;
        case "ArrowRight":
          e.preventDefault();
          seekRelative(10);
          break;
        case "ArrowUp":
          e.preventDefault();
          handleVolumeChange(volume + 0.1);
          break;
        case "ArrowDown":
          e.preventDefault();
          handleVolumeChange(volume - 0.1);
          break;
        case "t":
        case "T":
          setIsTheaterMode((prev) => !prev);
          break;
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [togglePlay, toggleMute, seekRelative, volume]);

  // 10. Video Event Listeners (Time, Buffer, Progress save, End)
  const handleTimeUpdate = () => {
    if (!videoRef.current) return;
    const now = videoRef.current.currentTime;
    setCurrentTime(now);

    // Save progress periodically
    if (now > 5) {
      try {
        localStorage.setItem(localStorageKey, now.toString());
      } catch {
        // ignore
      }
    }

    // Buffer percentage
    if (videoRef.current.buffered.length > 0) {
      const bufferedEnd = videoRef.current.buffered.end(videoRef.current.buffered.length - 1);
      const total = videoRef.current.duration || 1;
      setBufferedPercent(Math.min(100, (bufferedEnd / total) * 100));
    }
  };

  const handleLoadedMetadata = () => {
    if (!videoRef.current) return;
    setDuration(videoRef.current.duration || 0);
    setIsLoading(false);
  };

  const handleVideoEnded = () => {
    setIsPlaying(false);
    if (hasNextEpisode && onNextEpisode) {
      setShowNextCountdown(true);
      setCountdownSeconds(5);
    }
  };

  // Next episode countdown timer
  useEffect(() => {
    if (!showNextCountdown) return;
    const timer = setInterval(() => {
      setCountdownSeconds((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          setShowNextCountdown(false);
          if (onNextEpisode) onNextEpisode();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(timer);
  }, [showNextCountdown, onNextEpisode]);

  // 11. Timeline Seeking Interaction
  const handleTimelineClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!progressBarRef.current || !videoRef.current) return;
    const rect = progressBarRef.current.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const ratio = Math.max(0, Math.min(1, clickX / rect.width));
    const targetTime = ratio * (videoRef.current.duration || 0);
    videoRef.current.currentTime = targetTime;
    setCurrentTime(targetTime);
  };

  const handleTimelineMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!progressBarRef.current || !videoRef.current) return;
    const rect = progressBarRef.current.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const ratio = Math.max(0, Math.min(1, clickX / rect.width));
    setHoverPosition(clickX);
    setHoverTime(ratio * (videoRef.current.duration || 0));
  };

  const handleTimelineMouseLeave = () => {
    setHoverTime(null);
  };

  // 12. Mobile Double-tap gesture (left = -10s, right = +10s)
  const handleTouchStart = (e: React.TouchEvent<HTMLDivElement>) => {
    const touch = e.touches[0];
    const now = Date.now();
    const timeDiff = now - lastTapRef.current.time;
    const containerWidth = containerRef.current?.clientWidth || window.innerWidth;
    const touchX = touch.clientX;

    if (timeDiff < 300) {
      // Double-tap detected
      if (touchX < containerWidth * 0.4) {
        seekRelative(-10);
        setDoubleTapFeedback({ type: "rewind" });
      } else if (touchX > containerWidth * 0.6) {
        seekRelative(10);
        setDoubleTapFeedback({ type: "forward" });
      } else {
        togglePlay();
      }
      setTimeout(() => setDoubleTapFeedback({ type: null }), 600);
    } else {
      showControlsTemporarily();
    }

    lastTapRef.current = { time: now, x: touchX };
  };

  // Resume handlers
  const handleResumeConfirm = () => {
    if (videoRef.current) {
      videoRef.current.currentTime = savedResumeTime;
      videoRef.current.play().then(() => setIsPlaying(true)).catch(() => {});
    }
    setShowResumeToast(false);
  };

  const handleResumeDismiss = () => {
    setShowResumeToast(false);
  };

  // Audio / Translation switch
  const handleLanguageSelect = (lang: string) => {
    if (lang === selectedLanguage) {
      setIsAudioMenuOpen(false);
      return;
    }
    const currentPos = videoRef.current ? videoRef.current.currentTime : 0;
    setSelectedLanguage(lang);
    setIsAudioMenuOpen(false);
    setTimeout(() => {
      if (videoRef.current) {
        videoRef.current.currentTime = currentPos;
        videoRef.current.play().then(() => setIsPlaying(true)).catch(() => {});
      }
    }, 150);
  };

  return (
    <div
      ref={containerRef}
      onMouseMove={handleMouseMove}
      onTouchStart={handleTouchStart}
      className={`relative select-none overflow-hidden bg-black font-body-md transition-all duration-300 ${
        isTheaterMode
          ? "w-full aspect-video md:aspect-[21/9] max-h-[85vh] rounded-none shadow-2xl"
          : "w-full aspect-video rounded-2xl border border-white/10 shadow-2xl shadow-black/80"
      }`}
    >
      {/* If in Telegram Embed Mode */}
      {playerMode === "telegram" && tgEmbedUrl ? (
        <div className="w-full h-full relative bg-black flex flex-col">
          <iframe
            src={tgEmbedUrl}
            className="w-full h-full bg-black border-0 rounded-2xl flex-1"
            allow="autoplay; fullscreen"
            allowFullScreen
          />
          {/* Top Switcher Bar */}
          <div className="absolute top-2 right-2 z-30 flex items-center gap-2 bg-black/80 backdrop-blur-md px-3 py-1.5 rounded-xl border border-white/10 text-xs">
            <span className="text-[11px] text-primary font-bold flex items-center gap-1.5">
              <svg className="w-3.5 h-3.5 text-[#229ED9]" fill="currentColor" viewBox="0 0 24 24">
                <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.896-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/>
              </svg>
              <span>Telegram Video</span>
            </span>
            <button
              onClick={() => {
                setPlayerMode("cinema");
                setHasError(false);
              }}
              className="text-[11px] text-text-secondary hover:text-white transition-colors ml-1 underline cursor-pointer"
            >
              Kinoteatr
            </button>
          </div>
        </div>
      ) : (
        <>
          {/* HTML5 Video Element */}
          <video
            ref={videoRef}
            src={streamSrc}
            poster={posterUrl}
            preload="metadata"
            playsInline
            onTimeUpdate={handleTimeUpdate}
            onLoadedMetadata={handleLoadedMetadata}
            onWaiting={() => setIsLoading(true)}
            onPlaying={() => {
              setIsLoading(false);
              setIsPlaying(true);
            }}
            onEnded={handleVideoEnded}
            onError={() => {
              setIsLoading(false);
              setHasError(true);
            }}
            onClick={togglePlay}
            className="w-full h-full object-contain cursor-pointer bg-black"
          />

          {/* Double-tap Visual Feedback Animation (Mobile) */}
          {doubleTapFeedback.type && (
            <div
              className={`absolute top-0 bottom-0 ${
                doubleTapFeedback.type === "rewind" ? "left-0" : "right-0"
              } w-1/3 flex items-center justify-center bg-white/10 backdrop-blur-xs pointer-events-none z-30 animate-pulse`}
            >
              <div className="flex flex-col items-center gap-1 text-white">
                <span className="material-symbols-outlined text-4xl">
                  {doubleTapFeedback.type === "rewind" ? "fast_rewind" : "fast_forward"}
                </span>
                <span className="text-xs font-bold font-mono">
                  {doubleTapFeedback.type === "rewind" ? "-10s" : "+10s"}
                </span>
              </div>
            </div>
          )}

          {/* Loading Spinner */}
          {isLoading && (
            <div className="absolute inset-0 flex items-center justify-center bg-black/40 backdrop-blur-xs pointer-events-none z-20">
              <div className="w-14 h-14 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
            </div>
          )}

          {/* Error / Fallback Card (If stream not directly available in browser) */}
          {hasError && (
            <div className="absolute inset-0 flex flex-col items-center justify-center bg-surface-container-low/95 p-6 text-center z-25">
              <span className="material-symbols-outlined text-5xl text-primary mb-3">play_circle</span>
              <h4 className="text-lg font-bold text-white mb-2">Telegram Pleyerida Ko'rish</h4>
              <p className="text-text-secondary text-sm max-w-md mb-5 leading-relaxed">
                Ushbu film rasmiy Telegram omborimizda (@mediaplusstorage) to'liq sifatda saqlanmoqda. 
                Uni to'g'ridan-to'g'ri Telegram pleyerida ochish uchun pastdagi tugmani bosing:
              </p>
              <div className="flex flex-wrap gap-3 justify-center">
                {tgEmbedUrl && (
                  <button
                    onClick={() => {
                      setHasError(false);
                      setPlayerMode("telegram");
                    }}
                    className="flex items-center gap-2 bg-primary hover:bg-inverse-primary text-white px-5 py-3 rounded-xl font-bold text-xs uppercase tracking-wider transition-all shadow-lg hover:scale-105 active:scale-95 cursor-pointer"
                  >
                    <span className="material-symbols-outlined text-base">play_arrow</span>
                    <span>Telegram Pleyerini Yoqish</span>
                  </button>
                )}
                {telegramDeepLink && (
                  <a
                    href={telegramDeepLink}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 bg-white/10 hover:bg-white/20 text-white px-5 py-3 rounded-xl font-bold text-xs uppercase tracking-wider transition-all shadow-md"
                  >
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.896-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/>
                    </svg>
                    <span>Telegram Botda Ochish</span>
                  </a>
                )}
                <button
                  onClick={() => {
                    setHasError(false);
                    setIsLoading(true);
                    if (videoRef.current) videoRef.current.load();
                  }}
                  className="flex items-center gap-1.5 bg-white/10 hover:bg-white/20 text-white px-4 py-3 rounded-xl font-bold text-xs uppercase tracking-wider transition-all cursor-pointer"
                >
                  <span className="material-symbols-outlined text-sm">refresh</span>
                  <span>Qayta urinish</span>
                </button>
              </div>
            </div>
          )}

      {/* Auto-Resume Notification Toast */}
      {showResumeToast && !isPlaying && (
        <div className="absolute top-4 left-4 right-4 md:left-auto md:right-4 z-40 bg-black/85 backdrop-blur-md border border-white/15 p-3 sm:p-4 rounded-xl shadow-2xl flex items-center justify-between gap-3 text-xs sm:text-sm animate-fade-in-up">
          <div className="flex items-center gap-2.5 text-white/90">
            <span className="material-symbols-outlined text-rating-gold text-lg">history</span>
            <span>
              Siz ushbu videoni <strong className="text-white font-mono">{formatTime(savedResumeTime)}</strong> da to'xtatgansiz.
            </span>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <button
              onClick={handleResumeConfirm}
              className="bg-primary hover:bg-inverse-primary text-white font-bold px-3 py-1.5 rounded-lg text-xs uppercase tracking-wider transition-all"
            >
              Davom ettirish
            </button>
            <button
              onClick={handleResumeDismiss}
              className="text-text-secondary hover:text-white p-1"
              title="Yopish"
            >
              <span className="material-symbols-outlined text-base">close</span>
            </button>
          </div>
        </div>
      )}

      {/* Next Episode Countdown Overlay Modal */}
      {showNextCountdown && (
        <div className="absolute inset-0 bg-black/80 backdrop-blur-md z-40 flex flex-col items-center justify-center p-6 text-center animate-fade-in-up">
          <p className="text-text-secondary font-label-caps text-xs uppercase tracking-widest mb-2">
            Qism tugadi
          </p>
          <h3 className="text-xl sm:text-2xl font-bold text-white mb-4">
            Keyingi qism boshlanmoqda... ({countdownSeconds})
          </h3>
          <div className="w-48 h-1.5 bg-white/10 rounded-full overflow-hidden mb-6">
            <div
              className="h-full bg-primary transition-all duration-1000 ease-linear"
              style={{ width: `${(countdownSeconds / 5) * 100}%` }}
            ></div>
          </div>
          <div className="flex gap-3">
            <button
              onClick={() => {
                setShowNextCountdown(false);
                if (onNextEpisode) onNextEpisode();
              }}
              className="bg-primary hover:bg-inverse-primary text-white font-bold px-6 py-2.5 rounded-xl text-xs uppercase tracking-widest shadow-lg transition-transform hover:scale-105 active:scale-95"
            >
              Hozir o'tish
            </button>
            <button
              onClick={() => setShowNextCountdown(false)}
              className="bg-white/10 hover:bg-white/20 text-white font-bold px-4 py-2.5 rounded-xl text-xs uppercase tracking-widest transition-all"
            >
              Bekor qilish
            </button>
          </div>
        </div>
      )}

      {/* Top Gradient & Title Info Overlay */}
      <div
        className={`absolute top-0 inset-x-0 p-4 bg-gradient-to-b from-black/80 via-black/40 to-transparent transition-opacity duration-300 pointer-events-none z-20 flex items-center justify-between ${
          isControlsVisible ? "opacity-100" : "opacity-0"
        }`}
      >
        <div className="flex items-center gap-3">
          <span className="w-2 h-2 rounded-full bg-primary animate-pulse"></span>
          <h3 className="text-white font-bold text-sm sm:text-base drop-shadow-md truncate max-w-[280px] sm:max-w-md">
            {seriesTitle ? `${seriesTitle} • ${seasonNumber}-Fasl ${episodeNumber}-Qism` : title}
          </h3>
          <span className="text-[10px] bg-primary/20 border border-primary/40 text-red-200 px-2 py-0.5 rounded font-black tracking-wider uppercase">
            {selectedLanguage}
          </span>
        </div>

        {/* Theater mode indicator */}
        <div className="hidden sm:flex items-center gap-2 text-xs text-text-secondary">
          <span className="material-symbols-outlined text-sm">hd</span>
          <span>1080p • 100% Reklamasiz</span>
        </div>
      </div>

      {/* Center Big Play Button (when paused) */}
      {!isPlaying && !isLoading && !hasError && (
        <button
          onClick={togglePlay}
          className="absolute inset-0 m-auto w-16 h-16 sm:w-20 sm:h-20 rounded-full bg-primary/90 hover:bg-primary text-white flex items-center justify-center shadow-2xl shadow-primary/50 transition-all duration-300 hover:scale-110 active:scale-95 z-20 group"
          aria-label="Play"
        >
          <span className="material-symbols-outlined text-4xl sm:text-5xl ml-1 group-hover:scale-105 transition-transform">
            play_arrow
          </span>
        </button>
      )}

      {/* Bottom Controls Overlay */}
      <div
        className={`absolute bottom-0 inset-x-0 bg-gradient-to-t from-black/95 via-black/70 to-transparent pt-12 pb-3 px-3 sm:px-5 transition-opacity duration-300 z-20 flex flex-col gap-2 ${
          isControlsVisible ? "opacity-100 pointer-events-auto" : "opacity-0 pointer-events-none"
        }`}
      >
        {/* Interactive Progress Bar */}
        <div
          ref={progressBarRef}
          onClick={handleTimelineClick}
          onMouseMove={handleTimelineMouseMove}
          onMouseLeave={handleTimelineMouseLeave}
          className="relative w-full h-1.5 sm:h-2 bg-white/20 hover:h-3 rounded-full cursor-pointer transition-all group"
        >
          {/* Buffer Progress */}
          <div
            className="absolute top-0 left-0 h-full bg-white/30 rounded-full"
            style={{ width: `${bufferedPercent}%` }}
          ></div>

          {/* Played Progress */}
          <div
            className="absolute top-0 left-0 h-full bg-primary rounded-full relative"
            style={{ width: `${duration > 0 ? (currentTime / duration) * 100 : 0}%` }}
          >
            {/* Scrubber Knob */}
            <div className="absolute right-0 top-1/2 -translate-y-1/2 translate-x-1/2 w-3.5 h-3.5 sm:w-4 sm:h-4 rounded-full bg-white shadow-lg ring-2 ring-primary scale-0 group-hover:scale-100 transition-transform"></div>
          </div>

          {/* Hover Time Tooltip */}
          {hoverTime !== null && (
            <div
              className="absolute -top-7 -translate-x-1/2 bg-black/90 border border-white/20 text-white font-mono text-[11px] px-1.5 py-0.5 rounded shadow pointer-events-none"
              style={{ left: `${hoverPosition}px` }}
            >
              {formatTime(hoverTime)}
            </div>
          )}
        </div>

        {/* Buttons Row */}
        <div className="flex items-center justify-between text-white mt-1">
          {/* Left Controls (Play, Rewind, Forward, Volume, Time) */}
          <div className="flex items-center gap-1.5 sm:gap-3">
            <button
              onClick={togglePlay}
              className="p-1.5 hover:text-primary transition-colors focus:outline-none"
              title={isPlaying ? "To'xtatish (Space)" : "Ijro etish (Space)"}
            >
              <span className="material-symbols-outlined text-2xl sm:text-3xl">
                {isPlaying ? "pause" : "play_arrow"}
              </span>
            </button>

            {/* Rewind 10s */}
            <button
              onClick={() => seekRelative(-10)}
              className="p-1.5 hover:text-primary transition-colors hidden sm:block focus:outline-none"
              title="10 soniya orqaga (←)"
            >
              <span className="material-symbols-outlined text-xl sm:text-2xl">replay_10</span>
            </button>

            {/* Forward 10s */}
            <button
              onClick={() => seekRelative(10)}
              className="p-1.5 hover:text-primary transition-colors hidden sm:block focus:outline-none"
              title="10 soniya oldinga (→)"
            >
              <span className="material-symbols-outlined text-xl sm:text-2xl">forward_10</span>
            </button>

            {/* Next Episode Button (Series only) */}
            {hasNextEpisode && onNextEpisode && (
              <button
                onClick={onNextEpisode}
                className="p-1.5 hover:text-primary transition-colors focus:outline-none"
                title="Keyingi qism"
              >
                <span className="material-symbols-outlined text-xl sm:text-2xl">skip_next</span>
              </button>
            )}

            {/* Volume Control */}
            <div className="flex items-center gap-1 group/vol ml-1">
              <button
                onClick={toggleMute}
                className="p-1 hover:text-primary transition-colors focus:outline-none"
                title={isMuted ? "Ovozni yoqish (M)" : "Ovozni o'chirish (M)"}
              >
                <span className="material-symbols-outlined text-xl sm:text-2xl">
                  {isMuted || volume === 0 ? "volume_off" : volume < 0.5 ? "volume_down" : "volume_up"}
                </span>
              </button>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={isMuted ? 0 : volume}
                onChange={(e) => handleVolumeChange(parseFloat(e.target.value))}
                className="w-14 sm:w-20 h-1 accent-primary bg-white/20 rounded-lg cursor-pointer opacity-80 group-hover/vol:opacity-100 transition-opacity"
              />
            </div>

            {/* Time Display */}
            <div className="font-mono text-[11px] sm:text-xs text-text-secondary ml-1 sm:ml-2">
              <span className="text-white font-medium">{formatTime(currentTime)}</span> / {formatTime(duration)}
            </div>
          </div>

          {/* Right Controls (Audio Selector, Speed, Theater, PiP, Fullscreen) */}
          <div className="flex items-center gap-1 sm:gap-2 relative">
            {/* Audio / Translation Selector Dropdown */}
            {translations.length > 0 && (
              <div className="relative">
                <button
                  onClick={() => {
                    setIsAudioMenuOpen((prev) => !prev);
                    setIsSpeedMenuOpen(false);
                  }}
                  className={`flex items-center gap-1 px-2 py-1 rounded-lg text-xs font-bold tracking-wide uppercase transition-all ${
                    isAudioMenuOpen
                      ? "bg-primary text-white"
                      : "bg-white/10 hover:bg-white/20 text-white/90"
                  }`}
                  title="Ovoz va Tarjima tanlash"
                >
                  <span className="material-symbols-outlined text-sm">record_voice_over</span>
                  <span className="hidden md:inline">{selectedLanguage}</span>
                  <span className="material-symbols-outlined text-xs">expand_more</span>
                </button>

                {isAudioMenuOpen && (
                  <div className="absolute bottom-10 right-0 w-44 bg-surface-container-high/95 backdrop-blur-md border border-white/15 rounded-xl shadow-2xl p-1.5 flex flex-col gap-1 z-50">
                    <div className="text-[10px] uppercase font-bold text-text-secondary px-2 py-1 border-b border-white/10">
                      Ovoz tanlovi
                    </div>
                    {translations.map((tr) => (
                      <button
                        key={tr.id || tr.language}
                        onClick={() => handleLanguageSelect(tr.language)}
                        className={`flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs font-medium text-left transition-colors ${
                          selectedLanguage === tr.language
                            ? "bg-primary text-white font-bold"
                            : "hover:bg-white/10 text-white/90"
                        }`}
                      >
                        <span>{tr.language}</span>
                        {selectedLanguage === tr.language && (
                          <span className="material-symbols-outlined text-sm">check</span>
                        )}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Speed Selector Dropdown */}
            <div className="relative">
              <button
                onClick={() => {
                  setIsSpeedMenuOpen((prev) => !prev);
                  setIsAudioMenuOpen(false);
                }}
                className={`px-2 py-1 rounded-lg text-xs font-bold transition-all ${
                  isSpeedMenuOpen
                    ? "bg-primary text-white"
                    : "bg-white/10 hover:bg-white/20 text-white/90"
                }`}
                title="Ijro tezligi"
              >
                {playbackRate}x
              </button>

              {isSpeedMenuOpen && (
                <div className="absolute bottom-10 right-0 w-24 bg-surface-container-high/95 backdrop-blur-md border border-white/15 rounded-xl shadow-2xl p-1.5 flex flex-col gap-0.5 z-50">
                  <div className="text-[10px] uppercase font-bold text-text-secondary px-2 py-1 border-b border-white/10 text-center">
                    Tezlik
                  </div>
                  {SPEED_OPTIONS.map((rate) => (
                    <button
                      key={rate}
                      onClick={() => handleRateChange(rate)}
                      className={`px-2 py-1 rounded-md text-xs font-mono text-center transition-colors ${
                        playbackRate === rate
                          ? "bg-primary text-white font-bold"
                          : "hover:bg-white/10 text-white/90"
                      }`}
                    >
                      {rate}x
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Theater Mode Toggle */}
            <button
              onClick={() => setIsTheaterMode((prev) => !prev)}
              className="p-1.5 hover:text-primary transition-colors hidden md:block focus:outline-none"
              title={isTheaterMode ? "Standart o'lcham (T)" : "Teatr rejimi (T)"}
            >
              <span className="material-symbols-outlined text-xl sm:text-2xl">
                {isTheaterMode ? "aspect_ratio" : "crop_landscape"}
              </span>
            </button>

            {/* Picture in Picture */}
            <button
              onClick={togglePiP}
              className="p-1.5 hover:text-primary transition-colors hidden sm:block focus:outline-none"
              title="Kichik oyna (PiP)"
            >
              <span className="material-symbols-outlined text-xl sm:text-2xl">picture_in_picture_alt</span>
            </button>

            {/* Fullscreen */}
            <button
              onClick={toggleFullscreen}
              className="p-1.5 hover:text-primary transition-colors focus:outline-none"
              title={isFullscreen ? "To'liq ekrandan chiqish (F)" : "To'liq ekran (F)"}
            >
              <span className="material-symbols-outlined text-2xl sm:text-3xl">
                {isFullscreen ? "fullscreen_exit" : "fullscreen"}
              </span>
            </button>
          </div>
        </div>
      </div>
        </>
      )}
    </div>
  );
}
