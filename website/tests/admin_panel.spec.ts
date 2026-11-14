import { test, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

test.describe('ADMIN FLOW STABILIZATION: ADMIN-ISSUE-001 & 003', () => {
  const rootDir = path.resolve(__dirname, '../../');
  const adminPanelDir = path.join(rootDir, 'admin-panel');

  test('ADMIN-ISSUE-001: Admin logout must cleanly delete refresh_token and use API_URL', async () => {
    const adminShellPath = path.join(adminPanelDir, 'components', 'AdminShell.tsx');
    const sidebarPath = path.join(adminPanelDir, 'components', 'Sidebar.tsx');

    const adminShellContent = fs.readFileSync(adminShellPath, 'utf-8');
    const sidebarContent = fs.readFileSync(sidebarPath, 'utf-8');

    // Both AdminShell and Sidebar must remove refresh_token on logout
    expect(adminShellContent).toContain('localStorage.removeItem("refresh_token")');
    expect(sidebarContent).toContain('localStorage.removeItem("refresh_token")');

    // Both must import API_URL from @/lib/api rather than hardcoding /api/v1
    expect(adminShellContent).toMatch(/import\s+{[^}]*API_URL[^}]*}\s+from\s+["']@\/lib\/api["']/);
    expect(sidebarContent).toMatch(/import\s+{[^}]*API_URL[^}]*}\s+from\s+["']@\/lib\/api["']/);
  });

  test('ADMIN-ISSUE-003: Admin panel metadata and login page must use Kinochi branding', async () => {
    const layoutPath = path.join(adminPanelDir, 'app', 'layout.tsx');
    const loginPath = path.join(adminPanelDir, 'app', 'login', 'page.tsx');

    const layoutContent = fs.readFileSync(layoutPath, 'utf-8');
    const loginContent = fs.readFileSync(loginPath, 'utf-8');

    // Layout metadata must not reference obsolete MediaPlus branding
    expect(layoutContent).not.toContain('MediaPlus');
    expect(layoutContent).toContain('Kinochi');

    // Login page must not reference obsolete MediaPlus branding
    expect(loginContent).not.toContain('MediaPlus');
    expect(loginContent).toContain('Kinochi');
  });
});
