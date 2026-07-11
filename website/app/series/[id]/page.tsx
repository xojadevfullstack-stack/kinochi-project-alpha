import { fetchApi } from "@/lib/api";
import { notFound } from "next/navigation";
import Image from "next/image";
import { Metadata } from "next";

type Props = {
  params: { id: string };
};

export const revalidate = 60;

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

type Episode = {
  id: number;
  season_id: number;
  episode_number: number;
  title: string | null;
  code: string;
};

type Season = {
  id: number;
  series_id: number;
  season_number: number;
  title: string | null;
  description: string | null;
  episodes: Episode[];
};

export default async function SeriesDetailsPage({ params }: Props) {
  let series;
  try {
    series = await fetchApi(`/series/${params.id}`);
  } catch (error) {
    notFound();
  }

  const botUsername = process.env.NEXT_PUBLIC_BOT_USERNAME || "kinochi_uz_bot";

  return (
    <div className="min-h-screen bg-background pt-24 pb-12 px-4 sm:px-6 lg:px-8 text-white">
      <div className="max-w-5xl mx-auto bg-surface rounded-2xl overflow-hidden shadow-2xl flex flex-col md:flex-row mb-12">
        
        {/* Left Side: Poster */}
        <div className="w-full md:w-1/3 relative aspect-[2/3] bg-gray-900 flex-shrink-0">
          {series.poster_url ? (
            <Image 
              src={series.poster_url}
              alt={series.title}
              fill
              className="object-cover"
              priority
            />
          ) : (
            <div className="absolute inset-0 flex items-center justify-center text-gray-500">
              Rasm mavjud emas
            </div>
          )}
        </div>

        {/* Right Side: Details */}
        <div className="w-full md:w-2/3 p-6 md:p-8 flex flex-col">
          <h1 className="text-3xl md:text-5xl font-bold mb-4">{series.title}</h1>
          <div className="text-gray-300 text-base md:text-lg leading-relaxed mb-8 flex-grow">
            {series.description || "Ushbu serial uchun batafsil ma'lumot kiritilmagan."}
          </div>
        </div>
      </div>

      {/* Seasons and Episodes */}
      <div className="max-w-5xl mx-auto">
        <h2 className="text-2xl md:text-3xl font-bold mb-8 text-white/90">Fasllar va Qismlar</h2>
        
        {!series.seasons || series.seasons.length === 0 ? (
          <div className="bg-surface/50 rounded-xl p-8 text-center text-gray-400">
            Hozircha qismlar yuklanmagan.
          </div>
        ) : (
          <div className="space-y-8">
            {series.seasons
              .sort((a: Season, b: Season) => a.season_number - b.season_number)
              .map((season: Season) => (
              <div key={season.id} className="bg-surface rounded-xl overflow-hidden ring-1 ring-white/5">
                <div className="bg-white/5 px-6 py-4 border-b border-white/5">
                  <h3 className="text-xl font-semibold">
                    {season.season_number}-Fasl {season.title ? `- ${season.title}` : ""}
                  </h3>
                  {season.description && (
                    <p className="text-sm text-gray-400 mt-1">{season.description}</p>
                  )}
                </div>
                
                <div className="p-4 md:p-6 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
                  {!season.episodes || season.episodes.length === 0 ? (
                    <div className="col-span-full text-gray-500 text-sm py-2">
                      Bu faslga qismlar qo'shilmagan.
                    </div>
                  ) : (
                    season.episodes
                      .sort((a, b) => a.episode_number - b.episode_number)
                      .map((episode) => {
                      const telegramDeepLink = `https://t.me/${botUsername}?start=${episode.code}`;
                      return (
                        <a 
                          href={telegramDeepLink}
                          target="_blank"
                          rel="noopener noreferrer"
                          key={episode.id} 
                          className="group bg-background rounded-lg p-4 border border-white/5 hover:border-primary/50 transition-all duration-300 hover:shadow-[0_0_15px_rgba(220,38,38,0.2)] flex items-center justify-between"
                        >
                          <div>
                            <div className="font-medium text-white group-hover:text-primary transition-colors">
                              {episode.episode_number}-qism
                            </div>
                            {episode.title && (
                              <div className="text-xs text-gray-400 mt-1 truncate max-w-[120px]" title={episode.title}>
                                {episode.title}
                              </div>
                            )}
                          </div>
                          
                          <div className="w-10 h-10 rounded-full bg-white/5 flex items-center justify-center group-hover:bg-primary/20 group-hover:text-primary transition-colors text-gray-400">
                            <svg className="w-5 h-5 ml-1" fill="currentColor" viewBox="0 0 24 24">
                              <path d="M8 5v14l11-7z" />
                            </svg>
                          </div>
                        </a>
                      )
                    })
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
