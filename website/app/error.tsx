'use client'; // Error components must be Client Components

import { useEffect } from 'react';
import Link from 'next/link';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log the error to an error reporting service
    console.error(error);
  }, [error]);

  return (
    <div className="min-h-[70vh] flex flex-col items-center justify-center px-4 text-center">
      <div className="space-y-6 max-w-md">
        <h2 className="text-3xl font-bold text-slate-900 dark:text-white">Xatolik yuz berdi</h2>
        <p className="text-slate-600 dark:text-zinc-400">
          Uzr so&apos;raymiz, server bilan bog&apos;lanishda muammo yuzaga keldi. Xizmat tez orada o&apos;z holiga qaytadi.
        </p>
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <button
            onClick={
              // Attempt to recover by trying to re-render the segment
              () => reset()
            }
            className="px-6 py-2.5 bg-[#E50914] hover:bg-[#B80710] text-white font-medium rounded-lg transition-colors w-full sm:w-auto cursor-pointer"
          >
            Qayta urinish
          </button>
          <Link
            href="/"
            className="px-6 py-2.5 bg-slate-200 hover:bg-slate-300 dark:bg-zinc-800 dark:hover:bg-zinc-700 text-slate-900 dark:text-white font-medium rounded-lg transition-colors w-full sm:w-auto"
          >
            Bosh sahifaga qaytish
          </Link>
        </div>
      </div>
    </div>
  );
}
