import CastCrewSection from "@/components/media/CastCrewSection";
import SeasonEpisodesSection from "@/components/media/SeasonEpisodesSection";
import { fetchApi } from "@/lib/api";
import { notFound } from "next/navigation";
import { Metadata } from "next";
import ShareButton from "@/components/ShareButton";
import ReviewsSection from "@/components/reviews/ReviewsSection";
import KinochiRatingBadge from "@/components/reviews/KinochiRatingBadge";
import TrailerModal from "@/components/TrailerModal";
import TelegramWatchButton from "@/components/TelegramWatchButton";
import AgeVerificationModal from "@/components/AgeVerificationModal";
import ReportIssueButton from "@/components/ReportIssueButton";
import SubscribeButton from "@/components/SubscribeButton";

import { isAdultContent } from "@/lib/adult";
import AdultPoster from "@/components/AdultPoster";
import HeroTrailerBackdrop from "@/components/media/HeroTrailerBackdrop";
import BackButton from "@/components/BackButton";
import SourceBadge from "@/components/SourceBadge";

type Props = {
  params: { id: string };
};

export const revalidate = 60; // 60s ISR kesh: Vercel CDN orqali Render trafigini tejaydi

type Episode = {
  id: number;
  season_id: number;
  episode_number: number;
  title: string | null;
  duration: number | null;
  code: string;
};

type Season = {
  id: number;
  series_id: number;
  season_number: number;
  title: string | null;
  description: string | null;
  poster_url: string | null;
  episode_count: number | null;
  episodes: Episode[];
};

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  try {
    let series;
    try {
      series = await fetchApi(`/series/${params.id}`);
    } catch {
      series = await fetchApi(`/series/code/${params.id}`);
    }
    
    return {
      title: `${series.title} - Kinochi`,
      description: series.description || `${series.title} serialini bepul tomosha qiling.`,
      openGraph: {
        title: `${series.title} - Kinochi`,
        description: series.description || `${series.title} serialini bepul tomosha qiling.`,
        url: `https://kinochi-project-alpha.vercel.app/series/${params.id}`,
        images: series.poster_url ? [
          {
            url: series.poster_url,
            width: 1200,
            height: 630,
            alt: series.title,
          }
        ] : [],
      },
    };
  } catch (error) {
    return {
      title: "Serial topilmadi - Kinochi"
    };
  }
}

