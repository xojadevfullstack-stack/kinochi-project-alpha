"use client";

import { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import BackButton from "@/components/BackButton";

interface Actor {
  id: number;
  name: string;
  original_name?: string;
  photo_url: string;
  role: string;
  movies_count: number;
  popular_movie: string;
}

const POPULAR_ACTORS: Actor[] = [
  {
    id: 1,
    name: "Jeyson Steytem",
    original_name: "Jason Statham",
    photo_url: "https://image.tmdb.org/t/p/w500/whNwkEQYWLFJA8ij00Ke24TN9Y7.jpg",
    role: "Jangari, Triller",
    movies_count: 28,
    popular_movie: "Forsaj, Tashuvchi, Mexanik"
  },
  {
    id: 2,
    name: "Tom Kruz",
    original_name: "Tom Cruise",
    photo_url: "https://image.tmdb.org/t/p/w500/8qB95557xV9qN955.jpg",
    role: "Jangari, Sarguzasht",
    movies_count: 32,
    popular_movie: "Uddalab bo'lmas topshiriq, Top Gun"
  },
  {
    id: 3,
    name: "Leonardo Di Kaprio",
    original_name: "Leonardo DiCaprio",
    photo_url: "https://image.tmdb.org/t/p/w500/wo2hxAzE6n2xnwv5QOZZ1Q3KyUX.jpg",
    role: "Drama, Triller",
    movies_count: 24,
    popular_movie: "Titanik, Muqaddima (Inception)"
  },
  {
    id: 4,
    name: "Kianu Rivz",
    original_name: "Keanu Reeves",
    photo_url: "https://image.tmdb.org/t/p/w500/4D0PpNI0km5GR7u1imWmxME4Pq5.jpg",
    role: "Fantastika, Jangari",
    movies_count: 26,
    popular_movie: "Jon Uik, Matritsa"
  },
  {
    id: 5,
    name: "Jonni Depp",
    original_name: "Johnny Depp",
    photo_url: "https://image.tmdb.org/t/p/w500/ilPB9e5q1y2U31n2U3.jpg",
    role: "Sarguzasht, Fantastika",
    movies_count: 30,
    popular_movie: "Karib dengizi qaroqchilari"
  },
  {
    id: 6,
    name: "Jeki Chan",
    original_name: "Jackie Chan",
    photo_url: "https://image.tmdb.org/t/p/w500/nrazenTDne2n1x8Z5U3yM89uCj1.jpg",
    role: "Komediya, Jangari",
    movies_count: 45,
    popular_movie: "Tig'iz vaqt, Politsiya hikoyasi"
  },
  {
    id: 7,
    name: "Killian Merfi",
    original_name: "Cillian Murphy",
    photo_url: "https://image.tmdb.org/t/p/w500/360R4cgh67xnm1Vw1r3.jpg",
    role: "Drama, Tarixiy",
    movies_count: 18,
    popular_movie: "Oppengeymer, O'tkir soyabonlar"
  },
  {
    id: 8,
    name: "Kristian Beyl",
    original_name: "Christian Bale",
    photo_url: "https://image.tmdb.org/t/p/w500/b7fTC9WFuvq0vM5o32.jpg",
    role: "Drama, Triller",
    movies_count: 22,
    popular_movie: "Qora Ritsar, Ford Ferrari-ga qarshi"
  }
];

export default function ActorsPage() {
  const [searchQuery, setSearchQuery] = useState("");

  const filtered = POPULAR_ACTORS.filter((actor) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      actor.name.toLowerCase().includes(q) ||
      actor.original_name?.toLowerCase().includes(q) ||
      actor.popular_movie.toLowerCase().includes(q)
    );
  });

  return (
    <div className="min-h-screen pt-20 sm:pt-24 pb-28 xl:pb-16 px-4 md:px-8 bg-background-obsidian text-text-primary">
      <div className="max-w-5xl mx-auto space-y-6">
        
        {/* Header Bar */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-white/10">
          <div className="flex items-center gap-3">
            <BackButton fallbackUrl="/" />
            <div>
              <h1 className="text-xl sm:text-2xl font-black text-text-primary font-headline-md tracking-tight flex items-center gap-2">
                <span className="material-symbols-outlined text-rating-gold text-2xl">groups</span>
                <span>Aktyorlar va Ijodkorlar</span>
              </h1>
              <p className="text-xs text-text-secondary mt-0.5">
                Mashhur kino yulduzlari va ularning filmlari to'plami
              </p>
            </div>
          </div>

          {/* Actor Search Input */}
          <div className="relative w-full sm:w-72">
            <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-text-secondary text-lg pointer-events-none">
              search
            </span>
            <input
              type="text"
              placeholder="Aktyor ismini qidiring..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-white/5 border border-white/10 rounded-xl pl-10 pr-4 py-2 text-white text-xs outline-none focus:border-white/20 transition-colors"
            />
          </div>
        </div>

        {/* Actors Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4 sm:gap-6">
          {filtered.map((actor) => (
            <Link
              key={actor.id}
              href={`/catalog?search=${encodeURIComponent(actor.original_name || actor.name)}`}
              className="bg-white/5 border border-white/10 hover:border-white/20 rounded-2xl p-4 flex flex-col items-center text-center transition-all duration-300 hover:scale-[1.03] group shadow-md"
            >
              {/* Actor Photo */}
              <div className="w-24 h-24 sm:w-28 sm:h-28 rounded-full overflow-hidden relative mb-3 border-2 border-white/10 group-hover:border-white/30 transition-all bg-white/10 shadow-lg">
                <div className="w-full h-full flex items-center justify-center bg-white/10 text-white/40">
                  <span className="material-symbols-outlined text-4xl">person</span>
                </div>
              </div>

              <h3 className="font-bold text-sm text-white group-hover:text-white transition-colors mb-0.5 line-clamp-1">
                {actor.name}
              </h3>
              {actor.original_name && (
                <span className="text-[11px] text-text-secondary font-mono mb-1.5 block">
                  {actor.original_name}
                </span>
              )}

              <div className="text-[10px] text-text-secondary bg-white/5 px-2 py-0.5 rounded-full border border-white/5 mb-2">
                {actor.role}
              </div>

              <div className="mt-auto pt-2 border-t border-white/5 w-full flex items-center justify-between text-[11px] text-text-secondary">
                <span>{actor.movies_count} ta film</span>
                <span className="text-rating-gold font-semibold flex items-center gap-0.5">
                  Filmlar &rarr;
                </span>
              </div>
            </Link>
          ))}
        </div>

      </div>
    </div>
  );
}
