"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { normalizeBreadcrumbPath } from "@/lib/breadcrumbHelpers.mjs";

type BreadcrumbContextValue = {
  overrides: Record<string, string>;
  setOverride: (path: string, title: string) => void;
  clearOverride: (path: string, title: string) => void;
};

const BreadcrumbContext = createContext<BreadcrumbContextValue>({
  overrides: {},
  setOverride: () => {},
  clearOverride: () => {},
});

export function BreadcrumbProvider({ children }: { children: ReactNode }) {
  const [overrides, setOverrides] = useState<Record<string, string>>({});

  const setOverride = useCallback((path: string, title: string) => {
    const cleanTitle = title.trim();
    if (!cleanTitle) return;
    const key = normalizeBreadcrumbPath(path);
    setOverrides((prev) => (prev[key] === cleanTitle ? prev : { ...prev, [key]: cleanTitle }));
  }, []);

  const clearOverride = useCallback((path: string, title: string) => {
    const cleanTitle = title.trim();
    const key = normalizeBreadcrumbPath(path);
    setOverrides((prev) => {
      if (prev[key] !== cleanTitle) return prev;
      const next = { ...prev };
      delete next[key];
      return next;
    });
  }, []);

  return (
    <BreadcrumbContext.Provider value={{ overrides, setOverride, clearOverride }}>
      {children}
    </BreadcrumbContext.Provider>
  );
}

export function useBreadcrumbOverrides() {
  return useContext(BreadcrumbContext).overrides;
}

/**
 * Registers a human-readable title for the active route in the global Breadcrumb.
 */
export function BreadcrumbTitle({
  path,
  title,
}: {
  path: string;
  title?: string | null;
}) {
  const { setOverride, clearOverride } = useContext(BreadcrumbContext);

  useEffect(() => {
    if (!title || !title.trim()) return;
    setOverride(path, title);
    return () => {
      clearOverride(path, title);
    };
  }, [path, title, setOverride, clearOverride]);

  return null;
}
