const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export async function fetchApi(endpoint: string, options: RequestInit = {}) {
  const url = `${API_URL}${endpoint}`;
  
  // Public website endpoints shouldn't need credentials generally, but we can set defaults.
  const defaultOptions: RequestInit = {
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    // Adding Next.js revalidation cache control
    next: { revalidate: 60 }, // Cache for 60 seconds
    ...options,
  };

  const res = await fetch(url, defaultOptions);
  
  if (!res.ok) {
    let errorMsg = "API Error";
    try {
      const errorData = await res.json();
      errorMsg = errorData.detail || errorMsg;
    } catch (e) {}
    throw new Error(errorMsg);
  }
  
  return res.json();
}
