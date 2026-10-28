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
