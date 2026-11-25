import CastCrewSection from "@/components/media/CastCrewSection";
import SeasonEpisodesSection from "@/components/media/SeasonEpisodesSection";
import { fetchApi, getPublicConfig } from "@/lib/api";
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
import { BreadcrumbTitle } from "@/components/BreadcrumbContext";
import SourceBadge from "@/components/SourceBadge";
import MediaViewTracker from "@/components/media/MediaViewTracker";
import OnboardingSpotlight, { TourStep } from "@/components/OnboardingSpotlight";

const SERIES_TOUR_STEPS: TourStep[] = [
  {
    badge: "Telegram Bot",
    title: "Telegram botda tomosha qiling",
    description:
      "Tugmani bossangiz, ushbu serial rasmiy Telegram botimizda HD/4K sifatda va reklamasiz ochiladi.",
    selectors: ['a[href*="t.me/"]'],
  },
  {
    badge: "Fasllar va Qismlar",
    title: "To'g'ridan-to'g'ri kerakli qismga o'ting",
    description:
      "Fasl va qism raqamini tanlang — har bir tugma botda aynan o'sha qismni darhol ochib beradi.",
    selectors: ['[data-tour="series-episodes"]'],
  },
  {
    badge: "Obuna",
    title: "Yangi qismlardan birinchi bo'lib xabar oling",
    description:
      "Serialga obuna bo'lib qo'ying — yangi qism yuklanishi bilan Telegram orqali xabarnoma keladi.",
    selectors: ['button[title*="Obuna"], button[aria-label*="Obuna"]'],
  },
];

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
      title: `${series.title} - MediaPlus`,
      description: series.description || `${series.title} serialini bepul tomosha qiling.`,
      openGraph: {
        title: `${series.title} - MediaPlus`,
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
      title: "Serial topilmadi - MediaPlus"
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

  const { bot_username: botUsername, stream_enabled: streamEnabled } = await getPublicConfig();
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
      <BreadcrumbTitle path={`/series/${params.id}`} title={series.title} />
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
          <div className="max-w-container-max mx-auto px-gutter w-full flex flex-col gap-3 sm:gap-5">
          <div className="w-full flex flex-col md:flex-row items-center md:items-center gap-3.5 sm:gap-5 md:gap-8 lg:gap-10">
            {/* Left: Poster */}
            <div className="w-28 sm:w-44 md:w-[270px] lg:w-[330px] shrink-0 mt-1 sm:mt-2 md:mt-0 mx-auto md:mx-0 relative group perspective-1000">
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
          <div className="flex-1 flex flex-col w-full min-w-0">
            <h1 className="font-display-hero text-xl sm:text-3xl md:text-4xl lg:text-[2.75rem] text-white mb-1.5 sm:mb-3 drop-shadow-lg text-center md:text-left tracking-tighter leading-tight line-clamp-2">
              {series.title}
            </h1>
            
            {/* Badges Row */}
            <div className="flex flex-wrap items-center justify-center md:justify-start gap-1.5 sm:gap-2.5 mb-2.5 sm:mb-stack-md">
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
            <p className="font-body-lg text-xs sm:text-sm md:text-base text-slate-200 mb-3 sm:mb-5 max-w-3xl text-center md:text-left leading-relaxed line-clamp-2 sm:line-clamp-3 md:line-clamp-4">
              {series.description || "Ushbu serial haqida batafsil ma'lumot kiritilmagan. Lekin bu sizni ajoyib premyerani tomosha qilishdan to'xtatib qolmasligi kerak!"}
            </p>
            
            {/* Action Buttons (Mobile 2-col grid matching prototype, Desktop flex row) */}
            <div className="grid grid-cols-2 sm:flex sm:flex-wrap gap-2 sm:gap-3 items-stretch sm:items-center justify-center md:justify-start w-full">
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
                className="col-span-2 sm:col-span-1 sm:w-auto flex items-center justify-center gap-2 bg-[#E50914] text-white px-5 sm:px-7 py-3 sm:py-3.5 rounded-xl font-label-caps text-xs sm:text-sm uppercase tracking-wider hover:bg-[#B80710] hover:scale-[1.02] hover:-translate-y-0.5 active:scale-95 shadow-lg shadow-primary/30 transition-all duration-200 group font-bold cursor-pointer"
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
                className="flex items-center justify-center gap-2 bg-white/10 hover:bg-white/15 text-white border border-white/15 hover:border-white/30 px-3 sm:px-6 py-3 sm:py-3.5 rounded-xl font-label-caps text-xs sm:text-sm uppercase tracking-wider font-bold shadow-md shadow-black/20 transition-all duration-200 hover:scale-[1.02] active:scale-95 cursor-pointer"
              />
              <SubscribeButton
                targetType="series"
                targetId={series.id}
                title={series.title}
                className="col-span-1 sm:w-auto px-3 sm:px-6 py-3 sm:py-3.5 text-xs sm:text-sm"
              />
              {(() => {
                const hasTrailer = Boolean(
                  series.trailer_url &&
                    series.trailer_url !== "" &&
                    series.trailer_url !== "null" &&
                    series.trailer_url !== "undefined"
                );
                const secondaryCount = (hasTrailer ? 1 : 0) + 3; // Share + Subscribe + Report
                const isEvenGrid = secondaryCount % 2 === 0;
                return (
                  <ReportIssueButton
                    mediaType="series"
                    seriesId={series.id}
                    mediaTitle={series.title}
                    className={`${isEvenGrid ? "col-span-1" : "col-span-2"} sm:col-span-1 sm:w-auto`}
                  />
                );
              })()}
            </div>
          </div>
        </div>
      </div>
        </HeroTrailerBackdrop>
    </section>





      {/* Seasons & Episodes Section */}
      <SeasonEpisodesSection seasons={series.seasons} series={series} botUsername={botUsername} streamEnabled={streamEnabled} />

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
      <OnboardingSpotlight
        storageKey="mediaplus_tour_series_v1"
        steps={SERIES_TOUR_STEPS}
      />
      <MediaViewTracker mediaType="series" seriesId={series.id} />
    </>
  );
}
