import { test, expect } from '@playwright/test';
import { resolveContinueWatchingItems } from '../components/home/ContinueWatchingSection';

test.describe('BUG-010: ContinueWatching localStorage Desynchronization Fix', () => {
  test('authenticated user with cleared history (0 items) must purge localStorage and return 0 items', async () => {
    const removedKeys: string[] = [];
    const mockStorage = {
      getItem: (key: string) => {
        if (key === 'mediaplus_continue_watching') {
          return JSON.stringify([
            { id: 999, title: 'Old Stale Guest Movie', code: '999' }
          ]);
        }
        return null;
      },
      removeItem: (key: string) => {
        removedKeys.push(key);
      }
    };

    // User is authenticated, but server history is empty (e.g. user cleared history via bot)
    const mockGetHistory = async () => ({ items: [] });

    const items = await resolveContinueWatchingItems({
      status: 'authenticated',
      getHistoryFn: mockGetHistory,
      storage: mockStorage,
    });

    // Expect items to be empty (NOT showing resurrected guest movie)
    expect(items.length).toBe(0);
    // Expect localStorage entry to have been purged
    expect(removedKeys).toContain('mediaplus_continue_watching');
  });

  test('unauthenticated guest user continues to receive localStorage items', async () => {
    const mockStorage = {
      getItem: (key: string) => {
        if (key === 'mediaplus_continue_watching') {
          return JSON.stringify([
            { id: 101, title: 'Guest Watching Movie', code: '101' }
          ]);
        }
        return null;
      },
      removeItem: () => {}
    };

    const items = await resolveContinueWatchingItems({
      status: 'unauthenticated',
      storage: mockStorage,
    });

    expect(items.length).toBe(1);
    expect(items[0].title).toBe('Guest Watching Movie');
  });

  test('GUEST-ISSUE-005: unauthenticated guest user with no progress data must NOT have hardcoded 60% progress', async () => {
    const mockStorage = {
      getItem: (key: string) => {
        if (key === 'mediaplus_continue_watching') {
          return JSON.stringify([
            { id: 101, title: 'Guest Watching Movie', code: '101' }
          ]);
        }
        return null;
      },
      removeItem: () => {}
    };

    const items = await resolveContinueWatchingItems({
      status: 'unauthenticated',
      storage: mockStorage,
    });

    expect(items.length).toBe(1);
    expect(items[0].progress).toBeUndefined();
  });

  test('GUEST-ISSUE-005: authenticated in_progress item with no progress data must NOT have hardcoded 55% or 65% progress', async () => {
    const mockGetHistory = async () => ({
      items: [
        {
          id: 1,
          status: 'in_progress',
          type: 'movie',
          last_watched_at: new Date().toISOString(),
          movie: { id: 10, title: 'Test Movie', code: 'TM1' }
        }
      ]
    });

    const items = await resolveContinueWatchingItems({
      status: 'authenticated',
      getHistoryFn: mockGetHistory,
      storage: null,
    });

    expect(items.length).toBe(1);
    expect(items[0].progress).toBeUndefined();
  });
});
