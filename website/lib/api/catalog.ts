import { fetchApi } from "../api";

export type PageResponse = {
  id: number;
  title: string;
  slug: string;
  is_active: boolean;
};

export type CatalogItem = {
  id: number;
  code?: string;
  title: string;
  original_title?: string | null;
  description?: string | null;
  imdb_rating?: number | null;
  tmdb_rating?: number | null;
  genres?: string | null;
  release_year?: number | null;
  poster_url?: string | null;
  is_series?: boolean;
  created_at?: string;
};

export async function getPages(): Promise<PageResponse[]> {
  try {
    const res = await fetchApi("/pages?limit=100", { next: { revalidate: 300 } });
    return res.items || [];
  } catch (error) {
    console.error("Failed to fetch pages:", error);
    return [];
  }
}

export async function getPageContent(
  slug: string,
  skip: number = 0,
  limit: number = 20
): Promise<{ items: CatalogItem[]; total: number; page_id: number | null }> {
  try {
    // 1. Get pages to find the ID for the slug
    const pages = await getPages();
    const page = pages.find((p) => p.slug === slug);
    
    if (!page) {
      return { items: [], total: 0, page_id: null };
    }

    const page_id = page.id;

    // 2. Fetch movies and series for this page
    const [moviesRes, seriesRes] = await Promise.all([
      fetchApi(`/movies?page_id=${page_id}&skip=${skip}&limit=${limit}`, { next: { revalidate: 300 } }),
      fetchApi(`/series?page_id=${page_id}&skip=${skip}&limit=${limit}`, { next: { revalidate: 300 } })
    ]);

    // 3. Combine and sort
    const movies = (moviesRes?.items || []).map((m: any) => ({ ...m, is_series: false }));
    const series = (seriesRes?.items || []).map((s: any) => ({ ...s, is_series: true }));

    const combined: CatalogItem[] = [...movies, ...series];
    
    // Sort by created_at descending (newest first)
    combined.sort((a, b) => {
      const dateA = new Date(a.created_at || 0).getTime();
      const dateB = new Date(b.created_at || 0).getTime();
      return dateB - dateA;
    });

    // Handle combined pagination slicing on client side.
    // By returning ALL items fetched in this batch (up to 2*limit), 
    // we ensure no items are dropped. They will be appended in the grid.
    // Local sorting per batch means global order might slightly vary, but it's safe.
    const total = (moviesRes?.total || 0) + (seriesRes?.total || 0);

    return { items: combined, total, page_id };
  } catch (error) {
    console.error(`Failed to fetch content for page ${slug}:`, error);
    return { items: [], total: 0, page_id: null };
  }
}
