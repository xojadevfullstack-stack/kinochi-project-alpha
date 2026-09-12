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
        setVotesCount(res.kinochi_votes_count || votesCount + 1);
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
        <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6 bg-surface-container/60 p-6 md:p-8 rounded-3xl border border-white/5">
          <div>
            <div className="flex items-center gap-2.5 mb-2">
              <span className="material-symbols-outlined text-rating-gold text-2xl" style={{ fontVariationSettings: "'FILL' 1" }}>
                stars
              </span>
              <h2 className="text-2xl md:text-3xl font-display-hero font-bold text-white tracking-tight">
                Baholar va Sharhlar
              </h2>
            </div>
            <p className="text-sm text-text-secondary max-w-xl">
              Ushbu asar haqida tomoshabinlar va mutaxassislar fikrlari. Siz ham o'z bahoyingizni qoldiring!
            </p>
          </div>

          {/* Score Badges Comparison */}
          <div className="flex flex-wrap items-center gap-4 w-full lg:w-auto">
            {/* IMDb Badge */}
            <div className="flex items-center gap-3 bg-black/40 px-5 py-3 rounded-2xl border border-white/10">
              <div className="w-10 h-10 rounded-xl bg-amber-400/20 flex items-center justify-center text-amber-400 font-black text-xs shrink-0">
                IMDb
              </div>
              <div>
                <div className="flex items-center gap-1">
                  <span className="material-symbols-outlined text-rating-gold text-[18px]" style={{ fontVariationSettings: "'FILL' 1" }}>
                    star
                  </span>
                  <span className="text-lg font-bold text-white">
                    {imdbRating ? `${imdbRating}` : "N/A"}
                  </span>
                  <span className="text-xs text-text-secondary">/10</span>
                </div>
                <span className="text-[11px] text-text-secondary uppercase tracking-wider font-semibold">Rasmiy IMDb</span>
              </div>
            </div>

            {/* Kinochi Community Badge */}
            <div className="flex items-center gap-3 bg-primary-container/10 px-5 py-3 rounded-2xl border border-primary-container/30 shadow-lg shadow-primary-container/5">
              <div className="w-10 h-10 rounded-xl bg-primary-container/30 flex items-center justify-center text-primary-container font-black text-xs shrink-0">
                Kinochi
              </div>
              <div>
                <div className="flex items-center gap-1">
                  <span className="material-symbols-outlined text-primary-container text-[18px]" style={{ fontVariationSettings: "'FILL' 1" }}>
                    hotel_class
                  </span>
                  <span className="text-lg font-bold text-white">
                    {kinochiRating !== null ? `${kinochiRating}` : "Yangi"}
                  </span>
                  {kinochiRating !== null && <span className="text-xs text-text-secondary">/10</span>}
                </div>
                <span className="text-[11px] text-text-secondary font-semibold">
                  {votesCount > 0 ? `${votesCount} ta ovoz` : "Hali baholanmagan"}
                </span>
              </div>
            </div>

            {/* Action button */}
            <button
              onClick={() => setFormOpen(!formOpen)}
              className="ml-auto lg:ml-0 flex items-center gap-2 px-5 py-3 rounded-2xl bg-primary-container hover:bg-primary-container/80 text-on-primary-container font-bold text-sm transition-all shadow-lg shadow-primary-container/20 cursor-pointer"
            >
              <span className="material-symbols-outlined text-[20px]">
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
          <div className="bg-surface-container/80 p-6 md:p-8 rounded-3xl border border-primary-container/30 shadow-xl shadow-primary-container/5 transition-all">
            {status !== "authenticated" ? (
              <div className="flex flex-col items-center justify-center py-8 text-center gap-4">
                <span className="material-symbols-outlined text-5xl text-primary-container">lock</span>
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
                    <span className="text-xs font-bold text-primary-container">
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
                    className="w-full bg-background-obsidian/80 border border-white/10 rounded-2xl p-4 text-sm text-white placeholder:text-text-secondary focus:border-primary-container focus:outline-none transition-all resize-none"
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
                    className="px-6 py-2.5 rounded-xl text-sm font-bold bg-primary-container hover:bg-primary-container/80 text-on-primary-container transition-all flex items-center gap-2 disabled:opacity-50 cursor-pointer shadow-lg shadow-primary-container/20"
                  >
                    {submitting ? (
                      <>
                        <div className="w-4 h-4 rounded-full border-2 border-white/20 border-t-white animate-spin"></div>
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
              <span className="material-symbols-outlined text-primary-container text-xl">comment</span>
              Foydalanuvchilar fikrlari ({reviews.length})
            </h3>
          </div>

          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="w-8 h-8 rounded-full border-2 border-primary-container border-t-transparent animate-spin"></div>
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
                className="mt-2 text-xs font-bold text-primary-container hover:underline cursor-pointer"
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
                        <div className="w-9 h-9 rounded-full bg-primary-container/20 text-primary-container font-bold text-sm flex items-center justify-center shrink-0">
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
