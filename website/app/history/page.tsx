"use client";

import { useEffect, useState, useRef } from "react";
import { useAuth } from "@/lib/auth/AuthProvider";
import { getHistory, HistoryItem } from "@/lib/api/history";
import TelegramLoginWidget from "@/components/auth/TelegramLoginWidget";
import ContinueWatchingBanner from "@/components/history/ContinueWatchingBanner";
import HistoryTabs from "@/components/history/HistoryTabs";
import HistoryGrid from "@/components/history/HistoryGrid";

export default function HistoryPage() {
  const { status, environment: env } = useAuth();
  
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"in_progress" | "completed">("in_progress");
  const userSwitchedTab = useRef(false);

  useEffect(() => {
    if (status === "authenticated") {
      setLoading(true);
      getHistory(0, 100) // Fetching a reasonable amount for the client-side filter
        .then(res => {
          const historyItems = res.items || [];
          setItems(historyItems);
          setLoading(false);

          // Intelligent UX Default: if user hasn't manually switched tab,
          // and has 0 in-progress but has completed items, switch to completed!
          if (!userSwitchedTab.current) {
            const hasInProgress = historyItems.some(i => i.status === "in_progress");
            const hasCompleted = historyItems.some(i => i.status === "completed");
            if (!hasInProgress && hasCompleted) {
              setActiveTab("completed");
            }
          }
        })
        .catch(err => {
          console.error(err);
          setLoading(false);
        });
    } else if (status === "unauthenticated") {
      setLoading(false);
    }
  }, [status]);

  const handleTabChange = (tab: "in_progress" | "completed") => {
    userSwitchedTab.current = true;
    setActiveTab(tab);
  };

  if (status === "loading" || (status === "authenticated" && loading)) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background-obsidian">
        <div className="w-10 h-10 rounded-full border-2 border-white/20 border-t-rating-gold animate-spin"></div>
      </div>
    );
  }

  if (status === "unauthenticated") {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background-obsidian px-gutter pt-20 pb-24">
        <div className="text-center bg-white/[0.04] backdrop-blur-xl p-8 rounded-3xl border border-white/10 max-w-md w-full shadow-2xl">
          <div className="w-16 h-16 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center mx-auto mb-5 text-rating-gold">
            <span className="material-symbols-outlined text-3xl">history</span>
          </div>
          <h1 className="text-2xl font-display-hero font-bold text-white mb-2">Ko&apos;rish tarixi</h1>
          <p className="text-text-secondary mb-6 font-body-lg text-sm">
            Siz ko&apos;rgan kinolar va seriallar tarixini ko&apos;rish uchun profilingizga kiring.
          </p>
          {env === "browser" ? (
            <TelegramLoginWidget />
          ) : (
            <p className="text-sm text-text-secondary">Avtorizatsiya kutilmoqda...</p>
          )}
        </div>
      </div>
    );
  }

  const inProgressItems = items.filter(i => i.status === "in_progress");
  const completedItems = items.filter(i => i.status === "completed");
  const displayedItems = activeTab === "in_progress" ? inProgressItems : completedItems;

  return (
    <div className="min-h-screen bg-background-obsidian pt-28 pb-24 px-gutter">
      <div className="max-w-container-max mx-auto">
        {/* Header with Title and Stats */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
          <div>
            <h1 className="text-2xl sm:text-3xl md:text-4xl font-display-hero font-extrabold text-white tracking-tight flex items-center gap-3">
              <span className="material-symbols-outlined text-3xl sm:text-4xl text-rating-gold">history</span>
              Ko&apos;rish tarixi
            </h1>
            <p className="text-text-secondary text-xs sm:text-sm mt-1">
              Siz tomosha qilgan barcha kinolar va seriallar ro&apos;yxati
            </p>
          </div>

          {/* Quick Stats Pill */}
          <div className="flex items-center gap-2 self-start sm:self-auto">
            <div className="px-3.5 py-1.5 rounded-xl bg-white/5 border border-white/10 text-text-secondary text-xs font-medium flex items-center gap-2 shadow-inner">
              <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
              <span>Jami: <strong className="text-white font-bold">{items.length} ta</strong></span>
            </div>
          </div>
        </div>

        {/* Continue Watching Hero Banner if an item is in progress */}
        <ContinueWatchingBanner items={items} />

        {/* Modern Segmented Pill Tabs */}
        <HistoryTabs 
          activeTab={activeTab} 
          setActiveTab={handleTabChange} 
          inProgressCount={inProgressItems.length}
          completedCount={completedItems.length}
        />

        {/* History Grid or Helpful Empty State */}
        <HistoryGrid 
          items={displayedItems} 
          emptyType={activeTab}
          emptyMessage={
            activeTab === "in_progress" 
              ? "Davom etayotgan hech narsa yo'q" 
              : "Hali hech narsani to'liq ko'rmadingiz"
          }
        />
      </div>
    </div>
  );
}
