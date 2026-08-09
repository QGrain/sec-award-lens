# Architecture

The system is deliberately database-free. Reviewed YAML and append-only JSONL are the
source of truth; deterministic JSON is the frontend contract.

```text
official award pages ── adapters ──> curated award/paper YAML
                                          │
OpenAlex / S2 / Scholar via SerpApi ─────> reviewed provider bindings
                                          │
pinned OpenAlex works ── metadata review ─> topic / affiliation enrichment
                                          │
pinned provider IDs ── direct refresh ────> immutable JSONL snapshots
                                          │
                              validation + metric build
                                          │
                                  static site JSON
                                          │
                                  React / ECharts
```

Python owns source parsing, normalization, identity resolution, provider access,
validation, metric computation, and static-data generation. Pydantic models reject
unknown fields. JSON Schemas are generated for external tooling.

The web application is a Vite-built React/TypeScript single-page app using hash routes,
which work on GitHub Pages without rewrite rules. ECharts is lazy-loaded for
conference comparisons and year-level citation profiles. All data is fetched from
versioned static JSON; the browser never calls a scholarly API.

GitHub Actions has four independent paths: pull-request CI, monthly citation refresh
via a reviewable bot PR, monthly official-source contract checks, and deployment from
`main`. Provider candidate discovery remains a local maintainer command so search
results and quota-consuming entity resolution cannot bypass review.

## File lifecycle

Repository files follow four explicit lifecycles:

- `data/curated/`, `data/provenance/`, and accepted review forms are maintained source
  records. They change only through reviewed corrections or coverage expansion.
- `data/snapshots/` is append-only evidence. A refresh creates at most one file per
  provider and UTC date; validation rejects duplicate paper/provider/timestamp
  observations. Older files remain inputs to citation history and are not stale build
  artifacts.
- `schemas/` and `web/public/data/` are deterministic, committed outputs. Their files
  are overwritten by `schema export` and `build`; they are never edited manually. CI
  regenerates both and fails when the checked-in result differs.
- `.env*`, virtual environments, dependencies, caches, coverage reports, and `dist/`
  directories are local-only and ignored. They may be deleted and regenerated at any
  time and must never appear in a data or release commit.

Adding another conference year intentionally adds paper detail JSON files. Citation
refreshes do not add another set of paper files; they rewrite the same per-paper and
per-year frontend contracts while adding only the dated source snapshot.

Google Scholar is a provider label, not an API vendor: Google offers no public Scholar
API. Candidate discovery uses SerpApi. After review, a numeric Scholar `cites_id` is
pinned and routine updates query that cluster directly. Refresh checks live account
capacity and prefers SerpApi because it returns structured citing-year counts; a
verified ScraperAPI HTML transport can supply current totals when SerpApi cannot cover
the batch. Each observation records the retrieval service, and CAPTCHA or missing-count
pages are hard failures. The public source selector is generated from actual snapshots,
so an implemented but empty provider never becomes a blank site default.
