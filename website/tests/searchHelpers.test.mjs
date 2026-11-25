import test from "node:test";
import assert from "node:assert/strict";
import {
  buildSearchTrackPayload,
  getDisplaySearchCode,
  getSearchResultHref,
} from "../lib/searchHelpers.mjs";

test("getSearchResultHref builds routes for movie, series, and collection", () => {
  assert.equal(getSearchResultHref({ id: 10, code: "ABC", type: "movie" }), "/movie/ABC");
  assert.equal(getSearchResultHref({ id: 25, code: "s_25", type: "series" }), "/series/25");
  assert.equal(getSearchResultHref({ id: 3, code: "marvel", type: "collection" }), "/collections/marvel");
});

test("buildSearchTrackPayload tracks movies and series and skips collections", () => {
  assert.deepEqual(buildSearchTrackPayload({ id: 12, type: "movie" }), {
    media_type: "movie",
    item_id: 12,
  });
  assert.deepEqual(buildSearchTrackPayload({ id: 44, type: "series" }), {
    media_type: "series",
    item_id: 44,
  });
  assert.equal(buildSearchTrackPayload({ id: 3, type: "collection" }), null);
});

test("getDisplaySearchCode prefers short_code over internal code", () => {
  assert.equal(getDisplaySearchCode({ code: "ABC123", short_code: "3955" }), "3955");
  assert.equal(getDisplaySearchCode({ code: "s_25", short_code: null }), "s_25");
});
