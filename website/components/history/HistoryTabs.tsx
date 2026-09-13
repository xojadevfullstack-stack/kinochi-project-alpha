"use client";

type Props = {
  activeTab: "in_progress" | "completed";
  setActiveTab: (tab: "in_progress" | "completed") => void;
  inProgressCount: number;
  completedCount: number;
};

export default function HistoryTabs({ activeTab, setActiveTab, inProgressCount, completedCount }: Props) {
  return (
    <div className="flex items-center gap-2 p-1.5 bg-white/[0.04] backdrop-blur-md rounded-2xl border border-white/10 mb-6 w-full sm:w-auto max-w-md">
      <button
        onClick={() => setActiveTab("in_progress")}
        className={`flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl text-xs sm:text-sm font-semibold transition-all cursor-pointer ${
          activeTab === "in_progress" 
            ? "bg-white/15 text-white border border-white/20 shadow-md backdrop-blur-md font-bold" 
            : "text-text-secondary hover:text-text-primary hover:bg-white/5 border border-transparent"
        }`}
      >
        <span className="material-symbols-outlined text-[17px]">schedule</span>
        <span>Davom etayotgan ({inProgressCount})</span>
      </button>

      <button
        onClick={() => setActiveTab("completed")}
        className={`flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl text-xs sm:text-sm font-semibold transition-all cursor-pointer ${
          activeTab === "completed" 
            ? "bg-white/15 text-white border border-white/20 shadow-md backdrop-blur-md font-bold" 
            : "text-text-secondary hover:text-text-primary hover:bg-white/5 border border-transparent"
        }`}
      >
        <span className="material-symbols-outlined text-[17px]">check_circle</span>
        <span>Ko&apos;rilgan ({completedCount})</span>
      </button>
    </div>
  );
}
