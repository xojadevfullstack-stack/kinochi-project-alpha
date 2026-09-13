"use client";

import { useState } from "react";

interface TrailerModalProps {
  trailerUrl: string;
  posterUrl?: string;
  title?: string;
}

export default function TrailerModal({ trailerUrl, posterUrl, title }: TrailerModalProps) {
  const [isOpen, setIsOpen] = useState(false);

  // Helper function to extract YouTube video ID
  const getYoutubeId = (url: string) => {
    const regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|&v=)([^#&?]*).*/;
    const match = url.match(regExp);
    return match && match[2].length === 11 ? match[2] : null;
  };

  const isYoutube = trailerUrl.includes("youtube.com") || trailerUrl.includes("youtu.be");
  const youtubeId = isYoutube ? getYoutubeId(trailerUrl) : null;
  
  const isDirectMp4 = trailerUrl.endsWith(".mp4");
  const isTelegram = trailerUrl.includes("t.me/") && !trailerUrl.includes("/c/");

  const renderPlayer = () => {
    if (youtubeId) {
      return (
        <iframe
          className="w-full h-full rounded-xl"
          src={`https://www.youtube.com/embed/${youtubeId}?autoplay=1`}
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          allowFullScreen
        ></iframe>
      );
    }
    
    if (isDirectMp4) {
      return (
        <video controls autoPlay className="w-full h-full rounded-xl bg-black">
          <source src={trailerUrl} type="video/mp4" />
          Sizning brauzeringiz video teglarni qo'llab-quvvatlamaydi.
        </video>
      );
    }

    if (isTelegram) {
      const tgUrl = trailerUrl.split("?")[0] + "?embed=1&autoplay=1";
      return (
        <iframe
          className="w-full h-full rounded-xl bg-black"
          src={tgUrl}
          allow="autoplay; fullscreen"
          allowFullScreen
        ></iframe>
      );
    }

    return (
      <div className="flex flex-col items-center justify-center h-full text-center p-6">
        <span className="material-symbols-outlined text-5xl mb-4 text-text-secondary">link</span>
        <p className="text-text-primary mb-4">Bu treylerni to'g'ridan-to'g'ri pleyerda ochib bo'lmadi.</p>
        <a 
          href={trailerUrl} 
          target="_blank" 
          rel="noopener noreferrer" 
          className="px-6 py-3 bg-primary-container hover:bg-inverse-primary text-white rounded-xl font-label-caps text-xs sm:text-sm uppercase tracking-widest font-bold shadow-lg shadow-primary-container/25 transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5 active:scale-95 cursor-pointer"
        >
          Havolaga o'tish
        </a>
      </div>
    );
  };

  return (
    <>
      <div 
        onClick={() => setIsOpen(true)}
        className="aspect-video w-full max-w-5xl mx-auto rounded-xl overflow-hidden relative group cursor-pointer border border-white/10 bg-surface-container-lowest"
      >
        <div className="absolute inset-0 bg-cover bg-center opacity-60 group-hover:opacity-40 transition-opacity duration-500" 
             style={{ backgroundImage: `url('${posterUrl || ""}')` }}></div>
        <div className="absolute inset-0 flex items-center justify-center bg-black/20 group-hover:bg-black/40 transition-colors duration-500">
          <div className="w-20 h-20 sm:w-24 sm:h-24 rounded-full bg-white/10 backdrop-blur-md border border-white/20 flex items-center justify-center text-text-primary group-hover:bg-primary-container group-hover:border-primary-container group-hover:text-white group-hover:shadow-xl group-hover:shadow-primary-container/30 group-hover:scale-105 transition-all duration-300 ease-out">
            <span className="material-symbols-outlined text-[40px] sm:text-[48px] ml-1.5" style={{ fontVariationSettings: "'FILL' 1" }}>play_arrow</span>
          </div>
        </div>
      </div>

      {isOpen && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/90 backdrop-blur-sm">
          <div className="relative w-full max-w-4xl aspect-video bg-surface-container-lowest rounded-xl border border-white/10 shadow-2xl animate-fade-in">
            {/* Close button */}
            <button
              onClick={() => setIsOpen(false)}
              className="absolute -top-12 right-0 md:-right-12 text-white hover:text-primary-container transition-colors w-10 h-10 flex items-center justify-center bg-white/5 hover:bg-white/10 rounded-full"
            >
              <span className="material-symbols-outlined">close</span>
            </button>
            
            {/* Player Container */}
            <div className="w-full h-full rounded-xl overflow-hidden shadow-[0_0_50px_rgba(0,0,0,0.5)]">
              {renderPlayer()}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
