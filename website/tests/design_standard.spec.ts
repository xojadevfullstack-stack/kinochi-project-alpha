import { test, expect } from "@playwright/test";
import fs from "fs";
import path from "path";

test.describe("Cinematic Red Design Standard Law Enforcement", () => {
  test("LiveSearch CTA buttons must use Primary Red and NEVER rating-gold", () => {
    const filePath = path.resolve(__dirname, "../components/LiveSearch.tsx");
    const content = fs.readFileSync(filePath, "utf-8");

    // Line 556 and 612 CTA buttons must not use rating-gold for CTA styling
    expect(content).not.toContain("bg-rating-gold/20 hover:bg-rating-gold");
    expect(content).not.toContain("bg-rating-gold text-background-obsidian");
  });

  test("ReportIssueModal and Button must use Primary Red instead of amber for CTA, active chips, and focus", () => {
    const modalPath = path.resolve(__dirname, "../components/ReportIssueModal.tsx");
    const modalContent = fs.readFileSync(modalPath, "utf-8");

    // Submit button must not use amber gradient
    expect(modalContent).not.toContain("from-amber-600 to-amber-500");
    // Active chip must not use amber border
    expect(modalContent).not.toContain("border-amber-500");
    // Focus ring must not use amber
    expect(modalContent).not.toContain("focus:ring-amber-500");

    const btnPath = path.resolve(__dirname, "../components/ReportIssueButton.tsx");
    const btnContent = fs.readFileSync(btnPath, "utf-8");
    // Report button hovers must not be amber
    expect(btnContent).not.toContain("hover:border-amber-500");
    expect(btnContent).not.toContain("hover:bg-amber-500");
  });
});
