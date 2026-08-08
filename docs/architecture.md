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

Google Scholar is a provider label, not an API vendor: Google offers no public Scholar
API. The adapter uses SerpApi as a third-party transport. Candidate search is isolated
from refresh; after review, a numeric Scholar `cites_id` is pinned and routine updates
query that cluster directly. The public source selector is generated from actual
snapshots, so an implemented but empty provider never becomes a blank site default.
