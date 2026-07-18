"use client";

import { useState, useRef } from "react";
import { fetchApi, uploadWithProgress, HEALTH_URL } from "@/lib/api";

interface VideoUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  entityName: string; // 'Kino' or 'Qism'
  uploadEndpoint: string;
  linkEndpoint: string;
  onSuccess: () => void;
}

export default function VideoUploadModal({
  isOpen,
  onClose,
  entityName,
  uploadEndpoint,
  linkEndpoint,
  onSuccess
}: VideoUploadModalProps) {
  const [uploadMethod, setUploadMethod] = useState<'file' | 'message'>('file');
  const [messageId, setMessageId] = useState("");
  const [language, setLanguage] = useState("Asosiy");
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<number | null>(null);

  if (!isOpen) return null;

  const submitVideo = async () => {
    try {
      setIsUploading(true);
      
      if (uploadMethod === 'file') {
        const file = fileInputRef.current?.files?.[0];
        if (!file) {
          alert("Iltimos, video faylni tanlang!");
          setIsUploading(false);
          return;
        }
        
        // Fayl hajmini tekshirish (50MB limit)
        const MAX_MB = 50;
        if (file.size > MAX_MB * 1024 * 1024) {
          alert(`Fayl hajmi ${MAX_MB}MB dan oshmasligi kerak. Hozirgi fayl: ${(file.size / 1024 / 1024).toFixed(1)}MB`);
          setIsUploading(false);
          return;
        }
        
        // Server uyg'onishini kutish (Render free tier uyquda bo'lishi mumkin)
        setUploadProgress(0);
        try {
          await fetch(HEALTH_URL, { method: "GET", signal: AbortSignal.timeout(10000) });
        } catch (e) {
          // health check ishlamasa ham davom etamiz
        }
        
        await uploadWithProgress(
          uploadEndpoint,
          file,
          (percent) => setUploadProgress(percent),
          { language }
        );
        
        alert(`${entityName} fayli muvaffaqiyatli yuklandi!`);
      } else {
        // Parse the message ID from input (number or url)
        let parsedId: number | null = null;
        const inputStr = messageId.trim();
        
        if (/^\d+$/.test(inputStr)) {
          parsedId = parseInt(inputStr);
        } else {
          try {
            const url = new URL(inputStr);
            const pathParts = url.pathname.split('/').filter(p => p);
            const lastPart = pathParts[pathParts.length - 1];
            if (/^\d+$/.test(lastPart)) {
              parsedId = parseInt(lastPart);
            }
          } catch (e) {
            // Not a valid URL
          }
        }
        
        if (!parsedId || isNaN(parsedId)) {
          alert("Iltimos, yaroqli Telegram xabar ID sini yoki to'g'ri linkni kiriting!");
          setIsUploading(false);
          return;
        }
        
        await fetchApi(linkEndpoint, {
          method: "POST",
          body: JSON.stringify({ message_id: parsedId, language })
        });
        
        alert(`${entityName} Telegram ID orqali muvaffaqiyatli ulandi!`);
      }
      
      onSuccess();
      onClose();
    } catch (e: any) {
      alert("Xato yuz berdi: " + e.message);
    } finally {
      setIsUploading(false);
      setUploadProgress(null);
    }
  };

  const isSubmitDisabled = isUploading || (uploadMethod === 'message' && !messageId.trim()) || !language.trim();

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-surface-container-lowest border border-white/10 rounded-2xl shadow-2xl w-full max-w-lg mx-4 overflow-hidden transform transition-all">
        <div className="px-6 py-5 border-b border-white/10 flex justify-between items-center bg-surface-container-high/30">
          <h3 className="font-headline-md text-xl text-text-primary flex items-center gap-3">
            <span className="material-symbols-outlined text-primary-container">cloud_upload</span>
            Video yuklash yoki ulash
          </h3>
          <button onClick={onClose} className="text-text-secondary hover:text-text-primary transition-colors bg-white/5 hover:bg-white/10 p-1.5 rounded-full flex items-center justify-center">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <div className="p-6">
          <div className="mb-5">
            <label className="block text-sm font-medium text-text-secondary mb-2">Studiya nomi (Til)</label>
            <input 
              type="text" 
              placeholder="Masalan: Asosiy, O'zbekcha, Tarjima Kinolar..." 
              value={language} 
              onChange={(e) => setLanguage(e.target.value)} 
              className="w-full bg-surface-container border border-white/10 rounded-xl p-3 text-text-primary focus:border-primary-container focus:ring-1 focus:ring-primary-container focus:outline-none placeholder-text-secondary/50 transition-all" 
            />
          </div>

          <label className="block text-sm font-medium text-text-secondary mb-3">Video manbasini tanlang</label>
          <div className="flex gap-4 mb-6 bg-surface-container p-1 rounded-xl border border-white/5">
            <button
              type="button"
              onClick={() => setUploadMethod('file')}
              className={`flex-1 py-2.5 px-4 rounded-lg text-sm font-medium transition-all flex items-center justify-center gap-2 ${
                uploadMethod === 'file' 
                  ? 'bg-white/10 text-text-primary shadow-sm' 
                  : 'text-text-secondary hover:text-text-primary hover:bg-white/5'
              }`}
            >
              <span className="material-symbols-outlined text-[18px]">upload_file</span>
              Fayl yuklash
            </button>
            <button
              type="button"
              onClick={() => setUploadMethod('message')}
              className={`flex-1 py-2.5 px-4 rounded-lg text-sm font-medium transition-all flex items-center justify-center gap-2 ${
                uploadMethod === 'message' 
                  ? 'bg-white/10 text-text-primary shadow-sm' 
                  : 'text-text-secondary hover:text-text-primary hover:bg-white/5'
              }`}
            >
              <span className="material-symbols-outlined text-[18px]">link</span>
              Telegram Link/ID
            </button>
          </div>

          {uploadMethod === 'file' ? (
            <div className="mb-4 animate-in fade-in slide-in-from-bottom-2 duration-300">
              <label className="block text-sm font-medium text-text-secondary mb-2">Video faylni tanlang</label>
              <input 
                type="file" 
                accept="video/*" 
                ref={fileInputRef} 
                className="w-full bg-surface-container border border-white/10 rounded-xl p-2.5 text-text-primary file:mr-4 file:py-2.5 file:px-5 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-primary-container file:text-text-primary hover:file:bg-primary-container/90 focus:outline-none cursor-pointer file:transition-colors file:cursor-pointer transition-all" 
              />
              {uploadProgress !== null && (
                <div className="mt-4">
                  <div className="flex justify-between text-xs text-text-secondary mb-1">
                    <span>
                      {uploadProgress === 0
                        ? "Server uyg'otilmoqda..."
                        : uploadProgress < 100 
                          ? "Serverga yuklanmoqda..." 
                          : "Telegram kanalga joylanmoqda (Biroz kuting)..."}
                    </span>
                    <span className={uploadProgress === 100 ? "text-green-400" : "text-blue-400"}>
                      {uploadProgress > 0 ? `${uploadProgress}%` : ""}
                    </span>
                  </div>
                  <div className="w-full bg-surface-container-highest rounded-full h-2.5 overflow-hidden border border-white/5">
                    <div 
                      className={`h-full rounded-full transition-all duration-300 ${uploadProgress === 0 ? "bg-yellow-500 animate-pulse w-full" : (uploadProgress === 100 ? "bg-green-500" : "bg-blue-500")}`}
                      style={{ width: uploadProgress === 0 ? "100%" : `${uploadProgress}%` }}
                    >
                      <div className="absolute inset-0 bg-white/20 animate-pulse"></div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="mb-4 animate-in fade-in slide-in-from-bottom-2 duration-300">
              <label className="block text-sm font-medium text-text-secondary mb-2">Storage kanaldagi xabar IDsi yoki Linki</label>
              <input 
                type="text" 
                placeholder="Masalan: 45 yoki https://t.me/c/123/45" 
                value={messageId} 
                onChange={(e) => setMessageId(e.target.value)} 
                className="w-full bg-surface-container border border-white/10 rounded-xl p-3 text-text-primary focus:border-primary-container focus:ring-1 focus:ring-primary-container focus:outline-none placeholder-text-secondary/50 transition-all font-mono text-sm" 
              />
              <p className="mt-3 text-xs text-text-secondary/70 flex items-start gap-1.5">
                <span className="material-symbols-outlined text-[14px] text-primary-container mt-0.5">info</span>
                Video yuklangan bazadagi postning IDsini yoki uning to'liq linkini kiriting.
              </p>
            </div>
          )}

          <div className="flex justify-end gap-3 mt-8 pt-6 border-t border-white/10">
            <button 
              onClick={onClose} 
              disabled={isUploading} 
              className="px-5 py-2.5 text-sm font-medium text-text-secondary bg-transparent border border-white/10 rounded-xl hover:bg-white/5 hover:text-text-primary transition-all disabled:opacity-50"
            >
              Bekor qilish
            </button>
            <button 
              onClick={submitVideo} 
              disabled={isSubmitDisabled} 
              className="px-6 py-2.5 text-sm font-medium text-text-primary bg-primary-container rounded-xl hover:bg-primary-container/90 transition-all shadow-lg shadow-primary-container/20 disabled:opacity-50 disabled:shadow-none flex items-center gap-2"
            >
              {isUploading ? (
                <>
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg> 
                  Yuklanmoqda...
                </>
              ) : (
                <>
                  <span className="material-symbols-outlined text-[18px]">save</span>
                  Saqlash
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
