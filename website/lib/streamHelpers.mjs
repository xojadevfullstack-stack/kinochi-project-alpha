/**
 * Pure helper utilities for MTProto stream URL signing and browser playback fallback.
 */

export function getStreamableTranslations(translations) {
  if (!Array.isArray(translations)) return [];
  return translations
    .filter(
      (t) =>
        t &&
        Number.isInteger(Number(t.id)) &&
        Number(t.id) > 0 &&
        Number.isInteger(Number(t.storage_channel_message_id)) &&
        Number(t.storage_channel_message_id) > 0
    )
    .map((t) => ({
      id: Number(t.id),
      language: String(t.language || "").trim() || "Asl / Dublyaj",
      storage_channel_message_id: Number(t.storage_channel_message_id),
    }));
}

export function buildStreamSignEndpoint(mediaType, translationId) {
  const safeType = mediaType === "episode" ? "episode" : "movie";
  const safeId = Number(translationId);
  return `/stream/url?media_type=${encodeURIComponent(safeType)}&translation_id=${safeId}`;
}

export function mapStreamErrorToUzbek(statusOrCode) {
  if (statusOrCode === 503) {
    return "Sayt playeri hozircha texnik sozlanmoqda. Hozircha Telegram bot orqali ko'rishingiz mumkin.";
  }
  if (statusOrCode === 404) {
    return "Ushbu dublyaj uchun video fayl serverda topilmadi. Telegram bot orqali ko'ring.";
  }
  if (statusOrCode === "codec") {
    return "Brauzer ushbu video formatini (MKV/HEVC) ocholmadi. Telegram bot orqali muammosiz ko'rishingiz mumkin.";
  }
  return "Video oqimini yuklashda xatolik yuz berdi. Telegram bot orqali ko'rishingiz mumkin.";
}

export function saveContinueWatching(item, storage) {
  const target = storage || (typeof window !== "undefined" ? window.localStorage : null);
  if (!target || !item || item.id == null) return;
  try {
    const entry = {
      ...item,
      last_watched_at: item.last_watched_at || new Date().toISOString(),
    };
    const raw = target.getItem("mediaplus_continue_watching");
    let list = raw ? JSON.parse(raw) : [];
    if (!Array.isArray(list)) list = [];
    list = [entry, ...list.filter((x) => String(x?.id) !== String(entry.id))].slice(0, 10);
    target.setItem("mediaplus_continue_watching", JSON.stringify(list));
    if (typeof window !== "undefined") {
      window.dispatchEvent(new Event("mediaplus_continue_watching_updated"));
    }
  } catch {}
}
