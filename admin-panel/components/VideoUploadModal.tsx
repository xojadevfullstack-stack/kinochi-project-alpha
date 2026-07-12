"use client";

import { useState, useRef } from "react";
import { fetchApi, uploadWithProgress } from "@/lib/api";

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
        setUploadProgress(0);
        
        await uploadWithProgress(
          uploadEndpoint,
          file,
          (percent) => setUploadProgress(percent),
          { language }
        );
        
        alert(`${entityName} fayli muvaffaqiyatli yuklandi!`);
      } else {
        const parsedId = parseInt(messageId);
        if (!messageId || isNaN(parsedId)) {
          alert("Iltimos, yaroqli Telegram xabar ID sini kiriting (faqat raqam)!");
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

  const isSubmitDisabled = isUploading || (uploadMethod === 'message' && (!messageId || isNaN(Number(messageId)))) || !language.trim();

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-lg mx-4 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100 flex justify-between items-center bg-gray-50">
          <h3 className="text-lg font-bold text-gray-800">Video yuklash yoki ulash</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 transition-colors">
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <div className="p-6">
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">Studiya nomi (Til)</label>
            <input 
              type="text" 
              placeholder="Masalan: Asosiy, O'zbekcha, Tarjima Kinolar..." 
              value={language} 
              onChange={(e) => setLanguage(e.target.value)} 
              className="w-full border border-gray-300 rounded-lg p-2.5 focus:ring-2 focus:ring-blue-500" 
            />
          </div>

          <label className="block text-sm font-medium text-gray-700 mb-3">Video manbasini tanlang</label>
          <div className="flex gap-6 mb-6">
            <label className="flex items-center gap-2 cursor-pointer">
              <input 
                type="radio" 
                value="file" 
                checked={uploadMethod === 'file'} 
                onChange={() => setUploadMethod('file')} 
                className="w-4 h-4 text-blue-600 focus:ring-blue-500 border-gray-300" 
              />
              <span className="text-sm text-gray-700">Fayl yuklash</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input 
                type="radio" 
                value="message" 
                checked={uploadMethod === 'message'} 
                onChange={() => setUploadMethod('message')} 
                className="w-4 h-4 text-blue-600 focus:ring-blue-500 border-gray-300" 
              />
              <span className="text-sm text-gray-700">Telegram ID orqali</span>
            </label>
          </div>

          {uploadMethod === 'file' ? (
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">Video faylni tanlang</label>
              <input 
                type="file" 
                accept="video/*" 
                ref={fileInputRef} 
                className="w-full border border-gray-300 rounded-lg p-2.5 focus:ring-2 focus:ring-blue-500" 
              />
              {uploadProgress !== null && (
                <div className="mt-4">
                  <div className="flex justify-between text-xs text-gray-500 mb-1">
                    <span>Yuklanmoqda...</span>
                    <span>{uploadProgress}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-blue-600 h-2 rounded-full transition-all duration-300" 
                      style={{ width: `${uploadProgress}%` }}
                    ></div>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">Storage kanaldagi xabar IDsi (Message ID)</label>
              <input 
                type="number" 
                placeholder="Masalan: 45" 
                value={messageId} 
                onChange={(e) => setMessageId(e.target.value)} 
                className="w-full border border-gray-300 rounded-lg p-2.5 focus:ring-2 focus:ring-blue-500" 
              />
              <p className="mt-2 text-xs text-gray-500">Video yuklangan bazadagi (storage channel) postning IDsini kiriting.</p>
            </div>
          )}

          <div className="flex justify-end gap-3 mt-6 pt-4 border-t border-gray-100">
            <button 
              onClick={onClose} 
              disabled={isUploading} 
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
            >
              Bekor qilish
            </button>
            <button 
              onClick={submitVideo} 
              disabled={isSubmitDisabled} 
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
            >
              {isUploading ? (
                <>
                  <svg className="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg> 
                  Yuklanmoqda...
                </>
              ) : "Saqlash"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
