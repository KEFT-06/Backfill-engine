# Schema eras

> The eras of the GH Archive event schema, **discovered** from the data itself
> (`scripts/discover_schema_eras.py`), not assumed.

## Method

Sample one hour per year (`YYYY-06-15-12`), read it with DuckDB, and record a
compact signature: top-level columns, whether `actor` is a struct, and whether the
production whitelist (`id, type, actor.login, repo.name, created_at`) resolves.
Where the signature changes = an era boundary. **Discovery, never assumption** —
this project was burned twice in one evening by a-priori guesses (see below).

## Findings (first pass — 2026-07-14)

| Year | Whitelist | `actor` is struct? | Note |
|------|-----------|--------------------|------|
| 2011 | ✅ OK      | oui                | |
| 2012 | — | — | download failed (SSL/network) |
| 2013 | ❌ **CASSE** | **NON**            | `Binder Error: Column "id" ...` — real drift |
| 2014 | — | — | download failed (network) |
| 2015 | — | — | download timed out (network) |
| 2016 | ✅ OK      | oui                | |
| 2018 | — | — | download failed (network) |
| 2020 | ✅ OK      | oui                | |
| 2022 | ✅ OK      | oui                | |

**Key finding:** the whitelist is **not** uniformly robust. **2013 breaks it** —
`actor` is not a struct there, so `actor.login` fails. A real schema era exists in
the pre-2015 range. (2011 works, 2013 doesn't → the boundary is not a clean single
year; it needs a denser, cleaner sweep to pin down.)

**Two a-priori assumptions this pass DISPROVED:**
1. "In 2011 `actor` was a string" — false; 2011 `actor` is a struct and the
   whitelist works there.
2. "The whitelist is robust across all eras" (claimed from only 2 samples: 2011 +
   2015) — false; a broader sweep found 2013 breaks it.

The lesson, twice over: **sample, don't assume.**

## Open questions (for the next session, fresh)

- Re-run the discovery on a stable connection (many years were unavailable tonight
  due to network) to fill the gaps and pin the exact era boundary/boundaries.
- What exactly is `actor` in the broken era (string? different nesting?) — inspect
  a 2013 file directly.
- Decide the mapping strategy: a versioned parser for the broken era(s), or a
  tolerant extraction (e.g., `TRY`/coalesce) that normalizes both shapes to the
  stable output contract.

## Decision

_tbd — Karl's call, with a clean sweep. Do NOT assume; measure first._
