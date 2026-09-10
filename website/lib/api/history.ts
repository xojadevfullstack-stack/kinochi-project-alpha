import { fetchApi } from '../api';

export interface HistoryItem {
  id: number;
  status: "in_progress" | "completed";
  last_watched_at: string;
  type: "movie" | "episode";
  movie?: {
    id: number;
    title: string;
    poster_url: string | null;
    code: string;
  };
  episode?: {
    id: number;
    display_code: string;
    code: string;
    season_number: number;
    episode_number: number;
    series_id: number;
    series_title: string;
    series_poster: string | null;
  };
}

export interface RecommendationItem {
  type: "movie" | "series";
  id: number;
  title: string;
  poster_url: string | null;
  code?: string;
  rating: number | null;
  genres: string[];
}

export async function getHistory(skip: number = 0, limit: number = 20): Promise<{ items: HistoryItem[], total: number }> {
  try {
    const res = await fetchApi(`/users/me/history?skip=${skip}&limit=${limit}`);
    return {
      items: res?.items || [],
      total: res?.total || 0,
    };
  } catch (error) {
    console.error("Failed to fetch history:", error);
    return { items: [], total: 0 };
  }
}

export async function getRecommendations(): Promise<{ items: RecommendationItem[] }> {
  try {
    const res = await fetchApi('/users/me/recommendations');
    return {
      items: res?.items || [],
    };
  } catch (error) {
    console.error("Failed to fetch recommendations:", error);
    return { items: [] };
  }
}
