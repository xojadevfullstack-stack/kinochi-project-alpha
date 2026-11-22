export function normalizeTmdbId(
  value: number | string | null | undefined
): number | null;

export interface DuplicateLookupResponse {
  exact?: Array<{
    type: string;
    id: number;
    title: string;
    code?: string;
    year?: number | null;
    release_year?: number | null;
    tmdb_id?: number | null;
  }>;
  similar?: Array<{
    type: string;
    id: number;
    title: string;
    code?: string;
    year?: number | null;
    release_year?: number | null;
    tmdb_id?: number | null;
  }>;
}

export function filterDuplicateResults(
  dupRes: DuplicateLookupResponse | null | undefined,
  editingId: number | null | undefined,
  contentType: "movie" | "series"
): DuplicateLookupResponse | null;

export function mergeTmdbDetails<T extends Record<string, any>>(
  prev: T,
  incoming: Record<string, any>,
  options?: { fillEmptyOnly?: boolean }
): T;
