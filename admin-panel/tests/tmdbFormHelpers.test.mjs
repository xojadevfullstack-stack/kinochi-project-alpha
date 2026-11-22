import test from "node:test";
import assert from "node:assert/strict";

import {
  normalizeTmdbId,
  filterDuplicateResults,
  mergeTmdbDetails,
} from "../lib/tmdbFormHelpers.mjs";

test("normalizeTmdbId returns positive integers and null for empty/zero/invalid", () => {
  assert.equal(normalizeTmdbId(null), null);
  assert.equal(normalizeTmdbId(undefined), null);
  assert.equal(normalizeTmdbId(""), null);
  assert.equal(normalizeTmdbId("   "), null);
  assert.equal(normalizeTmdbId(0), null);
  assert.equal(normalizeTmdbId("0"), null);
  assert.equal(normalizeTmdbId(-12), null);
  assert.equal(normalizeTmdbId("abc"), null);
  assert.equal(normalizeTmdbId("19995"), 19995);
  assert.equal(normalizeTmdbId(" 550 "), 550);
  assert.equal(normalizeTmdbId(1396), 1396);
});

test("filterDuplicateResults excludes self when editing movie or series", () => {
  const dupRes = {
    exact: [
      { id: 42, type: "movie", title: "Inception", code: "1001" },
      { id: 99, type: "movie", title: "Inception Copy", code: "1099" },
    ],
    similar: [
      { id: 42, type: "movie", title: "Inception", code: "1001" },
      { id: 42, type: "series", title: "Inception Series", code: "s_42" },
    ],
  };

  const filteredMovie = filterDuplicateResults(dupRes, 42, "movie");
  assert.deepEqual(filteredMovie, {
    exact: [{ id: 99, type: "movie", title: "Inception Copy", code: "1099" }],
    similar: [{ id: 42, type: "series", title: "Inception Series", code: "s_42" }],
  });

  const onlySelf = filterDuplicateResults(
    { exact: [{ id: 42, type: "series", title: "Dark" }], similar: [] },
    42,
    "series"
  );
  assert.equal(onlySelf, null);

  const whenCreating = filterDuplicateResults(dupRes, null, "movie");
  assert.equal(whenCreating.exact.length, 2);
});

test("mergeTmdbDetails overwrites by default and preserves non-empty fields when fillEmptyOnly is true", () => {
  const prev = {
    title: "Maxsus O'zbekcha Nom",
    description: "",
    tmdb_id: null,
    poster_url: "https://custom.uz/poster.jpg",
    trailer_url: "",
    genres: "Jangari",
    director: "",
    cast: "",
    release_year: 2020,
    duration_minutes: 120,
    imdb_rating: 0,
    category_ids: [1],
  };

  const incoming = {
    title: "Muqaddima",
    description: "Tushlar haqida film",
    tmdb_id: 27205,
    poster_url: "https://image.tmdb.org/t/p/w500/inc.jpg",
    trailer_url: "https://youtube.com/watch?v=abc",
    genres: "Ilmiy fantastika, Jangari",
    director: "Christopher Nolan",
    cast: "Leonardo DiCaprio",
    release_year: 2010,
    duration_minutes: 148,
    imdb_rating: 8.8,
    category_ids: [1, 5],
  };

  const emptyOnlyResult = mergeTmdbDetails(prev, incoming, { fillEmptyOnly: true });
  assert.equal(emptyOnlyResult.title, "Maxsus O'zbekcha Nom");
  assert.equal(emptyOnlyResult.poster_url, "https://custom.uz/poster.jpg");
  assert.equal(emptyOnlyResult.genres, "Jangari");
  assert.equal(emptyOnlyResult.description, "Tushlar haqida film");
  assert.equal(emptyOnlyResult.trailer_url, "https://youtube.com/watch?v=abc");
  assert.equal(emptyOnlyResult.director, "Christopher Nolan");
  assert.equal(emptyOnlyResult.imdb_rating, 8.8);
  assert.equal(emptyOnlyResult.tmdb_id, 27205);
  assert.deepEqual(emptyOnlyResult.category_ids, [1, 5]);

  const fullResult = mergeTmdbDetails(prev, incoming, { fillEmptyOnly: false });
  assert.equal(fullResult.title, "Muqaddima");
  assert.equal(fullResult.poster_url, "https://image.tmdb.org/t/p/w500/inc.jpg");
  assert.equal(fullResult.release_year, 2010);

  const untranslatedResult = mergeTmdbDetails(
    { ...prev, description: "Mavjud o'zbekcha ta'rif" },
    {
      ...incoming,
      title: "星河入梦",
      description: "В будущем...",
      isTitleTranslated: false,
      isDescriptionTranslated: false,
    },
    { fillEmptyOnly: false }
  );
  assert.equal(untranslatedResult.title, "Maxsus O'zbekcha Nom");
  assert.equal(untranslatedResult.description, "Mavjud o'zbekcha ta'rif");
});
