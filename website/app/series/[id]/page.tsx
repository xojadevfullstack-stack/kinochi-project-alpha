import { fetchApi } from "@/lib/api";
import { notFound } from "next/navigation";
import Image from "next/image";
import { Metadata } from "next";
import ShareButton from "@/components/ShareButton";

type Props = {
  params: { id: string };
};

export const revalidate = 60;

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
    const series = await fetchApi(`/series/${params.id}`);
    
    return {
      title: `${series.title} - Kinochi`,
      description: series.description || `${series.title} serialini bepul tomosha qiling.`,
      openGraph: {
        title: `${series.title} - Kinochi`,
        description: series.description || `${series.title} serialini bepul tomosha qiling.`,
        url: `https://kinochi.uz/series/${params.id}`,
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
    notFound();
  }

  const botUsername = process.env.NEXT_PUBLIC_BOT_USERNAME || "kinochi_uz_bot";
  // Fallback direct link to bot
  const telegramDeepLink = `https://t.me/${botUsername}?start=s_${series.id}`;

  return (
    <>
      <section className="relative w-full min-h-[100svh] md:min-h-[800px] flex items-center pt-32 pb-16 overflow-hidden">
        {/* Background Blur & Gradient Overlays */}
        <div className="absolute inset-0 bg-background-obsidian">
           {series.poster_url ? (
            <div className="absolute inset-0 bg-cover bg-center opacity-30 blur-xl" 
               style={{ backgroundImage: `url('${series.poster_url}')` }}></div>
           ) : (
            <div className="absolute inset-0 bg-gradient-to-b from-surface-container to-background-obsidian"></div>
           )}
        </div>
        <div className="absolute inset-0 bg-gradient-to-t from-background-obsidian via-background-obsidian/[0.85] to-transparent"></div>
        <div className="absolute inset-0 bg-gradient-to-r from-background-obsidian via-background-obsidian/[0.55] to-transparent hidden md:block"></div>
        
        {/* Content Container */}
        <div className="relative z-10 max-w-container-max mx-auto px-gutter w-full flex flex-col md:flex-row items-center md:items-end gap-margin-desktop">
          {/* Left: Poster */}
          <div className="w-full md:w-1/3 lg:w-[400px] shrink-0 mt-stack-lg md:mt-0 relative group perspective-1000">
            <div className="aspect-[2/3] rounded-xl overflow-hidden shadow-2xl shadow-primary-container/20 border border-white/10 transition-transform duration-500 ease-out group-hover:scale-[1.02] group-hover:shadow-primary-container/40 relative bg-surface-container-high">
              {series.poster_url ? (
                <Image 
                  src={series.poster_url}
                  alt={series.title}
                  fill
                  priority
                  className="object-cover"
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
            <h1 className="font-display-hero text-4xl sm:text-[48px] md:text-display-hero text-text-primary mb-stack-sm drop-shadow-lg text-center md:text-left tracking-tighter leading-tight">
              {series.title}
            </h1>
            
            {/* Badges Row */}
            <div className="flex flex-wrap items-center justify-center md:justify-start gap-3 mb-stack-md font-label-caps text-label-caps tracking-widest uppercase text-xs">
              <div className="flex items-center gap-1 text-rating-gold bg-black/50 px-3 py-1.5 rounded backdrop-blur-sm border border-white/5">
                <span className="material-symbols-outlined text-[16px]" style={{ fontVariationSettings: "'FILL' 1" }}>star</span>
                <span>{series.imdb_rating || "N/A"}</span>
              </div>
              <span className="text-text-secondary bg-white/5 px-3 py-1.5 rounded border border-white/5">{series.release_year || "Yil no'malum"}</span>
              <span className="text-text-primary bg-white/10 px-3 py-1.5 rounded font-bold border border-white/10">SERIAL</span>
              <span className="text-white bg-primary-container px-3 py-1.5 rounded font-bold border border-primary-container">YANGI</span>
            </div>
            
            {/* Description */}
            <p className="font-body-lg text-body-lg text-text-secondary mb-stack-lg max-w-3xl text-center md:text-left leading-relaxed">
              {series.description || "Ushbu serial haqida batafsil ma'lumot kiritilmagan. Lekin bu sizni ajoyib premyerani tomosha qilishdan to'xtatib qolmasligi kerak!"}
            </p>
            
            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 items-center justify-center md:justify-start">
              <a 
                href={telegramDeepLink}
                target="_blank"
                rel="noopener noreferrer"
                className="w-full sm:w-auto flex items-center justify-center gap-2 bg-primary-container text-white px-8 py-4 rounded-full font-label-caps text-xs uppercase tracking-widest hover:bg-inverse-primary hover:scale-105 hover:shadow-[0_0_30px_rgba(229,9,20,0.4)] transition-all duration-300 ease-out group font-bold"
              >
                <svg className="w-5 h-5 group-hover:scale-110 transition-transform" fill="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.896-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/>
                </svg>
                TELEGRAM ORQALI TOMOSHA QILISH
              </a>
              <ShareButton 
                title={series.title} 
                text={`${series.title} serialini bepul tomosha qiling.`}
                url={`https://kinochi.uz/series/${series.id}`}
              />
            </div>
          </div>
        </div>
      </section>

      {/* Seasons & Episodes Section */}
      <section className="max-w-container-max mx-auto px-gutter py-stack-lg border-t border-white/5">
        <h2 className="font-headline-md text-headline-md text-text-primary mb-stack-md flex items-center gap-3">
          <span className="w-1.5 h-8 bg-primary-container rounded-full block"></span>
          Fasllar va Qismlar
        </h2>
        
        {!series.seasons || series.seasons.length === 0 ? (
          <div className="bg-white/5 border border-white/10 rounded-2xl p-12 text-center text-text-secondary flex flex-col items-center justify-center">
             <span className="material-symbols-outlined text-4xl mb-4 opacity-50">hourglass_empty</span>
             <p className="font-body-lg">Hozircha qismlar yuklanmagan.</p>
          </div>
        ) : (
          <div className="space-y-12">
            {series.seasons
              .sort((a: Season, b: Season) => a.season_number - b.season_number)
              .map((season: Season) => (
              <div key={season.id} className="bg-gradient-to-br from-white/5 to-transparent backdrop-blur-sm rounded-2xl overflow-hidden border border-white/5 shadow-2xl relative">
                <div className="flex flex-col md:flex-row gap-8 p-6 md:p-8">
                  {/* Season Poster */}
                  <div className="w-full md:w-56 aspect-[2/3] relative flex-shrink-0 bg-surface-container-low rounded-xl overflow-hidden shadow-xl border border-white/10 group cursor-pointer">
                    {season.poster_url ? (
                      <Image 
                        src={season.poster_url} 
                        alt={`${season.season_number}-fasl`}
                        fill
                        className="object-cover transition-transform duration-500 group-hover:scale-105"
                      />
                    ) : series.poster_url ? (
                      <Image 
                        src={series.poster_url} 
                        alt="Fasl"
                        fill
                        className="object-cover opacity-40 grayscale blur-[2px]"
                      />
                    ) : (
                      <div className="absolute inset-0 flex items-center justify-center text-text-secondary text-sm">
                        Rasm yo'q
                      </div>
                    )}
                    <div className="absolute top-4 left-4 bg-black/60 backdrop-blur-md px-3 py-1.5 rounded-lg border border-white/10 font-bold">
                       {season.season_number}-Fasl
                    </div>
                  </div>
                  
                  {/* Season Content & Episodes */}
                  <div className="flex-grow flex flex-col">
                    <div className="mb-6">
                      <h3 className="text-3xl font-display-hero text-text-primary mb-2">
                        {season.title || `${season.season_number}-Fasl`}
                      </h3>
                      {season.episode_count && (
                        <p className="text-text-secondary font-label-caps text-xs tracking-widest uppercase mb-4">
                          Mavsumda jami: <span className="text-white font-bold">{season.episode_count} ta qism</span>
                        </p>
                      )}
                      {season.description && (
                        <p className="text-on-secondary-container leading-relaxed text-sm md:text-base">
                          {season.description}
                        </p>
                      )}
                    </div>
                    
                    {/* Episodes Grid */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 mt-auto">
                      {!season.episodes || season.episodes.length === 0 ? (
                        <div className="col-span-full text-text-secondary text-sm py-4 italic">
                          Bu faslga qismlar qo'shilmagan.
                        </div>
                      ) : (
                        season.episodes
                          .sort((a, b) => a.episode_number - b.episode_number)
                          .map((episode) => {
                          const episodeLink = `https://t.me/${botUsername}?start=${episode.code}`;
                          return (
                            <a 
                              href={episodeLink}
                              target="_blank"
                              rel="noopener noreferrer"
                              key={episode.id} 
                              className="group bg-white/5 hover:bg-white/10 border border-white/5 hover:border-primary-container/50 rounded-xl p-4 transition-all duration-300 flex flex-col relative overflow-hidden"
                            >
                              <div className="absolute inset-0 bg-gradient-to-r from-primary-container/0 to-primary-container/10 opacity-0 group-hover:opacity-100 transition-opacity"></div>
                              <div className="flex justify-between items-start mb-2 relative z-10">
                                <span className="text-xl font-bold text-white group-hover:text-primary-container transition-colors">
                                  {episode.episode_number}
                                </span>
                                {episode.duration && (
                                  <span className="text-[10px] bg-black/40 px-2 py-1 rounded text-text-secondary font-mono">
                                    {episode.duration} min
                                  </span>
                                )}
                              </div>
                              <span className="text-sm text-text-secondary group-hover:text-white transition-colors truncate relative z-10">
                                {episode.title && episode.title !== `${episode.episode_number}-qism` 
                                  ? episode.title 
                                  : `${episode.episode_number}-qism`}
                              </span>
                            </a>
                          )
                        })
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Trailer Section */}
      <section className="max-w-container-max mx-auto px-gutter py-stack-lg border-t border-white/5 mb-stack-lg">
        <h2 className="font-headline-md text-headline-md text-text-primary mb-stack-md flex items-center gap-3">
          <span className="w-1.5 h-8 bg-primary-container rounded-full block"></span>
          Treyler
        </h2>
        <div className="aspect-video w-full max-w-5xl mx-auto rounded-xl overflow-hidden relative group cursor-pointer border border-white/10 bg-surface-container-lowest shadow-2xl">
          <div className="absolute inset-0 bg-cover bg-center opacity-60 group-hover:opacity-40 transition-opacity duration-500" 
               style={{ backgroundImage: `url('${series.poster_url || ""}')` }}></div>
          <div className="absolute inset-0 bg-gradient-to-t from-background-obsidian/80 to-transparent"></div>
          <div className="absolute inset-0 flex items-center justify-center bg-black/20 group-hover:bg-black/40 transition-colors duration-500">
            <div className="w-20 h-20 md:w-24 md:h-24 rounded-full bg-primary-container/90 backdrop-blur-md border border-white/20 flex items-center justify-center text-text-primary group-hover:bg-primary-container group-hover:border-primary-container group-hover:text-white group-hover:shadow-[0_0_40px_rgba(229,9,20,0.8)] group-hover:scale-110 transition-all duration-500 ease-out">
              <span className="material-symbols-outlined text-[40px] md:text-[48px] ml-2" style={{ fontVariationSettings: "'FILL' 1" }}>play_arrow</span>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}
