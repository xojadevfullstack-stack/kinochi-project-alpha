"use client";

import { useState, useEffect } from "react";
import { fetchApi } from "@/lib/api";

interface BlacklistItem {
  id: number;
  title: string | null;
  url: string | null;
  reason: string | null;
  created_at: string;
}

export default function BlacklistPage() {
  const [items, setItems] = useState<BlacklistItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [total, setTotal] = useState(0);

  // Modal
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [formTitle, setFormTitle] = useState("");
  const [formUrl, setFormUrl] = useState("");
  const [formReason, setFormReason] = useState("Ichi bo'sh / buzilgan element");
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  const fetchBlacklist = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (search.trim()) params.append("q", search.trim());
      params.append("limit", "100");

      const res = await fetchApi(`/blacklist?${params.toString()}`);
      setItems(res.items || []);
      setTotal(res.total || 0);
    } catch (e: any) {
      console.error("Error fetching blacklist:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBlacklist();
  }, [search]);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formTitle.trim() && !formUrl.trim()) {
      setErrorMsg("Kino nomi yoki URL havolasini kiritishingiz shart.");
      return;
    }

    try {
      setSubmitting(true);
      setErrorMsg("");
      await fetchApi("/blacklist", {
        method: "POST",
        body: JSON.stringify({
          title: formTitle.trim() || null,
          url: formUrl.trim() || null,
          reason: formReason.trim() || "Ichi bo'sh serial",
        }),
      });

      setIsModalOpen(false);
      setFormTitle("");
      setFormUrl("");
      setFormReason("Ichi bo'sh / buzilgan element");
      fetchBlacklist();
    } catch (err: any) {
      setErrorMsg(err.message || "Xatolik yuz berdi");
    } finally {
      setSubmitting(false);
    }
  };

  const handleRemove = async (id: number, title: string | null) => {
    if (!confirm(`Haqiqatan ham "${title || id}" ni qora ro'yxatdan chiqarmoqchimisiz?`)) {
      return;
    }
    try {
      await fetchApi(`/blacklist/${id}`, { method: "DELETE" });
      fetchBlacklist();
    } catch (err: any) {
      alert("O'chirishda xatolik: " + (err.message || "Noma'lum"));
    }
  };

  return (
    <div className="p-6 sm:p-8 space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <span className="material-symbols-outlined text-rose-400 text-3xl">block</span>
              <h1 className="text-2xl sm:text-3xl font-bold text-white">Qora Ro'yxat (Blacklist)</h1>
            </div>
            <p className="text-sm text-gray-400 mt-1">
              Scraper va Parser ushbu ro'yxatdagi kino va bo'sh seriallarni e'tiborsiz qoldiradi (skip qiladi).
            </p>
          </div>

          <button
            onClick={() => setIsModalOpen(true)}
            className="flex items-center gap-2 px-4 py-2.5 bg-rose-600 hover:bg-rose-500 text-white rounded-xl font-medium transition-colors shadow-lg shadow-rose-900/30"
          >
            <span className="material-symbols-outlined text-xl">add</span>
            <span>Taqiq Qo'shish</span>
          </button>
        </div>

        {/* Search & Stats */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 bg-surface-container-high/40 p-4 rounded-2xl border border-white/5">
          <div className="relative w-full sm:w-96">
            <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-xl">
              search
            </span>
            <input
              type="text"
              placeholder="Nom, URL yoki sabab bo'yicha qidirish..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-surface-container-lowest/80 border border-white/10 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-rose-500 text-sm"
            />
          </div>
          <div className="text-sm text-gray-400 font-medium">
            Jami taqiqlanganlar: <span className="text-rose-400 font-bold">{total}</span> ta
          </div>
        </div>

        {/* Table */}
        <div className="bg-surface-container-lowest border border-white/5 rounded-2xl overflow-hidden shadow-xl">
          {loading ? (
            <div className="py-20 flex flex-col items-center justify-center text-gray-400 space-y-3">
              <div className="w-8 h-8 border-2 border-rose-500 border-t-transparent rounded-full animate-spin" />
              <p>Qora ro'yxat yuklanmoqda...</p>
            </div>
          ) : items.length === 0 ? (
            <div className="py-20 flex flex-col items-center justify-center text-gray-400 space-y-3">
              <span className="material-symbols-outlined text-5xl text-gray-600">check_circle</span>
              <p className="text-base font-medium">Qora ro'yxat hozircha bo'sh.</p>
              <p className="text-xs text-gray-500">Xato qilayotgan bo'sh seriallarni qo'shishingiz mumkin.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-white/5 bg-white/[0.02] text-xs font-semibold text-gray-400 uppercase tracking-wider">
                    <th className="py-3.5 px-4">#ID</th>
                    <th className="py-3.5 px-4">Kino / Serial Nomi</th>
                    <th className="py-3.5 px-4">URL Manzil</th>
                    <th className="py-3.5 px-4">Sababi</th>
                    <th className="py-3.5 px-4">Sana</th>
                    <th className="py-3.5 px-4 text-right">Amal</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5 text-sm text-gray-300">
                  {items.map((item) => (
                    <tr key={item.id} className="hover:bg-white/[0.02] transition-colors">
                      <td className="py-3.5 px-4 font-mono text-xs text-gray-500">#{item.id}</td>
                      <td className="py-3.5 px-4 font-medium text-white">
                        {item.title ? (
                          <div className="flex items-center gap-2">
                            <span className="material-symbols-outlined text-rose-400 text-base">block</span>
                            <span>{item.title}</span>
                          </div>
                        ) : (
                          <span className="text-gray-500 italic">Barcha nomlar</span>
                        )}
                      </td>
                      <td className="py-3.5 px-4">
                        {item.url ? (
                          <a
                            href={item.url}
                            target="_blank"
                            rel="noreferrer"
                            className="text-blue-400 hover:underline max-w-xs truncate block text-xs"
                          >
                            {item.url}
                          </a>
                        ) : (
                          <span className="text-gray-600">—</span>
                        )}
                      </td>
                      <td className="py-3.5 px-4">
                        <span className="inline-block px-2.5 py-1 rounded-full text-xs font-medium bg-rose-500/10 text-rose-300 border border-rose-500/20">
                          {item.reason || "Buzilgan / bo'sh"}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-xs text-gray-500">
                        {new Date(item.created_at).toLocaleDateString("uz-UZ")}
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        <button
                          onClick={() => handleRemove(item.id, item.title)}
                          className="px-3 py-1.5 rounded-lg bg-white/5 hover:bg-emerald-500/20 text-gray-300 hover:text-emerald-400 text-xs font-medium transition-colors"
                          title="Qora ro'yxatdan chiqarish"
                        >
                          Oq ro'yxatga qaytarish
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Modal */}
        {isModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
            <div className="bg-surface-container-high border border-white/10 rounded-2xl w-full max-w-md p-6 space-y-5 shadow-2xl">
              <div className="flex items-center justify-between border-b border-white/10 pb-4">
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  <span className="material-symbols-outlined text-rose-400">block</span>
                  Yangi Taqiqlangan Kontent
                </h3>
                <button
                  onClick={() => setIsModalOpen(false)}
                  className="p-1 rounded-lg text-gray-400 hover:text-white"
                >
                  <span className="material-symbols-outlined">close</span>
                </button>
              </div>

              {errorMsg && (
                <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs">
                  {errorMsg}
                </div>
              )}

              <form onSubmit={handleAdd} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-gray-300 uppercase mb-1">
                    Kino / Serial Nomi
                  </label>
                  <input
                    type="text"
                    placeholder="Masalan: Tokyo Ghoul yoki Odisseya"
                    value={formTitle}
                    onChange={(e) => setFormTitle(e.target.value)}
                    className="w-full px-3.5 py-2.5 bg-surface-container-lowest border border-white/10 rounded-xl text-white text-sm focus:outline-none focus:border-rose-500"
                  />
                  <span className="text-[11px] text-gray-500 mt-1 block">
                    Scraper ushbu nomdagi har qanday sahifani chetlab o'tadi.
                  </span>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-gray-300 uppercase mb-1">
                    URL Havolasi (Ixtiyoriy)
                  </label>
                  <input
                    type="text"
                    placeholder="https://uzmovi.net/..."
                    value={formUrl}
                    onChange={(e) => setFormUrl(e.target.value)}
                    className="w-full px-3.5 py-2.5 bg-surface-container-lowest border border-white/10 rounded-xl text-white text-sm focus:outline-none focus:border-rose-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-gray-300 uppercase mb-1">
                    Taqiqlash Sababi
                  </label>
                  <select
                    value={formReason}
                    onChange={(e) => setFormReason(e.target.value)}
                    className="w-full px-3.5 py-2.5 bg-surface-container-lowest border border-white/10 rounded-xl text-white text-sm focus:outline-none focus:border-rose-500"
                  >
                    <option value="Ichi bo'sh serial (qismlar yo'q)">Ichi bo'sh serial (qismlar yo'q)</option>
                    <option value="Buzilgan pleer / video yo'q">Buzilgan pleer / video yo'q</option>
                    <option value="Keraksiz reklama / soxta kontent">Keraksiz reklama / soxta kontent</option>
                    <option value="Admin tomonidan bloklangan">Admin tomonidan bloklangan</option>
                  </select>
                </div>

                <div className="flex items-center justify-end gap-3 pt-3">
                  <button
                    type="button"
                    onClick={() => setIsModalOpen(false)}
                    className="px-4 py-2 rounded-xl text-sm font-medium text-gray-400 hover:text-white hover:bg-white/5"
                  >
                    Bekor qilish
                  </button>
                  <button
                    type="submit"
                    disabled={submitting}
                    className="px-5 py-2 rounded-xl text-sm font-semibold bg-rose-600 hover:bg-rose-500 text-white transition-colors disabled:opacity-50"
                  >
                    {submitting ? "Saqlanmoqda..." : "Qora Ro'yxatga Qo'shish"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </AdminShell>
  );
}
