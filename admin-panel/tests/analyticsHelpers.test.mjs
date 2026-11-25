import test from "node:test";
import assert from "node:assert/strict";
import {
  computeBarHeightPct,
  computeSourceShare,
  summarizeTmdbCoverage,
} from "../lib/analyticsHelpers.mjs";

test("computeBarHeightPct handles zero and clamps between 4 and 100", () => {
  assert.equal(computeBarHeightPct(0, 100), 0);
  assert.equal(computeBarHeightPct(1, 1000), 4);
  assert.equal(computeBarHeightPct(50, 100), 50);
  assert.equal(computeBarHeightPct(120, 100), 100);
});

test("computeSourceShare computes exact normalized percentages", () => {
  assert.deepEqual(computeSourceShare(0, 0, 0), {
    total: 0,
    botPct: 0,
    webPct: 0,
    streamPct: 0,
  });
  assert.deepEqual(computeSourceShare(60, 30, 10), {
    total: 100,
    botPct: 60,
    webPct: 30,
    streamPct: 10,
  });
});

test("summarizeTmdbCoverage classifies in_library, requested, and missing items", () => {
  const summary = summarizeTmdbCoverage([
    { tmdb_id: 1, in_library: true, is_requested: false },
    { tmdb_id: 2, in_library: false, is_requested: true },
    { tmdb_id: 3, in_library: false, is_requested: false },
    { tmdb_id: 4, in_library: true, is_requested: true },
  ]);
  assert.deepEqual(summary, {
    total: 4,
    inLibrary: 2,
    requested: 1,
    missing: 1,
  });
});
