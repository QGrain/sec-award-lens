# Source inventory

## Award ground truth

The table describes what has been verified in the initial 2023 release. Historical
expansion is not marked complete until each conference-year appears in the coverage
matrix. The current data is machine-assisted and source-backed, but it still needs an
independent maintainer sign-off: `verified` means the extractor found the expected
official section and passed structural validation, not that a second person reviewed
every row.

| Conference | Verified 2023 source | Observed structure | Automation assessment | Human follow-up |
| --- | --- | --- | --- | --- |
| IEEE S&P | [official awards program](https://www.ieee-security.org/TC/SP2023/program-awards.html) | A dedicated Distinguished Paper Award section with repeated title/author cards | High for 2023; event-site templates and award labels must be checked per era | Compare all 12 titles; check the manually separated `Pubali Datta / Noel Warford` and `Moritz Schloegel / Manuel Vögele` names |
| USENIX Security | [official technical sessions](https://www.usenix.org/conference/usenixsecurity23/technical-sessions) | Award marker inside each paper card; title, author markup, and paper URL are nearby | High within this Drupal template; older conference templates need separate adapters | Highest priority: sign off all 16 cards, review 11 repository/preprint overrides, and resolve the five entities below |
| ACM CCS | [SIGSAC award archive](https://www.sigsac.org/ccs/CCS_awards/ccs-bestpaper.html) | One organizer-maintained page grouped by year | High coverage potential, but the 2023 HTML omits closing list-item tags and requires tolerant parsing | Visually sign off all 17 records because the source HTML is malformed |
| NDSS | [official 2023 symposium page](https://www.ndss-symposium.org/ndss2023/) | A Distinguished Paper Award heading followed by exactly two linked papers | Moderate; annual WordPress pages vary and no single verified historical table is assumed | Low risk: sign off the two-title list; program titles/authors already cross-check |

The monitor hashes the normalized extracted records rather than an entire page, so an
analytics script or navigation edit does not create noise. A changed record count or
digest fails the monitor. A maintainer then compares the source and updates curated
data and digest together if the organizer made a legitimate correction.

Historical gaps remain explicit. The next target years are 2022 and 2024; no source is
treated as complete merely because a search returned no awards.

### Unresolved 2023 entities

Five USENIX Security papers remain `pending` after a keyed OpenAlex full-text search
and work-autocomplete check on 2026-08-08. They have no OpenAlex citation count on the
site and are not treated as zero-citation papers:

- Account Security Interfaces: Important, Unintuitive, and Untrustworthy
- Don’t be Dense: Efficient Keyword PIR for Sparse Databases
- A Two-Decade Retrospective Analysis of a University's Vulnerability to Attacks
  Exploiting Reused Passwords
- Remote Direct Memory Introspection
- An Efficient Design of Intelligent Network Data Plane

Semantic Scholar independently resolves four of these five OpenAlex gaps. Provider
coverage remains separate: an S2 count does not fill or replace a missing OpenAlex
observation. Use the [human curation workflow](manual-curation-workflow.md) for future
entity decisions.

### Why NDSS has two included papers

The official NDSS 2023 main-symposium page has a distinct “2023 Distinguished Paper
Award Winners” heading followed by exactly two papers. Best Technical Poster and Best
Poster Presentation are separate sections and outside the project scope. Search
results also surface co-located workshops such as VehicleSec; those are separate venues
and must not be added to the NDSS main-conference cohort.

## Scholarly providers

### OpenAlex

OpenAlex is the open scholarly-graph comparison source. Its API exposes persistent work IDs,
DOIs, work-specific authorships and institutions, machine-assigned primary topics,
publication year, locations, total cited-by count, and recent `counts_by_year`. A
citing-work group-by query can reconstruct a fuller year profile.
Singleton work refreshes are reproducible and do not require search. OpenAlex may
merge or split conference, repository, and preprint versions, so IDs are reviewed and
pinned; known alternatives are recorded rather than summed.

As of February 2026, production API requests require a free API key. Singleton work
lookups are priced at zero API credits, while search and filters consume the free daily
allowance. API documentation: <https://developers.openalex.org/api-reference/authentication>

### Semantic Scholar

The provider adapter supports DOI lookup, exact and ranked title search, persistent
paper IDs, total citation count, and influential citation count. The approved key is
used only in maintainer-controlled jobs at less than one request per second. Reviewed
IDs and minimal citation observations are published as a distinct provider series;
raw API responses are not committed. S2-derived fields remain outside the project's
CC0 dedication because S2 data and underlying third-party content may carry separate
licenses. See [the publication decision](semantic-scholar-publication.md).

Public pages include Semantic Scholar name/logo attribution, a link-back carrying
`utm_source=api`, and a citation to *The Semantic Scholar Open Data Platform*. This
provides the required display attribution for the published S2 comparison view.

API documentation: <https://api.semanticscholar.org/api-docs/graph>

### Crossref

Crossref is a DOI and bibliographic metadata helper. It is useful for independently
confirming a publisher DOI from title, authors, year, and proceedings venue. Its
`is-referenced-by-count` is not used as the site's citation metric because Crossref
coverage depends on deposited references and does not provide the same history model.

REST API documentation: <https://www.crossref.org/documentation/retrieve-metadata/rest-api/>

### Google Scholar

Google Scholar usually reports larger counts because it crawls a broader set of
scholarly material, including theses, books, repositories, preprints, conference
copies, and non-English documents. It also clusters versions differently from
OpenAlex and Semantic Scholar. A larger number therefore means broader observed
coverage, not a provider-independent “true” count.

Google does not offer a public Scholar API and its help page asks automated software
to respect Scholar's robots.txt. SecAwardLens does not directly scrape Scholar.
Instead, its optional adapter uses the third-party SerpApi Google Scholar API. An
exact-title search produces review candidates; after title, authors, year, venue, and
versions are checked, the numeric `cites_id` is pinned. Refreshes query `cites_id`
directly, append total counts and the available `citations_per_year`, and never repeat
title matching.

SerpApi's free plan currently provides 250 successful searches per month and 50 per
hour. A 47-paper candidate or refresh pass uses roughly 47 searches; two passes fit
comfortably, while several historical years will require staggered updates or a paid
plan. SerpApi is still a parser of Google result pages: its release history includes
fixes for blank IDs and valid searches returning no results after upstream layout
changes. The pipeline therefore treats missing expected fields as a hard failure and
opens reviewable data PRs rather than publishing directly.

API documentation: <https://serpapi.com/google-scholar-api>
