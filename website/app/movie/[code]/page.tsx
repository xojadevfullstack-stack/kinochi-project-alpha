import { fetchApi } from "@/lib/api";
import { notFound } from "next/navigation";
import Image from "next/image";
import { Metadata } from "next";

type Props = {
  params: { code: string };
};

export const revalidate = 60; 

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  try {
    const movie = await fetchApi(`/movies/code/${params.code}`);
    
    return {
      title: `${movie.title} - KINOCHI`,
      description: movie.description || `${movie.title} filmini bepul tomosha qiling.`,
      openGraph: {
        title: `${movie.title} - KINOCHI`,
        description: movie.description || `${movie.title} filmini bepul tomosha qiling.`,
        url: `https://kinochi.uz/movie/${params.code}`,
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
      title: "Kino topilmadi - KINOCHI"
    };
  }
}

// Helper to mock actor avatars since API just returns a string
const renderActors = (castString: string) => {
  if (!castString) return null;
  const actors = castString.split(',').map(a => a.trim()).slice(0, 6); // max 6 actors
  
  return (
    <div className="mt-8">
      <h3 className="text-xl font-bold mb-4 text-white flex items-center gap-2">
        <svg className="w-5 h-5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" /></svg>
        Aktyorlar
      </h3>
      <div className="flex flex-wrap gap-4 sm:gap-6">
        {actors.map((actor, idx) => (
          <div key={idx} className="flex flex-col items-center gap-2">
            <div className="w-14 h-14 sm:w-16 sm:h-16 rounded-full bg-surface border border-white/10 flex items-center justify-center overflow-hidden shadow-lg group">
              <svg className="w-6 h-6 sm:w-8 sm:h-8 text-gray-500 group-hover:scale-110 transition-transform" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" />
              </svg>
            </div>
            <span className="text-xs sm:text-sm font-medium text-gray-300 text-center w-16 sm:w-20 line-clamp-2 leading-tight">{actor}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

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
    <div className="min-h-screen bg-[#09090B] pb-20">
      
      {/* Hero Section */}
      <div className="relative w-full">
        {/* Dynamic Background */}
        <div className="absolute inset-0 h-[80vh] w-full overflow-hidden z-0">
          {movie.poster_url ? (
            <>
              <Image 
                src={movie.poster_url}
                alt="Background"
                fill
                priority
                className="object-cover object-top opacity-30 blur-[10px] scale-110"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-[#09090B] via-[#09090B]/80 to-transparent" />
              <div className="absolute inset-0 bg-gradient-to-r from-[#09090B] via-[#09090B]/60 to-transparent" />
            </>
          ) : (
            <div className="absolute inset-0 bg-gradient-to-b from-surface to-[#09090B]" />
          )}
        </div>

        {/* Content Container */}
        <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-32 lg:pt-40 pb-12 flex flex-col lg:flex-row gap-10 lg:gap-16">
          
          {/* Left: Poster */}
          <div className="w-full max-w-[280px] sm:max-w-[320px] mx-auto lg:mx-0 flex-shrink-0">
            <div className="aspect-[2/3] relative rounded-2xl overflow-hidden shadow-2xl shadow-black/50 ring-1 ring-white/10 group">
              {movie.poster_url ? (
                <Image 
                  src={movie.poster_url}
                  alt={movie.title}
                  fill
                  className="object-cover transition-transform duration-700 group-hover:scale-105"
                  priority
                />
              ) : (
                <div className="absolute inset-0 flex items-center justify-center bg-surface text-gray-500">
                  Poster yo'q
                </div>
              )}
              <div className="absolute inset-0 ring-1 ring-inset ring-white/10 rounded-2xl pointer-events-none"></div>
            </div>
          </div>

          {/* Right: Info */}
          <div className="flex-1 flex flex-col justify-center text-center lg:text-left">
            
            {/* Badges */}
            <div className="flex flex-wrap items-center justify-center lg:justify-start gap-3 mb-6">
              <span className="bg-star text-black text-xs sm:text-sm font-bold px-2.5 py-1 rounded-sm uppercase tracking-wider flex items-center gap-1">
                ★ IMDb {movie.imdb_rating || movie.tmdb_rating || "N/A"}
              </span>
              <span className="text-xs sm:text-sm font-bold text-white/90 bg-white/10 px-3 py-1 rounded-sm uppercase tracking-widest">
                {movie.release_year || "2024"}
              </span>
              {movie.runtime && (
                <span className="text-xs sm:text-sm font-bold text-white/90 bg-white/10 px-3 py-1 rounded-sm uppercase tracking-widest">
                  {movie.runtime} daqiqa
                </span>
              )}
            </div>
            
            {/* Title */}
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-display font-black tracking-tighter mb-2 lg:mb-4 text-white drop-shadow-lg leading-tight">
              {movie.title}
            </h1>
            {movie.original_title && (
              <h2 className="text-lg sm:text-xl text-gray-400 font-medium mb-6 italic">
                {movie.original_title}
              </h2>
            )}

            {/* Genres */}
            <div className="flex flex-wrap justify-center lg:justify-start gap-2 mb-8">
              {(movie.genres || "Kino").split(',').map((genre: string, i: number) => (
                <span key={i} className="px-3 py-1.5 rounded-full border border-white/20 text-xs font-semibold uppercase tracking-wider text-gray-300 backdrop-blur-md">
                  {genre.trim()}
                </span>
              ))}
            </div>

            {/* Description */}
            <p className="text-gray-300 text-base sm:text-lg leading-relaxed max-w-3xl mb-10 font-medium opacity-90 mx-auto lg:mx-0">
              {movie.description || "Ushbu kino uchun batafsil tavsif kiritilmagan. Ammo bu filmni telegram orqali tomosha qilishingiz mumkin."}
            </p>

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row items-center justify-center lg:justify-start gap-4">
              <a 
                href={telegramDeepLink}
                target="_blank"
                rel="noopener noreferrer"
                className="w-full sm:w-auto bg-primary hover:bg-red-700 text-white font-bold py-4 px-10 rounded-full transition-transform duration-300 flex items-center justify-center gap-3 shadow-[0_0_40px_rgba(229,9,20,0.4)] hover:shadow-[0_0_60px_rgba(229,9,20,0.6)] hover:-translate-y-1"
              >
                <svg className="w-6 h-6 fill-current" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
                Tomosha qilish
              </a>
              <button className="w-14 h-14 rounded-full bg-white/10 hover:bg-white/20 border border-white/10 backdrop-blur-md flex items-center justify-center transition-colors text-white hidden sm:flex">
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" /></svg>
              </button>
            </div>

            {/* Actors Grid */}
            {movie.cast && renderActors(movie.cast)}

          </div>
        </div>
      </div>

      {/* Trailer Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-12 relative z-20">
        <h2 className="text-2xl font-bold mb-6 text-white flex items-center gap-2">
          <svg className="w-6 h-6 text-primary" fill="currentColor" viewBox="0 0 24 24"><path d="M19.615 3.184c-3.604-.246-11.631-.245-15.23 0-3.897.266-4.356 2.62-4.385 8.816.029 6.185.484 8.549 4.385 8.816 3.6.245 11.626.246 15.23 0 3.897-.266 4.356-2.62 4.385-8.816-.029-6.185-.484-8.549-4.385-8.816zm-10.615 12.816v-8l8 3.993-8 4.007z"/></svg>
          Rasmiy Treyler
        </h2>
        <div className="aspect-video w-full rounded-2xl overflow-hidden bg-black ring-1 ring-white/10 shadow-2xl relative group cursor-pointer flex items-center justify-center mb-10">
          {/* Placeholder for YouTube Player (Since API might not have trailer URLs yet, showing a realistic mockup) */}
          {movie.poster_url ? (
            <Image 
              src={movie.poster_url}
              alt="Trailer Thumbnail"
              fill
              className="object-cover opacity-60 group-hover:opacity-40 transition-opacity"
            />
          ) : (
            <div className="absolute inset-0 bg-surface"></div>
          )}
          <div className="absolute inset-0 bg-black/30 group-hover:bg-black/10 transition-colors" />
          
          {/* Play Button Mockup */}
          <div className="relative w-20 h-20 sm:w-24 sm:h-24 rounded-full bg-primary/90 flex items-center justify-center shadow-[0_0_30px_rgba(229,9,20,0.5)] group-hover:scale-110 group-hover:bg-primary transition-all duration-300">
            <svg className="w-10 h-10 sm:w-12 sm:h-12 text-white ml-2" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
          </div>
        </div>
      </div>

    </div>
  );
}
