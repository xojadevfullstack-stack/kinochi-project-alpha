"use client";

type Props = {
  activeTab: "in_progress" | "completed";
  setActiveTab: (tab: "in_progress" | "completed") => void;
  inProgressCount: number;
  completedCount: number;
};

export default function HistoryTabs({ activeTab, setActiveTab, inProgressCount, completedCount }: Props) {
  return (
    <div className="flex items-center gap-2 p-1.5 bg-white dark:bg-white/[0.04] backdrop-blur-md rounded-2xl border border-slate-200 dark:border-white/10 mb-6 w-full sm:w-auto max-w-md shadow-sm dark:shadow-none">
      <button
        onClick={() => setActiveTab("in_progress")}
        className={`flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl text-xs sm:text-sm font-semibold transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5 active:scale-95 cursor-pointer ${
          activeTab === "in_progress" 
            ? "bg-[#E50914] text-white border border-[#E50914] shadow-md font-bold" 
            : "text-slate-600 dark:text-text-secondary hover:text-slate-900 dark:hover:text-text-primary hover:bg-slate-100 dark:hover:bg-white/5 border border-transparent"
        }`}
      >
        <span className="material-symbols-outlined text-[17px]">schedule</span>
        <span>Davom etayotgan ({inProgressCount})</span>
      </button>

      <button
        onClick={() => setActiveTab("completed")}
        className={`flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl text-xs sm:text-sm font-semibold transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5 active:scale-95 cursor-pointer ${
          activeTab === "completed" 
            ? "bg-[#E50914] text-white border border-[#E50914] shadow-md font-bold" 
            : "text-slate-600 dark:text-text-secondary hover:text-slate-900 dark:hover:text-text-primary hover:bg-slate-100 dark:hover:bg-white/5 border border-transparent"
        }`}
      >
        <span className="material-symbols-outlined text-[17px]">check_circle</span>
        <span>Ko&apos;rilgan ({completedCount})</span>
      </button>
    </div>
  );
}
