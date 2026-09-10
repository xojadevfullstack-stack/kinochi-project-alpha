"use client";

import { useEffect, useState } from "react";
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

  useEffect(() => {
    if (status === "authenticated") {
      setLoading(true);
      getHistory(0, 100) // Fetching a reasonable amount for the client-side filter
        .then(res => {
          setItems(res.items);
          setLoading(false);
        })
        .catch(err => {
          console.error(err);
          setLoading(false);
        });
    } else if (status === "unauthenticated") {
      setLoading(false);
    }
  }, [status]);

  if (status === "loading" || (status === "authenticated" && loading)) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background-obsidian">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-container"></div>
      </div>
    );
  }

  if (status === "unauthenticated") {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background-obsidian px-gutter">
        <div className="text-center bg-surface-container p-8 rounded-2xl border border-white/10 max-w-md w-full">
          <span className="material-symbols-outlined text-6xl text-primary-container mb-4">history</span>
          <h1 className="text-2xl font-display-hero font-bold text-white mb-2">Ko'rish tarixi</h1>
          <p className="text-text-secondary mb-6 font-body-lg">
            Siz ko'rgan kinolar va seriallar tarixini ko'rish uchun profilingizga kiring.
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
    <div className="min-h-screen bg-background-obsidian pt-24 pb-20">
      <div className="max-w-container-max mx-auto px-gutter">
        <h1 className="text-3xl md:text-4xl font-display-hero font-bold text-white mb-8 flex items-center gap-3">
          <span className="material-symbols-outlined text-4xl text-primary-container">history</span>
          Ko'rish tarixi
        </h1>

        <ContinueWatchingBanner items={items} />

        <div className="bg-surface-container/30 rounded-3xl p-4 md:p-8 border border-white/5">
          <HistoryTabs 
            activeTab={activeTab} 
            setActiveTab={setActiveTab} 
            inProgressCount={inProgressItems.length}
            completedCount={completedItems.length}
          />
          <HistoryGrid 
            items={displayedItems} 
            emptyMessage={
              activeTab === "in_progress" 
                ? "Davom etayotgan hech narsa yo'q" 
                : "Hali hech narsani to'liq ko'rmadingiz"
            }
          />
        </div>
      </div>
    </div>
  );
}
