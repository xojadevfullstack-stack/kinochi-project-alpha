import assert from "node:assert/strict";
import test from "node:test";
import { buildSocialItems } from "../lib/socialLinks.mjs";

test("buildSocialItems returns verified links in consistent order and omits empty entries", () => {
  const items = buildSocialItems("@MediaPlusOfficialBot", {
    telegram_channel: "https://t.me/MediaPlusOfficial",
    instagram: "https://www.instagram.com/mediaplusofficialbot/",
    youtube: "https://www.youtube.com/@MediaPlusOfficialbot",
    facebook: "https://www.facebook.com/profile.php?id=1321205927744639",
    tiktok: "",
  });

  assert.deepEqual(
    items.map((x) => x.key),
    ["telegram_bot", "telegram_channel", "instagram", "youtube", "facebook"]
  );
  assert.equal(items[0].href, "https://t.me/MediaPlusOfficialBot");
  assert.equal(items[1].href, "https://t.me/MediaPlusOfficial");
});

test("buildSocialItems includes TikTok when configured and drops unsafe non-http schemes", () => {
  const items = buildSocialItems("MediaPlusOfficialBot", {
    telegram_channel: "javascript:alert(1)",
    instagram: "https://www.instagram.com/mediaplusofficialbot/",
    youtube: "",
    facebook: "",
    tiktok: "https://www.tiktok.com/@mediaplusofficial",
  });

  assert.deepEqual(
    items.map((x) => x.key),
    ["telegram_bot", "instagram", "tiktok"]
  );
  assert.equal(items[2].href, "https://www.tiktok.com/@mediaplusofficial");
});
