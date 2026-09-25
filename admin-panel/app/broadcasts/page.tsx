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
    
    localStorage.setItem("test_telegram_id", testTelegramId);

    try {
      await fetchApi(`/broadcasts/${id}/test`, {
        method: "POST",
        body: JSON.stringify({ test_telegram_id: parseInt(testTelegramId) })
      });
      alert("Test xabar Telegram'ga yuborildi! Botni tekshiring.");
    } catch (e: any) {
      alert("Test yuborishda xato: " + e.message);
    }
  };

  const handleRealSend = async (id: number, count: number) => {
    if (!confirm(`DIQQAT! Ushbu xabar barcha ${count} ta foydalanuvchiga yuboriladi! Tasdiqlaysizmi?`)) {
      return;
    }

    try {
      await fetchApi(`/broadcasts/${id}/send`, { method: "POST" });
      const items = await loadBroadcasts();
      checkAndStartPolling(items);
    } catch (e: any) {
      alert("Xabar yuborishni boshlashda xato: " + e.message);
    }
  };

  if (loading) return <div className="p-8 text-center text-text-secondary">Yuklanmoqda...</div>;

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-text-primary tracking-tight">Ommaviy Xabarnomalar</h1>
          <p className="text-xs sm:text-sm text-text-secondary mt-1">Bot foydalanuvchilariga ommaviy xabarlar yuborish (Broadcast)</p>
        </div>
      </div>

      {/* Info Notice Banner */}
      <div className="bg-surface-container-high/40 border border-white/10 rounded-2xl p-4 mb-6 flex items-start gap-3">
        <span className="material-symbols-outlined text-rating-gold text-xl flex-shrink-0 mt-0.5">info</span>
        <div className="text-xs text-text-secondary space-y-1">
          <p className="text-text-primary font-medium">Xabarnoma yuborish haqida eslatma:</p>
          <p>
            Xabarlar barcha faol foydalanuvchilarga ketma-ket yuboriladi. Agar ayrim foydalanuvchilarda xato qayd etilsa, bu odatda ular botni to‘xtatgani (bloklagani) yoki akkauntini o‘chirgani sababli yuz beradi. Tizim bunday nofaol hisoblarni kelgusi xabarlardan avtomatik chetlatadi.
          </p>
        </div>
      </div>
      
      {/* Create Broadcast Form */}
      <div className="metric-card p-4 sm:p-6 rounded-2xl mb-6">
        <h2 className="text-lg sm:text-xl font-semibold mb-4 text-text-primary flex items-center gap-2">
          <span className="material-symbols-outlined text-primary-container">campaign</span>
          Yangi Xabarnoma yaratish
        </h2>
        <form onSubmit={handleCreate} className="space-y-4">
          <div>
            <label className="block text-xs sm:text-sm font-medium text-text-secondary mb-1">Xabar matni</label>
            <textarea 
              required 
              rows={4}
              className="w-full bg-surface-container-lowest border border-white/10 rounded-xl p-3 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container text-sm" 
              value={form.message_text} 
              onChange={e => setForm({ message_text: e.target.value })} 
              placeholder="Assalomu alaykum! Tizimga yangi kinolar qo'shildi..."
            />
          </div>
          <button 
            type="submit" 
            className="bg-primary-container text-white px-6 py-3 rounded-xl hover:scale-[1.02] active:scale-95 transition-all font-medium text-sm w-full sm:w-auto text-center min-h-[44px]"
          >
            Saqlash (Qoralama yaratish)
          </button>
        </form>
      </div>

      {/* Test ID Helper Card */}
      <div className="metric-card p-4 sm:p-6 rounded-2xl mb-8">
         <h2 className="text-base sm:text-lg font-semibold mb-2 text-text-primary flex items-center gap-2">
           <span className="material-symbols-outlined text-rating-gold">security</span>
           Xavfsizlik: Test uchun Telegram ID
         </h2>
         <p className="text-xs sm:text-sm text-text-secondary mb-4">
           Haqiqiy foydalanuvchilarga yuborishdan oldin o'zingizning Telegram ID'ingizni kiritib test qilib ko'ring.
         </p>
         <div className="flex flex-col sm:flex-row gap-3 sm:items-center">
            <input 
              type="text" 
              placeholder="Masalan: 123456789" 
              className="w-full sm:w-72 bg-surface-container-lowest border border-white/10 rounded-xl p-3 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container text-sm"
              value={testTelegramId}
              onChange={(e) => setTestTelegramId(e.target.value)}
            />
            <span className="text-xs text-text-secondary">
              Telegram'da @userinfobot orqali ID raqamingizni olishingiz mumkin.
            </span>
         </div>
      </div>

      {/* Broadcasts List Table */}
      <div className="metric-card rounded-2xl overflow-hidden shadow-xl">
        <div className="p-4 sm:p-5 border-b border-white/5 bg-[#1a0908]/80 flex items-center justify-between">
          <h3 className="font-display font-bold text-base sm:text-lg text-text-primary">Xabarnomalar tarixi ({broadcasts.length})</h3>
        </div>

        <div className="overflow-x-auto custom-scrollbar">
          <table className="min-w-[700px] w-full text-left border-collapse">
            <thead className="bg-surface-container-lowest border-b border-white/10">
              <tr>
                <th className="px-4 sm:px-6 py-3.5 text-xs font-semibold text-text-secondary uppercase tracking-wider">ID / Sana</th>
                <th className="px-4 sm:px-6 py-3.5 text-xs font-semibold text-text-secondary uppercase tracking-wider w-1/3">Matn</th>
                <th className="px-4 sm:px-6 py-3.5 text-xs font-semibold text-text-secondary uppercase tracking-wider">Holat</th>
                <th className="px-4 sm:px-6 py-3.5 text-xs font-semibold text-text-secondary uppercase tracking-wider">Progress</th>
                <th className="px-4 sm:px-6 py-3.5 text-right text-xs font-semibold text-text-secondary uppercase tracking-wider">Amallar</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5 text-sm">
              {broadcasts.map(b => (
                <tr key={b.id} className={`data-table-row ${b.status === "sending" ? "bg-primary-container/5" : ""}`}>
                  <td className="px-4 sm:px-6 py-4 whitespace-nowrap text-text-primary">
                    <span className="text-white font-bold">#{b.id}</span> <br />
                    <span className="text-[11px] text-text-secondary">{new Date(b.created_at).toLocaleDateString('uz-UZ')}</span>
                  </td>
                  <td className="px-4 sm:px-6 py-4 text-xs sm:text-sm text-text-secondary">
                    <div className="truncate max-w-xs" title={b.message_text}>
                      {b.message_text.length > 80 ? b.message_text.substring(0, 80) + "..." : b.message_text}
                    </div>
                  </td>
                  <td className="px-4 sm:px-6 py-4 whitespace-nowrap">
                    <span className={`px-2.5 py-1 inline-flex text-xs font-bold rounded-full border 
                      ${b.status === 'draft' ? 'bg-surface-container-high text-text-secondary border-white/10' : 
                        b.status === 'sending' ? 'bg-primary-container/20 text-primary-container border-primary-container/30 animate-pulse' : 
                        b.status === 'completed' ? 'bg-green-500/20 text-green-400 border-green-500/30' : 
                        'bg-red-500/20 text-red-400 border-red-500/30'}`
                    }>
                      {b.status.toUpperCase()}
                    </span>
                  </td>
                  <td className="px-4 sm:px-6 py-4 whitespace-nowrap text-xs text-text-secondary">
                    <div className="flex items-center gap-1.5 font-mono">
                      <span className="font-bold text-text-primary">{b.sent_count} / {b.total_recipients}</span>
                      {b.failed_count > 0 && (
                        <span 
                          className="text-red-400 text-[11px] cursor-help underline decoration-dotted" 
                          title={`${b.failed_count} ta foydalanuvchiga yetkazilmadi (Botni to'xtatgan, Telegram akkauntini o'chirgan yoki test hisoblar)`}
                        >
                          ({b.failed_count} xato)
                        </span>
                      )}
                    </div>
                    {b.status === "sending" || b.status === "completed" ? (
                      <div className="w-full bg-surface-container-high rounded-full h-1.5 mt-2 overflow-hidden border border-white/5 flex">
                        <div 
                          className="bg-green-500 h-1.5 transition-all" 
                          style={{ width: `${b.total_recipients > 0 ? Math.min(100, Math.round(b.sent_count / b.total_recipients * 100)) : 0}%` }}
                          title={`Muvaffaqiyatli yetkazildi: ${b.sent_count}`}
                        ></div>
                        {b.failed_count > 0 && (
                          <div 
                            className="bg-red-500 h-1.5 transition-all" 
                            style={{ width: `${b.total_recipients > 0 ? Math.min(100, Math.round(b.failed_count / b.total_recipients * 100)) : 0}%` }}
                            title={`Yetkazilmadi (bot bloklangan/nofaol): ${b.failed_count}`}
                          ></div>
                        )}
                      </div>
                    ) : null}
                    {b.failed_count > 0 && (
                      <span 
                        className="text-[10px] text-text-secondary block mt-1" 
                        title="Botni to'xtatgan yoki nofaol foydalanuvchilar"
                      >
                        (bot bloklangan/nofaol)
                      </span>
                    )}
                  </td>
                  <td className="px-4 sm:px-6 py-4 whitespace-nowrap text-right">
                    {b.status === "draft" && (
                      <div className="flex items-center justify-end gap-2">
                        <button 
                          onClick={() => handleTestSend(b.id)} 
                          className="bg-rating-gold/10 text-rating-gold border border-rating-gold/30 hover:bg-rating-gold/20 px-3 py-1.5 rounded-lg transition-all text-xs font-medium min-h-[32px]"
                          title="O'zimga test qilib yuborish"
                        >
                          Test
                        </button>
                        <button 
                          onClick={() => handleRealSend(b.id, b.total_recipients)} 
                          className="bg-primary-container text-white hover:bg-inverse-primary px-3 py-1.5 rounded-lg transition-all text-xs font-bold shadow-[0_0_10px_rgba(229,9,20,0.3)] min-h-[32px]"
                        >
                          YUBORISH!
                        </button>
                      </div>
                    )}
                    {b.status === "sending" && (
                      <span className="text-primary-container font-bold text-xs animate-pulse">Yuborilmoqda...</span>
                    )}
                    {b.status === "completed" && (
                      <span className="text-green-400 font-bold text-xs">Yakunlangan</span>
                    )}
                  </td>
                </tr>
              ))}
              {broadcasts.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-text-secondary">Hech qanday ommaviy xabar topilmadi</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
