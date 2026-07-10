"use client";

import { useEffect, useState } from "react";
import { fetchApi } from "@/lib/api";

type Channel = {
  id: number;
  channel_id: number | null;
  channel_username: string;
  channel_title: string;
  is_active: boolean;
};

export default function ChannelsPage() {
  const [channels, setChannels] = useState<Channel[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState<number | null>(null);

  const [form, setForm] = useState({
    channel_username: "",
    channel_title: "",
    is_active: true,
  });

  useEffect(() => {
    loadChannels();
  }, []);

  const loadChannels = async () => {
    try {
      const data = await fetchApi("/channels/?limit=100");
      setChannels(data.items || []);
      setLoading(false);
    } catch (e: any) {
      alert("Xato: " + e.message);
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingId) {
        await fetchApi(`/channels/${editingId}`, { method: "PUT", body: JSON.stringify(form) });
      } else {
        await fetchApi("/channels/", { method: "POST", body: JSON.stringify(form) });
      }
      handleCancel();
      loadChannels();
    } catch (e: any) {
      alert("Saqlashda xato: " + e.message);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("O'chirilsinmi?")) return;
    try {
      await fetchApi(`/channels/${id}`, { method: "DELETE" });
      loadChannels();
    } catch (e: any) {
      alert("O'chirishda xato: " + e.message);
    }
  };

  const handleEdit = (c: Channel) => {
    setEditingId(c.id);
    setForm({
      channel_username: c.channel_username || "",
      channel_title: c.channel_title || "",
      is_active: c.is_active,
    });
  };

  const handleCancel = () => {
    setEditingId(null);
    setForm({ channel_username: "", channel_title: "", is_active: true });
  };

  if (loading) return <div>Yuklanmoqda...</div>;

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6 text-gray-800">Kanallar (Majburiy Obuna)</h1>
      
      <div className="bg-white p-6 rounded-lg shadow-md mb-8">
        <h2 className="text-xl font-semibold mb-4">{editingId ? "Tahrirlash" : "Yangi Kanal"}</h2>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4 max-w-md">
          <div>
            <label className="block text-sm">Username (masalan: kinochi_mvp)</label>
            <input required type="text" className="w-full border p-2 rounded mt-1" value={form.channel_username} onChange={e => setForm({...form, channel_username: e.target.value.replace('@', '')})} />
          </div>
          <div>
            <label className="block text-sm">Sarlavha</label>
            <input required type="text" className="w-full border p-2 rounded mt-1" value={form.channel_title} onChange={e => setForm({...form, channel_title: e.target.value})} />
          </div>
          <div className="flex items-center mt-2">
            <label className="flex items-center cursor-pointer">
              <input type="checkbox" className="mr-2" checked={form.is_active} onChange={e => setForm({...form, is_active: e.target.checked})} /> 
              Majburiy obuna uchun faol
            </label>
          </div>
          <div className="flex gap-4 mt-4">
            <button type="submit" className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700">Saqlash</button>
            {editingId && <button type="button" onClick={handleCancel} className="bg-gray-300 text-gray-800 px-4 py-2 rounded-md hover:bg-gray-400">Bekor qilish</button>}
          </div>
        </form>
      </div>

      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ID</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Username</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Sarlavha</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Holat</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Amallar</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {channels.map(c => (
              <tr key={c.id}>
                <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-500">{c.id}</td>
                <td className="px-4 py-4 whitespace-nowrap text-sm font-bold text-gray-900">@{c.channel_username}</td>
                <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900">{c.channel_title}</td>
                <td className="px-4 py-4 whitespace-nowrap">
                  <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${c.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                    {c.is_active ? 'Faol' : 'Nofaol'}
                  </span>
                </td>
                <td className="px-4 py-4 whitespace-nowrap text-sm font-medium">
                  <button onClick={() => handleEdit(c)} className="text-indigo-600 hover:text-indigo-900 mr-4">Tahrirlash</button>
                  <button onClick={() => handleDelete(c.id)} className="text-red-600 hover:text-red-900">O'chirish</button>
                </td>
              </tr>
            ))}
            {channels.length === 0 && <tr><td colSpan={5} className="px-4 py-4 text-center text-gray-500">Hech qanday kanal topilmadi</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}
