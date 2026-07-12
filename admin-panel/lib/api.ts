const API_URL = "/api/v1";
const DIRECT_API_URL = "https://kinochi-project-alpha.onrender.com/api/v1";

export async function fetchApi(endpoint: string, options: RequestInit = {}) {
  const url = `${API_URL}${endpoint}`;
  
  const defaultHeaders: any = {
    "Content-Type": "application/json",
  };

  const headers = {
    ...defaultHeaders,
    ...options.headers,
  };

  if (options.body instanceof FormData) {
    delete headers["Content-Type"];
  }

  const response = await fetch(url, {
    ...options,
    credentials: "include",
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

  // 204 No Content for successful deletes usually
  if (response.status === 204) return null;

  return response.json();
}

/**
 * Katta fayllarni (video, rasm) yuklash uchun maxsus funksiya.
 * Vercel'ning 4.5MB chegarasini chetlab o'tib, to'g'ridan-to'g'ri
 * Render'ga yuboradi.
 */
export async function fetchApiUpload(endpoint: string, options: RequestInit = {}) {
  const url = `${DIRECT_API_URL}${endpoint}`;

  // sessionStorage'dan tokenni olib, Authorization header'ga qo'shamiz
  const token = typeof window !== "undefined" ? sessionStorage.getItem("access_token") : null;
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
  return new Promise((resolve, reject) => {
    const url = `${DIRECT_API_URL}${endpoint}`;
    const token = typeof window !== "undefined" ? sessionStorage.getItem("access_token") : null;
    
    const xhr = new XMLHttpRequest();
    xhr.open("POST", url, true);
    
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
        let errorMsg = `Error: ${xhr.status} ${xhr.statusText}`;
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
      reject(new Error("Network Error occurred during upload"));
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

