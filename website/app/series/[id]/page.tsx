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
  poster_url: string | null;
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
          <h1 className="text-3xl md:text-5xl font-bold mb-2">{series.title}</h1>
          
          <div className="flex flex-wrap items-center gap-4 text-sm md:text-base mb-6">
            <span className="text-star font-bold flex items-center gap-1">
              ★ {series.imdb_rating || "N/A"}
            </span>
            <span>|</span>
            <span className="text-gray-300">{series.release_year || "Yil no'malum"}</span>
          </div>

          <div className="mb-6 space-y-2 text-sm text-gray-300">
            {series.categories && series.categories.length > 0 && (
              <p><strong className="text-white">Kategoriya:</strong> {series.categories.map((c: any) => c.name).join(', ')}</p>
            )}
            <p><strong className="text-white">Rejissyor:</strong> {series.director || "Kiritilmagan"}</p>
            <p><strong className="text-white">Aktyorlar:</strong> {series.cast || "Kiritilmagan"}</p>
          </div>
          
          <div className="mb-8 flex-grow">
            <h3 className="text-lg font-semibold mb-2 text-white">Serial haqida:</h3>
            <p className="text-gray-300 leading-relaxed text-sm md:text-base">
              {series.description || "Ushbu serial uchun batafsil ma'lumot kiritilmagan."}
            </p>
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
              <div key={season.id} className="bg-surface rounded-xl overflow-hidden ring-1 ring-white/5 relative">
                {/* Timeline connector (optional decorative line) */}
                <div className="hidden md:block absolute left-8 top-0 bottom-0 w-px bg-white/5 z-0"></div>
                
                <div className="relative z-10 flex flex-col md:flex-row gap-6 p-6">
                  {/* Season Poster */}
                  <div className="w-full md:w-48 aspect-[2/3] relative flex-shrink-0 bg-background/50 rounded-lg overflow-hidden shadow-lg border border-white/5">
                    {season.poster_url ? (
                      <Image 
                        src={season.poster_url} 
                        alt={`${season.season_number}-fasl`}
                        fill
                        className="object-cover"
                      />
                    ) : series.poster_url ? (
                      <Image 
                        src={series.poster_url} 
                        alt="Fasl"
                        fill
                        className="object-cover opacity-30 grayscale blur-[2px]"
                      />
                    ) : (
                      <div className="absolute inset-0 flex items-center justify-center text-gray-500 text-sm">
                        Rasm yo'q
                      </div>
                    )}
                  </div>
                  
                  {/* Season Content */}
                  <div className="flex-grow flex flex-col">
                    <div className="mb-6">
                      <h3 className="text-2xl font-bold flex items-center gap-3">
                        <span className="bg-white/10 px-3 py-1 rounded-md text-primary text-xl">
                          {season.season_number}-Fasl
                        </span>
                        {season.title && <span>{season.title}</span>}
                      </h3>
                      {season.description && (
                        <p className="text-gray-400 mt-4 leading-relaxed text-sm">
                          {season.description}
                        </p>
                      )}
                    </div>
                    
                    {/* Episodes Grid */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 mt-auto">
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
                              className="bg-primary hover:bg-red-700 text-white font-semibold py-3 px-6 rounded-full transition-all flex items-center justify-center gap-2 shadow-lg shadow-primary/30 hover:scale-105 w-full"
                            >
                              <svg className="w-5 h-5 fill-current flex-shrink-0" viewBox="0 0 24 24">
                                <path d="M8 5v14l11-7z" />
                              </svg>
                              <span className="truncate">
                                {episode.episode_number}-qism
                                {episode.title && <span className="ml-1 opacity-80 font-normal">- {episode.title}</span>}
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
      </div>
    </div>
  );
}