export default async function SeriesDetailsPage({ params }: Props) {
  let series;
  try {
    series = await fetchApi(`/series/${params.id}`);
  } catch (error) {
    try {
      series = await fetchApi(`/series/code/${params.id}`);
    } catch {
      notFound();
    }
  }

  let creditsData: any = null;
  try {
    creditsData = await fetchApi(`/series/${series.id}/credits`);
  } catch {}

  const botUsername = process.env.NEXT_PUBLIC_BOT_USERNAME || "kinochi_mvp_bot";
  // Fallback direct link to bot
  const telegramDeepLink = `https://t.me/${botUsername}?start=s_${series.id}`;
  const is18Plus = isAdultContent(series);

  // Sifat matnli yorlig'i (Quality badge)
  const qualityList = (series.seasons || [])
    .flatMap((s: any) => s.episodes || [])
    .flatMap((e: any) => e.translations || [])
    .map((t: any) => (t.language || '').trim())
    .filter(Boolean);

  let qualityBadgeText = 'Full HD';
  const joinedQualities = qualityList.join(' ').toLowerCase();
  if (joinedQualities.includes('4k') || joinedQualities.includes('2160')) {
    qualityBadgeText = '4K Ultra HD';
  } else if (joinedQualities.includes('1080') || joinedQualities.includes('fhd')) {
    qualityBadgeText = '1080p FHD';
  } else if (joinedQualities.includes('720') || joinedQualities.includes('hd')) {
    qualityBadgeText = '720p HD';
  } else if (joinedQualities.includes('480')) {
    qualityBadgeText = '480p SD';
  }

  return (
    <>
      <AgeVerificationModal is18Plus={is18Plus} />
      <section className="relative w-full">
        {/* Background Ambient Trailer & Poster Overlay with Cinema Mode */}
        <HeroTrailerBackdrop
          posterUrl={series.poster_url}
          trailerUrl={series.trailer_url}
          title={series.title}
          is18Plus={is18Plus}
        >
          {/* Content Container */}
          <div className="max-w-container-max mx-auto px-gutter w-full flex flex-col gap-4 sm:gap-6">
          {/* Smart Back Navigation */}
          <div className="flex items-center">
            <BackButton fallbackUrl="/series" />
          </div>

          <div className="w-full flex flex-col md:flex-row items-center md:items-end gap-5 md:gap-margin-desktop">
            {/* Left: Poster */}
            <div className="w-44 sm:w-52 md:w-1/3 lg:w-[380px] shrink-0 mt-2 sm:mt-4 md:mt-0 mx-auto md:mx-0 relative group perspective-1000">
            <div className="aspect-[2/3] rounded-xl overflow-hidden shadow-2xl shadow-black/60 border border-white/10 transition-transform duration-500 ease-out group-hover:scale-[1.02] group-hover:shadow-black/80 relative bg-surface-container-high">
              {series.poster_url ? (
                <AdultPoster 
                  src={series.poster_url}
                  alt={series.title}
                  is18Plus={is18Plus}
                  isDetailPage={true}
                  fill
                  priority
                  imageClassName="object-cover"
                />
              ) : (
                <div className="absolute inset-0 flex items-center justify-center text-gray-500">
                   <span className="material-symbols-outlined text-6xl opacity-30">live_tv</span>
                </div>
              )}
              <div className="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"></div>
            </div>
          </div>
          
          {/* Right: Movie Info */}
          <div className="flex-1 flex flex-col w-full md:pb-stack-lg">
            <h1 className="font-display-hero text-2xl sm:text-4xl md:text-display-hero text-text-primary mb-2 sm:mb-stack-sm drop-shadow-lg text-center md:text-left tracking-tighter leading-tight">
              {series.title}
            </h1>
            
            {/* Badges Row */}
            <div className="flex flex-wrap items-center justify-center md:justify-start gap-2 sm:gap-2.5 mb-3 sm:mb-stack-md">
              <div 
                className="inline-flex items-center gap-1.5 h-7 sm:h-8 px-2.5 sm:px-3 rounded-lg bg-black/60 backdrop-blur-md border border-white/10 text-white shadow-sm font-medium text-xs" 
                title="Rasmiy IMDb reytingi"
              >
                <span className="material-symbols-outlined text-[15px] text-rating-gold" style={{ fontVariationSettings: "'FILL' 1" }}>
                  star
                </span>
                <span className="text-white font-bold tracking-tight">
                  {series.imdb_rating ? Number(series.imdb_rating).toFixed(1) : "N/A"}
                </span>
                <span className="text-[10px] text-text-secondary font-normal uppercase tracking-wider">IMDb</span>
              </div>

              <KinochiRatingBadge 
                initialRating={series.kinochi_rating} 
                initialVotesCount={series.kinochi_votes_count} 
              />

              <div className="inline-flex items-center gap-1.5 h-7 sm:h-8 px-2.5 sm:px-3 rounded-lg bg-white/[0.06] backdrop-blur-md border border-white/10 text-white/90 text-xs font-medium shadow-sm">
                <span className="material-symbols-outlined text-[13px] text-white/40">calendar_today</span>
                <span>{series.release_year || "Yil no'malum"}</span>
              </div>

              <div className="inline-flex items-center gap-1.5 h-7 sm:h-8 px-2.5 sm:px-3 rounded-lg bg-white/[0.08] backdrop-blur-md border border-white/15 text-white text-[11px] font-bold tracking-wider uppercase shadow-sm">
                <span className="material-symbols-outlined text-[14px] text-white/60">live_tv</span>
                <span>SERIAL</span>
              </div>

              {/* Quality Text Badge */}
              <div 
                className="inline-flex items-center gap-1.5 h-7 sm:h-8 px-2.5 sm:px-3 rounded-lg bg-emerald-500/15 backdrop-blur-md border border-emerald-400/30 text-emerald-300 text-xs font-bold tracking-wide shadow-sm"
                title="Mavjud tasvir sifati"
              >
                <span className="material-symbols-outlined text-[14px] text-emerald-400">hd</span>
                <span>{qualityBadgeText}</span>
              </div>

              {/* Source Branding Badge */}
              <SourceBadge 
                sourceType={series.source_type} 
                customSourceName={series.custom_source_name} 
                customSourceLogo={series.custom_source_logo} 
              />

              {is18Plus && (
                <div className="inline-flex items-center gap-1.5 h-7 sm:h-8 px-2.5 sm:px-3 rounded-lg bg-red-600/20 backdrop-blur-md border border-red-500/40 text-red-200 text-xs font-black tracking-wide shadow-sm shadow-red-950/40">
                  <span className="text-[13px]">🔞</span>
                  <span>18+</span>
                </div>
              )}

              {series.categories && series.categories.length > 0 ? (
                series.categories.map((cat: any) => (
                  <a
                    key={cat.id}
                    href={`/category/${cat.id}`}
                    className="inline-flex items-center gap-1.5 h-7 sm:h-8 px-2.5 sm:px-3 rounded-lg bg-white/[0.06] hover:bg-white/[0.12] backdrop-blur-md border border-white/10 text-text-secondary hover:text-white text-xs font-medium shadow-sm transition-all"
                  >
                    <span className="material-symbols-outlined text-[13px] text-white/40">category</span>
                    <span>{cat.name}</span>
                  </a>
                ))
              ) : null}
            </div>
            
            {/* Description */}
            <p className="font-body-lg text-sm sm:text-base md:text-body-lg text-text-secondary mb-4 sm:mb-stack-lg max-w-3xl text-center md:text-left leading-relaxed line-clamp-3 md:line-clamp-none">
              {series.description || "Ushbu serial haqida batafsil ma'lumot kiritilmagan. Lekin bu sizni ajoyib premyerani tomosha qilishdan to'xtatib qolmasligi kerak!"}
            </p>
            
            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row flex-wrap gap-3 sm:gap-4 items-center justify-center md:justify-start w-full sm:w-auto">
              <TelegramWatchButton 
                url={telegramDeepLink}
                mediaTitle={series.title}
                mediaId={series.id}
                seriesId={series.id}
                mediaType="series"
                posterUrl={series.poster_url || ""}
                releaseYear={series.release_year}
                imdbRating={series.imdb_rating || series.tmdb_rating}
                genres={series.categories?.[0]?.name || "Serial"}
                className="w-full sm:w-auto flex items-center justify-center gap-2.5 bg-primary-container text-white px-6 sm:px-8 py-3.5 sm:py-4 rounded-xl font-label-caps text-xs sm:text-sm uppercase tracking-widest hover:bg-inverse-primary hover:scale-[1.02] hover:-translate-y-0.5 active:scale-95 shadow-lg shadow-black/40 hover:shadow-black/60 transition-all duration-200 group font-bold cursor-pointer"
              >
                <svg className="w-5 h-5 group-hover:scale-110 transition-transform" fill="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.896-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/>
                </svg>
                <span>TELEGRAM ORQALI TOMOSHA QILISH</span>
              </TelegramWatchButton>
              {series.trailer_url && series.trailer_url !== "" && series.trailer_url !== "null" && series.trailer_url !== "undefined" && (
                <TrailerModal
                  trailerUrl={series.trailer_url}
                  posterUrl={series.poster_url || ""}
                  variant="button"
                />
              )}
              <ShareButton 
                title={series.title} 
                text={`${series.title} serialini bepul tomosha qiling.`}
                url={`/series/${series.id}`}
                code={`s_${series.id}`}
                botUsername={botUsername}
                className="w-full sm:w-auto flex items-center justify-center gap-2.5 bg-white/10 hover:bg-white/15 text-white border border-white/15 hover:border-white/30 px-6 sm:px-8 py-3.5 sm:py-4 rounded-xl font-label-caps text-xs sm:text-sm uppercase tracking-widest font-bold shadow-md shadow-black/20 transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5 active:scale-95 cursor-pointer"
              />
                            <SubscribeButton
                targetType="series"
                targetId={series.id}
                title={series.title}
                className="w-full sm:w-auto flex items-center justify-center gap-2.5 px-6 sm:px-8 py-3.5 sm:py-4 rounded-xl font-label-caps text-xs sm:text-sm uppercase tracking-widest font-bold shadow-md shadow-black/20 transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5 active:scale-95 cursor-pointer"
              />
              <ReportIssueButton
                mediaType="series"
                seriesId={series.id}
                mediaTitle={series.title}
                className="w-full sm:w-auto"
              />
            </div>
          </div>
        </div>
      </div>
        </HeroTrailerBackdrop>
    </section>





      {/* Seasons & Episodes Section */}
      <SeasonEpisodesSection seasons={series.seasons} series={series} botUsername={botUsername} />

      {/* Suratga olish guruhi (TMDb) */}
      <CastCrewSection
        mediaIdOrCode={series.id}
        mediaType="series"
        initialCredits={creditsData?.items}
        initialDetails={creditsData?.details}
      />

      {/* Reviews & Comments Section */}
      <ReviewsSection
        seriesId={series.id}
        imdbRating={series.imdb_rating}
        initialKinochiRating={series.kinochi_rating}
        initialVotesCount={series.kinochi_votes_count || 0}
      />
    </>
  );
}
