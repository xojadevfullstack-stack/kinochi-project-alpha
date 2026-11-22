import React from "react";
import Link from "next/link";

interface EmptyStateProps {
  icon?: string;
  title: string;
  description?: string;
  actionLabel?: string;
  actionHref?: string;
  onAction?: () => void;
  secondaryLabel?: string;
  secondaryHref?: string;
  className?: string;
  compact?: boolean;
}

/**
 * Unified Empty State card for zero-result filters, empty profiles, and missing items.
 * Follows Cinematic Red Design Standard (#E50914 active CTAs, crisp Dark/Light contrast).
 */
export default function EmptyState({
  icon = "movie_off",
  title,
  description,
  actionLabel,
  actionHref,
  onAction,
  secondaryLabel,
  secondaryHref,
  className = "",
  compact = false,
}: EmptyStateProps) {
  return (
    <div
      className={`w-full rounded-3xl border border-slate-200/80 dark:border-white/10 bg-white/95 dark:bg-[#11131A]/85 flex flex-col items-center justify-center text-center ${
        compact ? "py-10 px-4" : "py-14 sm:py-16 px-5 sm:px-8"
      } shadow-sm ${className}`}
    >
      <div className="w-14 h-14 sm:w-16 sm:h-16 rounded-2xl bg-[#E50914]/10 border border-[#E50914]/25 flex items-center justify-center mb-4 text-[#E50914]">
        <span className="material-symbols-outlined text-3xl sm:text-4xl">{icon}</span>
      </div>

      <h3 className="font-heading text-lg sm:text-xl font-bold text-slate-900 dark:text-white mb-1.5">
        {title}
      </h3>

      {description ? (
        <p className="text-xs sm:text-sm text-slate-600 dark:text-text-secondary max-w-md leading-relaxed mb-6">
          {description}
        </p>
      ) : (
        <div className="mb-4" />
      )}

      {(actionLabel || secondaryLabel) && (
        <div className="flex flex-wrap items-center justify-center gap-2.5">
          {actionLabel && actionHref ? (
            <Link
              href={actionHref}
              className="px-5 py-2.5 rounded-full bg-[#E50914] hover:bg-[#c40710] text-white text-xs sm:text-sm font-bold transition-all shadow-md shadow-[#E50914]/25 inline-flex items-center gap-1.5"
            >
              <span>{actionLabel}</span>
            </Link>
          ) : actionLabel && onAction ? (
            <button
              type="button"
              onClick={onAction}
              className="px-5 py-2.5 rounded-full bg-[#E50914] hover:bg-[#c40710] text-white text-xs sm:text-sm font-bold transition-all shadow-md shadow-[#E50914]/25 inline-flex items-center gap-1.5 cursor-pointer"
            >
              <span>{actionLabel}</span>
            </button>
          ) : null}

          {secondaryLabel && secondaryHref ? (
            <Link
              href={secondaryHref}
              className="px-5 py-2.5 rounded-full bg-slate-100 hover:bg-slate-200 dark:bg-white/10 dark:hover:bg-white/15 text-slate-900 dark:text-white text-xs sm:text-sm font-semibold border border-slate-200 dark:border-white/10 transition-colors"
            >
              {secondaryLabel}
            </Link>
          ) : null}
        </div>
      )}
    </div>
  );
}
