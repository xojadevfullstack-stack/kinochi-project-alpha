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
  categories?: { id: number; name: string }[];
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
  limit: number = 36,
  categoryId?: string | number | null
): Promise<{ items: CatalogItem[]; total: number; page_id: number | null }> {
  try {
    // 1. Get pages to find the ID for the slug
    const pages = await getPages();
    const page = pages.find((p) => p.slug.toLowerCase() === slug.toLowerCase());
    
    if (!page) {
      return { items: [], total: 0, page_id: null };
    }

    const page_id = page.id;

    // 2. Fetch movies and series for this page
    let moviesUrl = `/movies?page_id=${page_id}&skip=${skip}&limit=${limit}`;
    let seriesUrl = `/series?page_id=${page_id}&skip=${skip}&limit=${limit}`;
    if (categoryId) {
      moviesUrl += `&category_id=${categoryId}`;
      seriesUrl += `&category_id=${categoryId}`;
    }

    const [moviesRes, seriesRes] = await Promise.all([
      fetchApi(moviesUrl, { next: { revalidate: 300 } }).catch(() => ({ items: [], total: 0 })),
      fetchApi(seriesUrl, { next: { revalidate: 300 } }).catch(() => ({ items: [], total: 0 }))
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

    const total = (moviesRes?.total || 0) + (seriesRes?.total || 0);

    return { items: combined, total, page_id };
  } catch (error) {
    console.error(`Failed to fetch content for page ${slug}:`, error);
    return { items: [], total: 0, page_id: null };
  }
}
