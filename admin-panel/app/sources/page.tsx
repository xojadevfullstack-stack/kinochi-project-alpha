"use client";

import { useEffect, useState } from "react";
import { fetchApi } from "@/lib/api";

type Source = {
  id: number;
  name: string;
  chat_id: number;
  topic_id: number | null;
  type: string;
};

export default function SourcesPage() {
  const [sources, setSources] = useState<Source[]>([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState({ name: "", link_or_id: "", type: "superguruh" });
  const [editingId, setEditingId] = useState<number | null>(null);

  useEffect(() => {
    loadSources();
  }, []);

  const loadSources = async () => {
    try {
      const data = await fetchApi("/sources");
      setSources(data);
    } catch (e: any) {
      alert("Xato: " + e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    let finalChatId: number | null = null;
    let finalTopicId: number | null = null;
    const input = form.link_or_id.trim();

    if (input.startsWith('http')) {
        try {
            const url = new URL(input);
            const parts = url.pathname.split('/').filter(p => p);
            
            if (parts[0] === 'c' && parts.length >= 2) {
                const rawChatId = parts[1];
                finalChatId = parseInt(`-100${rawChatId}`, 10);
                
                if (parts.length >= 3 && form.type === 'superguruh') {
                    finalTopicId = parseInt(parts[2], 10);
                }
            } else {
                alert("Iltimos, yopiq (private) link kiriting (masalan: https://t.me/c/12345/2) yoki raqamli ID yozing.");
                return;
            }
        } catch(err) {
            alert("Noto'g'ri link formati.");
            return;
        }
    } else {
        if (!/^-?\d+$/.test(input)) {
            alert("Iltimos, yopiq link kiriting yoki to'g'ridan-to'g'ri raqamli ID yozing.");
            return;
        }
        finalChatId = parseInt(input, 10);
    }

    if (!finalChatId || isNaN(finalChatId)) {
        alert("Chat ID ni aniqlab bo'lmadi.");
        return;
    }

    try {
      const payload = {
        name: form.name,
        chat_id: finalChatId,
        topic_id: finalTopicId,
        type: form.type,
      };

      if (editingId) {
        await fetchApi(`/sources/${editingId}`, {
          method: "PUT",
          body: JSON.stringify(payload),
        });
      } else {
        await fetchApi("/sources", {
          method: "POST",
          body: JSON.stringify(payload),
        });
      }
      setForm({ name: "", link_or_id: "", type: "superguruh" });
      setEditingId(null);
      loadSources();
    } catch (e: any) {
      alert("Saqlashda xato: " + e.message);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("O'chirilsinmi?")) return;
    try {
      await fetchApi(`/sources/${id}`, { method: "DELETE" });
      loadSources();
    } catch (e: any) {
      alert("O'chirishda xato: " + e.message);
    }
  };

  const handleEdit = (s: Source) => {
    setEditingId(s.id);
    let linkVal = s.chat_id.toString();
    
    if (s.chat_id.toString().startsWith('-100')) {
       const cleanId = s.chat_id.toString().replace('-100', '');
       if (s.topic_id) {
         linkVal = `https://t.me/c/${cleanId}/${s.topic_id}`;
       } else {
         linkVal = `https://t.me/c/${cleanId}`;
       }
    }

    setForm({ 
      name: s.name, 
      link_or_id: linkVal,
      type: s.type 
    });
  };

  if (loading) return <div>Yuklanmoqda...</div>;

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-text-primary">Manbalar (Sources)</h1>
      </div>
      
      <div className="metric-card p-6 rounded-xl mb-8">
        <h2 className="text-xl font-semibold mb-4 text-text-primary">{editingId ? "Tahrirlash" : "Yangi Manba"}</h2>
        <form onSubmit={handleSubmit} className="flex flex-wrap gap-4 items-end">
          <div className="flex-1 min-w-[150px]">
            <label className="block text-sm font-medium text-text-secondary mb-1">Turi</label>
            <select className="w-full bg-surface-container-lowest border border-white/10 rounded-lg p-2.5 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container" value={form.type} onChange={e => setForm({...form, type: e.target.value})}>
              <option value="superguruh">Superguruh</option>
              <option value="kanal">Kanal</option>
            </select>
          </div>
          <div className="flex-1 min-w-[200px]">
            <label className="block text-sm font-medium text-text-secondary mb-1">Nomi</label>
            <input required type="text" className="w-full bg-surface-container-lowest border border-white/10 rounded-lg p-2.5 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container" value={form.name} onChange={e => setForm({...form, name: e.target.value})} placeholder="Masalan: Taxtlar O'yini" />
          </div>
          <div className="flex-[2] min-w-[300px]">
            <label className="block text-sm font-medium text-text-secondary mb-1">Manba linki (yoki ID)</label>
            <input required type="text" className="w-full bg-surface-container-lowest border border-white/10 rounded-lg p-2.5 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container" value={form.link_or_id} onChange={e => setForm({...form, link_or_id: e.target.value})} placeholder="Masalan: https://t.me/c/3941035700/2 yoki -100..." />
          </div>
          <button type="submit" className="bg-primary-container text-white px-6 py-2.5 rounded-lg hover:scale-105 transition-all h-[46px] font-medium w-full sm:w-auto">
            Saqlash
          </button>
          {editingId && (
            <button type="button" onClick={() => { setEditingId(null); setForm({name: "", link_or_id: "", type: "superguruh"}) }} className="bg-white/5 border border-white/10 text-text-primary px-6 py-2.5 rounded-lg hover:bg-white/10 transition-all h-[46px] font-medium w-full sm:w-auto">
              Bekor qilish
            </button>
          )}
        </form>
      </div>

      <div className="metric-card rounded-xl overflow-hidden overflow-x-auto">
        <table className="min-w-full">
          <thead className="bg-surface-container-lowest border-b border-white/10">
            <tr>
              <th className="px-6 py-4 text-left text-xs font-semibold text-text-secondary uppercase tracking-wider">ID</th>
              <th className="px-6 py-4 text-left text-xs font-semibold text-text-secondary uppercase tracking-wider">Nomi</th>
              <th className="px-6 py-4 text-left text-xs font-semibold text-text-secondary uppercase tracking-wider">Chat ID</th>
              <th className="px-6 py-4 text-left text-xs font-semibold text-text-secondary uppercase tracking-wider">Topic ID</th>
              <th className="px-6 py-4 text-left text-xs font-semibold text-text-secondary uppercase tracking-wider">Turi</th>
              <th className="px-6 py-4 text-left text-xs font-semibold text-text-secondary uppercase tracking-wider">Amallar</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {sources.map(s => (
              <tr key={s.id} className="data-table-row">
                <td className="px-6 py-4 whitespace-nowrap text-text-primary">{s.id}</td>
                <td className="px-6 py-4 whitespace-nowrap text-text-primary font-medium">{s.name}</td>
                <td className="px-6 py-4 whitespace-nowrap text-text-secondary font-mono text-sm">{s.chat_id}</td>
                <td className="px-6 py-4 whitespace-nowrap text-text-secondary font-mono text-sm">{s.topic_id || "-"}</td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="px-3 py-1 inline-flex text-xs leading-5 font-bold rounded-full bg-surface-container-high text-text-secondary border border-white/10 capitalize">
                    {s.type}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium flex gap-3">
                  <button onClick={() => handleEdit(s)} className="text-tertiary-fixed hover:text-white transition-colors">Tahrirlash</button>
                  <button onClick={() => handleDelete(s.id)} className="text-primary-container hover:text-red-400 transition-colors">O'chirish</button>
                </td>
              </tr>
            ))}
            {sources.length === 0 && (
              <tr>
                <td colSpan={6} className="px-6 py-8 text-center text-text-secondary">Hech qanday manba topilmadi</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
