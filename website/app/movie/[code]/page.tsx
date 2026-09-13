import { fetchApi } from "@/lib/api";
import { notFound } from "next/navigation";
import Image from "next/image";
import { Metadata } from "next";
import ShareButton from "@/components/ShareButton";
import ReviewsSection from "@/components/reviews/ReviewsSection";
import KinochiRatingBadge from "@/components/reviews/KinochiRatingBadge";
import TrailerModal from "@/components/TrailerModal";

type Props = {
  params: { code: string };
};

export const revalidate = 0; 

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  try {
    const movie = await fetchApi(`/movies/code/${params.code}`);
    
    return {
      title: `${movie.title} - Kinochi`,
      description: movie.description || `${movie.title} filmini bepul tomosha qiling.`,
      openGraph: {
        title: `${movie.title} - Kinochi`,
        description: movie.description || `${movie.title} filmini bepul tomosha qiling.`,
        url: `https://kinochi-project-alpha.vercel.app/movie/${params.code}`,
        images: movie.poster_url ? [
          {
            url: movie.poster_url,
            width: 1200,
            height: 630,
            alt: movie.title,
          }
        ] : [],
      },
    };
  } catch (error) {
    return {
      title: "Kino topilmadi - Kinochi"
    };
  }
}

export default async function MovieDetailsPage({ params }: Props) {
  let movie;
  try {
    movie = await fetchApi(`/movies/code/${params.code}`);
  } catch (error) {
    notFound();
  }

  const botUsername = process.env.NEXT_PUBLIC_BOT_USERNAME || "kinochi_uz_bot";
  const telegramDeepLink = `https://t.me/${botUsername}?start=${movie.code}`;

  return (
    <>
      <section className="relative w-full min-h-[100svh] md:min-h-[800px] flex items-center pt-20 sm:pt-24 md:pt-32 pb-12 md:pb-16 overflow-hidden">
        {/* Background Blur & Gradient Overlays */}
        <div className="absolute inset-0 bg-background-obsidian">
           {movie.poster_url ? (
            <div className="absolute inset-0 bg-cover bg-center opacity-30 blur-xl" 
               style={{ backgroundImage: `url('${movie.poster_url}')` }}></div>
           ) : (
            <div className="absolute inset-0 bg-gradient-to-b from-surface-container to-background-obsidian"></div>
           )}
        </div>
        <div className="absolute inset-0 bg-gradient-to-t from-background-obsidian via-background-obsidian/[0.85] to-transparent"></div>
        <div className="absolute inset-0 bg-gradient-to-r from-background-obsidian via-background-obsidian/[0.55] to-transparent hidden md:block"></div>
        
        {/* Content Container */}
        <div className="relative z-10 max-w-container-max mx-auto px-gutter w-full flex flex-col md:flex-row items-center md:items-end gap-5 md:gap-margin-desktop">
          {/* Left: Poster */}
          <div className="w-44 sm:w-52 md:w-1/3 lg:w-[380px] shrink-0 mt-2 sm:mt-4 md:mt-0 mx-auto md:mx-0 relative group perspective-1000">
            <div className="aspect-[2/3] rounded-xl overflow-hidden shadow-2xl shadow-primary-container/20 border border-white/10 transition-transform duration-500 ease-out group-hover:scale-[1.02] group-hover:shadow-primary-container/40 relative bg-surface-container-high">
              {movie.poster_url ? (
                <Image 
                  src={movie.poster_url}
                  alt={movie.title}
                  fill
                  priority
                  className="object-cover"
                />
              ) : (
                <div className="absolute inset-0 flex items-center justify-center text-gray-500">
                   <span className="material-symbols-outlined text-6xl opacity-30">movie</span>
                </div>
              )}
              <div className="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"></div>
            </div>
          </div>
          
          {/* Right: Movie Info */}
          <div className="flex-1 flex flex-col w-full md:pb-stack-lg">
            <h1 className="font-display-hero text-2xl sm:text-4xl md:text-display-hero text-text-primary mb-2 sm:mb-stack-sm drop-shadow-lg text-center md:text-left tracking-tighter leading-tight">
              {movie.title}
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
                  {(movie.imdb_rating || movie.tmdb_rating) ? Number(movie.imdb_rating || movie.tmdb_rating).toFixed(1) : "N/A"}
                </span>
                <span className="text-[10px] text-text-secondary font-normal uppercase tracking-wider">IMDb</span>
              </div>

              <KinochiRatingBadge 
                initialRating={movie.kinochi_rating} 
                initialVotesCount={movie.kinochi_votes_count} 
              />

              <div className="inline-flex items-center gap-1.5 h-7 sm:h-8 px-2.5 sm:px-3 rounded-lg bg-white/[0.06] backdrop-blur-md border border-white/10 text-white/90 text-xs font-medium shadow-sm">
                <span className="material-symbols-outlined text-[13px] text-white/40">calendar_today</span>
                <span>{movie.release_year || "2024"}</span>
              </div>

              <div className="inline-flex items-center gap-1.5 h-7 sm:h-8 px-2.5 sm:px-3 rounded-lg bg-white/[0.08] backdrop-blur-md border border-white/15 text-white text-[11px] font-bold tracking-wider uppercase shadow-sm">
                <span className="material-symbols-outlined text-[14px] text-white/60">movie</span>
                <span>KINO</span>
              </div>

              {(movie.genres?.split(',')[0]?.trim() || movie.categories?.[0]?.name) && (
                <div className="inline-flex items-center gap-1.5 h-7 sm:h-8 px-2.5 sm:px-3 rounded-lg bg-white/[0.06] backdrop-blur-md border border-white/10 text-text-secondary text-xs font-medium shadow-sm">
                  <span className="material-symbols-outlined text-[13px] text-white/40">category</span>
                  <span>{movie.genres?.split(',')[0]?.trim() || movie.categories?.[0]?.name}</span>
                </div>
              )}
            </div>
            
            {/* Description */}
            <p className="font-body-lg text-sm sm:text-base md:text-body-lg text-text-secondary mb-4 sm:mb-stack-lg max-w-3xl text-center md:text-left leading-relaxed line-clamp-3 md:line-clamp-none">
              {movie.description || "Ushbu kino haqida batafsil ma'lumot kiritilmagan. Lekin bu sizni ajoyib premyerani tomosha qilishdan to'xtatib qolmasligi kerak!"}
            </p>
            
            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 items-center justify-center md:justify-start w-full sm:w-auto">
              <a 
                href={telegramDeepLink}
                target="_blank"
                rel="noopener noreferrer"
                className="w-full sm:w-auto flex items-center justify-center gap-2.5 bg-primary-container text-white px-6 sm:px-8 py-3.5 sm:py-4 rounded-xl font-label-caps text-xs sm:text-sm uppercase tracking-widest hover:bg-inverse-primary hover:scale-[1.02] hover:-translate-y-0.5 active:scale-95 shadow-lg shadow-primary-container/25 hover:shadow-primary-container/35 transition-all duration-200 group font-bold cursor-pointer"
              >
                <svg className="w-5 h-5 group-hover:scale-110 transition-transform" fill="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.896-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/>
                </svg>
                <span>TELEGRAM ORQALI TOMOSHA QILISH</span>
              </a>
              <ShareButton 
                title={movie.title} 
                text={`${movie.title} filmini bepul tomosha qiling.`}
                url={`/movie/${movie.code}`}
                code={movie.code}
                botUsername={botUsername}
                className="w-full sm:w-auto flex items-center justify-center gap-2.5 bg-white/10 hover:bg-white/15 text-white border border-white/15 hover:border-white/30 px-6 sm:px-8 py-3.5 sm:py-4 rounded-xl font-label-caps text-xs sm:text-sm uppercase tracking-widest font-bold shadow-md shadow-black/20 transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5 active:scale-95 cursor-pointer"
              />
            </div>
          </div>
        </div>
      </section>

      {/* Trailer Section */}
      {movie.trailer_url && movie.trailer_url !== "" && movie.trailer_url !== "null" && movie.trailer_url !== "undefined" && (
        <section className="max-w-container-max mx-auto px-gutter py-stack-lg border-t border-white/5">
          <h2 className="font-headline-md text-headline-md text-text-primary mb-stack-md">Treyler</h2>
          <TrailerModal trailerUrl={movie.trailer_url} posterUrl={movie.poster_url || ""} />
        </section>
      )}

      {/* Reviews & Comments Section */}
      <ReviewsSection
        movieId={movie.id}
        movieCode={movie.code}
        imdbRating={movie.imdb_rating || movie.tmdb_rating}
        initialKinochiRating={movie.kinochi_rating}
        initialVotesCount={movie.kinochi_votes_count || 0}
      />
    </>
  );
}
