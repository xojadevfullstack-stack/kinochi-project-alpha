export interface CategoryItem {
  id: number | string;
  name: string;
}

export interface GenreItem {
  id: string;
  name: string;
  icon?: string;
}

export const DEFAULT_GENRES: GenreItem[] = [
  { id: "action", name: "Jangari", icon: "swords" },
  { id: "comedy", name: "Komediya", icon: "sentiment_very_satisfied" },
  { id: "scifi", name: "Fantastika", icon: "rocket_launch" },
  { id: "thriller", name: "Triller", icon: "visibility" },
  { id: "drama", name: "Drama", icon: "theater_comedy" },
  { id: "horror", name: "Qo'rqinchli", icon: "skull" },
  { id: "romance", name: "Melodrama", icon: "favorite" },
  { id: "detective", name: "Detektiv", icon: "search" },
  { id: "animation", name: "Multfilm", icon: "animation" },
  { id: "history", name: "Tarixiy", icon: "history_edu" },
  { id: "adventure", name: "Sarguzasht", icon: "explore" },
  { id: "crime", name: "Jinoyat", icon: "local_police" },
  { id: "military", name: "Harbiy", icon: "shield" }
];

export interface MediaTypeItem {
  id: string;
  name: string;
  icon?: string;
}

export const DEFAULT_MEDIA_TYPES: MediaTypeItem[] = [
  { id: "movie", name: "Kinolar", icon: "movie" },
  { id: "series", name: "Seriallar", icon: "live_tv" },
  { id: "dorama", name: "Doramalar", icon: "theater_comedy" },
  { id: "animation", name: "Multfilmlar / Anime", icon: "animation" },
];

export const DEFAULT_YEARS: number[] = [2026, 2025, 2024, 2023, 2022, 2021, 2020, 2019, 2018, 2017, 2016, 2015, 2010, 2005, 2000];
