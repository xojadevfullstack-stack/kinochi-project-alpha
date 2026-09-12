import { fetchApi } from "../api";

export interface ReviewItem {
  id: number;
  user_id: number;
  user_name: string;
  username?: string | null;
  rating: number;
  comment?: string | null;
  created_at: string;
  updated_at?: string | null;
}

export interface ReviewsResponse {
  items: ReviewItem[];
  total: number;
  average_rating: number | null;
  votes_count: number;
}

export async function getReviews(params: {
  movieId?: number;
  movieCode?: string;
  seriesId?: number;
  episodeId?: number;
  limit?: number;
  offset?: number;
}): Promise<ReviewsResponse> {
  const query = new URLSearchParams();
  if (params.movieId) query.set("movie_id", params.movieId.toString());
  if (params.movieCode) query.set("movie_code", params.movieCode);
  if (params.seriesId) query.set("series_id", params.seriesId.toString());
  if (params.episodeId) query.set("episode_id", params.episodeId.toString());
  if (params.limit) query.set("limit", params.limit.toString());
  if (params.offset) query.set("offset", params.offset.toString());

  return fetchApi(`/reviews?${query.toString()}`, {
    next: { revalidate: 10 },
  });
}

export async function getMyReview(params: {
  movieId?: number;
  movieCode?: string;
  seriesId?: number;
  episodeId?: number;
}): Promise<ReviewItem | null> {
  const query = new URLSearchParams();
  if (params.movieId) query.set("movie_id", params.movieId.toString());
  if (params.movieCode) query.set("movie_code", params.movieCode);
  if (params.seriesId) query.set("series_id", params.seriesId.toString());
  if (params.episodeId) query.set("episode_id", params.episodeId.toString());

  return fetchApi(`/reviews/my?${query.toString()}`, {
    cache: "no-store",
  });
}

export async function submitReview(data: {
  movieId?: number;
  seriesId?: number;
  episodeId?: number;
  rating: number;
  comment?: string;
}) {
  return fetchApi("/reviews", {
    method: "POST",
    body: JSON.stringify({
      movie_id: data.movieId,
      series_id: data.seriesId,
      episode_id: data.episodeId,
      rating: data.rating,
      comment: data.comment,
    }),
  });
}
