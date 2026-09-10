"use client";

type Props = {
  activeTab: "in_progress" | "completed";
  setActiveTab: (tab: "in_progress" | "completed") => void;
  inProgressCount: number;
  completedCount: number;
};

export default function HistoryTabs({ activeTab, setActiveTab, inProgressCount, completedCount }: Props) {
  return (
    <div className="flex items-center gap-4 border-b border-white/10 mb-6">
      <button
        onClick={() => setActiveTab("in_progress")}
        className={`pb-3 text-sm font-bold transition-all relative ${
          activeTab === "in_progress" 
            ? "text-primary-container" 
            : "text-text-secondary hover:text-white"
        }`}
      >
        Davom etayotgan ({inProgressCount})
        {activeTab === "in_progress" && (
          <span className="absolute bottom-0 left-0 w-full h-0.5 bg-primary-container rounded-t-full shadow-[0_0_10px_rgba(229,9,20,0.5)]"></span>
        )}
      </button>

      <button
        onClick={() => setActiveTab("completed")}
        className={`pb-3 text-sm font-bold transition-all relative ${
          activeTab === "completed" 
            ? "text-primary-container" 
            : "text-text-secondary hover:text-white"
        }`}
      >
        Ko'rilgan ({completedCount})
        {activeTab === "completed" && (
          <span className="absolute bottom-0 left-0 w-full h-0.5 bg-primary-container rounded-t-full shadow-[0_0_10px_rgba(229,9,20,0.5)]"></span>
        )}
      </button>
    </div>
  );
}
