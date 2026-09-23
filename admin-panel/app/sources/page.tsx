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
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  if (loading) return <div className="p-8 text-center text-text-secondary">Yuklanmoqda...</div>;

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-text-primary tracking-tight">Manbalar (Sources)</h1>
          <p className="text-xs sm:text-sm text-text-secondary mt-1">Videolar va kontent saqlanadigan Telegram guruh/kanallari</p>
        </div>
      </div>
      
      {/* Form Card */}
      <div className="metric-card p-4 sm:p-6 rounded-2xl mb-8">
        <h2 className="text-lg sm:text-xl font-semibold mb-4 text-text-primary flex items-center gap-2">
          <span className="material-symbols-outlined text-primary-container">
            {editingId ? "edit" : "add_circle"}
          </span>
          {editingId ? "Manbani tahrirlash" : "Yangi Manba qo'shish"}
        </h2>

        <form onSubmit={handleSubmit} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 items-end">
          <div>
            <label className="block text-xs sm:text-sm font-medium text-text-secondary mb-1">Turi</label>
            <select 
              className="w-full bg-surface-container-lowest border border-white/10 rounded-xl p-3 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container text-sm" 
              value={form.type} 
              onChange={e => setForm({...form, type: e.target.value})}
            >
              <option value="superguruh">Superguruh (Topic)</option>
              <option value="kanal">Kanal</option>
            </select>
          </div>

          <div>
            <label className="block text-xs sm:text-sm font-medium text-text-secondary mb-1">Nomi</label>
            <input 
              required 
              type="text" 
              className="w-full bg-surface-container-lowest border border-white/10 rounded-xl p-3 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container text-sm" 
              value={form.name} 
              onChange={e => setForm({...form, name: e.target.value})} 
              placeholder="Masalan: Asosiy Baza" 
            />
          </div>

          <div>
            <label className="block text-xs sm:text-sm font-medium text-text-secondary mb-1">Manba havolasi yoki ID</label>
            <input 
              required 
              type="text" 
              className="w-full bg-surface-container-lowest border border-white/10 rounded-xl p-3 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container text-sm" 
              value={form.link_or_id} 
              onChange={e => setForm({...form, link_or_id: e.target.value})} 
              placeholder="https://t.me/c/... yoki -100..." 
            />
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
                onClick={() => { setEditingId(null); setForm({name: "", link_or_id: "", type: "superguruh"}); }} 
                className="bg-white/5 border border-white/10 text-text-primary px-4 py-3 rounded-xl hover:bg-white/10 active:scale-95 text-sm font-medium transition-all min-h-[44px]"
              >
                Bekor
              </button>
            )}
          </div>
        </form>
      </div>

      {/* Sources Table */}
      <div className="metric-card rounded-2xl overflow-hidden shadow-xl">
        <div className="p-4 sm:p-5 border-b border-white/5 bg-[#1a0908]/80 flex items-center justify-between">
          <h3 className="font-display font-bold text-base sm:text-lg text-text-primary">Mavjud manbalar ({sources.length})</h3>
        </div>

        <div className="overflow-x-auto custom-scrollbar">
          <table className="min-w-[650px] w-full text-left border-collapse">
            <thead className="bg-surface-container-lowest border-b border-white/10">
              <tr>
                <th className="px-4 sm:px-6 py-3.5 text-xs font-semibold text-text-secondary uppercase tracking-wider">ID</th>
                <th className="px-4 sm:px-6 py-3.5 text-xs font-semibold text-text-secondary uppercase tracking-wider">Nomi</th>
                <th className="px-4 sm:px-6 py-3.5 text-xs font-semibold text-text-secondary uppercase tracking-wider">Chat ID</th>
                <th className="px-4 sm:px-6 py-3.5 text-xs font-semibold text-text-secondary uppercase tracking-wider">Topic ID</th>
                <th className="px-4 sm:px-6 py-3.5 text-xs font-semibold text-text-secondary uppercase tracking-wider">Turi</th>
                <th className="px-4 sm:px-6 py-3.5 text-right text-xs font-semibold text-text-secondary uppercase tracking-wider">Amallar</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5 text-sm">
              {sources.map(s => (
                <tr key={s.id} className="data-table-row">
                  <td className="px-4 sm:px-6 py-4 whitespace-nowrap text-text-secondary font-mono text-xs">#{s.id}</td>
                  <td className="px-4 sm:px-6 py-4 whitespace-nowrap text-text-primary font-medium">{s.name}</td>
                  <td className="px-4 sm:px-6 py-4 whitespace-nowrap text-text-secondary font-mono text-xs">{s.chat_id}</td>
                  <td className="px-4 sm:px-6 py-4 whitespace-nowrap text-text-secondary font-mono text-xs">{s.topic_id || "-"}</td>
                  <td className="px-4 sm:px-6 py-4 whitespace-nowrap">
                    <span className="px-2.5 py-1 inline-flex text-xs leading-4 font-bold rounded-full bg-surface-container-high text-text-secondary border border-white/10 capitalize">
                      {s.type}
                    </span>
                  </td>
                  <td className="px-4 sm:px-6 py-4 whitespace-nowrap text-right">
                    <div className="flex items-center justify-end gap-2">
                      <button onClick={() => handleEdit(s)} className="text-xs bg-white/5 border border-white/10 hover:bg-white/15 text-text-primary px-3 py-1.5 rounded-lg transition-colors min-h-[32px]">
                        Tahrirlash
                      </button>
                      <button onClick={() => handleDelete(s.id)} className="text-xs bg-red-500/10 border border-red-500/20 hover:bg-red-500/20 text-red-400 px-3 py-1.5 rounded-lg transition-colors min-h-[32px]">
                        O'chirish
                      </button>
                    </div>
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
    </div>
  );
}
