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
    // Fetch all movies with pagination
    let movies: any[] = [];
    let skip = 0;
    const limit = 100;
    while (true) {
      const moviesData = await fetchApi(`/movies?limit=${limit}&skip=${skip}`).catch(() => null);
      if (!moviesData || !moviesData.items || moviesData.items.length === 0) {
        break;
      }
      movies = movies.concat(moviesData.items);
      if (moviesData.items.length < limit) {
        break;
      }
      skip += limit;
    }

    const movieRoutes: MetadataRoute.Sitemap = movies.map((movie: any) => ({
      url: `${BASE_URL}/movie/${movie.code}`,
      lastModified: new Date(movie.updated_at || movie.created_at || new Date()),
      changeFrequency: 'weekly',
      priority: 0.8,
    }));

    routes.push(...movieRoutes);
    
    // Add Category pages
    const categoriesData = await fetchApi('/categories').catch(() => null);
    const categories = (categoriesData || []).filter((c: any) => c.is_active !== false); // fallback if is_active is undefined
    
    const categoryRoutes: MetadataRoute.Sitemap = categories.map((cat: any) => ({
      url: `${BASE_URL}/category/${cat.id}`,
      lastModified: new Date(),
      changeFrequency: 'weekly',
      priority: 0.6,
    }));
    
    routes.push(...categoryRoutes);

  } catch (error) {
    console.error("Error generating sitemap:", error);
  }

  // TODO: When Movie Details page is created (/movie/[code]/page.tsx), 
  // remember to use generateMetadata() inside that page to dynamically set og:title, og:image, etc.

  return routes;
}
