/**
 * Utility functions for 18+ adult content detection.
 * Safe to use in both Server and Client Components.
 */

export function isAdultContent(item: any): boolean {
  if (!item) return false;

  // Direct boolean flag
  if (item.is_18_plus === true) {
    return true;
  }

  // Check categories array (objects or strings)
  if (Array.isArray(item.categories)) {
    for (const cat of item.categories) {
      const name = (typeof cat === "string" ? cat : cat?.name || cat?.slug || "").toLowerCase();
      if (
        name.includes("18+") ||
        name.includes("18-plus") ||
        name.includes("kattalar") ||
        name.includes("adult") ||
        name.includes("erotika") ||
        name.includes("ecchi") ||
        name.includes("hentai")
      ) {
        return true;
      }
    }
  }

  // Check genres string (e.g. "Anime, Drama, 18+")
  if (typeof item.genres === "string") {
    const genresLower = item.genres.toLowerCase();
    const adultKeywords = ["18+", "erotika", "erotik", "ecchi", "hentai", "kattalar", "adult"];
    for (const kw of adultKeywords) {
      if (genresLower.includes(kw)) {
        return true;
      }
    }
  }

  return false;
}
