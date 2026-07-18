"use client";

import { useEffect, useState } from "react";
import { fetchApi } from "@/lib/api";

type Category = {
  id: number;
  name: string;
  slug: string;
  is_active: boolean;
};

export default function CategoriesPage() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState({ name: "", slug: "", is_active: true });
  const [editingId, setEditingId] = useState<number | null>(null);

  useEffect(() => {
    loadCategories();
  }, []);

  const loadCategories = async () => {
    try {
      const data = await fetchApi("/categories/");
      setCategories(data);
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
        await fetchApi(`/categories/${editingId}`, {
          method: "PUT",
          body: JSON.stringify(form),
        });
      } else {
        await fetchApi("/categories/", {
          method: "POST",
          body: JSON.stringify(form),
        });
      }
      setForm({ name: "", slug: "", is_active: true });
      setEditingId(null);
      loadCategories();
    } catch (e: any) {
      alert("Saqlashda xato: " + e.message);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("O'chirilsinmi?")) return;
    try {
      await fetchApi(`/categories/${id}`, { method: "DELETE" });
      loadCategories();
    } catch (e: any) {
      alert("O'chirishda xato: " + e.message);
    }
  };

  const handleEdit = (c: Category) => {
    setEditingId(c.id);
    setForm({ name: c.name, slug: c.slug, is_active: c.is_active });
  };

  if (loading) return <div>Yuklanmoqda...</div>;

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-text-primary">Kategoriyalar</h1>
      </div>
      
      <div className="metric-card p-6 rounded-xl mb-8">
        <h2 className="text-xl font-semibold mb-4 text-text-primary">{editingId ? "Tahrirlash" : "Yangi Kategoriya"}</h2>
        <form onSubmit={handleSubmit} className="flex gap-4 items-end flex-wrap">
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-1">Nomi</label>
            <input required type="text" className="w-full bg-surface-container-lowest border border-white/10 rounded-lg p-2.5 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container" value={form.name} onChange={e => setForm({...form, name: e.target.value})} />
          </div>
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-1">Slug</label>
            <input required type="text" className="w-full bg-surface-container-lowest border border-white/10 rounded-lg p-2.5 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container" value={form.slug} onChange={e => setForm({...form, slug: e.target.value})} />
          </div>
          <div className="flex items-center h-[46px]">
            <label className="flex items-center text-text-secondary cursor-pointer">
              <input type="checkbox" className="mr-2 w-4 h-4 rounded border-white/10 bg-surface-container-lowest focus:ring-primary-container text-primary-container" checked={form.is_active} onChange={e => setForm({...form, is_active: e.target.checked})} />
              Faol
            </label>
          </div>
          <button type="submit" className="bg-primary-container text-white px-6 py-2.5 rounded-lg hover:scale-105 transition-all h-[46px] font-medium">
            Saqlash
          </button>
          {editingId && (
            <button type="button" onClick={() => { setEditingId(null); setForm({name: "", slug: "", is_active: true}) }} className="bg-white/5 border border-white/10 text-text-primary px-6 py-2.5 rounded-lg hover:bg-white/10 h-[46px] font-medium transition-all">
              Bekor qilish
            </button>
          )}
        </form>
      </div>

      <div className="metric-card rounded-xl overflow-hidden">
        <table className="min-w-full">
          <thead className="bg-surface-container-lowest border-b border-white/10">
            <tr>
              <th className="px-6 py-4 text-left text-xs font-semibold text-text-secondary uppercase tracking-wider">ID</th>
              <th className="px-6 py-4 text-left text-xs font-semibold text-text-secondary uppercase tracking-wider">Nomi</th>
              <th className="px-6 py-4 text-left text-xs font-semibold text-text-secondary uppercase tracking-wider">Slug</th>
              <th className="px-6 py-4 text-left text-xs font-semibold text-text-secondary uppercase tracking-wider">Holati</th>
              <th className="px-6 py-4 text-left text-xs font-semibold text-text-secondary uppercase tracking-wider">Amallar</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {categories.map(c => (
              <tr key={c.id} className="data-table-row">
                <td className="px-6 py-4 whitespace-nowrap text-text-primary font-medium">{c.id}</td>
                <td className="px-6 py-4 whitespace-nowrap text-text-primary font-medium">{c.name}</td>
                <td className="px-6 py-4 whitespace-nowrap text-text-secondary">{c.slug}</td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`px-3 py-1 inline-flex text-xs leading-5 font-bold rounded-full ${c.is_active ? 'bg-primary-container/20 text-primary-container border border-primary-container/30' : 'bg-surface-container-high text-text-secondary border border-white/10'}`}>
                    {c.is_active ? 'Faol' : 'Nofaol'}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium flex gap-3">
                  <button onClick={() => handleEdit(c)} className="text-tertiary-fixed hover:text-white transition-colors">Tahrirlash</button>
                  <button onClick={() => handleDelete(c.id)} className="text-primary-container hover:text-red-400 transition-colors">O'chirish</button>
                </td>
              </tr>
            ))}
            {categories.length === 0 && (
              <tr>
                <td colSpan={5} className="px-6 py-8 text-center text-text-secondary">Hech qanday kategoriya topilmadi</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
