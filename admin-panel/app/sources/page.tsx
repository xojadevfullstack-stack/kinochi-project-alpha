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
    <div>
      <h1 className="text-3xl font-bold mb-6 text-gray-800">Manbalar (Sources)</h1>
      
      <div className="bg-white p-6 rounded-lg shadow-md mb-8">
        <h2 className="text-xl font-semibold mb-4">{editingId ? "Tahrirlash" : "Yangi Manba"}</h2>
        <form onSubmit={handleSubmit} className="flex flex-wrap gap-4 items-end">
          <div className="flex-1 min-w-[150px]">
            <label className="block text-sm font-medium text-gray-700">Turi</label>
            <select className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border" value={form.type} onChange={e => setForm({...form, type: e.target.value})}>
              <option value="superguruh">Superguruh</option>
              <option value="kanal">Kanal</option>
            </select>
          </div>
          <div className="flex-1 min-w-[200px]">
            <label className="block text-sm font-medium text-gray-700">Nomi</label>
            <input required type="text" className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border" value={form.name} onChange={e => setForm({...form, name: e.target.value})} placeholder="Masalan: Taxtlar O'yini" />
          </div>
          <div className="flex-[2] min-w-[300px]">
            <label className="block text-sm font-medium text-gray-700">Manba linki (yoki ID)</label>
            <input required type="text" className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border" value={form.link_or_id} onChange={e => setForm({...form, link_or_id: e.target.value})} placeholder="Masalan: https://t.me/c/3941035700/2 yoki -100..." />
          </div>
          <button type="submit" className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 h-10 w-full sm:w-auto">
            Saqlash
          </button>
          {editingId && (
            <button type="button" onClick={() => { setEditingId(null); setForm({name: "", link_or_id: "", type: "superguruh"}) }} className="bg-gray-300 text-gray-800 px-4 py-2 rounded-md hover:bg-gray-400 h-10 w-full sm:w-auto">
              Bekor qilish
            </button>
          )}
        </form>
      </div>

      <div className="bg-white rounded-lg shadow-md overflow-hidden overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ID</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nomi</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Chat ID</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Topic ID</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Turi</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Amallar</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {sources.map(s => (
              <tr key={s.id}>
                <td className="px-6 py-4 whitespace-nowrap text-gray-900">{s.id}</td>
                <td className="px-6 py-4 whitespace-nowrap text-gray-900 font-medium">{s.name}</td>
                <td className="px-6 py-4 whitespace-nowrap text-gray-500 font-mono">{s.chat_id}</td>
                <td className="px-6 py-4 whitespace-nowrap text-gray-500 font-mono">{s.topic_id || "-"}</td>
                <td className="px-6 py-4 whitespace-nowrap text-gray-500 capitalize">{s.type}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                  <button onClick={() => handleEdit(s)} className="text-indigo-600 hover:text-indigo-900 mr-4">Tahrirlash</button>
                  <button onClick={() => handleDelete(s.id)} className="text-red-600 hover:text-red-900">O'chirish</button>
                </td>
              </tr>
            ))}
            {sources.length === 0 && (
              <tr>
                <td colSpan={6} className="px-6 py-4 text-center text-gray-500">Hech qanday manba topilmadi</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
