"use client";

import { useEffect, useState } from "react";
import { fetchApi } from "@/lib/api";

type PageItem = {
  id: number;
  title: string;
  slug: string;
  is_active: boolean;
};

export default function PagesPage() {
  const [pages, setPages] = useState<PageItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState({ title: "", slug: "", is_active: true });
  const [editingId, setEditingId] = useState<number | null>(null);

  useEffect(() => {
    loadPages();
  }, []);

  const loadPages = async () => {
    try {
      const data = await fetchApi("/pages");
      if (data && data.items) {
          setPages(data.items);
      } else if (Array.isArray(data)) {
          setPages(data);
      } else {
          setPages([]);
      }
    } catch (e: any) {
      alert("Xato: " + e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingId) {
        await fetchApi(`/pages/${editingId}`, {
          method: "PUT",
          body: JSON.stringify(form),
        });
      } else {
        await fetchApi("/pages", {
          method: "POST",
          body: JSON.stringify(form),
        });
      }
      setForm({ title: "", slug: "", is_active: true });
      setEditingId(null);
      loadPages();
    } catch (e: any) {
      alert("Saqlashda xato: " + e.message);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("O'chirilsinmi?")) return;
    try {
      await fetchApi(`/pages/${id}`, { method: "DELETE" });
      loadPages();
    } catch (e: any) {
      alert("O'chirishda xato: " + e.message);
    }
  };

  const handleEdit = (p: PageItem) => {
    setEditingId(p.id);
    setForm({ title: p.title, slug: p.slug, is_active: p.is_active });
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  if (loading) return <div className="p-8 text-center text-text-secondary">Yuklanmoqda...</div>;

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-text-primary tracking-tight">Sahifalar</h1>
          <p className="text-xs sm:text-sm text-text-secondary mt-1">Botdagi to'plamlar va bo'lim sahifalarini boshqarish</p>
        </div>
      </div>
      
      {/* Form Card */}
      <div className="metric-card p-4 sm:p-6 rounded-2xl mb-8">
        <h2 className="text-lg sm:text-xl font-semibold mb-4 text-text-primary flex items-center gap-2">
          <span className="material-symbols-outlined text-primary-container">
            {editingId ? "edit" : "add_circle"}
          </span>
          {editingId ? "Sahifani tahrirlash" : "Yangi Sahifa qo'shish"}
        </h2>

        <form onSubmit={handleSubmit} className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4 items-end">
          <div>
            <label className="block text-xs sm:text-sm font-medium text-text-secondary mb-1">Nomi (Sarlavha)</label>
            <input 
              required 
              type="text" 
              className="w-full bg-surface-container-lowest border border-white/10 rounded-xl p-3 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container text-sm" 
              value={form.title} 
              onChange={e => setForm({...form, title: e.target.value})} 
              placeholder="Masalan: Top 10 Kinolar"
            />
          </div>

          <div>
            <label className="block text-xs sm:text-sm font-medium text-text-secondary mb-1">Slug</label>
            <input 
              required 
              type="text" 
              className="w-full bg-surface-container-lowest border border-white/10 rounded-xl p-3 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container text-sm" 
              value={form.slug} 
              onChange={e => setForm({...form, slug: e.target.value})} 
              placeholder="top-10"
            />
          </div>

          <div className="flex items-center h-[48px]">
            <label className="flex items-center text-text-primary cursor-pointer bg-surface-container-lowest border border-white/10 px-3.5 py-2.5 rounded-xl text-xs sm:text-sm w-full min-h-[44px]">
              <input 
                type="checkbox" 
                className="mr-2.5 w-4 h-4 rounded border-white/10 bg-surface-container-lowest focus:ring-primary-container text-primary-container" 
                checked={form.is_active} 
                onChange={e => setForm({...form, is_active: e.target.checked})} 
              />
              Faol sahifa
            </label>
          </div>

          <div className="flex gap-2 w-full">
            <button 
              type="submit" 
              className="flex-1 bg-primary-container text-white px-5 py-3 rounded-xl hover:scale-[1.02] active:scale-95 transition-all text-sm font-medium min-h-[44px] text-center"
            >
              {editingId ? "Saqlash" : "Qo'shish"}
            </button>
            {editingId && (
              <button 
                type="button" 
                onClick={() => { setEditingId(null); setForm({title: "", slug: "", is_active: true}); }} 
                className="bg-white/5 border border-white/10 text-text-primary px-4 py-3 rounded-xl hover:bg-white/10 active:scale-95 text-sm font-medium transition-all min-h-[44px]"
              >
                Bekor
              </button>
            )}
          </div>
        </form>
      </div>

      {/* Pages Table */}
      <div className="metric-card rounded-2xl overflow-hidden shadow-xl">
        <div className="p-4 sm:p-5 border-b border-white/5 bg-[#1a0908]/80 flex items-center justify-between">
          <h3 className="font-display font-bold text-base sm:text-lg text-text-primary">Sahifalar ro'yxati ({pages.length})</h3>
        </div>

        <div className="overflow-x-auto custom-scrollbar">
          <table className="min-w-[550px] w-full text-left border-collapse">
            <thead className="bg-surface-container-lowest border-b border-white/10">
              <tr>
                <th className="px-4 sm:px-6 py-3.5 text-xs font-semibold text-text-secondary uppercase tracking-wider">ID</th>
                <th className="px-4 sm:px-6 py-3.5 text-xs font-semibold text-text-secondary uppercase tracking-wider">Nomi</th>
                <th className="px-4 sm:px-6 py-3.5 text-xs font-semibold text-text-secondary uppercase tracking-wider">Slug</th>
                <th className="px-4 sm:px-6 py-3.5 text-xs font-semibold text-text-secondary uppercase tracking-wider">Holati</th>
                <th className="px-4 sm:px-6 py-3.5 text-right text-xs font-semibold text-text-secondary uppercase tracking-wider">Amallar</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5 text-sm">
              {pages.map(p => (
                <tr key={p.id} className="data-table-row">
                  <td className="px-4 sm:px-6 py-4 whitespace-nowrap text-text-secondary font-mono text-xs">#{p.id}</td>
                  <td className="px-4 sm:px-6 py-4 whitespace-nowrap text-text-primary font-medium">{p.title}</td>
                  <td className="px-4 sm:px-6 py-4 whitespace-nowrap text-text-secondary text-xs font-mono">{p.slug}</td>
                  <td className="px-4 sm:px-6 py-4 whitespace-nowrap">
                    <span className={`px-2.5 py-1 inline-flex text-xs leading-4 font-bold rounded-full ${p.is_active ? 'bg-primary-container/20 text-primary-container border border-primary-container/30' : 'bg-surface-container-high text-text-secondary border border-white/10'}`}>
                      {p.is_active ? 'Faol' : 'Nofaol'}
                    </span>
                  </td>
                  <td className="px-4 sm:px-6 py-4 whitespace-nowrap text-right">
                    <div className="flex items-center justify-end gap-2">
                      <button onClick={() => handleEdit(p)} className="text-xs bg-white/5 border border-white/10 hover:bg-white/15 text-text-primary px-3 py-1.5 rounded-lg transition-colors min-h-[32px]">
                        Tahrirlash
                      </button>
                      <button onClick={() => handleDelete(p.id)} className="text-xs bg-red-500/10 border border-red-500/20 hover:bg-red-500/20 text-red-400 px-3 py-1.5 rounded-lg transition-colors min-h-[32px]">
                        O'chirish
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {pages.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-text-secondary">Hech qanday sahifa topilmadi</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
