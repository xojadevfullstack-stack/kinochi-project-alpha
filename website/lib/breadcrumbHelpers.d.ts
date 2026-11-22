export interface BreadcrumbItem {
  label: string;
  href: string;
  isLast: boolean;
}

export const SEGMENT_LABELS: Record<string, string>;

export function normalizeBreadcrumbPath(path: string): string;
export function formatSegmentLabel(segment: string, prevSegment?: string): string;
export function buildBreadcrumbs(
  pathname: string,
  overrides?: Record<string, string>
): BreadcrumbItem[];
