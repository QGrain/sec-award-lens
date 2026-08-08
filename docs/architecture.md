# Architecture

The system is deliberately database-free. Reviewed YAML and append-only JSONL are the
source of truth; deterministic JSON is the frontend contract.

```text
official award pages ── adapters ──> curated award/paper YAML
                                          │
OpenAlex / Crossref ── candidate search ──> reviewed provider bindings
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

GitHub Actions has four independent paths: pull-request CI, weekly citation refresh
via a reviewable bot PR, monthly official-source contract checks, and deployment from
`main`. This keeps external drift from bypassing review.
