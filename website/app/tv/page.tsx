"use client";

import { useState } from "react";
import BackButton from "@/components/BackButton";

interface TVChannel {
  id: string;
  name: string;
  category: "milliy" | "kino" | "sport" | "yangiliklar";
  description: string;
  streamUrl?: string;
  logoText: string;
  isLive: boolean;
}

const CHANNELS: TVChannel[] = [
  {
    id: "milliy-tv",
    name: "Milliy TV",
    category: "milliy",
    description: "Eng sara o'zbek musiqalari, ko'ngilochar shoular va seriallar.",
    logoText: "MTV",
    isLive: true
  },
  {
    id: "sevimli-tv",
    name: "Sevimli TV",
    category: "milliy",
    description: "Oilaviy telekanal: seriallar, kinolar va qiziqarli ko'rsatuvlar.",
    logoText: "STV",
    isLive: true
  },
  {
    id: "zor-tv",
    name: "Zo'r TV",
    category: "milliy",
    description: "Zamonaviy madaniyat, mega-shoular va premyeralar.",
    logoText: "ZOR",
    isLive: true
  },
  {
    id: "my5-tv",
    name: "My5 (Mening Yurtim)",
    category: "milliy",
    description: "Yoshlar telekanali: musiqiy loyihalar va qiziqarli dasturlar.",
    logoText: "MY5",
    isLive: true
  },
  {
    id: "sport-tv",
    name: "Sport TV",
    category: "sport",
    description: "Futbol, UFC, boks va jahon sport musobaqalari jonli efirda.",
    logoText: "SPORT",
    isLive: true
  },
  {
    id: "uzbekistan-24",
    name: "O'zbekiston 24",
    category: "yangiliklar",
    description: "Mamlakat va dunyo bo'ylab eng dolzarb tezkor yangiliklar.",
    logoText: "UZB24",
    isLive: true
  },
  {
    id: "kinohit-hd",
    name: "Kinohit HD",
    category: "kino",
    description: "Dunyoning eng mashhur blokbasterlari va premyera filmlari.",
    logoText: "KINO",
    isLive: true
  }
];

export default function TVPage() {
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [activeChannel, setActiveChannel] = useState<TVChannel>(CHANNELS[0]);

  const filtered = CHANNELS.filter((ch) => {
    if (selectedCategory === "all") return true;
    return ch.category === selectedCategory;
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
                <span className="material-symbols-outlined text-rating-gold text-2xl">live_tv</span>
                <span>Onlayn TV va Jonli Efirlar</span>
              </h1>
              <p className="text-xs text-text-secondary mt-0.5">
                O'zbekiston va xorijiy telekanallarni yuqori sifatda tomosha qiling
              </p>
            </div>
          </div>

          {/* Category Tabs */}
          <div className="flex items-center gap-1.5 bg-white/5 p-1 rounded-xl border border-white/10 self-start sm:self-auto">
            <button
              onClick={() => setSelectedCategory("all")}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                selectedCategory === "all"
                  ? "bg-white/15 text-white font-bold border border-white/20 shadow-sm"
                  : "text-text-secondary hover:text-white"
              }`}
            >
              Barchasi
            </button>
            <button
              onClick={() => setSelectedCategory("milliy")}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                selectedCategory === "milliy"
                  ? "bg-white/15 text-white font-bold border border-white/20 shadow-sm"
                  : "text-text-secondary hover:text-white"
              }`}
            >
              Milliy
            </button>
            <button
              onClick={() => setSelectedCategory("kino")}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                selectedCategory === "kino"
                  ? "bg-white/15 text-white font-bold border border-white/20 shadow-sm"
                  : "text-text-secondary hover:text-white"
              }`}
            >
              Kino
            </button>
            <button
              onClick={() => setSelectedCategory("sport")}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                selectedCategory === "sport"
                  ? "bg-white/15 text-white font-bold border border-white/20 shadow-sm"
                  : "text-text-secondary hover:text-white"
              }`}
            >
              Sport
            </button>
          </div>
        </div>

        {/* Live TV Player Frame Showcase */}
        <div className="bg-white/5 border border-white/10 rounded-2xl overflow-hidden shadow-2xl p-4 sm:p-6 space-y-4">
          <div className="aspect-video w-full rounded-xl bg-black relative flex flex-col items-center justify-center border border-white/10 overflow-hidden">
            <div className="absolute top-4 left-4 flex items-center gap-2 z-10">
              <span className="w-2.5 h-2.5 rounded-full bg-red-500 animate-pulse" />
              <span className="px-2 py-0.5 rounded bg-black/60 backdrop-blur-md text-white text-[10px] font-bold uppercase border border-white/10">
                Jonli Efir
              </span>
            </div>

            <div className="text-center space-y-2 p-6 z-10">
              <div className="w-16 h-16 rounded-2xl bg-white/10 border border-white/15 flex items-center justify-center font-black text-xl text-white mx-auto shadow-inner">
                {activeChannel.logoText}
              </div>
              <h2 className="text-xl sm:text-2xl font-black text-white">
                {activeChannel.name}
              </h2>
              <p className="text-xs text-text-secondary max-w-md mx-auto">
                {activeChannel.description}
              </p>
              <div className="pt-2">
                <button className="bg-white/15 hover:bg-white/25 text-white font-bold px-5 py-2.5 rounded-xl text-xs flex items-center gap-2 mx-auto border border-white/20 transition cursor-pointer">
                  <span className="material-symbols-outlined text-[18px]">play_arrow</span>
                  <span>Efirni yoqish</span>
                </button>
              </div>
            </div>

            <div className="absolute inset-0 bg-gradient-to-t from-black via-transparent to-black/60 pointer-events-none" />
          </div>
        </div>

        {/* Channel Cards Grid */}
        <div className="space-y-3">
          <div className="text-xs font-bold text-text-secondary uppercase tracking-wider">
            Telekanallar ro'yxati ({filtered.length} ta)
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {filtered.map((ch) => {
              const active = activeChannel.id === ch.id;
              return (
                <div
                  key={ch.id}
                  onClick={() => setActiveChannel(ch)}
                  className={`p-3.5 rounded-xl border transition-all cursor-pointer flex items-center justify-between ${
                    active
                      ? "bg-white/15 border-white/30 shadow-lg text-white"
                      : "bg-white/5 border-white/10 text-text-secondary hover:text-white hover:bg-white/10"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-white/10 border border-white/10 flex items-center justify-center font-bold text-xs text-white shrink-0">
                      {ch.logoText}
                    </div>
                    <div>
                      <h4 className="font-bold text-xs text-white line-clamp-1">{ch.name}</h4>
                      <span className="text-[10px] text-text-secondary capitalize">{ch.category}</span>
                    </div>
                  </div>

                  <div className="flex items-center gap-1.5 text-[10px] text-emerald-400 font-semibold shrink-0">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                    <span>Jonli</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

      </div>
    </div>
  );
}
