import { test, expect } from '@playwright/test';
import fs from 'fs';
import path from 'path';

test.describe('GUEST-ISSUE-003: Truthful Telegram Watch Modal copy', () => {
  test('TelegramWatchButton component must NOT claim fake message dispatch', () => {
    const filePath = path.resolve(__dirname, '../components/TelegramWatchButton.tsx');
    const content = fs.readFileSync(filePath, 'utf-8');

    // Negative assertions: Fake dispatch claims must be removed
    expect(content).not.toContain('Muvaffaqiyatli yuborildi');
    expect(content).not.toContain('botdan yuborildi');
    expect(content).not.toContain('botingizga video fayl va tomosha qilish havolasi yuborildi');

    // Positive assertions: Honest guidance to continue in Telegram bot
    expect(content).toContain('Telegram botda davom eting');
    expect(content).toContain('Telegram bot ochilmoqda');
  });
});
