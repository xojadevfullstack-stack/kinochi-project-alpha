import test from "node:test";
import assert from "node:assert/strict";

import {
  getStreamableTranslations,
  buildStreamSignEndpoint,
  mapStreamErrorToUzbek,
  saveContinueWatching,
} from "../lib/streamHelpers.mjs";

test("getStreamableTranslations filters only items with valid id and storage_channel_message_id", () => {
  const input = [
    { id: 1, language: "O'zbekcha", storage_channel_message_id: 501 },
    { id: 2, language: "Ruscha", storage_channel_message_id: null },
    { id: 3, language: "  ", storage_channel_message_id: 502 },
    { id: null, language: "Inglizcha", storage_channel_message_id: 503 },
    { id: 4, language: "HD Dublyaj", storage_channel_message_id: 0 },
  ];
  const out = getStreamableTranslations(input);
  assert.deepEqual(out, [
    { id: 1, language: "O'zbekcha", storage_channel_message_id: 501 },
    { id: 3, language: "Asl / Dublyaj", storage_channel_message_id: 502 },
  ]);
  assert.deepEqual(getStreamableTranslations(null), []);
});

test("buildStreamSignEndpoint constructs clean query string", () => {
  assert.equal(
    buildStreamSignEndpoint("movie", 12),
    "/stream/url?media_type=movie&translation_id=12"
  );
  assert.equal(
    buildStreamSignEndpoint("episode", "44"),
    "/stream/url?media_type=episode&translation_id=44"
  );
});

test("mapStreamErrorToUzbek maps 503, 404, and codec/playback failures cleanly", () => {
  assert.match(mapStreamErrorToUzbek(503), /sozlanmoqda|Telegram/i);
  assert.match(mapStreamErrorToUzbek(404), /topilmadi|Telegram/i);
  assert.match(mapStreamErrorToUzbek("codec"), /format|Telegram/i);
});

test("saveContinueWatching deduplicates by id, caps at 10 items, and preserves newest first", () => {
  const mem = new Map();
  const fakeStorage = {
    getItem: (k) => mem.get(k) ?? null,
    setItem: (k, v) => mem.set(k, String(v)),
  };

  for (let i = 1; i <= 11; i += 1) {
    saveContinueWatching({ id: i, title: `Item ${i}`, type: "episode" }, fakeStorage);
  }
  saveContinueWatching({ id: 5, title: "Item 5 Updated", type: "episode" }, fakeStorage);

  const saved = JSON.parse(mem.get("mediaplus_continue_watching"));
  assert.equal(saved.length, 10);
  assert.equal(saved[0].id, 5);
  assert.equal(saved[0].title, "Item 5 Updated");
  assert.equal(saved.filter((x) => x.id === 5).length, 1);
});
