const PROD_API_URL = "https://kinochi-project-alpha-9g6j.onrender.com/api/v1";
const DEV_API_URL = "http://127.0.0.1:8000/api/v1";

function resolveApiUrl(): string {
  const raw = process.env.NEXT_PUBLIC_API_URL?.trim();
  if (raw) {
    return raw.replace(
      "https://kinochi-project-alpha.onrender.com",
      "https://kinochi-project-alpha-9g6j.onrender.com"
    );
  }
  return process.env.NODE_ENV === "production" ? PROD_API_URL : DEV_API_URL;
}

export const API_URL = resolveApiUrl();
import { getToken, clearToken } from "./auth/tokenStorage";

export interface SocialLinks {
  telegram_bot?: string;
  telegram_channel?: string;
  instagram?: string;
  youtube?: string;
  facebook?: string;
  tiktok?: string;
}

export interface PublicConfig {
  bot_username: string;
  website_url: string;
  stream_enabled: boolean;
  social_links?: SocialLinks;
}

const FALLBACK_BOT_USERNAME = (process.env.NEXT_PUBLIC_BOT_USERNAME || "MediaPlusOfficialBot")
  .trim()
  .replace(/^@+/, "");

export const DEFAULT_SOCIAL_LINKS: SocialLinks = {
  telegram_bot: `https://t.me/${FALLBACK_BOT_USERNAME}`,
  telegram_channel: (process.env.NEXT_PUBLIC_CHANNEL_URL || "https://t.me/MediaPlusOfficial").trim(),
  instagram: (process.env.NEXT_PUBLIC_INSTAGRAM_URL || "https://www.instagram.com/mediaplusofficialbot/").trim(),
  youtube: (process.env.NEXT_PUBLIC_YOUTUBE_URL || "https://www.youtube.com/@MediaPlusOfficialbot").trim(),
  facebook: (process.env.NEXT_PUBLIC_FACEBOOK_URL || "https://www.facebook.com/profile.php?id=1321205927744639").trim(),
  tiktok: (process.env.NEXT_PUBLIC_TIKTOK_URL || "").trim(),
};

export async function getPublicConfig(): Promise<PublicConfig> {
  const fallback: PublicConfig = {
    bot_username: FALLBACK_BOT_USERNAME,
    website_url: "https://kinochi-project-alpha.vercel.app",
    stream_enabled: false,
    social_links: DEFAULT_SOCIAL_LINKS,
  };
  try {
    const res = await fetch(`${API_URL}/auth/public-config`, {
      next: { revalidate: 60 },
    });
    if (!res.ok) return fallback;
    const data = await res.json();
    const rawBot = typeof data?.bot_username === "string" ? data.bot_username.trim().replace(/^@+/, "") : "";
    const bot = rawBot || fallback.bot_username;
    const remoteLinks = data?.social_links && typeof data.social_links === "object" ? data.social_links : {};
    return {
      bot_username: bot,
      website_url: typeof data?.website_url === "string" && data.website_url ? data.website_url : fallback.website_url,
      stream_enabled: Boolean(data?.stream_enabled),
      social_links: {
        ...DEFAULT_SOCIAL_LINKS,
        ...remoteLinks,
        telegram_bot: `https://t.me/${bot}`,
      },
    };
  } catch {
    return fallback;
  }
}

export async function fetchApi(endpoint: string, options: RequestInit = {}) {
  const url = `${API_URL}${endpoint}`;
  
  // Get token and add to headers if exists
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string> || {}),
  };
  
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const defaultOptions: RequestInit = {
    headers,
    // Adding Next.js revalidation cache control
    next: { revalidate: 60 }, // Cache for 60 seconds
    ...options,
  };

  const res = await fetch(url, defaultOptions);
  
  if (!res.ok) {
    if (res.status === 401 && token) {
      clearToken();
      if (typeof window !== "undefined") {
        window.dispatchEvent(new Event("auth:unauthorized"));
      }
    }

    let errorMsg = "API Error";
    try {
      const errorData = await res.json();
      errorMsg = errorData.detail || errorMsg;
    } catch (e) {}
    throw new Error(errorMsg);
  }
  
  return res.json();
}
