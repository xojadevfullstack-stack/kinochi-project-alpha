export const SMM_STATUS_LABELS = {
  all: "Barchasi",
  generating: "Tayyorlanmoqda",
  waiting_approval: "Tasdiq kutmoqda",
  scheduled: "Navbatda",
  publishing: "Chiqarilmoqda",
  completed: "Chiqarilgan",
  failed: "Xatolik",
  rejected: "Rad etilgan",
};

export function cleanMediaCode(raw) {
  return String(raw || "").trim().replace(/^#+/, "");
}

export function formatSmmStatusLabel(status) {
  return SMM_STATUS_LABELS[status] || status;
}

export function shouldPollProgress(progress, jobs) {
  if (progress?.cycle1?.in_progress > 0) return true;
  if ((progress?.cycle2?.generating || 0) + (progress?.cycle2?.publishing || 0) > 0) return true;
  return Array.isArray(jobs) && jobs.some((j) => j?.status === "generating" || j?.status === "publishing");
}

export function isLatestRequest(reqSeq, latestSeq) {
  return reqSeq === latestSeq;
}
