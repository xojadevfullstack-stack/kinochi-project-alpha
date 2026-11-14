import { test, expect } from '@playwright/test';
import fs from 'fs';
import path from 'path';

test.describe('USER-ISSUE-003 & 004: Profile UX & Functional Integrity', () => {
  const profilePagePath = path.resolve(__dirname, '../app/profile/page.tsx');
  const content = fs.readFileSync(profilePagePath, 'utf-8');

  test('USER-ISSUE-003: Profile settings must have an interactive notification toggle', () => {
    // Must NOT have static un-clickable emerald text without toggle handler
    expect(content).toContain('toggleNotifications');
    expect(content).toContain('kinochi_notifications_enabled');
  });

  test('USER-ISSUE-004: Profile favorites tab must NOT contain phantom "+ Sevimlilarga" instruction', () => {
    // Phantom "+ Sevimlilarga" instruction must be eliminated
    expect(content).not.toContain('+ Sevimlilarga');
  });
});
