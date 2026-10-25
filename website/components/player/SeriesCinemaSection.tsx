"use client";

import { useState, useMemo } from "react";
import CinemaPlayer from "./CinemaPlayer";

interface Episode {
  id: number;
  episode_number: number;
  title?: string;
  duration?: number;
  code: string;
  translations?: any[];
}

interface Season {
  id: number;
  season_number: number;
  title?: string;
  description?: string;
  episode_count?: number;
  posterUrl?: string;
  poster_url?: string;
  episodes: Episode[];
}

interface SeriesCinemaSectionProps {
  series: {
    id: number;
    title: string;
    poster_url?: string;
    seasons: Season[];
  };
  botUsername?: string;
}

export default function SeriesCinemaSection({
  series,
  botUsername = "kinochi_uz_bot",
}: SeriesCinemaSectionProps) {
  // Sort seasons
  const sortedSeasons = useMemo(() => {
    return [...(series.seasons || [])].sort((a, b) => a.season_number - b.season_number);
  }, [series.seasons]);

  // Initial active season
  const [selectedSeasonNumber, setSelectedSeasonNumber] = useState<number>(() => {
    if (sortedSeasons.length > 0) return sortedSeasons[0].season_number;
    return 1;
  });

  const activeSeason = useMemo(() => {
    return sortedSeasons.find((s) => s.season_number === selectedSeasonNumber) || sortedSeasons[0];
  }, [sortedSeasons, selectedSeasonNumber]);

  // Sorted episodes for active season
  const activeEpisodes = useMemo(() => {
    if (!activeSeason || !activeSeason.episodes) return [];
    return [...activeSeason.episodes].sort((a, b) => a.episode_number - b.episode_number);
  }, [activeSeason]);

  // Active episode state
  const [activeEpisodeId, setActiveEpisodeId] = useState<number | null>(() => {
    if (activeEpisodes.length > 0) return activeEpisodes[0].id;
    return null;
  });

  const activeEpisode = useMemo(() => {
    if (!activeEpisodes.length) return null;
    return activeEpisodes.find((ep) => ep.id === activeEpisodeId) || activeEpisodes[0];
  }, [activeEpisodes, activeEpisodeId]);

  // Handle switching to next episode
  const handleNextEpisode = () => {
    if (!activeEpisode || !activeEpisodes.length) return;
    const currentIndex = activeEpisodes.findIndex((ep) => ep.id === activeEpisode.id);
    if (currentIndex < activeEpisodes.length - 1) {
      // Next episode in current season
      setActiveEpisodeId(activeEpisodes[currentIndex + 1].id);
    } else {
      // Check if there is a next season
      const currentSeasonIndex = sortedSeasons.findIndex((s) => s.season_number === selectedSeasonNumber);
      if (currentSeasonIndex < sortedSeasons.length - 1) {
        const nextSeason = sortedSeasons[currentSeasonIndex + 1];
        setSelectedSeasonNumber(nextSeason.season_number);
        const sortedNextEps = [...(nextSeason.episodes || [])].sort((a, b) => a.episode_number - b.episode_number);
        if (sortedNextEps.length > 0) {
          setActiveEpisodeId(sortedNextEps[0].id);
        }
      }
    }
  };

  const hasNextEpisode = useMemo(() => {
    if (!activeEpisode || !activeEpisodes.length) return false;
    const currentIndex = activeEpisodes.findIndex((ep) => ep.id === activeEpisode.id);
    if (currentIndex < activeEpisodes.length - 1) return true;
    const currentSeasonIndex = sortedSeasons.findIndex((s) => s.season_number === selectedSeasonNumber);
    return currentSeasonIndex < sortedSeasons.length - 1;
  }, [activeEpisode, activeEpisodes, sortedSeasons, selectedSeasonNumber]);

  if (!sortedSeasons.length) {
    return null;
  }

  const telegramEpisodeLink = activeEpisode
    ? `https://t.me/${botUsername}?start=${activeEpisode.code}`
    : `https://t.me/${botUsername}?start=s_${series.id}`;

  return (
    <section id="series-cinema-player" className="w-full flex flex-col gap-6">
      {/* Cinema Player */}
      <div className="w-full">
        {activeEpisode ? (
          <CinemaPlayer
            key={`ep_${activeEpisode.id}`}
            title={`${series.title} • ${activeSeason?.season_number}-Fasl ${activeEpisode.episode_number}-Qism`}
            mediaCode={activeEpisode.code}
            mediaType="episode"
            posterUrl={activeSeason?.poster_url || activeSeason?.posterUrl || series.poster_url}
            translations={activeEpisode.translations || []}
            telegramDeepLink={telegramEpisodeLink}
            onNextEpisode={handleNextEpisode}
            hasNextEpisode={hasNextEpisode}
            episodeNumber={activeEpisode.episode_number}
            seasonNumber={activeSeason?.season_number}
            seriesTitle={series.title}
          />
        ) : (
          <div className="aspect-video w-full rounded-2xl bg-surface-container-low border border-white/10 flex flex-col items-center justify-center text-text-secondary p-8 text-center">
            <span className="material-symbols-outlined text-5xl mb-3 opacity-40">play_disabled</span>
            <p className="text-sm">Ushbu faslga qismlar hali biriktirilmagan.</p>
          </div>
        )}
      </div>

      {/* Season Selector Tabs */}
      {sortedSeasons.length > 1 && (
        <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-none">
          {sortedSeasons.map((season) => {
            const isActive = season.season_number === selectedSeasonNumber;
            return (
              <button
                key={season.id}
                onClick={() => {
                  setSelectedSeasonNumber(season.season_number);
                  const seasonEps = [...(season.episodes || [])].sort((a, b) => a.episode_number - b.episode_number);
                  if (seasonEps.length > 0) {
                    setActiveEpisodeId(seasonEps[0].id);
                  }
                }}
                className={`px-4 sm:px-5 py-2.5 rounded-xl font-bold text-xs uppercase tracking-wider transition-all shrink-0 cursor-pointer ${
                  isActive
                    ? "bg-primary text-white shadow-lg shadow-primary/30"
                    : "bg-white/5 hover:bg-white/10 text-text-secondary hover:text-white border border-white/5"
                }`}
              >
                {season.title || `${season.season_number}-Mavsum`}
              </button>
            );
          })}
        </div>
      )}

      {/* Episodes Navigation Carousel / Grid */}
      <div className="bg-surface-container-high/60 backdrop-blur-md border border-white/10 rounded-2xl p-4 sm:p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <span className="w-1.5 h-5 bg-primary rounded-full block"></span>
            <h4 className="font-bold text-sm sm:text-base text-white">
              {activeSeason?.title || `${activeSeason?.season_number}-Mavsum`} Qismlari
            </h4>
          </div>
          <span className="text-xs text-text-secondary font-mono">
            Jami: {activeEpisodes.length} ta qism
          </span>
        </div>

        {activeEpisodes.length === 0 ? (
          <p className="text-text-secondary text-xs italic py-4">Bu mavsumda qismlar yo'q.</p>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-8 gap-2.5 max-h-[300px] overflow-y-auto pr-1">
            {activeEpisodes.map((ep) => {
              const isCurrent = activeEpisode?.id === ep.id;
              return (
                <button
                  key={ep.id}
                  onClick={() => {
                    setActiveEpisodeId(ep.id);
                    // Scroll player smoothly into view if on mobile
                    const el = document.getElementById("series-cinema-player");
                    if (el && window.innerWidth < 768) {
                      el.scrollIntoView({ behavior: "smooth", block: "start" });
                    }
                  }}
                  className={`flex flex-col items-center justify-center p-3 rounded-xl border transition-all duration-200 cursor-pointer group ${
                    isCurrent
                      ? "bg-primary/20 border-primary text-white shadow-md shadow-primary/20 ring-1 ring-primary"
                      : "bg-white/5 hover:bg-white/10 border-white/5 hover:border-white/20 text-text-secondary hover:text-white"
                  }`}
                >
                  <div className="flex items-center gap-1 mb-1">
                    {isCurrent ? (
                      <span className="material-symbols-outlined text-base text-primary animate-pulse">
                        volume_up
                      </span>
                    ) : (
                      <span className="material-symbols-outlined text-xs opacity-50 group-hover:opacity-100">
                        play_arrow
                      </span>
                    )}
                    <span className="text-base font-bold font-mono text-white">
                      {ep.episode_number}
                    </span>
                  </div>
                  <span className="text-[10px] uppercase tracking-wider text-text-secondary truncate max-w-full">
                    {ep.duration ? `${ep.duration}m` : "Qism"}
                  </span>
                </button>
              );
            })}
          </div>
        )}
      </div>
    </section>
  );
}
