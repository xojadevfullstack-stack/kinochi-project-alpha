const API_URL = "/api/v1";

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
