import Link from "next/link";

export default function NotFound() {
  return (
    <div className="min-h-[75vh] flex items-center justify-center px-4 py-12">
      <div className="max-w-lg w-full rounded-3xl border border-slate-200 dark:border-white/10 bg-white/95 dark:bg-[#11131A]/90 p-7 sm:p-10 text-center shadow-xl">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-[#E50914]/15 border border-[#E50914]/30 text-[#E50914] mb-4">
          <span className="material-symbols-outlined text-4xl">theaters</span>
        </div>

        <p className="font-mono text-4xl sm:text-6xl font-black tracking-tight text-[#E50914] mb-2">
          404
        </p>

        <h1 className="font-heading text-xl sm:text-2xl font-extrabold text-slate-900 dark:text-white mb-2">
          Sahifa topilmadi
        </h1>

        <p className="text-xs sm:text-sm text-slate-600 dark:text-text-secondary leading-relaxed mb-7">
          Siz qidirayotgan kino, serial yoki sahifa o&apos;chirilgan, ko&apos;chirilgan yoki havola noto&apos;g&apos;ri kiritilgan bo&apos;lishi mumkin.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
          <Link
            href="/"
            className="w-full sm:w-auto px-6 py-3 rounded-full bg-[#E50914] hover:bg-[#c40710] text-white text-xs sm:text-sm font-bold transition-all shadow-lg shadow-[#E50914]/25 inline-flex items-center justify-center gap-2"
          >
            <span className="material-symbols-outlined text-[18px]">home</span>
            <span>Bosh sahifaga qaytish</span>
          </Link>

          <Link
            href="/catalog"
            className="w-full sm:w-auto px-6 py-3 rounded-full bg-slate-100 hover:bg-slate-200 dark:bg-white/10 dark:hover:bg-white/15 text-slate-900 dark:text-white text-xs sm:text-sm font-semibold border border-slate-200 dark:border-white/10 transition-colors inline-flex items-center justify-center gap-2"
          >
            <span className="material-symbols-outlined text-[18px]">grid_view</span>
            <span>Katalogni ko&apos;rish</span>
          </Link>
        </div>
      </div>
    </div>
  );
}
