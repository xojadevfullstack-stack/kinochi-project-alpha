"use client";

import { useEffect, Suspense } from "react";
import { useRouter } from "next/navigation";

function SubscriptionsRedirect() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/profile?tab=subscriptions");
  }, [router]);

  return (
    <div className="min-h-screen pt-28 flex flex-col items-center justify-center text-center px-4">
      <span className="material-symbols-outlined animate-spin text-3xl text-rating-gold mb-3">sync</span>
      <p className="text-sm text-text-secondary">Profil obunalar bo'limiga yo'naltirilmoqda...</p>
    </div>
  );
}

export default function SubscriptionsPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen pt-28 flex flex-col items-center justify-center text-center px-4">
          <span className="material-symbols-outlined animate-spin text-3xl text-rating-gold mb-3">sync</span>
        </div>
      }
    >
      <SubscriptionsRedirect />
    </Suspense>
  );
}
