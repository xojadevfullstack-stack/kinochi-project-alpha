"use client";

import { useState, useRef, useEffect } from "react";
import { fetchApi, uploadWithProgress, HEALTH_URL } from "@/lib/api";

interface VideoUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  entityName: string;
  entityId: number | null;
  uploadEndpoint: string;
  linkEndpoint: string;
  onSuccess: () => void;
}

type UploadPhase =
  | "idle"
  | "uploading"    // fayl server'ga yuklanmoqda (XHR)
  | "processing"   // server Telegram'ga yuklamoqda (polling)
  | "done"
  | "failed";

export default function VideoUploadModal({
  isOpen,
  onClose,
  entityName,
  entityId,
  uploadEndpoint,
  linkEndpoint,
  onSuccess,
}: VideoUploadModalProps) {
  const [uploadMethod, setUploadMethod] = useState<"file" | "message">("file");
  const [messageId, setMessageId] = useState("");
  const [language, setLanguage] = useState("Asosiy");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [phase, setPhase] = useState<UploadPhase>("idle");
  const [uploadProgress, setUploadProgress] = useState(0); // 0-100, XHR progress
  const [jobProgress, setJobProgress] = useState(0);       // 0-100, Telegram progress
  const [jobId, setJobId] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Polling — job tayyor bo'lgunga qadar har 3 sekundda so'rov yuboramiz
  useEffect(() => {
    if (phase === "processing" && jobId && entityId != null) {
      pollingRef.current = setInterval(async () => {
        try {
          const statusEndpoint = uploadEndpoint.replace("/upload-video", `/upload-jobs/${jobId}`);
          const job = await fetchApi(statusEndpoint);

          if (job.status === "done") {
            clearInterval(pollingRef.current!);
            setJobProgress(100);
            setPhase("done");
            onSuccess();
          } else if (job.status === "failed") {
            clearInterval(pollingRef.current!);
            setPhase("failed");
            setErrorMsg(job.error || "Telegram'ga yuklashda xato yuz berdi.");
          } else {
            // processing — progressni yangilaymiz
            setJobProgress(job.progress ?? 50);
          }
        } catch (e: any) {
          // Polling xatosi — keyingi urinishda davom etamiz
          console.warn("Polling error:", e.message);
        }
      }, 3000);

      return () => {
        if (pollingRef.current) clearInterval(pollingRef.current);
      };
    }
  }, [phase, jobId, entityId, uploadEndpoint, onSuccess]);

  // Modal yopilganda tozalaymiz
  useEffect(() => {
    if (!isOpen) {
      if (pollingRef.current) clearInterval(pollingRef.current);
      setPhase("idle");
      setUploadProgress(0);
      setJobProgress(0);
      setJobId(null);
      setErrorMsg(null);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleClose = () => {
    if (phase === "uploading" || phase === "processing") return; // upload paytida yopib bo'lmaydi
    onClose();
  };

  const submitVideo = async () => {
    setErrorMsg(null);

    try {
      if (uploadMethod === "file") {
        const file = fileInputRef.current?.files?.[0];
        if (!file) { alert("Iltimos, video faylni tanlang!"); return; }

        // ── 1-bosqich: fayl → server (XHR progress) ──
        setPhase("uploading");
        setUploadProgress(0);

        const response = await uploadWithProgress(
          uploadEndpoint,
          file,
          (pct) => setUploadProgress(pct),
          { language }
        );

        // Server job_id qaytardi
        if (response?.job_id) {
          setJobId(response.job_id);
          setJobProgress(5);
          setPhase("processing"); // → polling boshlanadi
        } else {
          // Eski format (backup) — darhol done
          setPhase("done");
          onSuccess();
        }
      } else {
        // ── Telegram link orqali ──
        let parsedId: number | null = null;
        const inputStr = messageId.trim();

        if (/^\d+$/.test(inputStr)) {
          parsedId = parseInt(inputStr);
        } else {
          try {
            const url = new URL(inputStr);
            const parts = url.pathname.split("/").filter(Boolean);
            const last = parts[parts.length - 1];
            if (/^\d+$/.test(last)) parsedId = parseInt(last);
          } catch { /* not a url */ }
        }

        if (!parsedId || isNaN(parsedId)) {
          alert("Iltimos, yaroqli Telegram xabar ID sini yoki to'g'ri linkni kiriting!");
          return;
        }

        setPhase("uploading");
        await fetchApi(linkEndpoint, {
          method: "POST",
          body: JSON.stringify({ message_id: parsedId, language }),
        });
        setPhase("done");
        onSuccess();
        setTimeout(() => onClose(), 1500);
      }
    } catch (e: any) {
      setPhase("failed");
      setErrorMsg(e.message || "Noma'lum xato");
    }
  };

  const isSubmitDisabled =
    phase === "uploading" ||
    phase === "processing" ||
    (uploadMethod === "message" && !messageId.trim()) ||
    !language.trim();

  // ── Progress bar rendering ──
  const renderProgress = () => {
    if (phase === "uploading") {
      return (
        <div className="mt-5 p-4 bg-surface-container rounded-xl border border-white/10 animate-in fade-in duration-300">
          <div className="flex justify-between text-xs text-text-secondary mb-2 font-medium">
            <span className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-blue-400 animate-pulse" />
              Serverga yuklanmoqda...
            </span>
            <span className="text-blue-400">{uploadProgress}%</span>
          </div>
          <div className="w-full bg-white/10 rounded-full h-2 overflow-hidden">
            <div
              className="h-full bg-blue-500 rounded-full transition-all duration-300"
              style={{ width: `${uploadProgress}%` }}
            />
          </div>
          <p className="text-xs text-text-secondary/60 mt-2">
            ⚡ Fayl qabul qilinmoqda — iltimos kutib turing...
          </p>
        </div>
      );
    }

    if (phase === "processing") {
      return (
        <div className="mt-5 p-4 bg-surface-container rounded-xl border border-white/10 animate-in fade-in duration-300">
          <div className="flex justify-between text-xs text-text-secondary mb-2 font-medium">
            <span className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-purple-400 animate-pulse" />
              Telegram'ga yuklanmoqda (orqa fonda)...
            </span>
            <span className="text-purple-400">{jobProgress}%</span>
          </div>
          <div className="w-full bg-white/10 rounded-full h-2 overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-purple-500 to-blue-500 rounded-full transition-all duration-500"
              style={{ width: `${Math.max(jobProgress, 8)}%` }}
            />
          </div>
          <p className="text-xs text-yellow-400/80 mt-2">
            🚀 Server Telegram'ga yuklayapti — sahifani yopmang, biroz kuting...
          </p>
        </div>
      );
    }

    if (phase === "done") {
      return (
        <div className="mt-5 p-4 bg-green-500/10 rounded-xl border border-green-500/30 animate-in fade-in duration-300">
          <div className="flex items-center gap-2 text-green-400 font-medium text-sm">
            <span>✅</span>
            <span>Video muvaffaqiyatli saqlandi!</span>
          </div>
        </div>
      );
    }

    if (phase === "failed") {
      return (
        <div className="mt-5 p-4 bg-red-500/10 rounded-xl border border-red-500/30 animate-in fade-in duration-300">
          <p className="text-red-400 font-medium text-sm">❌ Xato yuz berdi:</p>
          <p className="text-red-300/80 text-xs mt-1 break-words">{errorMsg}</p>
          <button
            onClick={() => { setPhase("idle"); setErrorMsg(null); setJobId(null); }}
            className="mt-3 text-xs text-red-400 underline hover:text-red-300"
          >
            Qaytadan urinish
          </button>
        </div>
      );
    }

    return null;
  };

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-surface-container-low rounded-2xl shadow-2xl w-full max-w-lg border border-white/10 overflow-hidden">
        {/* Header */}
        <div className="px-6 py-5 border-b border-white/10 flex justify-between items-center">
          <h3 className="text-lg font-bold text-text-primary">Video yuklash yoki ulash</h3>
          <button
            onClick={handleClose}
            disabled={phase === "uploading" || phase === "processing"}
            className="text-text-secondary hover:text-text-primary transition-colors disabled:opacity-30"
          >
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="p-6">
          {/* Studiya nomi */}
          <div className="mb-5">
            <label className="block text-sm font-medium text-text-secondary mb-2">
              Studiya nomi (Til)
            </label>
            <input
              type="text"
              placeholder="Masalan: Asosiy, O'zbekcha, Tarjima Kinolar..."
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              disabled={phase !== "idle" && phase !== "failed"}
              className="w-full bg-surface-container border border-white/10 rounded-xl p-3 text-text-primary focus:border-primary-container focus:ring-1 focus:ring-primary-container focus:outline-none placeholder-text-secondary/50 transition-all disabled:opacity-50"
            />
          </div>

          {/* Method tanlash */}
          <label className="block text-sm font-medium text-text-secondary mb-3">Video manbasini tanlang</label>
          <div className="flex gap-1 mb-5 bg-surface-container rounded-xl p-1">
            <button
              onClick={() => setUploadMethod("file")}
              disabled={phase !== "idle" && phase !== "failed"}
              className={`flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg text-sm font-medium transition-all ${
                uploadMethod === "file"
                  ? "bg-white/10 text-text-primary shadow-sm"
                  : "text-text-secondary hover:text-text-primary hover:bg-white/5"
              }`}
            >
              <span className="material-symbols-outlined text-[18px]">upload_file</span>
              Fayl yuklash
            </button>
            <button
              onClick={() => setUploadMethod("message")}
              disabled={phase !== "idle" && phase !== "failed"}
              className={`flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg text-sm font-medium transition-all ${
                uploadMethod === "message"
                  ? "bg-white/10 text-text-primary shadow-sm"
                  : "text-text-secondary hover:text-text-primary hover:bg-white/5"
              }`}
            >
              <span className="material-symbols-outlined text-[18px]">link</span>
              Telegram Link/ID
            </button>
          </div>

          {/* File input yoki Message ID */}
          {uploadMethod === "file" ? (
            <div className="mb-2 animate-in fade-in slide-in-from-bottom-2 duration-300">
              <label className="block text-sm font-medium text-text-secondary mb-2">Video faylni tanlang</label>
              <input
                type="file"
                accept="video/*"
                ref={fileInputRef}
                disabled={phase !== "idle" && phase !== "failed"}
                className="w-full bg-surface-container border border-white/10 rounded-xl p-2.5 text-text-primary file:mr-4 file:py-2.5 file:px-5 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-primary-container file:text-text-primary hover:file:bg-primary-container/90 focus:outline-none cursor-pointer file:transition-colors file:cursor-pointer transition-all disabled:opacity-50"
              />
              <p className="text-xs text-text-secondary/60 mt-2">Maksimal fayl hajmi: 50 MB</p>
              {renderProgress()}
            </div>
          ) : (
            <div className="mb-2 animate-in fade-in slide-in-from-bottom-2 duration-300">
              <label className="block text-sm font-medium text-text-secondary mb-2">
                Storage kanaldagi xabar IDsi yoki Linki
              </label>
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
              {renderProgress()}
            </div>
          )}

          {/* Buttons */}
          <div className="flex justify-end gap-3 mt-6 pt-5 border-t border-white/10">
            <button
              onClick={handleClose}
              disabled={phase === "uploading" || phase === "processing"}
              className="px-5 py-2.5 text-sm font-medium text-text-secondary bg-transparent border border-white/10 rounded-xl hover:bg-white/5 hover:text-text-primary transition-all disabled:opacity-30"
            >
              {phase === "done" ? "Yopish" : "Bekor qilish"}
            </button>
            {phase !== "done" && (
              <button
                onClick={submitVideo}
                disabled={isSubmitDisabled}
                className="px-5 py-2.5 text-sm font-medium text-white bg-primary-container border border-transparent rounded-xl hover:opacity-90 disabled:opacity-40 flex items-center gap-2 transition-all"
              >
                {(phase === "uploading" || phase === "processing") ? (
                  <>
                    <svg className="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    {phase === "uploading" ? "Yuklanmoqda..." : "Jarayonda..."}
                  </>
                ) : "Saqlash"}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
