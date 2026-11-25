/**
 * Pure helpers for LiveSearch & SearchClientView navigation and click tracking.
 */

export function getSearchResultHref(item) {
  if (!item) return "/";
  if (item.type === "movie") {
    return `/movie/${item.code}`;
  }
  if (item.type === "series") {
    const serialId = String(item.code || "").replace("s_", "") || item.id;
    return `/series/${serialId}`;
  }
  if (item.type === "collection") {
    return `/collections/${item.code}`;
  }
  return "/";
}

export function buildSearchTrackPayload(item) {
  if (!item || !item.id) return null;
  if (item.type === "movie" || item.type === "series") {
    return { media_type: item.type, item_id: Number(item.id) };
  }
  return null;
}

export function getDisplaySearchCode(item) {
  if (!item) return "";
  return item.short_code || item.code || "";
}
