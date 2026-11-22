import test from "node:test";
import assert from "node:assert/strict";

import {
  normalizeBreadcrumbPath,
  buildBreadcrumbs,
} from "../lib/breadcrumbHelpers.mjs";

test("normalizeBreadcrumbPath decodes URI components and strips trailing slashes", () => {
  assert.equal(normalizeBreadcrumbPath("/movie/PJH3KH/"), "/movie/PJH3KH");
  assert.equal(normalizeBreadcrumbPath("/collections/o%27zbek-kino"), "/collections/o'zbek-kino");
  assert.equal(normalizeBreadcrumbPath("/"), "/");
});

test("buildBreadcrumbs replaces last dynamic segment with matching route title", () => {
  const movieCrumbs = buildBreadcrumbs("/movie/PJH3KH", {
    "/movie/PJH3KH": "Qasoskorlar: Intiho",
  });
  assert.deepEqual(
    movieCrumbs.map((c) => ({ label: c.label, href: c.href, isLast: c.isLast })),
    [
      { label: "Film", href: "/catalog", isLast: false },
      { label: "Qasoskorlar: Intiho", href: "/movie/PJH3KH", isLast: true },
    ]
  );

  const seriesCrumbs = buildBreadcrumbs("/series/42", {
    "/series/42": "Chernobil",
  });
  assert.equal(seriesCrumbs[1].label, "Chernobil");

  const catCrumbs = buildBreadcrumbs("/category/7", {
    "/category/7": "Fantastika",
  });
  assert.equal(catCrumbs[1].label, "Fantastika");

  const colCrumbs = buildBreadcrumbs("/collections/marvel-koinoti", {
    "/collections/marvel-koinoti": "Marvel Koinoti",
  });
  assert.equal(colCrumbs[1].label, "Marvel Koinoti");

  const pageCrumbs = buildBreadcrumbs("/p/anime-olami", {
    "/p/anime-olami": "Anime Olami",
  });
  assert.equal(pageCrumbs[1].label, "Anime Olami");
});

test("buildBreadcrumbs ignores stale overrides from other routes and falls back cleanly", () => {
  const crumbs = buildBreadcrumbs("/movie/NEW999", {
    "/movie/OLD111": "Eski Kino Nomi",
  });
  assert.equal(crumbs[1].label, "#NEW999");

  const encodedCrumbs = buildBreadcrumbs("/collections/o%27zbek-kino", {
    "/collections/o'zbek-kino": "O'zbek Kino",
  });
  assert.equal(encodedCrumbs[1].label, "O'zbek Kino");
});
