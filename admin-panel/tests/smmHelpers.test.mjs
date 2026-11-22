import test from "node:test";
import assert from "node:assert/strict";
import { cleanMediaCode, formatSmmStatusLabel, shouldPollProgress } from "../lib/smmHelpers.mjs";

test("cleanMediaCode strips leading hash and whitespace", () => {
  assert.equal(cleanMediaCode(" #3956 "), "3956");
  assert.equal(cleanMediaCode("WPZ79R"), "WPZ79R");
});

test("formatSmmStatusLabel returns clear Uzbek labels for all statuses", () => {
  assert.equal(formatSmmStatusLabel("generating"), "Tayyorlanmoqda");
  assert.equal(formatSmmStatusLabel("waiting_approval"), "Tasdiq kutmoqda");
  assert.equal(formatSmmStatusLabel("scheduled"), "Navbatda");
  assert.equal(formatSmmStatusLabel("publishing"), "Chiqarilmoqda");
  assert.equal(formatSmmStatusLabel("completed"), "Chiqarilgan");
  assert.equal(formatSmmStatusLabel("failed"), "Xatolik");
  assert.equal(formatSmmStatusLabel("rejected"), "Rad etilgan");
});

test("shouldPollProgress activates when Cycle 1 or Cycle 2 has active work", () => {
  assert.equal(
    shouldPollProgress(
      { cycle1: { in_progress: 0 }, cycle2: { generating: 0, publishing: 0 } },
      []
    ),
    false
  );
  assert.equal(
    shouldPollProgress(
      { cycle1: { in_progress: 1 }, cycle2: { generating: 0, publishing: 0 } },
      []
    ),
    true
  );
  assert.equal(
    shouldPollProgress(null, [{ status: "generating" }]),
    true
  );
});
