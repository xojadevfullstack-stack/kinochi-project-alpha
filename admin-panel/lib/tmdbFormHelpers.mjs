/**
 * Normalize a raw TMDb ID input value into a positive integer or null.
 * Prevents sending 0, negative numbers, or empty strings to the backend.
 *
 * @param {number | string | null | undefined} value
 * @returns {number | null}
 */
export function normalizeTmdbId(value) {
  if (value === null || value === undefined) return null;
  const trimmed = String(value).trim();
  if (!trimmed || !/^\d+$/.test(trimmed)) return null;
  const parsed = Number.parseInt(trimmed, 10);
  return Number.isSafeInteger(parsed) && parsed > 0 ? parsed : null;
}

/**
 * Filter out the currently edited movie/series from /content-lookup/duplicates results
 * so editing an item does not warn that it duplicates itself.
 *
 * @param {{ exact?: any[]; similar?: any[] } | null | undefined} dupRes
 * @param {number | null | undefined} editingId
 * @param {"movie" | "series"} contentType
 * @returns {{ exact: any[]; similar: any[] } | null}
 */
export function filterDuplicateResults(dupRes, editingId, contentType) {
  if (!dupRes) return null;
  const isSelf = (item) =>
    Boolean(editingId && item && item.type === contentType && item.id === editingId);
  const exact = Array.isArray(dupRes.exact) ? dupRes.exact.filter((d) => !isSelf(d)) : [];
  const similar = Array.isArray(dupRes.similar) ? dupRes.similar.filter((s) => !isSelf(s)) : [];
  if (exact.length === 0 && similar.length === 0) return null;
  return { exact, similar };
}

/**
 * Merge fetched TMDb metadata into the current movie or series form state.
 * When fillEmptyOnly is true, non-empty existing form values are preserved.
 *
 * @template {Record<string, any>} T
 * @param {T} prev
 * @param {Record<string, any>} incoming
 * @param {{ fillEmptyOnly?: boolean }} [options]
 * @returns {T}
 */
export function mergeTmdbDetails(prev, incoming, options = {}) {
  const fillEmptyOnly = Boolean(options.fillEmptyOnly);
  const next = { ...prev };

  const stringFields = [
    "title",
    "description",
    "poster_url",
    "trailer_url",
    "genres",
    "director",
    "cast",
  ];

  for (const field of stringFields) {
    if (!(field in prev)) continue;
    const prevText = String(prev[field] ?? "").trim();
    if (fillEmptyOnly && prevText.length > 0) continue;
    if (field === "title" && incoming.isTitleTranslated === false && prevText.length > 0) {
      continue;
    }
    if (
      field === "description" &&
      incoming.isDescriptionTranslated === false &&
      prevText.length > 0
    ) {
      continue;
    }
    if (incoming[field]) {
      next[field] = incoming[field];
    }
  }

  if ("release_year" in prev && incoming.release_year) {
    if (!fillEmptyOnly || !prev.release_year) {
      next.release_year = incoming.release_year;
    }
  }

  if ("duration_minutes" in prev && incoming.duration_minutes) {
    if (!fillEmptyOnly || !prev.duration_minutes) {
      next.duration_minutes = incoming.duration_minutes;
    }
  }

  if ("imdb_rating" in prev && incoming.imdb_rating !== undefined && incoming.imdb_rating !== null) {
    if (!fillEmptyOnly || !prev.imdb_rating || Number(prev.imdb_rating) <= 0) {
      next.imdb_rating = incoming.imdb_rating;
    }
  }

  if ("tmdb_id" in prev) {
    next.tmdb_id = normalizeTmdbId(incoming.tmdb_id) ?? normalizeTmdbId(prev.tmdb_id);
  }

  if ("category_ids" in prev) {
    const prevCats = Array.isArray(prev.category_ids) ? prev.category_ids : [];
    const incomingCats = Array.isArray(incoming.category_ids) ? incoming.category_ids : [];
    next.category_ids = Array.from(new Set([...prevCats, ...incomingCats]));
  }

  return next;
}
