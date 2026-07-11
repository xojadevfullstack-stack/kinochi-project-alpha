import { MetadataRoute } from 'next';
import { fetchApi } from '@/lib/api';

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL || 'https://kinochi.uz';

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const routes: MetadataRoute.Sitemap = [
    {
      url: `${BASE_URL}/`,
      lastModified: new Date(),
      changeFrequency: 'daily',
      priority: 1,
    },
  ];

  try {
    // Fetch all movies (limit 1000 for sitemap purposes, or implement pagination if needed)
    const moviesData = await fetchApi('/movies?limit=1000').catch(() => null);
    const movies = moviesData?.items || [];

    const movieRoutes: MetadataRoute.Sitemap = movies.map((movie: any) => ({
      url: `${BASE_URL}/movie/${movie.code}`,
      lastModified: new Date(movie.updated_at || movie.created_at || new Date()),
      changeFrequency: 'weekly',
      priority: 0.8,
    }));

    routes.push(...movieRoutes);
    
    // Note: If you add dynamic Category pages in the future (e.g. /category/[id]), 
    // you should fetch categories and add them here as well.
    const categoriesData = await fetchApi('/categories').catch(() => null);
    const categories = (categoriesData || []).filter((c: any) => c.is_active);
    
    const categoryRoutes: MetadataRoute.Sitemap = categories.map((cat: any) => ({
      url: `${BASE_URL}/#category-${cat.id}`, // Placeholder until actual category routes exist
      lastModified: new Date(),
      changeFrequency: 'weekly',
      priority: 0.6,
    }));
    
    // We omit categoryRoutes for now since they don't have dedicated pages yet, 
    // but the code is ready for when they do.

  } catch (error) {
    console.error("Error generating sitemap:", error);
  }

  // TODO: When Movie Details page is created (/movie/[code]/page.tsx), 
  // remember to use generateMetadata() inside that page to dynamically set og:title, og:image, etc.

  return routes;
}
