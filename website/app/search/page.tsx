import { fetchApi } from "@/lib/api";
import { Metadata } from "next";
import SearchClientView from "@/components/SearchClientView";

// This page reads query params, so it will be dynamically rendered
export const dynamic = "force-dynamic";

export async function generateMetadata({
  searchParams,
}: {
  searchParams: { q?: string; type?: string };
}): Promise<Metadata> {
  const query = searchParams.q || "";
  const type = searchParams.type === "series" ? "seriallar" : "kinolar";
  if (!query) {
    return {
      title: "Qidiruv va Kashf etish - MediaPlus",
      description: "Eng so'nggi kinolar, seriallar, anime va doramalarni qidiring va tomosha qiling.",
    };
  }
  return {
    title: `"${query}" qidiruv natijalari - MediaPlus`,
    description: `"${query}" bo'yicha topilgan barcha ${type} ro'yxati.`,
  };
}

export default async function SearchPage({
  searchParams,
}: {
  searchParams: { q?: string; type?: string };
}) {
  const query = searchParams.q || "";
  const specificType = searchParams.type;

  let initialResults: any[] = [];
  let initialExternalResults: any[] = [];
  const defaultItems: any[] = [];
  let errorMsg: string | null = null;

  // 1. Fetch default trending/recommended items
  try {
    const [moviesRes, seriesRes] = await Promise.all([
      fetchApi("/movies?limit=12").catch(() => ({ items: [] })),
      fetchApi("/series?limit=12").catch(() => ({ items: [] })),
    ]);

    const defaultMovies = (moviesRes?.items || []).map((m: any) => ({ ...m, isSeries: false }));
    const defaultSeries = (seriesRes?.items || []).map((s: any) => ({ ...s, isSeries: true }));

    const maxLen = Math.max(defaultMovies.length, defaultSeries.length);
    for (let i = 0; i < maxLen; i++) {
      if (i < defaultMovies.length) defaultItems.push(defaultMovies[i]);
      if (i < defaultSeries.length) defaultItems.push(defaultSeries[i]);
    }
  } catch (err) {
    console.error("Failed to load default recommendations for search page:", err);
  }

  // 2. Initial SSR search if query is in URL
  if (query.trim().length >= 2) {
    try {
      if (specificType === "series") {
        const res = await fetchApi(`/series/search?q=${encodeURIComponent(query)}&limit=40`);
        initialResults = (res.items || []).map((i: any) => ({ ...i, isSeries: true }));
      } else if (specificType === "movie") {
        const res = await fetchApi(`/movies/search?q=${encodeURIComponent(query)}&limit=40`);
        initialResults = (res.items || []).map((i: any) => ({ ...i, isSeries: false }));
      } else {
        const [moviesRes, seriesRes] = await Promise.all([
          fetchApi(`/movies/search?q=${encodeURIComponent(query)}&limit=24`).catch(() => ({ items: [] })),
          fetchApi(`/series/search?q=${encodeURIComponent(query)}&limit=24`).catch(() => ({ items: [] })),
        ]);
        const movies = (moviesRes?.items || []).map((i: any) => ({ ...i, isSeries: false }));
        const series = (seriesRes?.items || []).map((i: any) => ({ ...i, isSeries: true }));
        initialResults = [...movies, ...series];
      }

      // If internal results are empty, search TMDB & Kinopoisk
      if (initialResults.length === 0) {
        try {
          const extRes = await fetchApi(
            `/content-requests/external-search?q=${encodeURIComponent(query)}&limit=12`
          ).catch(() => ({ results: [] }));
          initialExternalResults = extRes?.results || [];
        } catch (extErr) {
          console.error("External TMDB search failed:", extErr);
        }
      }
    } catch (error: any) {
      errorMsg = error.message;
    }
  }

  return (
    <SearchClientView
      initialQuery={query}
      initialType={specificType}
      initialResults={initialResults}
      initialExternalResults={initialExternalResults}
      defaultItems={defaultItems}
      initialError={errorMsg}
    />
  );
}
