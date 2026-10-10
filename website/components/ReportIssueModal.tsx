"use client";

import { useState, useRef, ChangeEvent, DragEvent } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

interface ReportIssueModalProps {
  isOpen: boolean;
  onClose: () => void;
  mediaType: "movie" | "series";
  movieId?: number;
  seriesId?: number;
  episodeId?: number;
  mediaTitle: string;
  seasonNumber?: number;
  episodeNumber?: number;
}

const ISSUE_OPTIONS = [
  { id: "poster_xato", label: "🖼 Poster noto'g'ri" },
  { id: "dublikat", label: "👥 Dublikat" },
  { id: "video_xato", label: "🎞 Video noto'g'ri" },
  { id: "ovoz_xato", label: "🔇 Ovozda muammo" },
  { id: "malumot_xato", label: "📝 Ma'lumot xato" },
  { id: "treyler_xato", label: "🍿 Treyler ishlamayapti" },
  { id: "boshqa", label: "✍️ Boshqa xatolik" },
];

export default function ReportIssueModal({
  isOpen,
  onClose,
  mediaType,
  movieId,
  seriesId,
  episodeId,
  mediaTitle,
  seasonNumber,
  episodeNumber,
}: ReportIssueModalProps) {
  const [selectedIssue, setSelectedIssue] = useState<string>("boshqa");
  const [description, setDescription] = useState<string>("");
  const [file, setFile] = useState<File | null>(null);
  const [filePreview, setFilePreview] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  const handleFileChange = (newFile: File | null) => {
    if (!newFile) {
      setFile(null);
      setFilePreview(null);
      return;
    }

    const isImage = newFile.type.startsWith("image/");
    const isVideo = newFile.type.startsWith("video/");

    if (!isImage && !isVideo) {
      setErrorMessage("Faqat rasm (PNG, JPG, WEBP) yoki video (MP4, WEBM, MOV) yuklashingiz mumkin.");
      return;
    }

    if (isImage && newFile.size > 10 * 1024 * 1024) {
      setErrorMessage("Rasm hajmi 10 MB dan oshmasligi kerak.");
      return;
    }

    if (isVideo && newFile.size > 50 * 1024 * 1024) {
      setErrorMessage("Video hajmi 50 MB dan oshmasligi kerak.");
      return;
    }

    setErrorMessage(null);
    setFile(newFile);

    if (isImage) {
      const reader = new FileReader();
      reader.onload = (e) => {
        setFilePreview(e.target?.result as string);
      };
      reader.readAsDataURL(newFile);
    } else {
      setFilePreview(null);
    }
  };

  const onDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const onDragLeave = () => {
    setIsDragging(false);
  };

  const onDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileChange(e.dataTransfer.files[0]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setSuccessMessage(null);
    setLoading(true);

    try {
      const formData = new FormData();
      formData.append("media_type", mediaType);
      formData.append("issue_type", selectedIssue);

      if (movieId) formData.append("movie_id", String(movieId));
      if (seriesId) formData.append("series_id", String(seriesId));
      if (episodeId) formData.append("episode_id", String(episodeId));
      if (description.trim()) formData.append("description", description.trim());
      if (file) formData.append("file", file);

      const res = await fetch(`${API_URL}/reports`, {
        method: "POST",
        body: formData,
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || "Xatolik haqida xabar yuborishda muammo yuz berdi.");
      }

      setSuccessMessage("✅ Rahmat! Xabaringiz adminga yetkazildi va tez orada ko'rib chiqiladi.");
      setTimeout(() => {
        onClose();
        // Reset form
        setSelectedIssue("boshqa");
        setDescription("");
        setFile(null);
        setFilePreview(null);
        setSuccessMessage(null);
      }, 2200);
    } catch (err: any) {
      setErrorMessage(err.message || "Xatolik yuz berdi. Bir ozdan so'ng qayta urinib ko'ring.");
    } finally {
      setLoading(false);
    }
  };

  const epContextText = episodeNumber
    ? `(${seasonNumber || 1}-mavsum, ${episodeNumber}-qism)`
    : "";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-200">
      <div className="relative w-full max-w-xl max-h-[92vh] overflow-y-auto bg-surface-container-high border border-white/10 rounded-2xl p-5 sm:p-7 shadow-2xl text-left custom-scrollbar">
        {/* Header */}
        <div className="flex items-start justify-between pb-4 border-b border-white/10 mb-5">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-amber-500/20 border border-amber-500/30 flex items-center justify-center text-amber-400 shrink-0">
              <span className="material-symbols-outlined text-2xl">warning</span>
            </div>
            <div>
              <h2 className="font-display text-lg sm:text-xl font-bold text-white tracking-tight">
                Xatolik haqida xabar berish
              </h2>
              <p className="text-xs text-text-secondary truncate max-w-xs sm:max-w-md">
                {mediaTitle} {epContextText}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            type="button"
            className="p-1.5 text-text-secondary hover:text-white rounded-lg hover:bg-white/5 transition-colors"
            aria-label="Yopish"
          >
            <span className="material-symbols-outlined text-xl">close</span>
          </button>
        </div>

        {/* Success Notice */}
        {successMessage ? (
          <div className="py-8 text-center flex flex-col items-center justify-center space-y-3">
            <span className="material-symbols-outlined text-5xl text-emerald-400 animate-bounce">
              task_alt
            </span>
            <p className="font-bold text-white text-base sm:text-lg">{successMessage}</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-5">
            {/* 1. Issue Type Chips */}
            <div>
              <label className="block text-xs sm:text-sm font-semibold text-white/90 mb-2.5">
                Muammo turini tanlang:
              </label>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                {ISSUE_OPTIONS.map((opt) => {
                  const isSelected = selectedIssue === opt.id;
                  return (
                    <button
                      key={opt.id}
                      type="button"
                      onClick={() => setSelectedIssue(opt.id)}
                      className={`px-3 py-2.5 rounded-xl text-xs sm:text-sm font-medium border text-left transition-all flex items-center justify-between ${
                        isSelected
                          ? "bg-amber-500/20 border-amber-500 text-amber-300 shadow-sm shadow-amber-500/20 font-bold"
                          : "bg-surface-container-lowest border-white/5 text-text-secondary hover:text-white hover:bg-white/5"
                      }`}
                    >
                      <span className="truncate">{opt.label}</span>
                      {isSelected && (
                        <span className="material-symbols-outlined text-xs text-amber-400 shrink-0 ml-1">
                          check
                        </span>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* 2. Description Textarea */}
            <div>
              <label className="block text-xs sm:text-sm font-semibold text-white/90 mb-1.5">
                Xatolik haqida izoh yozing:
              </label>
              <textarea
                rows={3}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="1-qism 12-daqiqasida ovoz yo'qolib qolyapti yoki video boshqa kinoga tegishli..."
                className="w-full bg-surface-container-lowest border border-white/10 rounded-xl p-3 text-sm text-text-primary placeholder:text-text-secondary/50 focus:outline-none focus:ring-2 focus:ring-amber-500/50 focus:border-amber-500"
              />
            </div>

            {/* 3. File Upload Area */}
            <div>
              <label className="block text-xs sm:text-sm font-semibold text-white/90 mb-1.5 flex items-center justify-between">
                <span>📎 Skrinshot yoki video biriktirish (ixtiyoriy):</span>
                <span className="text-[11px] text-text-secondary font-normal">
                  Rasm max 10MB • Video max 50MB
                </span>
              </label>

              <input
                type="file"
                ref={fileInputRef}
                onChange={(e: ChangeEvent<HTMLInputElement>) => {
                  if (e.target.files && e.target.files[0]) {
                    handleFileChange(e.target.files[0]);
                  }
                }}
                accept="image/png,image/jpeg,image/webp,video/mp4,video/webm,video/quicktime"
                className="hidden"
              />

              {!file ? (
                <div
                  onDragOver={onDragOver}
                  onDragLeave={onDragLeave}
                  onDrop={onDrop}
                  onClick={() => fileInputRef.current?.click()}
                  className={`border-2 border-dashed rounded-xl p-4 sm:p-5 text-center cursor-pointer transition-all flex flex-col items-center justify-center gap-1.5 ${
                    isDragging
                      ? "border-amber-500 bg-amber-500/10"
                      : "border-white/15 bg-surface-container-lowest hover:border-white/30 hover:bg-white/5"
                  }`}
                >
                  <span className="material-symbols-outlined text-3xl text-amber-400/80">
                    add_photo_alternate
                  </span>
                  <p className="text-xs sm:text-sm text-text-primary font-medium">
                    📸 Rasm (PNG, JPG) yoki 🎥 Video (MP4) yuklang
                  </p>
                  <p className="text-[11px] text-text-secondary">
                    Faylni bu yerga tashlang yoki tanlash uchun bosing
                  </p>
                </div>
              ) : (
                <div className="bg-surface-container-lowest border border-white/10 rounded-xl p-3 flex items-center justify-between gap-3">
                  <div className="flex items-center gap-3 min-w-0">
                    {filePreview ? (
                      <img
                        src={filePreview}
                        alt="Preview"
                        className="w-12 h-12 rounded-lg object-cover border border-white/10 shrink-0"
                      />
                    ) : (
                      <div className="w-12 h-12 rounded-lg bg-white/5 border border-white/10 flex items-center justify-center shrink-0">
                        <span className="material-symbols-outlined text-2xl text-amber-400">
                          videocam
                        </span>
                      </div>
                    )}
                    <div className="min-w-0">
                      <p className="text-xs sm:text-sm font-semibold text-white truncate">
                        {file.name}
                      </p>
                      <p className="text-[11px] text-text-secondary">
                        {(file.size / (1024 * 1024)).toFixed(1)} MB
                      </p>
                    </div>
                  </div>

                  <button
                    type="button"
                    onClick={() => handleFileChange(null)}
                    className="p-1.5 text-text-secondary hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors"
                    title="Faylni o'chirish"
                  >
                    <span className="material-symbols-outlined text-lg">delete</span>
                  </button>
                </div>
              )}
            </div>

            {/* Error Message */}
            {errorMessage && (
              <div className="p-3 bg-red-500/15 border border-red-500/30 rounded-xl text-red-300 text-xs sm:text-sm flex items-center gap-2">
                <span className="material-symbols-outlined text-base">error</span>
                <span>{errorMessage}</span>
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-gradient-to-r from-amber-600 to-amber-500 hover:from-amber-500 hover:to-amber-400 active:scale-[0.99] disabled:opacity-50 text-white font-bold py-3.5 px-6 rounded-xl text-sm transition-all shadow-lg shadow-amber-600/30 flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <span className="animate-spin material-symbols-outlined text-lg">
                    progress_activity
                  </span>
                  <span>Yuborilmoqda...</span>
                </>
              ) : (
                <>
                  <span className="material-symbols-outlined text-lg">rocket_launch</span>
                  <span className="tracking-wide">XABARNI YUBORISH</span>
                </>
              )}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
