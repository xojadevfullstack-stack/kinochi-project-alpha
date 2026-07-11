import { fetchApi } from "@/lib/api";
import Link from "next/link";
import Image from "next/image";
import { Metadata } from "next";

export const revalidate = 60;

export const metadata: Metadata = {
  title: "Seriallar - Kinochi",
  description: "Eng sara va so'nggi seriallarni bepul tomosha qiling.",
};

type Series = {
  id: number;
  title: string;
  description: string | null;
  poster_url: string | null;
};

export default async function SeriesListPage() {
  let seriesList: Series[] = [];
  
  try {
    const data = await fetchApi("/series?limit=50");
    seriesList = data.items || [];
  } catch (error) {
    console.error("Failed to fetch series:", error);
  }

  return (
    <div className="min-h-screen bg-background pt-24 pb-12 px-4 sm:px-6 lg:px-8 text-white">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl md:text-5xl font-bold mb-8 text-white/90">Barcha Seriallar</h1>
        
        {seriesList.length === 0 ? (
          <div className="text-center py-20 text-gray-500">
            Hozircha seriallar mavjud emas.
          </div>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-6">
            {seriesList.map(series => (
              <Link 
                href={`/series/${series.id}`} 
                key={series.id} 
                className="group relative rounded-xl overflow-hidden bg-surface transition-transform duration-300 hover:scale-105 hover:z-10 ring-1 ring-white/10 hover:ring-primary/50 flex flex-col"
              >
                <div className="aspect-[2/3] relative bg-gray-800">
                  {series.poster_url ? (
                    <Image 
                      src={series.poster_url} 
                      alt={series.title}
                      fill
                      sizes="(max-width: 768px) 160px, 224px"
                      className="object-cover"
                    />
                  ) : (
                    <div className="absolute inset-0 flex flex-col items-center justify-center bg-gradient-to-br from-surface to-background text-gray-500 border border-white/5">
                      <span className="text-xs font-medium uppercase tracking-wider opacity-60">Poster yo'q</span>
                    </div>
                  )}
                  {/* Gradient Overlay on hover */}
                  <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex flex-col justify-end p-4">
                    <div className="text-xs text-gray-300 line-clamp-3">{series.description || "Serial"}</div>
                  </div>
                </div>
                <div className="p-3 flex-1 flex flex-col justify-center">
                  <h3 className="font-medium text-sm md:text-base text-white line-clamp-2" title={series.title}>{series.title}</h3>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
