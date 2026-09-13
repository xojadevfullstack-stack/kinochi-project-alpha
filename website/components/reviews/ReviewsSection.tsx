"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth/AuthProvider";
import { getReviews, getMyReview, submitReview, ReviewItem } from "@/lib/api/reviews";
import TelegramLoginWidget from "../auth/TelegramLoginWidget";

interface ReviewsSectionProps {
  movieId?: number;
  movieCode?: string;
  seriesId?: number;
  episodeId?: number;
  imdbRating?: number | null;
  initialKinochiRating?: number | null;
  initialVotesCount?: number;
}

const RATING_LABELS: Record<number, string> = {
  1: "1/10 - Juda yomon",
  2: "2/10 - Qoniqarsiz",
  3: "3/10 - Yomon",
  4: "4/10 - Bo'ladi",
  5: "5/10 - O'rtacha",
  6: "6/10 - Qiziqarli",
  7: "7/10 - Yaxshi",
  8: "8/10 - Juda yaxshi",
  9: "9/10 - Ajoyib",
  10: "10/10 - Shodivona (Masterpiece)",
};

export default function ReviewsSection({
  movieId,
  movieCode,
  seriesId,
  episodeId,
  imdbRating,
  initialKinochiRating,
  initialVotesCount = 0,
}: ReviewsSectionProps) {
  const { status, user } = useAuth();
  const [reviews, setReviews] = useState<ReviewItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  const [kinochiRating, setKinochiRating] = useState<number | null>(initialKinochiRating ?? null);
  const [votesCount, setVotesCount] = useState<number>(initialVotesCount);

  const [myRating, setMyRating] = useState<number>(10);
  const [hoveredRating, setHoveredRating] = useState<number | null>(null);
  const [commentText, setCommentText] = useState("");
  const [formOpen, setFormOpen] = useState(false);
  const [alreadyReviewed, setAlreadyReviewed] = useState(false);
  const [statusMessage, setStatusMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      const data = await getReviews({ movieId, movieCode, seriesId, episodeId, limit: 30 });
      setReviews(data.items || []);
      if (data.average_rating !== undefined) {
        setKinochiRating(data.average_rating);
      }
      if (data.votes_count !== undefined) {
        setVotesCount(data.votes_count);
      }

      if (status === "authenticated") {
        const my = await getMyReview({ movieId, movieCode, seriesId, episodeId });
        if (my) {
          setMyRating(my.rating);
          setCommentText(my.comment || "");
          setAlreadyReviewed(true);
        }
      }
    } catch (err) {
      console.error("Error loading reviews:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [movieId, movieCode, seriesId, episodeId, status]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (status !== "authenticated") {
      setStatusMessage({ type: "error", text: "Baholash uchun Telegram orqali tizimga kiring." });
      return;
    }

    try {
      setSubmitting(true);
      setStatusMessage(null);
      const res = await submitReview({
        movieId,
        seriesId,
        episodeId,
        rating: myRating,
        comment: commentText.trim(),
      });

      if (res && res.kinochi_rating !== undefined) {
        setKinochiRating(res.kinochi_rating);
        const newVotes = res.kinochi_votes_count || votesCount + 1;
        setVotesCount(newVotes);

        if (typeof window !== "undefined") {
          window.dispatchEvent(
            new CustomEvent("kinochi:rating_updated", {
              detail: {
                rating: res.kinochi_rating,
                votesCount: newVotes,
              },
            })
          );
        }
      }

      setStatusMessage({ type: "success", text: "Baho va fikringiz muvaffaqiyatli saqlandi! Rahmat." });
      setAlreadyReviewed(true);
      setFormOpen(false);
      await loadData();
    } catch (err: any) {
      setStatusMessage({ type: "error", text: err.message || "Xatolik yuz berdi." });
    } finally {
      setSubmitting(false);
    }
  };

  const activeRating = hoveredRating || myRating;

  return (
    <section className="max-w-container-max mx-auto px-gutter py-12 border-t border-white/5">
      <div className="flex flex-col gap-8">
        {/* Section Header & Rating Overview Banner */}
        <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6 bg-surface-container/60 p-5 sm:p-6 md:p-8 rounded-3xl border border-white/5">
          <div className="space-y-1.5 max-w-xl">
            <div className="flex items-center gap-2.5">
              <span className="material-symbols-outlined text-rating-gold text-2xl" style={{ fontVariationSettings: "'FILL' 1" }}>
                stars
              </span>
              <h2 className="text-xl sm:text-2xl md:text-3xl font-display-hero font-bold text-white tracking-tight">
                Baholar va Sharhlar
              </h2>
            </div>
            <p className="text-xs sm:text-sm text-text-secondary leading-relaxed">
              Ushbu asar haqida tomoshabinlar va mutaxassislar fikrlari. Siz ham o'z bahoyingizni qoldiring!
            </p>
          </div>

          {/* Score Badges Comparison & Action Button */}
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 sm:gap-4 w-full lg:w-auto">
            {/* 2-Column Responsive Score Cards */}
            <div className="grid grid-cols-2 gap-2.5 sm:gap-3 w-full sm:w-auto">
              {/* IMDb Badge */}
              <div className="flex items-center gap-2.5 sm:gap-3.5 bg-black/40 backdrop-blur-md px-3 sm:px-4 py-3 rounded-2xl border border-white/10 shadow-sm">
                <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-xl bg-amber-400/15 border border-amber-400/25 flex items-center justify-center text-amber-400 font-black text-[11px] sm:text-xs shrink-0 tracking-wider">
                  IMDb
                </div>
                <div className="min-w-0">
                  <div className="flex items-center gap-1">
                    <span className="material-symbols-outlined text-rating-gold text-[15px] sm:text-[18px]" style={{ fontVariationSettings: "'FILL' 1" }}>
                      star
                    </span>
                    <span className="text-sm sm:text-lg font-bold text-white tracking-tight">
                      {imdbRating ? `${imdbRating}` : "N/A"}
                    </span>
                    <span className="text-[10px] sm:text-xs text-white/40">/10</span>
                  </div>
                  <span className="text-[10px] sm:text-[11px] text-white/50 uppercase tracking-wider font-semibold block truncate">
                    Rasmiy IMDb
                  </span>
                </div>
              </div>

              {/* Kinochi Community Badge */}
              <div className="flex items-center gap-2.5 sm:gap-3.5 bg-sky-500/10 backdrop-blur-md px-3 sm:px-4 py-3 rounded-2xl border border-sky-500/20 shadow-sm shadow-sky-500/5">
                <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-xl bg-sky-500/20 border border-sky-500/30 flex items-center justify-center text-sky-400 font-black text-[10px] sm:text-[11px] shrink-0 tracking-wider">
                  Kinochi
                </div>
                <div className="min-w-0">
                  <div className="flex items-center gap-1">
                    <span className="material-symbols-outlined text-sky-400 text-[15px] sm:text-[18px]" style={{ fontVariationSettings: "'FILL' 1" }}>
                      hotel_class
                    </span>
                    <span className="text-sm sm:text-lg font-bold text-white tracking-tight truncate">
                      {kinochiRating !== null ? `${kinochiRating}` : "Yangi"}
                    </span>
                    {kinochiRating !== null && <span className="text-[10px] sm:text-xs text-white/40">/10</span>}
                  </div>
                  <span className="text-[10px] sm:text-[11px] text-sky-400/80 font-semibold block truncate">
                    {votesCount > 0 ? `${votesCount} ta ovoz` : "Baholanmagan"}
                  </span>
                </div>
              </div>
            </div>

            {/* Action button */}
            <button
              onClick={() => setFormOpen(!formOpen)}
              className={`w-full sm:w-auto flex items-center justify-center gap-2 px-5 py-3 sm:py-3.5 rounded-xl sm:rounded-2xl font-bold text-xs sm:text-sm tracking-wide uppercase transition-all shadow-md active:scale-95 cursor-pointer shrink-0 ${
                formOpen
                  ? "bg-white/15 hover:bg-white/20 text-white border border-white/20"
                  : "bg-white hover:bg-white/90 text-slate-950 shadow-white/10"
              }`}
            >
              <span className="material-symbols-outlined text-[18px]">
                {formOpen ? "close" : "rate_review"}
              </span>
              <span>{alreadyReviewed ? "Bahoni yangilash" : "Fikr bildirish"}</span>
            </button>
          </div>
        </div>

        {/* Status Message */}
        {statusMessage && (
          <div
            className={`p-4 rounded-2xl text-sm font-semibold flex items-center gap-2 ${
              statusMessage.type === "success"
                ? "bg-green-500/10 border border-green-500/30 text-green-400"
                : "bg-red-500/10 border border-red-500/30 text-red-400"
            }`}
          >
            <span className="material-symbols-outlined text-base">
              {statusMessage.type === "success" ? "check_circle" : "error"}
            </span>
            {statusMessage.text}
          </div>
        )}

        {/* Review Form Drawer / Panel */}
        {formOpen && (
          <div className="bg-surface-container/80 p-5 sm:p-6 md:p-8 rounded-3xl border border-white/10 shadow-xl shadow-black/30 transition-all">
            {status !== "authenticated" ? (
              <div className="flex flex-col items-center justify-center py-8 text-center gap-4">
                <span className="material-symbols-outlined text-5xl text-sky-400">lock</span>
                <div>
                  <h3 className="text-lg font-bold text-white">Fikr va baho qoldirish uchun tizimga kiring</h3>
                  <p className="text-sm text-text-secondary mt-1">
                    Telegram orqali 1 ta bosishda hisobingizga kiring va o'z sharhingizni qoldiring.
                  </p>
                </div>
                <TelegramLoginWidget />
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="flex flex-col gap-6">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-white/5 pb-4">
                  <div>
                    <h3 className="text-lg font-bold text-white">
                      {alreadyReviewed ? "O'z sharhingizni tahrirlash" : "Ushbu asarga baho bering"}
                    </h3>
                    <p className="text-xs text-text-secondary mt-0.5">
                      1 dan 10 gacha yulduz tanlang va fikringizni yozing
                    </p>
                  </div>

                  {/* Selected rating badge */}
                  <div className="flex items-center gap-2 bg-black/40 px-4 py-2 rounded-xl border border-white/10 shrink-0">
                    <span className="text-xs font-bold text-amber-400">
                      {RATING_LABELS[activeRating] || `${activeRating}/10`}
                    </span>
                  </div>
                </div>

                {/* 1 to 10 Star Rating Selector */}
                <div className="flex flex-col gap-2">
                  <label className="text-xs font-bold uppercase tracking-wider text-text-secondary">
                    Bahoingiz (1 - 10):
                  </label>
                  <div className="flex flex-wrap items-center gap-1.5 sm:gap-2">
                    {Array.from({ length: 10 }, (_, i) => i + 1).map((val) => (
                      <button
                        key={val}
                        type="button"
                        onClick={() => setMyRating(val)}
                        onMouseEnter={() => setHoveredRating(val)}
                        onMouseLeave={() => setHoveredRating(null)}
                        className={`w-9 h-9 sm:w-11 sm:h-11 rounded-xl flex items-center justify-center transition-all cursor-pointer font-bold text-sm ${
                          val <= activeRating
                            ? "bg-rating-gold text-black shadow-lg shadow-rating-gold/30 scale-105"
                            : "bg-white/5 text-text-secondary hover:bg-white/10 hover:text-white"
                        }`}
                      >
                        {val}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Comment Textarea */}
                <div className="flex flex-col gap-2">
                  <label className="text-xs font-bold uppercase tracking-wider text-text-secondary">
                    Sharhingiz (ixtiyoriy):
                  </label>
                  <textarea
                    value={commentText}
                    onChange={(e) => setCommentText(e.target.value)}
                    rows={4}
                    maxLength={1000}
                    placeholder="Asar sizga qanday taassurot qoldirdi? Aktyorlar mahorati, syujet va voqealar haqida nima deya olasiz?.."
                    className="w-full bg-background-obsidian/80 border border-white/10 rounded-2xl p-4 text-sm text-white placeholder:text-text-secondary focus:border-sky-500/50 focus:outline-none transition-all resize-none"
                  />
                  <span className="text-[11px] text-text-secondary text-right">
                    {commentText.length} / 1000 belgi
                  </span>
                </div>

                {/* Form Buttons */}
                <div className="flex items-center justify-end gap-3 pt-2">
                  <button
                    type="button"
                    onClick={() => setFormOpen(false)}
                    className="px-5 py-2.5 rounded-xl text-sm font-semibold text-text-secondary hover:text-white transition-colors cursor-pointer"
                  >
                    Bekor qilish
                  </button>
                  <button
                    type="submit"
                    disabled={submitting}
                    className="px-6 py-2.5 rounded-xl text-sm font-bold bg-sky-500 hover:bg-sky-400 text-slate-950 transition-all flex items-center gap-2 disabled:opacity-50 cursor-pointer shadow-lg shadow-sky-500/20"
                  >
                    {submitting ? (
                      <>
                        <div className="w-4 h-4 rounded-full border-2 border-black/30 border-t-black animate-spin"></div>
                        <span>Saqlanmoqda...</span>
                      </>
                    ) : (
                      <>
                        <span className="material-symbols-outlined text-[18px]">send</span>
                        <span>Yuborish</span>
                      </>
                    )}
                  </button>
                </div>
              </form>
            )}
          </div>
        )}

        {/* Reviews List */}
        <div className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <span className="material-symbols-outlined text-sky-400 text-xl">comment</span>
              Foydalanuvchilar fikrlari ({reviews.length})
            </h3>
          </div>

          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="w-8 h-8 rounded-full border-2 border-sky-400 border-t-transparent animate-spin"></div>
            </div>
          ) : reviews.length === 0 ? (
            <div className="text-center py-12 bg-surface-container/30 rounded-3xl border border-white/5 p-6 flex flex-col items-center gap-2">
              <span className="material-symbols-outlined text-5xl text-text-secondary/50">chat_bubble_outline</span>
              <p className="font-bold text-white">Hozircha sharhlar mavjud emas</p>
              <p className="text-xs text-text-secondary max-w-sm">
                Birinchi bo'lib ushbu film/serial haqida o'z fikringiz va bahoyingizni qoldiring!
              </p>
              <button
                onClick={() => setFormOpen(true)}
                className="mt-2 text-xs font-bold text-sky-400 hover:text-sky-300 hover:underline cursor-pointer"
              >
                + Fikr qoldirish
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {reviews.map((r) => (
                <div
                  key={r.id}
                  className="bg-surface-container/40 p-5 rounded-2xl border border-white/5 flex flex-col justify-between gap-3 hover:border-white/10 transition-all"
                >
                  <div>
                    {/* Review Header */}
                    <div className="flex items-center justify-between gap-2 mb-2.5">
                      <div className="flex items-center gap-2.5">
                        <div className="w-9 h-9 rounded-full bg-sky-500/15 border border-sky-500/20 text-sky-400 font-bold text-sm flex items-center justify-center shrink-0">
                          {r.user_name.charAt(0).toUpperCase()}
                        </div>
                        <div className="overflow-hidden">
                          <h4 className="font-bold text-sm text-white truncate">{r.user_name}</h4>
                          {r.created_at && (
                            <span className="text-[11px] text-text-secondary">
                              {new Date(r.created_at).toLocaleDateString("uz-UZ", {
                                day: "numeric",
                                month: "short",
                                year: "numeric",
                              })}
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Rating pill */}
                      <div className="flex items-center gap-1 bg-rating-gold/15 text-rating-gold border border-rating-gold/20 px-2.5 py-1 rounded-xl text-xs font-black shrink-0">
                        <span className="material-symbols-outlined text-[14px]" style={{ fontVariationSettings: "'FILL' 1" }}>
                          star
                        </span>
                        <span>{r.rating}/10</span>
                      </div>
                    </div>

                    {/* Review Text */}
                    {r.comment ? (
                      <p className="text-sm text-text-primary/90 leading-relaxed break-words">
                        {r.comment}
                      </p>
                    ) : (
                      <p className="text-xs text-text-secondary italic">
                        Foydalanuvchi faqat baho qo'ydi (sharh yozilmagan).
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
