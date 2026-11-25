/**
 * Pure helper utilities for Admin Panel Analytics & TMDb Insights.
 */

export function computeBarHeightPct(value, maxValue) {
  const safeVal = Number(value) || 0;
  const safeMax = Number(maxValue) || 0;
  if (safeVal <= 0 || safeMax <= 0) return 0;
  return Math.max(4, Math.min(100, Math.round((safeVal / safeMax) * 100)));
}

export function computeSourceShare(botViews, webViews, streamViews) {
  const bot = Math.max(0, Number(botViews) || 0);
  const web = Math.max(0, Number(webViews) || 0);
  const stream = Math.max(0, Number(streamViews) || 0);
  const total = bot + web + stream;
  if (total === 0) {
    return { total: 0, botPct: 0, webPct: 0, streamPct: 0 };
  }
  const botPct = Math.round((bot / total) * 100);
  const webPct = Math.round((web / total) * 100);
  const streamPct = Math.max(0, 100 - botPct - webPct);
  return { total, botPct, webPct, streamPct };
}

export function summarizeTmdbCoverage(items) {
  const list = Array.isArray(items) ? items : [];
  let inLibrary = 0;
  let requested = 0;
  let missing = 0;
  for (const item of list) {
    if (item?.in_library) {
      inLibrary += 1;
    } else if (item?.is_requested) {
      requested += 1;
    } else {
      missing += 1;
    }
  }
  return { total: list.length, inLibrary, requested, missing };
}
