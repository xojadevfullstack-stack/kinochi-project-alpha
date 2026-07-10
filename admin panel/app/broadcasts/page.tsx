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
    <div>
      <h1 className="text-3xl font-bold mb-6 text-gray-800">Ommaviy Xabarlar (Broadcast)</h1>
      
      <div className="bg-white p-6 rounded-lg shadow-md mb-8">
        <h2 className="text-xl font-semibold mb-4">Yangi Xabar Yaratish</h2>
        <form onSubmit={handleCreate} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Xabar matni (HTML formatida ham yozish mumkin)</label>
            <textarea 
              required 
              rows={4}
              className="w-full border border-gray-300 p-2 rounded focus:ring-2 focus:ring-blue-500" 
              value={form.message_text} 
              onChange={e => setForm({ message_text: e.target.value })} 
              placeholder="Assalomu alaykum! Tizimga yangi kinolar qo'shildi..."
            />
          </div>
          <button type="submit" className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 font-medium">
            Saqlash (Qoralama yaratish)
          </button>
        </form>
      </div>

      <div className="bg-white p-6 rounded-lg shadow-md mb-8">
         <h2 className="text-xl font-semibold mb-4 text-gray-800 border-b pb-2">Xavfsizlik: Test uchun Telegram ID</h2>
         <p className="text-sm text-gray-600 mb-4">Haqiqiy foydalanuvchilarga yuborishdan oldin o'zingizning Telegram ID'ingizni kiritib test qilib ko'ring.</p>
         <div className="flex gap-4 items-center">
            <input 
              type="text" 
              placeholder="Masalan: 123456789" 
              className="border p-2 rounded w-64"
              value={testTelegramId}
              onChange={(e) => setTestTelegramId(e.target.value)}
            />
            <span className="text-xs text-gray-400">Telegram'da @userinfobot orqali ID'ingizni topishingiz mumkin.</span>
         </div>
      </div>

      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ID / Sana</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-1/3">Matn</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Holat</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Progress</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Amallar</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {broadcasts.map(b => (
              <tr key={b.id} className={b.status === "sending" ? "bg-blue-50" : ""}>
                <td className="px-4 py-4 text-sm text-gray-900">
                  <b>#{b.id}</b> <br />
                  <span className="text-xs text-gray-500">{new Date(b.created_at).toLocaleString('ru-RU')}</span>
                </td>
                <td className="px-4 py-4 text-sm text-gray-900">
                  <div className="truncate max-w-xs" title={b.message_text}>
                    {b.message_text.length > 80 ? b.message_text.substring(0, 80) + "..." : b.message_text}
                  </div>
                </td>
                <td className="px-4 py-4 whitespace-nowrap">
                  <span className={`px-2 py-1 text-xs font-bold rounded-full 
                    ${b.status === 'draft' ? 'bg-gray-200 text-gray-700' : 
                      b.status === 'sending' ? 'bg-blue-200 text-blue-800 animate-pulse' : 
                      b.status === 'completed' ? 'bg-green-200 text-green-800' : 
                      'bg-red-200 text-red-800'}`
                  }>
                    {b.status.toUpperCase()}
                  </span>
                </td>
                <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-700">
                  <div className="flex items-center gap-2">
                    <span className="font-bold">{b.sent_count} / {b.total_recipients}</span>
                    {b.failed_count > 0 && <span className="text-red-500 text-xs">({b.failed_count} error)</span>}
                  </div>
                  {b.status === "sending" || b.status === "completed" ? (
                    <div className="w-full bg-gray-200 rounded-full h-1.5 mt-2">
                      <div className="bg-blue-600 h-1.5 rounded-full" style={{ width: `${b.total_recipients > 0 ? Math.min(100, Math.round((b.sent_count + b.failed_count) / b.total_recipients * 100)) : 0}%` }}></div>
                    </div>
                  ) : null}
                </td>
                <td className="px-4 py-4 whitespace-nowrap text-sm font-medium">
                  {b.status === "draft" && (
                    <div className="flex gap-2">
                      <button 
                        onClick={() => handleTestSend(b.id)} 
                        className="bg-yellow-500 text-white hover:bg-yellow-600 px-3 py-1 rounded"
                        title="O'zimga test qilib yuborish"
                      >
                        Test
                      </button>
                      <button 
                        onClick={() => handleRealSend(b.id, b.total_recipients)} 
                        className="bg-green-600 text-white hover:bg-green-700 px-3 py-1 rounded shadow"
                      >
                        YUBORISH!
                      </button>
                    </div>
                  )}
                  {b.status === "sending" && (
                    <span className="text-blue-600 font-bold">Yuborilmoqda...</span>
                  )}
                  {b.status === "completed" && (
                    <span className="text-green-600 font-bold">Yakunlangan</span>
                  )}
                </td>
              </tr>
            ))}
            {broadcasts.length === 0 && <tr><td colSpan={5} className="px-4 py-4 text-center text-gray-500">Hech qanday ommaviy xabar topilmadi</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}
