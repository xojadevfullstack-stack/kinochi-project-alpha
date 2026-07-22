"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

const API_URL = "https://kinochi-project-alpha.onrender.com/api/v1";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  // Vercel/Render free tier muammosi: server uxlab qolgan bo'lsa uyg'otish uchun
  // sahifa ochilgandayoq fonda ping jo'natamiz.
  useEffect(() => {
    fetch(`${API_URL}/health`).catch(() => {});
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
          setError("Server uyqudan uyg'onmoqda... Yana bir marta 'Kirish' tugmasini bosing.");
          return;
        }
        const data = await res.json().catch(() => ({}));
        setError(data.detail || "Tizimga kirishda xatolik yuz berdi");
        return;
      }

      const data = await res.json();
      if (data.access_token) {
        localStorage.setItem("access_token", data.access_token);
        // Middleware uchun cookieni Vercel domenida o'rnatamiz
        document.cookie = `access_token=${data.access_token}; path=/; max-age=${30 * 24 * 60 * 60}; samesite=lax`;
      }

      router.push("/");
    } catch (err) {
      setError("Serverga ulanib bo'lmadi");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-surface-container-lowest">
      <div className="metric-card p-8 rounded-xl shadow-lg w-full max-w-md border border-white/5">
        <div className="text-center mb-8">
          <div className="w-16 h-16 mx-auto rounded-full border-2 border-primary-container bg-surface-container-high flex justify-center items-center mb-4">
             <span className="material-symbols-outlined text-primary-container text-3xl">admin_panel_settings</span>
          </div>
          <h1 className="text-3xl font-bold text-primary-container">Kinochi Admin</h1>
          <p className="text-text-secondary mt-2 font-medium">Boshqaruv paneliga kirish</p>
        </div>

        {error && (
          <div className="bg-red-500/10 border border-red-500/20 text-red-400 px-4 py-3 rounded-lg mb-6 text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-1">Email</label>
            <input
              type="email"
              required
              className="w-full bg-surface-container-lowest border border-white/10 rounded-lg p-3 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container outline-none transition"
              placeholder="admin@kinochi.uz"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-text-secondary mb-1">Parol</label>
            <input
              type="password"
              required
              className="w-full bg-surface-container-lowest border border-white/10 rounded-lg p-3 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container outline-none transition"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className={`w-full py-3 rounded-lg font-semibold transition-all duration-300 ${loading ? 'bg-primary-container/50 text-white cursor-not-allowed' : 'bg-primary-container text-white hover:scale-105'}`}
          >
            {loading ? "Yuklanmoqda..." : "Kirish"}
          </button>
        </form>
      </div>
    </div>
  );
}
