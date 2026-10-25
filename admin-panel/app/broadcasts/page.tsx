"use client";

import { useEffect, useState, useRef } from "react";
import { fetchApi } from "@/lib/api";

type Broadcast = {
  id: number;
  message_text: string;
  status: "draft" | "sending" | "completed" | "failed";
  media_type?: "text" | "photo" | "video";
  media_url?: string | null;
  button_text?: string | null;
  button_url?: string | null;
  total_recipients: number;
  sent_count: number;
  failed_count: number;
  created_at: string;
};

export default function BroadcastsPage() {
  const [broadcasts, setBroadcasts] = useState<Broadcast[]>([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState<{
    message_text: string;
    media_type: "text" | "photo" | "video";
    media_url: string;
    button_text: string;
    button_url: string;
  }>({
    message_text: "",
    media_type: "text",
    media_url: "",
    button_text: "",
    button_url: "",
  });
  const [testTelegramId, setTestTelegramId] = useState("");
  
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const loadBroadcasts = async () => {
    try {
      const data = await fetchApi("/broadcasts?limit=100");
      const items = data?.items || [];
      setBroadcasts(items);
      setErrorMsg(null);
      return items as Broadcast[];
    } catch (e: any) {
      console.error("Xato:", e);
      setErrorMsg(e.message || "Xatolik yuz berdi");
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
    if (!form.message_text.trim()) {
      alert("Xabar matnini kiriting!");
      return;
    }
    if (form.media_type !== "text" && !form.media_url.trim()) {
      alert("Tanlangan media turi uchun havola (URL yoki Telegram file_id) kiriting!");
      return;
    }
    if (form.button_text && !form.button_url) {
      alert("Tugma matniga havola (URL) kiritilishi shart!");
      return;
    }

    try {
      await fetchApi("/broadcasts", { 
        method: "POST", 
        body: JSON.stringify({ 
          message_text: form.message_text.trim(),
          media_type: form.media_type,
          media_url: form.media_url.trim() || null,
          button_text: form.button_text.trim() || null,
          button_url: form.button_url.trim() || null,
        }) 
      });
      setForm({
        message_text: "",
        media_type: "text",
        media_url: "",
        button_text: "",
        button_url: "",
      });
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
      alert("Test xabar Telegram'ga yuborildi! Botingizni tekshiring.");
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
    <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto space-y-6">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-text-primary tracking-tight">Ommaviy Xabarnomalar</h1>
          <p className="text-xs sm:text-sm text-text-secondary mt-1">Bot foydalanuvchilariga matn, rasm yoki video va tugmali xabarlar yuborish (Broadcast)</p>
        </div>
      </div>

      {errorMsg && (
        <div className="bg-red-500/10 border border-red-500/30 text-red-400 p-4 rounded-xl text-sm">
          {errorMsg}
        </div>
      )}

      {/* Info Notice Banner */}
      <div className="bg-surface-container-high/40 border border-white/10 rounded-2xl p-4 flex items-start gap-3">
        <span className="material-symbols-outlined text-rating-gold text-xl flex-shrink-0 mt-0.5">info</span>
        <div className="text-xs text-text-secondary space-y-1">
          <p className="text-text-primary font-medium">Xabarnoma yuborish bo‘yicha qo‘llanma:</p>
          <p>
            Rasm va video yuborilganda birinchi foydalanuvchiga yetkazilgach, Telegram uni avtomatik keshlaydi (<code className="text-primary font-mono text-[11px]">file_id</code>) va qolgan barcha foydalanuvchilarga lahzada yetkaziladi. Xabarga bevosita veb-sayt yoki botga olib boruvchi inline tugma ham qo‘shishingiz mumkin.
          </p>
        </div>
      </div>
      
      {/* Create Broadcast Form & Live Preview Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Form Column */}
        <div className="lg:col-span-7 metric-card p-4 sm:p-6 rounded-2xl">
          <h2 className="text-lg sm:text-xl font-semibold mb-4 text-text-primary flex items-center gap-2">
            <span className="material-symbols-outlined text-primary-container">campaign</span>
            Yangi Xabarnoma yaratish
          </h2>
          <form onSubmit={handleCreate} className="space-y-4">
            {/* Media Type Selector */}
            <div>
              <label className="block text-xs sm:text-sm font-medium text-text-secondary mb-2">Media turi</label>
              <div className="grid grid-cols-3 gap-2">
                <button
                  type="button"
                  onClick={() => setForm(f => ({ ...f, media_type: "text" }))}
                  className={`p-3 rounded-xl border text-xs sm:text-sm font-medium flex items-center justify-center gap-2 transition-all ${
                    form.media_type === "text"
                      ? "bg-primary-container text-white border-primary-container shadow-md"
                      : "bg-surface-container-lowest border-white/10 text-text-secondary hover:text-white"
                  }`}
                >
                  <span className="material-symbols-outlined text-base">article</span>
                  Matn
                </button>
                <button
                  type="button"
                  onClick={() => setForm(f => ({ ...f, media_type: "photo" }))}
                  className={`p-3 rounded-xl border text-xs sm:text-sm font-medium flex items-center justify-center gap-2 transition-all ${
                    form.media_type === "photo"
                      ? "bg-primary-container text-white border-primary-container shadow-md"
                      : "bg-surface-container-lowest border-white/10 text-text-secondary hover:text-white"
                  }`}
                >
                  <span className="material-symbols-outlined text-base">image</span>
                  Rasm
                </button>
                <button
                  type="button"
                  onClick={() => setForm(f => ({ ...f, media_type: "video" }))}
                  className={`p-3 rounded-xl border text-xs sm:text-sm font-medium flex items-center justify-center gap-2 transition-all ${
                    form.media_type === "video"
                      ? "bg-primary-container text-white border-primary-container shadow-md"
                      : "bg-surface-container-lowest border-white/10 text-text-secondary hover:text-white"
                  }`}
                >
                  <span className="material-symbols-outlined text-base">videocam</span>
                  Video
                </button>
              </div>
            </div>

            {/* Media URL if photo or video */}
            {form.media_type !== "text" && (
              <div>
                <label className="block text-xs sm:text-sm font-medium text-text-secondary mb-1">
                  {form.media_type === "photo" ? "Rasm havolasi (URL yoki Telegram file_id)" : "Video havolasi (URL yoki Telegram file_id)"}
                </label>
                <input
                  type="text"
                  required
                  placeholder={form.media_type === "photo" ? "https://kinochi.uz/posters/movie.jpg" : "https://kinochi.uz/trailers/promo.mp4"}
                  className="w-full bg-surface-container-lowest border border-white/10 rounded-xl p-3 text-text-primary focus:ring-2 focus:ring-primary-container text-sm"
                  value={form.media_url}
                  onChange={e => setForm(f => ({ ...f, media_url: e.target.value }))}
                />
              </div>
            )}

            {/* Message Text / Caption */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="text-xs sm:text-sm font-medium text-text-secondary">
                  {form.media_type === "text" ? "Xabar matni" : "Tavsif matni (Caption)"}
                </label>
                <span className="text-[11px] text-text-secondary">
                  {form.message_text.length} / {form.media_type === "text" ? "4096" : "1024"}
                </span>
              </div>
              <textarea 
                required 
                rows={4}
                maxLength={form.media_type === "text" ? 4096 : 1024}
                className="w-full bg-surface-container-lowest border border-white/10 rounded-xl p-3 text-text-primary focus:ring-2 focus:ring-primary-container focus:border-primary-container text-sm font-sans" 
                value={form.message_text} 
                onChange={e => setForm(f => ({ ...f, message_text: e.target.value }))} 
                placeholder="Assalomu alaykum! Kinochi botida yangi premyera premyera qilindi..."
              />
            </div>

            {/* Inline Button (Optional) */}
            <div className="p-3.5 bg-surface-container-lowest/60 border border-white/5 rounded-xl space-y-3">
              <span className="text-xs font-semibold text-text-primary flex items-center gap-1.5">
                <span className="material-symbols-outlined text-sm text-primary-container">smart_button</span>
                Inline tugma (ixtiyoriy)
              </span>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <input
                    type="text"
                    placeholder="Tugma matni (Masalan: Kinoni ko'rish)"
                    className="w-full bg-surface-container-lowest border border-white/10 rounded-lg p-2.5 text-xs sm:text-sm text-text-primary"
                    value={form.button_text}
                    onChange={e => setForm(f => ({ ...f, button_text: e.target.value }))}
                  />
                </div>
                <div>
                  <input
                    type="url"
                    placeholder="Havola (URL: https://...)"
                    className="w-full bg-surface-container-lowest border border-white/10 rounded-lg p-2.5 text-xs sm:text-sm text-text-primary"
                    value={form.button_url}
                    onChange={e => setForm(f => ({ ...f, button_url: e.target.value }))}
                  />
                </div>
              </div>
            </div>

            <button 
              type="submit" 
              className="bg-primary-container text-white px-6 py-3 rounded-xl hover:scale-[1.01] active:scale-95 transition-all font-semibold text-sm w-full text-center min-h-[44px] flex items-center justify-center gap-2 shadow-lg shadow-primary-container/20"
            >
              <span className="material-symbols-outlined text-lg">save</span>
              Qoralama sifatida saqlash
            </button>
          </form>
        </div>

        {/* Live Preview Column */}
        <div className="lg:col-span-5 metric-card p-4 sm:p-6 rounded-2xl flex flex-col justify-between">
          <div>
            <h2 className="text-base sm:text-lg font-semibold mb-3 text-text-primary flex items-center gap-2">
              <span className="material-symbols-outlined text-sky-400">visibility</span>
              Telegramda qanday ko'rinadi (Jonli ko'rinish)
            </h2>
            <p className="text-xs text-text-secondary mb-4">
              Xabar foydalanuvchi Telegram chatiga aynan quyidagi formatda tushadi:
            </p>

            {/* Telegram message mock */}
            <div className="bg-[#182533] text-white rounded-2xl p-3 sm:p-4 max-w-sm mx-auto shadow-2xl border border-white/5 space-y-3 font-sans">
              {/* Media preview */}
              {form.media_type === "photo" && (
                <div className="w-full aspect-video rounded-xl bg-black/40 overflow-hidden flex items-center justify-center border border-white/5 relative">
                  {form.media_url && (form.media_url.startsWith("http://") || form.media_url.startsWith("https://")) ? (
                    <img
                      src={form.media_url}
                      alt="Broadcast Media"
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        (e.target as HTMLElement).style.display = 'none';
                      }}
                    />
                  ) : (
                    <div className="text-center p-4 text-text-secondary">
                      <span className="material-symbols-outlined text-3xl text-white/40 block mb-1">image</span>
                      <span className="text-xs">Rasm namunasi</span>
                    </div>
                  )}
                </div>
              )}

              {form.media_type === "video" && (
                <div className="w-full aspect-video rounded-xl bg-black/50 overflow-hidden flex items-center justify-center border border-white/5 relative">
                  <div className="text-center p-4 text-text-secondary">
                    <span className="material-symbols-outlined text-4xl text-white/70 block mb-1">play_circle</span>
                    <span className="text-xs">Video premyera</span>
                  </div>
                </div>
              )}

              {/* Message caption or body */}
              <div className="text-xs sm:text-sm leading-relaxed whitespace-pre-wrap break-words text-slate-100">
                {form.message_text || (
                  <span className="text-slate-400 italic">Xabar matni bu yerda ko'rinadi...</span>
                )}
              </div>

              {/* Message time marker */}
              <div className="text-[10px] text-slate-400 text-right">
                {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </div>

              {/* Telegram inline button mockup */}
              {form.button_text && (
                <div className="pt-1">
                  <div className="w-full bg-[#2b5278] hover:bg-[#32618e] text-white py-2 px-3 rounded-lg text-center text-xs font-medium cursor-pointer transition-colors shadow-sm flex items-center justify-center gap-1.5">
                    <span>{form.button_text}</span>
                    <span className="material-symbols-outlined text-xs">arrow_outward</span>
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="mt-4 pt-4 border-t border-white/5 text-[11px] text-text-secondary flex items-center justify-center gap-1.5">
            <span className="material-symbols-outlined text-sm text-green-400">verified</span>
            Telegram Bot API 7.0+ talablariga to'liq mos keladi
          </div>
        </div>
      </div>

      {/* Test ID Helper Card */}
      <div className="metric-card p-4 sm:p-6 rounded-2xl">
         <h2 className="text-base sm:text-lg font-semibold mb-2 text-text-primary flex items-center gap-2">
           <span className="material-symbols-outlined text-rating-gold">security</span>
           Xavfsizlik: Test uchun Telegram ID
         </h2>
         <p className="text-xs sm:text-sm text-text-secondary mb-4">
           Haqiqiy foydalanuvchilarga yuborishdan oldin o'zingizning Telegram ID raqamingizga test yuborib ko'ring.
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
          <table className="min-w-[750px] w-full text-left border-collapse">
            <thead className="bg-surface-container-lowest border-b border-white/10">
              <tr>
                <th className="px-4 sm:px-6 py-3.5 text-xs font-semibold text-text-secondary uppercase tracking-wider">ID / Sana</th>
                <th className="px-4 sm:px-6 py-3.5 text-xs font-semibold text-text-secondary uppercase tracking-wider w-2/5">Xabar & Media</th>
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
                    <div className="flex items-center gap-2 mb-1.5">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider border ${
                        b.media_type === 'photo' ? 'bg-amber-500/10 text-amber-400 border-amber-500/30' :
                        b.media_type === 'video' ? 'bg-purple-500/10 text-purple-400 border-purple-500/30' :
                        'bg-blue-500/10 text-blue-400 border-blue-500/30'
                      }`}>
                        {b.media_type === 'photo' ? '🖼️ Rasm' : b.media_type === 'video' ? '🎥 Video' : '📝 Matn'}
                      </span>
                      {b.button_text && (
                        <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-white/5 border border-white/10 text-text-primary flex items-center gap-1">
                          <span className="material-symbols-outlined text-[11px]">link</span>
                          {b.button_text}
                        </span>
                      )}
                    </div>
                    <div className="truncate max-w-sm text-text-primary" title={b.message_text}>
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
                          title={`${b.failed_count} ta foydalanuvchiga yetkazilmadi (Botni to'xtatgan yoki test hisoblar)`}
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
                          title={`Yetkazildi: ${b.sent_count}`}
                        ></div>
                        {b.failed_count > 0 && (
                          <div 
                            className="bg-red-500 h-1.5 transition-all" 
                            style={{ width: `${b.total_recipients > 0 ? Math.min(100, Math.round(b.failed_count / b.total_recipients * 100)) : 0}%` }}
                            title={`Yetkazilmadi: ${b.failed_count}`}
                          ></div>
                        )}
                      </div>
                    ) : null}
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
