import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const websiteRoot = path.resolve(__dirname, "..");

function readRel(relPath) {
  return fs.readFileSync(path.join(websiteRoot, relPath), "utf8");
}

test("Portal modals adapt both backdrop and dialog surface to Light and Dark mode", () => {
  const portalModals = [
    "components/AgeVerificationModal.tsx",
    "components/ReportIssueModal.tsx",
    "components/RequestMovieModal.tsx",
  ];

  for (const file of portalModals) {
    const src = readRel(file);
    assert.match(
      src,
      /bg-slate-900\/55\s+dark:bg-black\//,
      `${file} must use a Light/Dark adaptive backdrop instead of fixed bg-black/80`
    );
    assert.match(
      src,
      /bg-white\/95\s+dark:bg-\[#12141D\]/,
      `${file} must render a light dialog surface (bg-white/95 dark:bg-[#12141D])`
    );
    assert.match(
      src,
      /text-slate-900\s+dark:text-/,
      `${file} must include dark-on-light typography (text-slate-900 dark:text-*)`
    );
  }
});

test("In-page modals and bottom sheets support Light Mode cleanly", () => {
  const inPageModals = [
    "components/SubscribeButton.tsx",
    "components/CategoryFilter.tsx",
    "components/media/ActorFilmographyModal.tsx",
    "app/actors/page.tsx",
    "app/profile/page.tsx",
  ];

  for (const file of inPageModals) {
    const src = readRel(file);
    assert.match(
      src,
      /bg-slate-900\/55\s+dark:bg-black\//,
      `${file} modal backdrop must use bg-slate-900/55 dark:bg-black/*`
    );
  }

  const categoryFilter = readRel("components/CategoryFilter.tsx");
  assert.doesNotMatch(
    categoryFilter,
    /\bbg-background-obsidian\/95\b/,
    "CategoryFilter sheet must not hardcode bg-background-obsidian/95"
  );
  assert.match(
    categoryFilter,
    /bg-white\/95\s+dark:bg-\[#12141D\]/,
    "CategoryFilter sheet must use light/dark surface classes"
  );
});

test("Interactive cards, skeletons, tabs, and error fallbacks handle Light Mode", () => {
  const mediaLoader = readRel("components/ui/MediaLoader.tsx");
  assert.match(
    mediaLoader,
    /bg-slate-200/,
    "MediaLoader skeleton placeholders must stay visible in Light Mode"
  );

  const reviews = readRel("components/reviews/ReviewsSection.tsx");
  assert.match(
    reviews,
    /bg-amber-50\s+dark:bg-black\/40/,
    "ReviewsSection selected rating badge must adapt to Light Mode"
  );

  const navbar = readRel("components/Navbar.tsx");
  assert.match(
    navbar,
    /bg-slate-100\/90.*dark:bg-white\/5/,
    "Navbar sidebar profile card must adapt to Light Mode"
  );

  const errorPage = readRel("app/error.tsx");
  assert.match(
    errorPage,
    /bg-slate-200\s+hover:bg-slate-300\s+dark:bg-zinc-800/,
    "app/error.tsx secondary action must be legible in Light Mode"
  );

  const historyTabs = readRel("components/history/HistoryTabs.tsx");
  assert.match(
    historyTabs,
    /bg-\[#E50914\]\s+text-white/,
    "HistoryTabs active tab must use Cinematic Red for clear Light/Dark contrast"
  );
});
