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
      title: `${movie.title} - Kinochi Premium`,
      description: movie.description || `${movie.title} filmini bepul tomosha qiling.`,
      openGraph: {
        title: `${movie.title} - Kinochi Premium`,
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
      <section className="relative w-full min-h-[1024px] flex items-center pt-[100px] pb-stack-lg overflow-hidden">
        {/* Background Blur & Gradient Overlays */}
        <div className="absolute inset-0 bg-cover bg-center opacity-30 blur-2xl mask-gradient-bottom" 
             style={{ backgroundImage: `url('${movie.poster_url || ""}')` }}></div>
        <div className="absolute inset-0 bg-gradient-to-t from-background-obsidian via-background-obsidian/60 to-transparent"></div>
        <div className="absolute inset-0 bg-gradient-to-r from-background-obsidian via-transparent to-transparent hidden md:block"></div>
        
        {/* Content Container */}
        <div className="relative z-10 max-w-container-max mx-auto px-gutter w-full flex flex-col md:flex-row items-center md:items-end gap-margin-desktop">
          {/* Left: Poster */}
          <div className="w-full md:w-1/3 lg:w-[400px] shrink-0 mt-stack-lg md:mt-0 relative group perspective-1000">
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
            <h1 className="font-display-hero-mobile md:font-display-hero text-[40px] md:text-display-hero text-text-primary mb-stack-sm drop-shadow-lg text-center md:text-left tracking-tighter">
              {movie.title}
            </h1>
            
            {/* Badges Row */}
            <div className="flex flex-wrap items-center justify-center md:justify-start gap-3 mb-stack-md font-label-caps text-label-caps tracking-widest uppercase text-xs">
              <div className="flex items-center gap-1 text-rating-gold bg-black/50 px-3 py-1.5 rounded backdrop-blur-sm border border-white/5">
                <span className="material-symbols-outlined text-[16px]" style={{ fontVariationSettings: "'FILL' 1" }}>star</span>
                <span>{movie.imdb_rating || movie.tmdb_rating || "N/A"}</span>
              </div>
              <span className="text-text-secondary bg-white/5 px-3 py-1.5 rounded border border-white/5">{movie.release_year || "2024"}</span>
              <span className="text-text-primary font-bold bg-white/10 px-3 py-1.5 rounded border border-white/20">{movie.original_title ? "Original: " + movie.original_title : "4K HDR"}</span>
              <span className="text-text-primary bg-white/5 px-3 py-1.5 rounded border border-white/5 hover:bg-white/10 transition-colors cursor-pointer">{movie.genres?.split(',')[0] || "KINO"}</span>
            </div>
            
            {/* Description */}
            <p className="font-body-lg text-body-lg text-text-secondary mb-stack-lg max-w-3xl text-center md:text-left leading-relaxed">
              {movie.description || "Ushbu kino haqida batafsil ma'lumot kiritilmagan. Lekin bu sizni ajoyib premyerani tomosha qilishdan to'xtatib qolmasligi kerak!"}
            </p>
            
            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 items-center justify-center md:justify-start">
              <a 
                href={telegramDeepLink}
                target="_blank"
                rel="noopener noreferrer"
                className="w-full sm:w-auto flex items-center justify-center gap-2 bg-primary-container text-white px-8 py-4 rounded-full font-label-caps text-xs uppercase tracking-widest hover:bg-inverse-primary hover:scale-105 hover:shadow-[0_0_30px_rgba(229,9,20,0.4)] transition-all duration-300 ease-out group font-bold"
              >
                <span className="material-symbols-outlined text-[20px] group-hover:scale-110 transition-transform" style={{ fontVariationSettings: "'FILL' 1" }}>play_arrow</span>
                TELEGRAMDA KO'RISH
              </a>
              <button className="w-full sm:w-auto flex items-center justify-center gap-2 bg-white/5 backdrop-blur-md border border-white/10 text-text-primary px-8 py-4 rounded-full font-label-caps text-xs uppercase tracking-widest hover:bg-white/10 hover:border-white/30 hover:scale-105 transition-all duration-300 ease-out group font-bold">
                <span className="material-symbols-outlined text-[20px] group-hover:rotate-90 transition-transform">share</span>
                ULASHISH
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Trailer Section */}
      <section className="max-w-container-max mx-auto px-gutter py-stack-lg border-t border-white/5">
        <h2 className="font-headline-md text-headline-md text-text-primary mb-stack-md">Treyler</h2>
        <div className="aspect-video w-full max-w-5xl mx-auto rounded-xl overflow-hidden relative group cursor-pointer border border-white/10 bg-surface-container-lowest">
          <div className="absolute inset-0 bg-cover bg-center opacity-60 group-hover:opacity-40 transition-opacity duration-500" 
               style={{ backgroundImage: `url('${movie.poster_url || ""}')` }}></div>
          <div className="absolute inset-0 flex items-center justify-center bg-black/20 group-hover:bg-black/40 transition-colors duration-500">
            <div className="w-24 h-24 rounded-full bg-white/10 backdrop-blur-md border border-white/20 flex items-center justify-center text-text-primary group-hover:bg-primary-container group-hover:border-primary-container group-hover:text-white group-hover:shadow-[0_0_40px_rgba(229,9,20,0.6)] group-hover:scale-110 transition-all duration-500 ease-out">
              <span className="material-symbols-outlined text-[48px] ml-2" style={{ fontVariationSettings: "'FILL' 1" }}>play_arrow</span>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}
