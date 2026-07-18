"use client";

import { useEffect, useState } from "react";
import { fetchApi } from "@/lib/api";

type Channel = {
  id: number;
  channel_id: number | null;
  channel_username: string;
  channel_title: string;
  is_active: boolean;
  subscriber_limit: number | null;
  current_subscriber_count: number;
};

export default function ChannelsPage() {
  const [channels, setChannels] = useState<Channel[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState<number | null>(null);

  const [form, setForm] = useState({
    channel_username: "",
    channel_title: "",
    is_active: true,
    subscriber_limit: "" as string | number,
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
      const payload = {
        ...form,
        subscriber_limit: form.subscriber_limit ? Number(form.subscriber_limit) : null
      };
      if (editingId) {
        await fetchApi(`/channels/${editingId}`, { method: "PUT", body: JSON.stringify(payload) });
      } else {
        await fetchApi("/channels/", { method: "POST", body: JSON.stringify(payload) });
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
      subscriber_limit: c.subscriber_limit || "",
    });
  };

  const handleCancel = () => {
    setEditingId(null);
    setForm({ channel_username: "", channel_title: "", is_active: true, subscriber_limit: "" });
  };

  if (loading) return <div>Yuklanmoqda...</div>;

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold mb-6 text-text-primary">Kanallar (Majburiy Obuna)</h1>
      </div>
      
      <div className="metric-card p-6 rounded-xl mb-8">
        <h2 className="text-xl font-semibold mb-4 text-text-primary">{editingId ? "Tahrirlash" : "Yangi Kanal"}</h2>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4 max-w-md">
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-1">Username (masalan: kinochi_mvp)</label>
            <input required type="text" className="w-full bg-surface-container-lowest border border-white/10 rounded-lg p-2.5 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container" value={form.channel_username} onChange={e => setForm({...form, channel_username: e.target.value.replace('@', '')})} />
          </div>
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-1">Sarlavha</label>
            <input required type="text" className="w-full bg-surface-container-lowest border border-white/10 rounded-lg p-2.5 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container" value={form.channel_title} onChange={e => setForm({...form, channel_title: e.target.value})} />
          </div>
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-1">Obunachi limiti (ixtiyoriy)</label>
            <input type="number" className="w-full bg-surface-container-lowest border border-white/10 rounded-lg p-2.5 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container" placeholder="Masalan: 200" value={form.subscriber_limit} onChange={e => setForm({...form, subscriber_limit: e.target.value})} />
          </div>
          <div className="flex items-center mt-2">
            <label className="flex items-center cursor-pointer text-text-secondary">
              <input type="checkbox" className="mr-2 w-4 h-4 rounded border-white/10 bg-surface-container-lowest focus:ring-primary-container text-primary-container" checked={form.is_active} onChange={e => setForm({...form, is_active: e.target.checked})} /> 
              Majburiy obuna uchun faol
            </label>
          </div>
          <div className="flex gap-4 mt-4">
            <button type="submit" className="bg-primary-container text-white px-6 py-2.5 rounded-lg hover:scale-105 transition-all font-medium">Saqlash</button>
            {editingId && <button type="button" onClick={handleCancel} className="bg-white/5 border border-white/10 text-text-primary px-6 py-2.5 rounded-lg hover:bg-white/10 transition-all font-medium">Bekor qilish</button>}
          </div>
        </form>
      </div>

      <div className="metric-card rounded-xl overflow-hidden">
        <table className="min-w-full">
          <thead className="bg-surface-container-lowest border-b border-white/10">
            <tr>
              <th className="px-6 py-4 text-left text-xs font-semibold text-text-secondary uppercase tracking-wider">ID</th>
              <th className="px-6 py-4 text-left text-xs font-semibold text-text-secondary uppercase tracking-wider">Username</th>
              <th className="px-6 py-4 text-left text-xs font-semibold text-text-secondary uppercase tracking-wider">Sarlavha</th>
              <th className="px-6 py-4 text-left text-xs font-semibold text-text-secondary uppercase tracking-wider">Progress</th>
              <th className="px-6 py-4 text-left text-xs font-semibold text-text-secondary uppercase tracking-wider">Holat</th>
              <th className="px-6 py-4 text-left text-xs font-semibold text-text-secondary uppercase tracking-wider">Amallar</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {channels.map(c => (
              <tr key={c.id} className="data-table-row">
                <td className="px-6 py-4 whitespace-nowrap text-text-primary">{c.id}</td>
                <td className="px-6 py-4 whitespace-nowrap font-bold text-text-primary">@{c.channel_username}</td>
                <td className="px-6 py-4 whitespace-nowrap text-text-secondary">{c.channel_title}</td>
                <td className="px-6 py-4 whitespace-nowrap text-text-secondary font-mono text-sm">
                  {c.subscriber_limit ? `${c.current_subscriber_count} / ${c.subscriber_limit}` : `${c.current_subscriber_count} (cheksiz)`}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`px-3 py-1 inline-flex text-xs leading-5 font-bold rounded-full ${c.is_active ? 'bg-primary-container/20 text-primary-container border border-primary-container/30' : 'bg-surface-container-high text-text-secondary border border-white/10'}`}>
                    {c.is_active ? 'Faol' : 'Nofaol'}
                  </span>
                  {!c.is_active && c.subscriber_limit && c.current_subscriber_count >= c.subscriber_limit && (
                    <span className="ml-2 px-3 py-1 inline-flex text-xs leading-5 font-bold rounded-full bg-rating-gold/20 text-rating-gold border border-rating-gold/30">
                      Limitga yetdi
                    </span>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium flex gap-3">
                  <button onClick={() => handleEdit(c)} className="text-tertiary-fixed hover:text-white transition-colors">Tahrirlash</button>
                  <button onClick={() => handleDelete(c.id)} className="text-primary-container hover:text-red-400 transition-colors">O'chirish</button>
                </td>
              </tr>
            ))}
            {channels.length === 0 && <tr><td colSpan={6} className="px-6 py-8 text-center text-text-secondary">Hech qanday kanal topilmadi</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}
