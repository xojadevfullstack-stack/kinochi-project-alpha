"use client";

import { useState } from "react";
import TelegramWatchButton from "@/components/TelegramWatchButton";

export type Episode = {
  id: number;
  season_id: number;
  episode_number: number;
  title: string | null;
  duration: number | null;
  code: string;
};

export type Season = {
  id: number;
  series_id: number;
  season_number: number;
  title: string | null;
  description: string | null;
  poster_url: string | null;
  episode_count: number | null;
  episodes: Episode[];
};

interface SeasonEpisodesSectionProps {
  seasons: Season[];
  series: any;
  botUsername?: string;
}

export default function SeasonEpisodesSection({
  seasons,
  series,
  botUsername,
}: SeasonEpisodesSectionProps) {
  const targetBotUser = botUsername || process.env.NEXT_PUBLIC_BOT_USERNAME || "kinochi_mvp_bot";
  const sortedSeasons = [...(seasons || [])].sort(
    (a, b) => a.season_number - b.season_number
  );

  const [activeSeasonId, setActiveSeasonId] = useState<number>(
    sortedSeasons[0]?.id || 0
  );

  const activeSeason =
    sortedSeasons.find((s) => s.id === activeSeasonId) || sortedSeasons[0];

  if (!sortedSeasons || sortedSeasons.length === 0) {
    return (
      <section className="max-w-container-max mx-auto px-gutter py-6 sm:py-8 border-t border-white/5">
        <h2 className="text-xl sm:text-2xl font-bold text-text-primary mb-4 flex items-center gap-2.5">
          <span className="w-1.5 h-6 bg-primary rounded-full block"></span>
          Fasllar va Qismlar
        </h2>
        <div className="bg-white/[0.03] border border-white/5 rounded-2xl p-8 sm:p-12 text-center text-text-secondary flex flex-col items-center justify-center">
          <span className="material-symbols-outlined text-3xl mb-2 opacity-40">hourglass_empty</span>
          <p className="text-sm sm:text-base">Hozircha qismlar yuklanmagan.</p>
        </div>
      </section>
    );
  }

  const episodes = [...(activeSeason?.episodes || [])].sort(
    (a, b) => a.episode_number - b.episode_number
  );

  return (
    <section className="max-w-container-max mx-auto px-gutter py-6 sm:py-8 border-t border-white/5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4 sm:mb-6">
        <h2 className="text-xl sm:text-2xl font-bold text-text-primary flex items-center gap-2.5">
          <span className="w-1.5 h-6 bg-primary rounded-full block"></span>
          Fasllar va Qismlar
        </h2>

        {/* Season Selector Tabs */}
        {sortedSeasons.length > 1 && (
          <div className="flex items-center gap-1.5 overflow-x-auto hide-scrollbar pb-1">
            {sortedSeasons.map((season) => {
              const isActive = season.id === activeSeason?.id;
              return (
                <button
                  key={season.id}
                  onClick={() => setActiveSeasonId(season.id)}
                  className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all duration-200 border cursor-pointer ${
                    isActive
                      ? "bg-primary text-white border-primary shadow-md shadow-primary/25"
                      : "bg-white/5 hover:bg-white/10 text-text-secondary hover:text-white border-white/5"
                  }`}
                >
                  {season.season_number}-Mavsum
                </button>
              );
            })}
          </div>
        )}
      </div>

      {/* Active Season Info Bar */}
      <div className="flex items-center justify-between text-xs text-text-secondary mb-3 px-1">
        <span className="font-medium text-white/80">
          {activeSeason?.title || `${activeSeason?.season_number}-Mavsum`}
        </span>
        <span>
          Jami: <strong className="text-white font-mono">{episodes.length}</strong> ta qism
        </span>
      </div>

      {/* Episodes Grid: Compact, touch-friendly, ergonomic */}
      {episodes.length === 0 ? (
        <div className="bg-white/[0.03] border border-white/5 rounded-xl p-6 text-center text-text-secondary text-xs sm:text-sm">
          Bu faslga hozircha qismlar kiritilmagan.
        </div>
      ) : (
        <div className="grid grid-cols-2 xs:grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 gap-2 sm:gap-2.5">
          {episodes.map((episode) => {
            const episodeCode = episode.code || episode.display_code || String(episode.id);
            const episodeLink = `https://t.me/${targetBotUser}?start=ep_${episodeCode}`;
            return (
              <TelegramWatchButton
                key={episode.id}
                url={episodeLink}
                mediaTitle={`${series.title} (${episode.episode_number}-qism)`}
                mediaCode={episodeCode}
                mediaId={episode.id}
                seriesId={series.id}
                mediaType="episode"
                posterUrl={activeSeason?.poster_url || series.poster_url || ""}
                releaseYear={series.release_year}
                imdbRating={series.imdb_rating || series.tmdb_rating}
                genres={series.categories?.[0]?.name || "Serial"}
                className="group relative flex flex-col justify-between p-2.5 sm:p-3 rounded-xl bg-white/[0.04] hover:bg-white/[0.08] border border-white/5 hover:border-primary/50 hover:shadow-lg hover:shadow-primary/10 transition-all duration-200 cursor-pointer overflow-hidden text-left"
              >
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-base sm:text-lg font-bold text-white group-hover:text-primary transition-colors font-mono">
                    {episode.episode_number}
                  </span>
                  <span className="material-symbols-outlined text-white/30 group-hover:text-primary group-hover:scale-110 transition-all text-lg">
                    play_circle
                  </span>
                </div>
                <div className="flex items-center justify-between text-[11px] text-text-secondary w-full">
                  <span className="truncate group-hover:text-white transition-colors">
                    {episode.title && episode.title !== `${episode.episode_number}-qism`
                      ? episode.title
                      : `${episode.episode_number}-qism`}
                  </span>
                  {episode.duration && (
                    <span className="text-[10px] text-white/40 shrink-0 ml-1 font-mono">
                      {episode.duration}m
                    </span>
                  )}
                </div>
              </TelegramWatchButton>
            );
          })}
        </div>
      )}
    </section>
  );
}
