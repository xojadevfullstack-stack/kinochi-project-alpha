"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
const HEALTH_URL = API_URL.replace(/\/api\/v1\/?$/, "") + "/health";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  // Free tier yoki uxlab qolgan serverni uyg'otish uchun sahifa ochilganda ping jo'natamiz
  useEffect(() => {
    fetch(HEALTH_URL).catch(() => {});
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const res = await fetch(`${API_URL}/auth/login`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      if (!res.ok) {
        if (res.status === 504 || res.status === 502) {
          setError("Server uyqudan uyg'onmoqda... Bir oz kutib, yana bir marta 'Kirish' tugmasini bosing.");
          return;
        }
        const data = await res.json().catch(() => ({}));
        setError(data.detail || "Email yoki parol noto'g'ri");
        return;
      }

      const data = await res.json();
      if (data.access_token) {
        localStorage.setItem("access_token", data.access_token);
        if (data.refresh_token) {
          localStorage.setItem("refresh_token", data.refresh_token);
        }
        document.cookie = `access_token=${data.access_token}; path=/; max-age=${30 * 24 * 60 * 60}; samesite=lax`;
      }

      router.push("/");
    } catch (err) {
      setError("Serverga ulanib bo'lmadi. Backend ishga tushirilganligini tekshiring.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-surface-container-lowest p-4 sm:p-6">
      <div className="metric-card p-6 sm:p-8 rounded-2xl shadow-2xl w-full max-w-md border border-white/10">
        <div className="text-center mb-6 sm:mb-8">
          <div className="w-14 h-14 sm:w-16 sm:h-16 mx-auto rounded-full border-2 border-primary-container bg-surface-container-high flex justify-center items-center mb-3 sm:mb-4">
             <span className="material-symbols-outlined text-primary-container text-2xl sm:text-3xl">admin_panel_settings</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-primary-container">Kinochi Admin</h1>
          <p className="text-xs sm:text-sm text-text-secondary mt-1 font-medium">Boshqaruv paneliga kirish</p>
        </div>

        {error && (
          <div className="bg-red-500/10 border border-red-500/20 text-red-400 px-4 py-3 rounded-xl mb-5 text-xs sm:text-sm leading-relaxed">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs sm:text-sm font-medium text-text-secondary mb-1">Email</label>
            <input
              type="email"
              required
              className="w-full bg-surface-container-lowest border border-white/10 rounded-xl p-3 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container outline-none transition text-sm min-h-[44px]"
              placeholder="admin@kinochi.uz"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>

          <div>
            <label className="block text-xs sm:text-sm font-medium text-text-secondary mb-1">Parol</label>
            <input
              type="password"
              required
              className="w-full bg-surface-container-lowest border border-white/10 rounded-xl p-3 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container outline-none transition text-sm min-h-[44px]"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className={`w-full py-3.5 rounded-xl font-semibold transition-all duration-200 text-sm min-h-[48px] mt-2 ${
              loading 
                ? 'bg-primary-container/50 text-white cursor-not-allowed' 
                : 'bg-primary-container text-white hover:scale-[1.02] active:scale-95'
            }`}
          >
            {loading ? "Yuklanmoqda..." : "Kirish"}
          </button>
        </form>
      </div>
    </div>
  );
}
