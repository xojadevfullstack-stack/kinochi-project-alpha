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
  { id: "anime", name: "Anime", icon: "auto_awesome" },
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
  { id: "anime", name: "Anime", icon: "auto_awesome" },
  { id: "animation", name: "Multfilmlar", icon: "animation" },
];

export const DEFAULT_YEARS: number[] = [2026, 2025, 2024, 2023, 2022, 2021, 2020, 2019, 2018, 2017, 2016, 2015, 2010, 2005, 2000];

export interface CountryItem {
  id: string;
  name: string;
}

export const DEFAULT_COUNTRIES: CountryItem[] = [
  { id: "uz", name: "O'zbekiston" },
  { id: "us", name: "AQSH" },
  { id: "tr", name: "Turkiya" },
  { id: "kr", name: "Janubiy Koreya" },
  { id: "ru", name: "Rossiya" },
  { id: "in", name: "Hindiston" },
  { id: "gb", name: "Buyuk Britaniya" },
  { id: "fr", name: "Fransiya" },
];

export interface SortOptionItem {
  id: string;
  name: string;
}

export const DEFAULT_SORT_OPTIONS: SortOptionItem[] = [
  { id: "all", name: "Barchasi" },
  { id: "imdb", name: "IMDb" },
  { id: "kinopoisk", name: "Kinopoisk" },
  { id: "itv", name: "iTV (MediaPlus)" },
];

export interface AudioItem {
  id: string;
  name: string;
}

export const DEFAULT_AUDIOTRACKS: AudioItem[] = [
  { id: "uz", name: "O'zbekcha" },
  { id: "ru", name: "Ruscha" },
  { id: "en", name: "Inglizcha" },
  { id: "orig", name: "Asl tili" },
];

export interface SubtitleItem {
  id: string;
  name: string;
}

export const DEFAULT_SUBTITLES: SubtitleItem[] = [
  { id: "uz", name: "O'zbekcha" },
  { id: "ru", name: "Ruscha" },
  { id: "en", name: "Inglizcha" },
  { id: "none", name: "Mavjud emas" },
];
