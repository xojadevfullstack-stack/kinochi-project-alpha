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
  const [form, setForm] = useState({ name: "", chat_id: "", topic_id: "", type: "supergroup" });
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
    try {
      const payload = {
        name: form.name,
        chat_id: parseInt(form.chat_id, 10),
        topic_id: form.topic_id ? parseInt(form.topic_id, 10) : null,
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
      setForm({ name: "", chat_id: "", topic_id: "", type: "supergroup" });
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
    setForm({ 
      name: s.name, 
      chat_id: s.chat_id.toString(), 
      topic_id: s.topic_id ? s.topic_id.toString() : "", 
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
          <div className="flex-1 min-w-[200px]">
            <label className="block text-sm font-medium text-gray-700">Nomi</label>
            <input required type="text" className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border" value={form.name} onChange={e => setForm({...form, name: e.target.value})} placeholder="Masalan: Taxtlar O'yini" />
          </div>
          <div className="flex-1 min-w-[200px]">
            <label className="block text-sm font-medium text-gray-700">Chat ID</label>
            <input required type="number" className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border" value={form.chat_id} onChange={e => setForm({...form, chat_id: e.target.value})} placeholder="-100123456789" />
          </div>
          <div className="flex-1 min-w-[200px]">
            <label className="block text-sm font-medium text-gray-700">Topic ID (Agar bo'lsa)</label>
            <input type="number" className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border" value={form.topic_id} onChange={e => setForm({...form, topic_id: e.target.value})} placeholder="1234" />
          </div>
          <div className="flex-1 min-w-[150px]">
            <label className="block text-sm font-medium text-gray-700">Turi</label>
            <select className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border" value={form.type} onChange={e => setForm({...form, type: e.target.value})}>
              <option value="supergroup">Supergroup</option>
              <option value="channel">Kanal</option>
            </select>
          </div>
          <button type="submit" className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 h-10 w-full sm:w-auto">
            Saqlash
          </button>
          {editingId && (
            <button type="button" onClick={() => { setEditingId(null); setForm({name: "", chat_id: "", topic_id: "", type: "supergroup"}) }} className="bg-gray-300 text-gray-800 px-4 py-2 rounded-md hover:bg-gray-400 h-10 w-full sm:w-auto">
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
