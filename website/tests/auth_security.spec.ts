import { test, expect } from '@playwright/test';
import fs from 'fs';
import path from 'path';

test.describe('GUEST-ISSUE-006: Diagnostic test-auth page security', () => {
  test('test-auth page.tsx must be guarded against production access', () => {
    const filePath = path.resolve(__dirname, '../app/test-auth/page.tsx');
    const content = fs.readFileSync(filePath, 'utf-8');

    // Must import notFound from next/navigation
    expect(content).toContain('notFound');
    expect(content).toContain('next/navigation');

    // Must check NODE_ENV production
    expect(content).toMatch(/process\.env\.NODE_ENV\s*===?\s*["']production["']/);
  });
});
