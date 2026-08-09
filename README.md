# SecAwardLens

[![CI](https://github.com/QGrain/sec-award-lens/actions/workflows/ci.yml/badge.svg)](https://github.com/QGrain/sec-award-lens/actions/workflows/ci.yml)
[![Original curation: CC0-1.0](https://img.shields.io/badge/original_curation-CC0--1.0-green.svg)](DATA_LICENSE.md)
[![Code: Apache-2.0](https://img.shields.io/badge/code-Apache--2.0-blue.svg)](LICENSE)

SecAwardLens is a reproducible dataset and static web application for exploring the
citation impact of award-winning papers from IEEE S&P, USENIX Security, ACM CCS,
and NDSS.

It treats an award, a scholarly entity, and a citation count as three separate,
auditable records. Official conference pages are the award ground truth. External
paper IDs are conservatively matched and then pinned. Citation counts are stored as
immutable, time-stamped observations.

## Current data release

The current release covers **69 core paper awards across 2022 and 2023**:

| Award year | Official awards | Google Scholar | OpenAlex | Semantic Scholar |
| --- | ---: | ---: | ---: | ---: |
| 2022 | 22 | 22 | 13 | 20 |
| 2023 | 47 | 47 | 42 | 46 |

The official 2022 award counts are IEEE S&P 4, USENIX Security 12, ACM CCS 5,
and NDSS 1; the 2023 counts are 12, 16, 17, and 2 respectively. Unresolved
provider entities remain visibly unavailable and are never assigned to weak
lookalikes or filled with another provider's count.

The pipeline supports Google Scholar observations primarily through SerpApi, with a
quota-aware ScraperAPI fallback for pinned citation clusters. Google Scholar has no
official public API, so records distinguish the underlying source from the retrieval
service. Reviewed Scholar snapshots are selected by default, while OpenAlex and
Semantic Scholar remain independently selectable comparison views.

## Quick start

Requirements: Python 3.11+, [uv](https://docs.astral.sh/uv/), Node.js 24+, and npm.

```bash
uv sync --all-extras
uv run secawardlens data validate
uv run secawardlens build

cd web
npm ci
npm run dev
```

Open <http://localhost:5173>. For a production-equivalent local preview, run
`npm run build && npm run preview` in `web/` and open <http://localhost:4173>.

Useful pipeline commands:

```bash
# Detect changed official award records; does not rewrite curated data.
uv run secawardlens awards check

# Print review candidates; does not change pinned bindings.
uv run secawardlens match openalex --paper-id PAPER_ID
uv run secawardlens match semantic-scholar --paper-id PAPER_ID
uv run secawardlens match google-scholar --paper-id PAPER_ID

# Append a UTC-dated snapshot using existing verified IDs only.
uv run secawardlens citations refresh

# Limit matching or refresh work to one award year.
uv run secawardlens match openalex --year 2022
uv run secawardlens citations refresh --provider all --year 2022

# Regenerate JSON Schema and frontend data.
uv run secawardlens schema export
uv run secawardlens build

# Validate and dry-run one maintainer review form; --write applies it atomically.
uv run secawardlens review validate data/review/submissions/FORM.yml
uv run secawardlens review apply data/review/submissions/FORM.yml
```

`OPENALEX_API_KEY` is recommended for OpenAlex API commands and required by the
scheduled workflow's configuration. Small anonymous singleton lookups can use
OpenAlex's limited anonymous allowance. `S2_API_KEY` is required for
Semantic Scholar candidate discovery and refresh. Create an OpenAlex key at
<https://openalex.org/settings/api> and export it locally with
`export OPENALEX_API_KEY=...`; export an approved S2 key with `export S2_API_KEY=...`.
Google Scholar candidate discovery uses a SerpApi account key exported as
`SERPAPI_KEY`. Refresh can also use `SCRAPERAPI_KEY` as a capacity-checked fallback;
never commit either key. The current 69-paper release costs about 69 SerpApi searches or
1,725 ScraperAPI credits for one complete refresh. SerpApi remains preferred because its
structured response includes citing-year counts; the ScraperAPI HTML fallback provides
only the current total.
Building or previewing already committed data needs neither key. Routine citation
refreshes never search or rematch a paper.

The web interface defaults to English and a light theme. Visitors can switch between
English/Chinese UI text and Light/Dark/System themes; paper titles, authors, venues,
and other source metadata remain in their original language.
An optional GoatCounter integration adds a privacy-friendly, site-wide view count to
the footer when the public `GOATCOUNTER_CODE` repository variable is configured; see
the deployment guide for the one-time setup.

## Repository map

```text
data/curated/       reviewed conferences, editions, awards, papers, bindings, overrides
data/provenance/    source registry and historical coverage matrix
data/snapshots/     append-only citation observations (JSONL)
schemas/            generated JSON Schemas
src/secawardlens/   Python collectors, providers, resolver, validation, build CLI
tests/              parser, entity-resolution, metric, and repository contract tests
web/                React + TypeScript + Vite static application
.github/workflows/  CI, source monitoring, citation refresh PRs, Pages deployment
docs/               methods, architecture, data-source and contributor guides
```

Start with [the methodology](docs/methodology.md). The official-source inventory,
current release audit, and provider limitations are in
[the source inventory](docs/sources.md); contributor workflows are in
[CONTRIBUTING.md](CONTRIBUTING.md).
Deployment and secret configuration are documented in
[the deployment guide](docs/deployment.md). Missing or ambiguous entities follow the
[human curation workflow](docs/manual-curation-workflow.md).

## Design principles

- Official organizers decide what won; scholarly APIs do not.
- A DOI match is accepted only with basic title/year sanity checks.
- Ambiguity is a review state, never an invitation to pick the first result.
- Confirmed external IDs persist across refreshes.
- Snapshot history is append-only and includes response digests.
- Conference totals are not used as an impact league table; distributions and
  paper-level age windows are shown instead.
- Generated site JSON is committed so every deployment is reproducible from a Git
  revision.

## License

Source code is Apache-2.0. Maintainer-owned selection, normalization, and curation are
dedicated to the public domain under CC0-1.0; upstream provider and conference content
remains subject to its original terms. See [DATA_LICENSE.md](DATA_LICENSE.md).
