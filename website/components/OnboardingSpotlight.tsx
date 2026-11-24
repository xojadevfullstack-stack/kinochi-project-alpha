"use client";

import React, { useCallback, useEffect, useState } from "react";
import { useOverlayBackClose } from "@/lib/hooks/useOverlayBackClose";

export type TourStep = {
  selectors: string[];
  title: string;
  description: string;
  badge: string;
};

type OnboardingSpotlightProps = {
  storageKey?: string;
  steps?: TourStep[];
  eventName?: string;
};

const STORAGE_KEY = "mediaplus_onboarding_v1";

const TOUR_STEPS: TourStep[] = [
  {
    badge: "Qidiruv",
    title: "Film va seriallarni bir zumda toping",
    description:
      "Nomi, aktyor, janr yoki Telegram bot kodi (#kod) ni yozib katalogdan darhol qidiring.",
    selectors: ['input[placeholder*="Qidiruv"]', 'button[aria-label="Qidiruv"]'],
  },
  {
    badge: "Tomosha qilish",
    title: "Telegram botda HD/4K ko'ring",
    description:
      "Yoqqan filmni tanlang va 'TOMOSHA QILISH' tugmasini bosing — video rasmiy Telegram botimiz orqali ochiladi.",
    selectors: ['a[href*="/movie/"]', 'a[href*="/series/"]'],
  },
  {
    badge: "Bo'limlar",
    title: "Barcha kategoriyalar bitta menyuda",
    description:
      "Menyu orqali Kinolar, Seriallar, To'plamlar, Premyeralar hamda film buyurtma berish bo'limiga o'ting.",
    selectors: ['button[aria-label="Menyuni ochish"]'],
  },
  {
    badge: "Yangiliklar",
    title: "Premyera va yangi qismlardan xabardor bo'ling",
    description:
      "Bildirishnomalar bo'limida kuzatayotgan seriallaringizning yangi qismlari haqida darhol bilib olasiz.",
    selectors: ['nav.site-top-nav a[href="/notifications"]'],
  },
  {
    badge: "Tezkor panel",
    title: "Asosiy bo'limlarga tez o'ting",
    description:
      "Pastki suzuvchi panel (mobilda) va profil tugmasi yordamida sevimlilar hamda tarixga bir klikda o'ting.",
    selectors: [
      'nav[aria-label="Mobil pastki navigatsiya"]',
      'nav.site-top-nav a[href="/profile"]',
    ],
  },
];

function findVisibleTarget(selectors: string[]): HTMLElement | null {
  if (typeof document === "undefined") return null;
  for (const selector of selectors) {
    const nodes = Array.from(document.querySelectorAll(selector));
    for (const node of nodes) {
      if (!(node instanceof HTMLElement)) continue;
      const rect = node.getBoundingClientRect();
      if (rect.width > 0 && rect.height > 0 && node.offsetParent !== null) {
        return node;
      }
      if (
        rect.width > 0 &&
        rect.height > 0 &&
        getComputedStyle(node).position === "fixed"
      ) {
        return node;
      }
    }
  }
  return null;
}

