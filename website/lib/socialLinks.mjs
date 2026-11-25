/**
 * Build sanitized ordered list of active social/community links for Footer & Sidebar.
 */
export function isSafeHttpUrl(raw) {
  if (typeof raw !== "string") return false;
  const trimmed = raw.trim();
  return trimmed.startsWith("https://") || trimmed.startsWith("http://");
}

export function buildSocialItems(botUsername = "MediaPlusOfficialBot", socialLinks = {}) {
  const cleanBot = String(botUsername || "MediaPlusOfficialBot").trim().replace(/^@+/, "");
  const botUrl = isSafeHttpUrl(socialLinks?.telegram_bot)
    ? socialLinks.telegram_bot.trim()
    : `https://t.me/${cleanBot}`;

  const specs = [
    { key: "telegram_bot", label: "Telegram Bot", href: botUrl },
    { key: "telegram_channel", label: "Kanal", href: socialLinks?.telegram_channel },
    { key: "instagram", label: "Instagram", href: socialLinks?.instagram },
    { key: "youtube", label: "YouTube", href: socialLinks?.youtube },
    { key: "facebook", label: "Facebook", href: socialLinks?.facebook },
    { key: "tiktok", label: "TikTok", href: socialLinks?.tiktok },
  ];

  return specs
    .filter((item) => isSafeHttpUrl(item.href))
    .map((item) => ({ ...item, href: item.href.trim() }));
}
