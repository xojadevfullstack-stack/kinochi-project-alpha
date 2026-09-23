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
      const data = await fetchApi("/channels?limit=100");
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
        await fetchApi("/channels", { method: "POST", body: JSON.stringify(payload) });
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
      channel_username: c.channel_username,
      channel_title: c.channel_title,
      is_active: c.is_active,
      subscriber_limit: c.subscriber_limit || "",
    });
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handleCancel = () => {
    setEditingId(null);
    setForm({ channel_username: "", channel_title: "", is_active: true, subscriber_limit: "" });
  };

  if (loading) return <div className="p-8 text-center text-text-secondary">Yuklanmoqda...</div>;

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-text-primary tracking-tight">Kanallar</h1>
          <p className="text-xs sm:text-sm text-text-secondary mt-1">Majburiy obuna kanallari va limitlarni boshqarish</p>
        </div>
      </div>
      
      {/* Form Card */}
      <div className="metric-card p-4 sm:p-6 rounded-2xl mb-8">
        <h2 className="text-lg sm:text-xl font-semibold mb-4 text-text-primary flex items-center gap-2">
          <span className="material-symbols-outlined text-primary-container">
            {editingId ? "edit" : "add_circle"}
          </span>
          {editingId ? "Kanalni tahrirlash" : "Yangi Kanal qo'shish"}
        </h2>

        <form onSubmit={handleSubmit} className="flex flex-col gap-3 sm:gap-4 max-w-xl">
          <div>
            <label className="block text-xs sm:text-sm font-medium text-text-secondary mb-1">
              Username (masalan: kinochi_mvp)
            </label>
            <input 
              required 
              type="text" 
              className="w-full bg-surface-container-lowest border border-white/10 rounded-xl p-3 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container text-sm" 
              value={form.channel_username} 
              onChange={e => setForm({...form, channel_username: e.target.value.replace('@', '')})} 
              placeholder="kinochi_rasmiy"
            />
          </div>

          <div>
            <label className="block text-xs sm:text-sm font-medium text-text-secondary mb-1">
              Sarlavha
            </label>
            <input 
              required 
              type="text" 
              className="w-full bg-surface-container-lowest border border-white/10 rounded-xl p-3 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container text-sm" 
              value={form.channel_title} 
              onChange={e => setForm({...form, channel_title: e.target.value})} 
              placeholder="Kinochi Rasmiy Kanal"
            />
          </div>

          <div>
            <label className="block text-xs sm:text-sm font-medium text-text-secondary mb-1">
              Obunachi limiti (ixtiyoriy)
            </label>
            <input 
              type="number" 
              className="w-full bg-surface-container-lowest border border-white/10 rounded-xl p-3 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container text-sm" 
              placeholder="Masalan: 500 (bo'sh qolsa cheksiz)" 
              value={form.subscriber_limit} 
              onChange={e => setForm({...form, subscriber_limit: e.target.value})} 
            />
          </div>

          <div className="flex items-center mt-1">
            <label className="flex items-center cursor-pointer text-text-primary bg-surface-container-lowest border border-white/10 px-3 py-2.5 rounded-xl text-xs sm:text-sm min-h-[40px]">
              <input 
                type="checkbox" 
                className="mr-2.5 w-4 h-4 rounded border-white/10 bg-surface-container-lowest focus:ring-primary-container text-primary-container" 
                checked={form.is_active} 
                onChange={e => setForm({...form, is_active: e.target.checked})} 
              /> 
              Majburiy obuna uchun faol
            </label>
          </div>

          <div className="flex flex-col sm:flex-row gap-3 mt-2">
            <button 
              type="submit" 
              className="bg-primary-container text-white px-6 py-3 rounded-xl hover:scale-[1.02] active:scale-95 transition-all font-medium text-sm w-full sm:w-auto text-center min-h-[44px]"
            >
              {editingId ? "O'zgarishlarni saqlash" : "Kanalni saqlash"}
            </button>
            {editingId && (
              <button 
                type="button" 
                onClick={handleCancel} 
                className="bg-white/5 border border-white/10 text-text-primary px-6 py-3 rounded-xl hover:bg-white/10 active:scale-95 transition-all font-medium text-sm w-full sm:w-auto text-center min-h-[44px]"
              >
                Bekor qilish
              </button>
            )}
          </div>
        </form>
      </div>

      {/* Channels Table */}
      <div className="metric-card rounded-2xl overflow-hidden shadow-xl">
        <div className="p-4 sm:p-5 border-b border-white/5 bg-[#1a0908]/80 flex items-center justify-between">
          <h3 className="font-display font-bold text-base sm:text-lg text-text-primary">Kanallar ro'yxati ({channels.length})</h3>
        </div>

        <div className="overflow-x-auto custom-scrollbar">
          <table className="min-w-[650px] w-full text-left border-collapse">
            <thead className="bg-surface-container-lowest border-b border-white/10">
              <tr>
                <th className="px-4 sm:px-6 py-3.5 text-xs font-semibold text-text-secondary uppercase tracking-wider">ID</th>
                <th className="px-4 sm:px-6 py-3.5 text-xs font-semibold text-text-secondary uppercase tracking-wider">Username</th>
                <th className="px-4 sm:px-6 py-3.5 text-xs font-semibold text-text-secondary uppercase tracking-wider">Sarlavha</th>
                <th className="px-4 sm:px-6 py-3.5 text-xs font-semibold text-text-secondary uppercase tracking-wider">Progress</th>
                <th className="px-4 sm:px-6 py-3.5 text-xs font-semibold text-text-secondary uppercase tracking-wider">Holat</th>
                <th className="px-4 sm:px-6 py-3.5 text-right text-xs font-semibold text-text-secondary uppercase tracking-wider">Amallar</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5 text-sm">
              {channels.map(c => (
                <tr key={c.id} className="data-table-row">
                  <td className="px-4 sm:px-6 py-4 whitespace-nowrap text-text-secondary font-mono text-xs">#{c.id}</td>
                  <td className="px-4 sm:px-6 py-4 whitespace-nowrap font-bold text-text-primary">
                    <a href={`https://t.me/${c.channel_username}`} target="_blank" rel="noreferrer" className="text-tertiary-fixed hover:underline flex items-center gap-1">
                      @{c.channel_username}
                      <span className="material-symbols-outlined text-[14px]">open_in_new</span>
                    </a>
                  </td>
                  <td className="px-4 sm:px-6 py-4 whitespace-nowrap text-text-secondary">{c.channel_title}</td>
                  <td className="px-4 sm:px-6 py-4 whitespace-nowrap text-text-secondary font-mono text-xs">
                    {c.subscriber_limit ? `${c.current_subscriber_count} / ${c.subscriber_limit}` : `${c.current_subscriber_count} (cheksiz)`}
                  </td>
                  <td className="px-4 sm:px-6 py-4 whitespace-nowrap">
                    <span className={`px-2.5 py-1 inline-flex text-xs leading-4 font-bold rounded-full ${c.is_active ? 'bg-primary-container/20 text-primary-container border border-primary-container/30' : 'bg-surface-container-high text-text-secondary border border-white/10'}`}>
                      {c.is_active ? 'Faol' : 'Nofaol'}
                    </span>
                    {!c.is_active && c.subscriber_limit && c.current_subscriber_count >= c.subscriber_limit && (
                      <span className="ml-1.5 px-2 py-0.5 inline-flex text-[11px] leading-4 font-bold rounded-full bg-rating-gold/20 text-rating-gold border border-rating-gold/30">
                        Limitga yetdi
                      </span>
                    )}
                  </td>
                  <td className="px-4 sm:px-6 py-4 whitespace-nowrap text-right">
                    <div className="flex items-center justify-end gap-2">
                      <button onClick={() => handleEdit(c)} className="text-xs bg-white/5 border border-white/10 hover:bg-white/15 text-text-primary px-3 py-1.5 rounded-lg transition-colors min-h-[32px]">
                        Tahrirlash
                      </button>
                      <button onClick={() => handleDelete(c.id)} className="text-xs bg-red-500/10 border border-red-500/20 hover:bg-red-500/20 text-red-400 px-3 py-1.5 rounded-lg transition-colors min-h-[32px]">
                        O'chirish
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {channels.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-text-secondary">Hech qanday kanal topilmadi</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