export default function OnboardingSpotlight({
  storageKey = STORAGE_KEY,
  steps = TOUR_STEPS,
  eventName = "mediaplus:start_onboarding",
}: OnboardingSpotlightProps) {
  const [active, setActive] = useState(false);
  const [stepIdx, setStepIdx] = useState(0);
  const [rect, setRect] = useState<DOMRect | null>(null);

  const finishTour = useCallback(() => {
    setActive(false);
    try {
      localStorage.setItem(storageKey, "done");
    } catch {}
  }, [storageKey]);

  const updateRectOnly = useCallback(
    (idx: number) => {
      const step = steps[idx];
      if (!step) return;
      const target = findVisibleTarget(step.selectors);
      setRect(target ? target.getBoundingClientRect() : null);
    },
    [steps]
  );

  const focusStep = useCallback(
    (idx: number) => {
      const step = steps[idx];
      if (!step) return;
      const target = findVisibleTarget(step.selectors);
      if (!target) {
        setRect(null);
        return;
      }
      target.scrollIntoView({ behavior: "smooth", block: "center" });
      updateRectOnly(idx);
      window.setTimeout(() => updateRectOnly(idx), 320);
    },
    [steps, updateRectOnly]
  );

  useEffect(() => {
    if (typeof window === "undefined") return;
    let timer: number | undefined;
    try {
      if (localStorage.getItem(storageKey) !== "done") {
        timer = window.setTimeout(() => {
          localStorage.setItem(storageKey, "done");
          setStepIdx(0);
          setActive(true);
        }, 900);
      }
    } catch {}

    const handleManualStart = () => {
      setStepIdx(0);
      setActive(true);
    };
    window.addEventListener(eventName, handleManualStart);
    return () => {
      if (timer) window.clearTimeout(timer);
      window.removeEventListener(eventName, handleManualStart);
    };
  }, [storageKey, eventName]);

  useOverlayBackClose(active, finishTour);

  useEffect(() => {
    if (!active) return;
    focusStep(stepIdx);
    const onUpdate = () => updateRectOnly(stepIdx);
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") finishTour();
    };
    window.addEventListener("resize", onUpdate);
    window.addEventListener("scroll", onUpdate, { passive: true });
    window.addEventListener("keydown", onKeyDown);
    return () => {
      window.removeEventListener("resize", onUpdate);
      window.removeEventListener("scroll", onUpdate);
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [active, stepIdx, focusStep, updateRectOnly, finishTour]);

  if (!active || steps.length === 0) return null;

  const step = steps[stepIdx];
  const isLast = stepIdx === steps.length - 1;
  const pad = 6;
  const vw = typeof window !== "undefined" ? window.innerWidth : 375;
  const vh = typeof window !== "undefined" ? window.innerHeight : 700;
  const placeAbove = rect ? rect.bottom + 210 > vh && rect.top > 210 : false;
  const tooltipTop = rect
    ? placeAbove
      ? Math.max(16, rect.top - 196)
      : Math.min(vh - 205, rect.bottom + 14)
    : Math.max(80, vh / 2 - 95);
  const tooltipLeft = rect
    ? Math.min(Math.max(12, rect.left + rect.width / 2 - 155), Math.max(12, vw - 322))
    : Math.max(12, vw / 2 - 155);

  return (
    <div className="fixed inset-0 z-[105]" role="dialog" aria-modal="true" aria-label="Sayt bo'yicha qo'llanma">
      <div className="absolute inset-0 bg-transparent" onClick={finishTour} />
      {rect ? (
        <div
          className="fixed pointer-events-none rounded-2xl border-2 border-primary-container transition-all duration-300"
          style={{
            top: Math.max(4, rect.top - pad),
            left: Math.max(4, rect.left - pad),
            width: Math.min(vw - 8, rect.width + pad * 2),
            height: rect.height + pad * 2,
            boxShadow: "0 0 0 9999px rgba(4, 6, 12, 0.72), 0 0 24px rgba(229, 9, 20, 0.45)",
          }}
        />
      ) : (
        <div className="fixed inset-0 bg-black/75 pointer-events-none" />
      )}

      <div
        className="fixed z-[110] w-[310px] rounded-2xl bg-white/95 dark:bg-[#12141D]/95 text-slate-900 dark:text-white backdrop-blur-2xl border border-slate-200 dark:border-white/15 p-4 shadow-2xl transition-all duration-300"
        style={{ top: tooltipTop, left: tooltipLeft }}
      >
        <div className="flex items-center justify-between mb-2">
          <span className="text-[10px] font-extrabold uppercase tracking-wider px-2 py-0.5 rounded-full bg-primary-container/15 text-primary-container border border-primary-container/30">
            {step.badge}
          </span>
          <span className="text-[11px] font-mono text-slate-500 dark:text-gray-400">
            {stepIdx + 1} / {steps.length}
          </span>
        </div>
        <h3 className="font-heading font-bold text-sm leading-snug mb-1">{step.title}</h3>
        <p className="text-xs text-slate-600 dark:text-gray-300 leading-relaxed mb-3.5">
          {step.description}
        </p>
        <div className="flex items-center justify-between gap-2">
          <button
            type="button"
            onClick={finishTour}
            className="text-[11px] font-semibold text-slate-500 hover:text-slate-900 dark:text-gray-400 dark:hover:text-white transition cursor-pointer"
          >
            O&apos;tkazib yuborish
          </button>
          <div className="flex items-center gap-1.5">
            {stepIdx > 0 && (
              <button
                type="button"
                onClick={() => setStepIdx((i) => Math.max(0, i - 1))}
                className="px-2.5 py-1.5 rounded-xl text-xs font-semibold bg-slate-100 hover:bg-slate-200 text-slate-700 dark:bg-white/10 dark:hover:bg-white/15 dark:text-gray-200 transition cursor-pointer"
              >
                Orqaga
              </button>
            )}
            <button
              type="button"
              onClick={() => (isLast ? finishTour() : setStepIdx((i) => i + 1))}
              className="px-3.5 py-1.5 rounded-xl text-xs font-bold bg-primary-container hover:bg-[#B80710] text-white shadow-md shadow-primary-container/30 transition cursor-pointer"
            >
              {isLast ? "Tushunarli ✓" : "Keyingi ›"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
