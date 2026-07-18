"use client";

import { useEffect, useState, useRef } from "react";
import { fetchApi } from "@/lib/api";

type Broadcast = {
  id: number;
  message_text: string;
  status: "draft" | "sending" | "completed" | "failed";
  total_recipients: number;
  sent_count: number;
  failed_count: number;
  created_at: string;
};

export default function BroadcastsPage() {
  const [broadcasts, setBroadcasts] = useState<Broadcast[]>([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState({ message_text: "" });
  const [testTelegramId, setTestTelegramId] = useState("");
  
  // Use a ref to store interval ID so we can clear it properly
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const loadBroadcasts = async () => {
    try {
      const data = await fetchApi("/broadcasts?limit=100");
      setBroadcasts(data.items);
      return data.items as Broadcast[];
    } catch (e: any) {
      alert("Xato: " + e.message);
      return [];
    }
  };

  useEffect(() => {
    loadBroadcasts().then((items) => {
      setLoading(false);
      checkAndStartPolling(items);
    });

    // Load saved test telegram ID from localstorage
    const savedTestId = localStorage.getItem("test_telegram_id");
    if (savedTestId) {
      setTestTelegramId(savedTestId);
    }

    return () => stopPolling();
  }, []);

  const checkAndStartPolling = (items: Broadcast[]) => {
    const isSending = items.some(b => b.status === "sending");
    if (isSending && !pollIntervalRef.current) {
      pollIntervalRef.current = setInterval(async () => {
        const updatedItems = await loadBroadcasts();
        const stillSending = updatedItems.some(b => b.status === "sending");
        if (!stillSending) {
          stopPolling();
        }
      }, 2000);
    } else if (!isSending) {
      stopPolling();
    }
  };

  const stopPolling = () => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await fetchApi("/broadcasts", { 
        method: "POST", 
        body: JSON.stringify({ message_text: form.message_text }) 
      });
      setForm({ message_text: "" });
      const items = await loadBroadcasts();
      checkAndStartPolling(items);
    } catch (e: any) {
      alert("Yaratishda xato: " + e.message);
    }
  };

  const handleTestSend = async (id: number) => {
    if (!testTelegramId) {
      alert("Iltimos, o'zingizning (test) Telegram ID raqamingizni kiriting.");
      return;
    }
    
    // Save to local storage for convenience
    localStorage.setItem("test_telegram_id", testTelegramId);

    try {
      await fetchApi(`/broadcasts/${id}/test`, {
        method: "POST",
        body: JSON.stringify({ test_telegram_id: parseInt(testTelegramId) })
      });
      alert("✅ Test xabari yuborildi! Telegram'ingizni tekshiring.");
    } catch (e: any) {
      alert("Test yuborishda xato: " + e.message);
    }
  };

  const handleRealSend = async (id: number, total: number) => {
    if (!confirm(`DIQQAT!!!\n\nHaqiqatan ham ushbu xabarni bazadagi BARCHA (${total} ta) foydalanuvchiga yubormoqchimisiz?\n\nBu amalni bekor qilib bo'lmaydi!`)) {
      return;
    }

    try {
      await fetchApi(`/broadcasts/${id}/send`, { method: "POST" });
      const items = await loadBroadcasts();
      checkAndStartPolling(items);
    } catch (e: any) {
      alert("Yuborishda xato: " + e.message);
    }
  };

  if (loading) return <div>Yuklanmoqda...</div>;

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold mb-6 text-text-primary">Ommaviy Xabarlar (Broadcast)</h1>
      </div>
      
      <div className="metric-card p-6 rounded-xl mb-8">
        <h2 className="text-xl font-semibold mb-4 text-text-primary">Yangi Xabar Yaratish</h2>
        <form onSubmit={handleCreate} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-1">Xabar matni (HTML formatida ham yozish mumkin)</label>
            <textarea 
              required 
              rows={4}
              className="w-full bg-surface-container-lowest border border-white/10 rounded-lg p-3 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container" 
              value={form.message_text} 
              onChange={e => setForm({ message_text: e.target.value })} 
              placeholder="Assalomu alaykum! Tizimga yangi kinolar qo'shildi..."
            />
          </div>
          <button type="submit" className="bg-primary-container text-white px-6 py-2.5 rounded-lg hover:scale-105 transition-all font-medium">
            Saqlash (Qoralama yaratish)
          </button>
        </form>
      </div>

      <div className="metric-card p-6 rounded-xl mb-8">
         <h2 className="text-xl font-semibold mb-4 text-text-primary border-b border-white/10 pb-2">Xavfsizlik: Test uchun Telegram ID</h2>
         <p className="text-sm text-text-secondary mb-4">Haqiqiy foydalanuvchilarga yuborishdan oldin o'zingizning Telegram ID'ingizni kiritib test qilib ko'ring.</p>
         <div className="flex gap-4 items-center">
            <input 
              type="text" 
              placeholder="Masalan: 123456789" 
              className="w-64 bg-surface-container-lowest border border-white/10 rounded-lg p-2.5 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container"
              value={testTelegramId}
              onChange={(e) => setTestTelegramId(e.target.value)}
            />
            <span className="text-xs text-text-secondary">Telegram'da @userinfobot orqali ID'ingizni topishingiz mumkin.</span>
         </div>
      </div>

      <div className="metric-card rounded-xl overflow-hidden">
        <table className="min-w-full">
          <thead className="bg-surface-container-lowest border-b border-white/10">
            <tr>
              <th className="px-6 py-4 text-left text-xs font-semibold text-text-secondary uppercase tracking-wider">ID / Sana</th>
              <th className="px-6 py-4 text-left text-xs font-semibold text-text-secondary uppercase tracking-wider w-1/3">Matn</th>
              <th className="px-6 py-4 text-left text-xs font-semibold text-text-secondary uppercase tracking-wider">Holat</th>
              <th className="px-6 py-4 text-left text-xs font-semibold text-text-secondary uppercase tracking-wider">Progress</th>
              <th className="px-6 py-4 text-left text-xs font-semibold text-text-secondary uppercase tracking-wider">Amallar</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {broadcasts.map(b => (
              <tr key={b.id} className={`data-table-row ${b.status === "sending" ? "bg-primary-container/5" : ""}`}>
                <td className="px-6 py-4 text-sm text-text-primary">
                  <b className="text-white font-bold">#{b.id}</b> <br />
                  <span className="text-xs text-text-secondary">{new Date(b.created_at).toLocaleString('ru-RU')}</span>
                </td>
                <td className="px-6 py-4 text-sm text-text-primary">
                  <div className="truncate max-w-xs text-text-secondary" title={b.message_text}>
                    {b.message_text.length > 80 ? b.message_text.substring(0, 80) + "..." : b.message_text}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`px-3 py-1 inline-flex text-xs font-bold rounded-full border 
                    ${b.status === 'draft' ? 'bg-surface-container-high text-text-secondary border-white/10' : 
                      b.status === 'sending' ? 'bg-primary-container/20 text-primary-container border-primary-container/30 animate-pulse' : 
                      b.status === 'completed' ? 'bg-green-500/20 text-green-400 border-green-500/30' : 
                      'bg-red-500/20 text-red-400 border-red-500/30'}`
                  }>
                    {b.status.toUpperCase()}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-text-secondary">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-text-primary">{b.sent_count} / {b.total_recipients}</span>
                    {b.failed_count > 0 && <span className="text-red-400 text-xs">({b.failed_count} error)</span>}
                  </div>
                  {b.status === "sending" || b.status === "completed" ? (
                    <div className="w-full bg-surface-container-high rounded-full h-1.5 mt-2 overflow-hidden border border-white/5">
                      <div className="bg-primary-container h-1.5 rounded-full shadow-[0_0_10px_rgba(229,9,20,0.5)]" style={{ width: `${b.total_recipients > 0 ? Math.min(100, Math.round((b.sent_count + b.failed_count) / b.total_recipients * 100)) : 0}%` }}></div>
                    </div>
                  ) : null}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                  {b.status === "draft" && (
                    <div className="flex gap-2">
                      <button 
                        onClick={() => handleTestSend(b.id)} 
                        className="bg-rating-gold/10 text-rating-gold border border-rating-gold/30 hover:bg-rating-gold/20 px-3 py-1.5 rounded transition-all"
                        title="O'zimga test qilib yuborish"
                      >
                        Test
                      </button>
                      <button 
                        onClick={() => handleRealSend(b.id, b.total_recipients)} 
                        className="bg-primary-container text-white hover:bg-inverse-primary px-3 py-1.5 rounded transition-all shadow-[0_0_10px_rgba(229,9,20,0.3)]"
                      >
                        YUBORISH!
                      </button>
                    </div>
                  )}
                  {b.status === "sending" && (
                    <span className="text-primary-container font-bold animate-pulse">Yuborilmoqda...</span>
                  )}
                  {b.status === "completed" && (
                    <span className="text-green-400 font-bold">Yakunlangan</span>
                  )}
                </td>
              </tr>
            ))}
            {broadcasts.length === 0 && <tr><td colSpan={5} className="px-6 py-8 text-center text-text-secondary">Hech qanday ommaviy xabar topilmadi</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}
