import { fetchApi } from "@/lib/api";
import { notFound } from "next/navigation";
import Image from "next/image";
import { Metadata } from "next";

// Define params for the page
type Props = {
  params: { code: string };
};

// Next.js ISR (optional, but good for production)
export const revalidate = 60; 

// Generate dynamic metadata (SEO / Open Graph)
export async function generateMetadata({ params }: Props): Promise<Metadata> {
  try {
    const movie = await fetchApi(`/movies/code/${params.code}`);
    
    return {
      title: `${movie.title} - Kinochi`,
      description: movie.description || `${movie.title} filmini bepul tomosha qiling.`,
      openGraph: {
        title: `${movie.title} - Kinochi`,
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
    // If API returns 404 or error, trigger Next.js notFound page
    notFound();
  }

  // Fallback to bot username if env is missing (for local dev)
  const botUsername = process.env.NEXT_PUBLIC_BOT_USERNAME || "kinochi_uz_bot";
  const telegramDeepLink = `https://t.me/${botUsername}?start=${movie.code}`;

  return (
    <div className="min-h-screen bg-background pt-24 pb-12 px-4 sm:px-6 lg:px-8 text-white">
      <div className="max-w-5xl mx-auto bg-surface rounded-2xl overflow-hidden shadow-2xl flex flex-col md:flex-row">
        
        {/* Left Side: Poster */}
        <div className="w-full md:w-1/3 relative aspect-[2/3] bg-gray-900 flex-shrink-0">
          {movie.poster_url ? (
            <Image 
              src={movie.poster_url}
              alt={movie.title}
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

        {/* Right Side: Movie Details (Functional Skeleton) */}
        <div className="w-full md:w-2/3 p-6 md:p-8 flex flex-col">
          
          <h1 className="text-3xl md:text-5xl font-bold mb-2">{movie.title}</h1>
          
          {movie.original_title && (
            <p className="text-gray-400 text-sm md:text-base italic mb-4">
              {movie.original_title}
            </p>
          )}

          <div className="flex flex-wrap items-center gap-4 text-sm md:text-base mb-6">
            <span className="text-star font-bold flex items-center gap-1">
              ★ {movie.imdb_rating || movie.tmdb_rating || "N/A"}
            </span>
            <span>|</span>
            <span className="text-gray-300">{movie.release_year || "Yil no'malum"}</span>
            <span>|</span>
            <span className="text-gray-300">{movie.runtime ? `${movie.runtime} daqiqa` : "Vaqti no'malum"}</span>
          </div>

          <div className="mb-6 space-y-2 text-sm text-gray-300">
            <p><strong className="text-white">Janrlar:</strong> {movie.genres || "Kiritilmagan"}</p>
            {movie.categories && movie.categories.length > 0 && (
              <p><strong className="text-white">Kategoriya:</strong> {movie.categories.map((c: any) => c.name).join(', ')}</p>
            )}
            <p><strong className="text-white">Rejissyor:</strong> {movie.director || "Kiritilmagan"}</p>
            <p><strong className="text-white">Aktyorlar:</strong> {movie.cast || "Kiritilmagan"}</p>
          </div>

          <div className="mb-8 flex-grow">
            <h3 className="text-lg font-semibold mb-2 text-white">Kino haqida:</h3>
            <p className="text-gray-300 leading-relaxed text-sm md:text-base">
              {movie.description || "Ushbu kino uchun tavsif kiritilmagan."}
            </p>
          </div>

          {/* TELEGRAM CTA BUTTON */}
          <div className="mt-auto">
            <a 
              href={telegramDeepLink}
              target="_blank"
              rel="noopener noreferrer"
              className="group inline-flex w-full md:w-auto items-center justify-between gap-4 bg-surface border border-white/5 hover:border-primary/50 text-white py-3 px-4 rounded-xl transition-all duration-300"
            >
              <span className="font-medium px-2">Telegram'da tomosha qilish</span>
              <div className="w-10 h-10 bg-primary/20 text-primary group-hover:bg-primary group-hover:text-white rounded-lg flex items-center justify-center transition-all duration-300 shadow-[0_0_0_rgba(229,9,20,0)] group-hover:shadow-[0_0_15px_rgba(229,9,20,0.5)]">
                <svg className="w-5 h-5 fill-current ml-1" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
              </div>
            </a>
          </div>
          
        </div>
      </div>
    </div>
  );
}
