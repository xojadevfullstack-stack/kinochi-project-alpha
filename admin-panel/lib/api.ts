const BASE_API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
const RENDER_BASE_URL = BASE_API_URL.replace(/\/api\/v1\/?$/, "");
const API_URL = BASE_API_URL;
const DIRECT_API_URL = BASE_API_URL;

export const HEALTH_URL = `${RENDER_BASE_URL}/health`;

async function getOrRefreshToken(): Promise<string | null> {
  if (typeof window === "undefined") return null;
  let token = localStorage.getItem("access_token");
  if (!token) {
    try {
      const storedRefreshToken = localStorage.getItem("refresh_token");
      const refreshHeaders: Record<string, string> = { "Content-Type": "application/json" };
      if (storedRefreshToken) {
        refreshHeaders["X-Refresh-Token"] = storedRefreshToken;
      }
      const refreshRes = await fetch(`${API_URL}/auth/refresh`, {
        method: "POST",
        credentials: "include",
        headers: refreshHeaders,
      });
      if (refreshRes.ok) {
        const refreshData = await refreshRes.json();
        if (refreshData.access_token) {
          token = refreshData.access_token;
          localStorage.setItem("access_token", token as string);
          document.cookie = `access_token=${token}; path=/; max-age=${30 * 24 * 60 * 60}; samesite=lax`;
          if (refreshData.refresh_token) {
            localStorage.setItem("refresh_token", refreshData.refresh_token);
          }
        }
      }
    } catch (e) {}
  }
  return token;
}

export async function fetchApi(endpoint: string, options: RequestInit = {}) {
  const url = `${API_URL}${endpoint}`;
  
  const defaultHeaders: any = {
    "Content-Type": "application/json",
  };

  const token = await getOrRefreshToken();

  const headers: any = {
    ...defaultHeaders,
    ...options.headers,
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  if (options.body instanceof FormData) {
    delete headers["Content-Type"];
  }

  let response: Response;
  try {
    response = await fetch(url, {
      ...options,
      credentials: "include",
      headers,
    });
  } catch (networkError: any) {
    console.error("fetchApi network error:", networkError);
    // "Failed to fetch" — server o'chiq yoki internet yo'q
    throw new Error("Server bilan ulanib bo'lmadi. Backend server ishlaydimi? Bir oz kuting va qayta urinib ko'ring.");
  }

  if (!response.ok) {
    let errorMsg = `Server xatosi: ${response.status} ${response.statusText}`;
    try {
      const data = await response.json();
      if (data.detail) {
          errorMsg = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail);
      }
    } catch (e) {
      // Ignore JSON parse error
    }
    throw new Error(errorMsg);
  }

  // 204 No Content for successful deletes usually
  if (response.status === 204) return null;

  return response.json();
}

/**
 * Katta fayllarni (video, rasm) yuklash uchun maxsus funksiya.
 * Vercel'ning 4.5MB chegarasini chetlab o'tib, to'g'ridan-to'g'ri
 * Backend'ga yuboradi.
 */
export async function fetchApiUpload(endpoint: string, options: RequestInit = {}) {
  const url = `${DIRECT_API_URL}${endpoint}`;
  const token = await getOrRefreshToken();

  const headers: any = { ...(options.headers || {}) };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorMsg = `Error: ${response.status} ${response.statusText}`;
    try {
      const data = await response.json();
      if (data.detail) {
          errorMsg = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail);
      }
    } catch (e) {
      // Ignore JSON parse error
    }
    throw new Error(errorMsg);
  }

  if (response.status === 204) return null;

  return response.json();
}

/**
 * Katta fayllarni yuklash uchun XHR asosidagi funksiya (Progress bar bilan)
 */
export function uploadWithProgress(
  endpoint: string, 
  file: File, 
  onProgress: (percent: number) => void,
  additionalData?: Record<string, string>
): Promise<any> {
  return new Promise(async (resolve, reject) => {
    const url = `${DIRECT_API_URL}${endpoint}`;
    const token = await getOrRefreshToken();

    const xhr = new XMLHttpRequest();
    xhr.open("POST", url, true);
    
    // CORS uchun cookie va header yuborish
    xhr.withCredentials = true;
    
    // Video upload uchun timeout: 5 daqiqa (300 000 ms)
    xhr.timeout = 300_000;
    
    if (token) {
      xhr.setRequestHeader("Authorization", `Bearer ${token}`);
    }

    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) {
        const percentComplete = Math.round((event.loaded / event.total) * 100);
        onProgress(percentComplete);
      }
    };

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          resolve(JSON.parse(xhr.responseText));
        } catch(e) {
          resolve(xhr.responseText);
        }
      } else {
        let errorMsg = `Server xatosi: ${xhr.status} ${xhr.statusText}`;
        try {
          const data = JSON.parse(xhr.responseText);
          if (data.detail) {
            errorMsg = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail);
          }
        } catch(e) {}
        reject(new Error(errorMsg));
      }
    };

    xhr.onerror = () => {
      reject(new Error(
        "Server bilan ulanib bo'lmadi. Backend server ishlayotganligini tekshiring."
      ));
    };
    
    xhr.ontimeout = () => {
      reject(new Error(
        "Upload vaqti tugadi (5 daqiqa). Fayl hajmi juda katta yoki internet sekin bo'lishi mumkin."
      ));
    };

    const formData = new FormData();
    formData.append("file", file);
    if (additionalData) {
      for (const key in additionalData) {
        formData.append(key, additionalData[key]);
      }
    }
    xhr.send(formData);
  });
}
