export const SEGMENT_LABELS = {
  movies: "Kinolar",
  movie: "Film",
  series: "Seriallar",
  anime: "Animelar",
  doramas: "Doramalar",
  cartoons: "Multfilmlar",
  catalog: "Katalog & Bo'limlar",
  category: "Bo'lim",
  collections: "Xronologiyalar",
  requests: "Buyurtma berish",
  tv: "Jonli TV",
  premieres: "Premyeralar",
  top100: "TOP 100",
  subscriptions: "Obunalar",
  profile: "Profil",
  history: "Ko'rish tarixi",
  notifications: "Bildirishnomalar",
  actors: "Aktyorlar",
  achievements: "Yutuqlar",
  search: "Qidiruv",
  p: "Sahifa",
  legal: "Ma'lumot",
  rules: "Foydalanish qoidalari",
  dmca: "Mualliflik huquqi (DMCA)",
  privacy: "Maxfiylik siyosati",
  about: "Reklama va hamkorlik",
  go: "Tezkor kod",
  "test-auth": "Kirish",
};

/**
 * Normalize a pathname for reliable breadcrumb label lookup across encoded/unencoded URLs.
 *
 * @param {string} path
 * @returns {string}
 */
export function normalizeBreadcrumbPath(path) {
  if (!path) return "/";
  const clean = String(path).split(/[?#]/)[0];
  let decoded = clean;
  try {
    decoded = decodeURIComponent(clean);
  } catch {
    decoded = clean;
  }
  const trimmed = decoded.replace(/\/+$/, "");
  return trimmed || "/";
}

/**
 * Format a fallback label for a URL segment when no explicit title override exists.
 *
 * @param {string} segment
 * @param {string | undefined} prevSegment
 * @returns {string}
 */
export function formatSegmentLabel(segment, prevSegment) {
  if (SEGMENT_LABELS[segment]) return SEGMENT_LABELS[segment];
  try {
    const decoded = decodeURIComponent(segment);
    if (prevSegment === "movie") return `#${decoded}`;
    return decoded
      .replace(/[-_]+/g, " ")
      .replace(/\b\w/g, (ch) => ch.toUpperCase());
  } catch {
    return segment;
  }
}

/**
 * Build breadcrumb items for a pathname, applying matching route title overrides.
 *
 * @param {string} pathname
 * @param {Record<string, string>} [overrides]
 * @returns {Array<{ label: string; href: string; isLast: boolean }>}
 */
export function buildBreadcrumbs(pathname, overrides = {}) {
  const normalizedFull = normalizeBreadcrumbPath(pathname);
  if (!normalizedFull || normalizedFull === "/") return [];

  const rawSegments = pathname.split(/[?#]/)[0].split("/").filter(Boolean);
  if (rawSegments.length === 0) return [];

  const normalizedOverrides = {};
  for (const [key, val] of Object.entries(overrides || {})) {
    if (val && String(val).trim()) {
      normalizedOverrides[normalizeBreadcrumbPath(key)] = String(val).trim();
    }
  }

  return rawSegments.map((seg, idx) => {
    const href = "/" + rawSegments.slice(0, idx + 1).join("/");
    const resolvedHref =
      seg === "legal"
        ? "/legal/rules"
        : seg === "movie" || seg === "category" || seg === "p"
        ? "/catalog"
        : href;

    const overrideLabel = normalizedOverrides[normalizeBreadcrumbPath(href)];
    return {
      label: overrideLabel || formatSegmentLabel(seg, rawSegments[idx - 1]),
      href: resolvedHref,
      isLast: idx === rawSegments.length - 1,
    };
  });
}
