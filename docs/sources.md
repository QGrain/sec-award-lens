# Source inventory

## Award ground truth

The table describes the verified 2022 and 2023 award sources. Expansion is not marked
complete until each conference-year appears in the coverage matrix. The data is
machine-assisted and source-backed, but it still benefits from independent maintainer
sign-off: `verified` means the extractor found the expected official section and
passed structural validation, not that a second person reviewed every row.

| Year | Conference | Official source | Included awards | Source-specific notes |
| ---: | --- | --- | ---: | --- |
| 2022 | IEEE S&P | [official awards page](https://www.ieee-security.org/TC/SP2022/awards.html) | 4 | The Distinguished Paper section is parsed and stops before Test of Time awards. |
| 2022 | USENIX Security | [official technical sessions](https://www.usenix.org/conference/usenixsecurity22/technical-sessions) | 12 | Award markers are attached to individual paper cards; each links to an official paper page. |
| 2022 | ACM CCS | [official awards page](https://www.sigsac.org/ccs/CCS2022/program/awards.html) | 5 | Distinguished Paper Awards are included; Best Paper Honorable Mentions and Test of Time awards are excluded. |
| 2022 | NDSS | [official symposium page](https://www.ndss-symposium.org/ndss2022/) | 1 | The single Distinguished Paper is included; poster and Test of Time awards are separate. |
| 2023 | IEEE S&P | [official awards program](https://www.ieee-security.org/TC/SP2023/program-awards.html) | 12 | Repeated title/author cards require checking names split by affiliation markup. |
| 2023 | USENIX Security | [official technical sessions](https://www.usenix.org/conference/usenixsecurity23/technical-sessions) | 16 | The same Drupal card pattern is handled by a year-specific adapter. |
| 2023 | ACM CCS | [SIGSAC award archive](https://www.sigsac.org/ccs/CCS_awards/ccs-bestpaper.html) | 17 | Malformed list markup requires tolerant parsing and visual sign-off. |
| 2023 | NDSS | [official symposium page](https://www.ndss-symposium.org/ndss2023/) | 2 | A dedicated Distinguished Paper heading is followed by exactly two linked papers. |

The monitor hashes the normalized extracted records rather than an entire page, so an
analytics script or navigation edit does not create noise. A changed record count or
digest fails the monitor. A maintainer then compares the source and updates curated
data and digest together if the organizer made a legitimate correction.

Historical gaps remain explicit. The next target years are 2021 and 2024; no source is
treated as complete merely because a search returned no awards.

### Unresolved 2022 entities

Google Scholar resolves all 22 records. Nine USENIX Security papers remain `pending`
in OpenAlex because no sufficiently reliable conference or preprint entity was found;
later journal-only records and artifact deposits were not substituted:

- OpenVPN is Open to VPN Fingerprinting
- The Antrim County 2020 Election Incident: An Independent Forensic Investigation
- An Audit of Facebook's Political Ad Policy Enforcement
- Online Website Fingerprinting: Evaluating Website Fingerprinting Attacks on Tor in the Real World
- Identity Confusion in WebView-based Mobile App-in-app Ecosystems
- Provably-Safe Multilingual Software Sandboxing using WebAssembly
- Faster Yet Safer: Logging System Via Fixed-Key Blockcipher
- Private Signaling
- FIXREVERTER: A Realistic Bug Injection Methodology for Benchmarking Fuzz Testing

Semantic Scholar resolves 20 of 22. It returned no suitable record for *Dos and Don'ts
of Machine Learning in Computer Security*, and its only result for *Private Signaling*
was a different 2025 paper. Both remain pending. The OpenVPN S2 record and the ePrint
version of *Faster Yet Safer* are explicit manual overrides with official-page evidence.

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

### Why NDSS has one 2022 paper and two 2023 papers

The official NDSS main-symposium pages list exactly one 2022 Distinguished Paper and
two 2023 Distinguished Papers. Poster awards, Test of Time awards, and co-located
workshops are separate categories or venues and remain outside this cohort.

## Scholarly providers

### OpenAlex

OpenAlex is the open scholarly-graph comparison source. Its API exposes persistent work IDs,
DOIs, work-specific authorships and institutions, machine-assigned primary topics,
publication year, locations, total cited-by count, and recent `counts_by_year`. A
citing-work group-by query can reconstruct a fuller year profile.
Singleton work refreshes are reproducible and do not require search. OpenAlex may
merge or split conference, repository, and preprint versions, so IDs are reviewed and
pinned; known alternatives are recorded rather than summed.

OpenAlex currently permits a small anonymous daily allowance and gives registered free
API keys a larger daily allowance. Singleton work lookups are priced at zero API
credits, while search and filters consume the allowance. The scheduled project workflow
still requires a configured key for predictable operation. API documentation:
<https://developers.openalex.org/api-reference/authentication>

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
to respect Scholar's robots.txt. SecAwardLens does not send requests directly from its
own runner to Scholar. Candidate discovery uses the third-party SerpApi Google Scholar
API. An exact-title search produces review candidates; after title, authors, year,
venue, and versions are checked, the numeric `cites_id` is pinned. Refreshes query that
ID through a configured transport and never repeat title matching.

Neither proxy is an official Google API or a grant of permission from Google. Project
maintainers remain responsible for reviewing Google Scholar's help, robots policy, and
applicable service terms before enabling scheduled access. Automated results enter a
reviewable pull request rather than deploying directly.

SerpApi's free plan currently provides 250 successful searches per month. A complete
69-paper refresh uses roughly 69 searches; candidate discovery for new years is a
separate cost and may need to be staggered. SerpApi is still a parser of Google result pages: its release history includes
fixes for blank IDs and valid searches returning no results after upstream layout
changes. The pipeline therefore treats missing expected fields as a hard failure and
opens reviewable data PRs rather than publishing directly.

API documentation: <https://serpapi.com/google-scholar-api>

ScraperAPI is a verified refresh fallback, not a fourth citation source. Its Google
SERP requests currently cost 25 credits each, so 69 papers cost about 1,725 credits.
The workflow reads the live `creditsLeft` account field and `/account/urlcost` before
selecting a transport, caps each request at 25 credits, rejects CAPTCHA pages even when
the proxy returns HTTP 200, and records `retrieval_service: scraperapi`. Scholar HTML
provides the current result total but not SerpApi's structured citing-year histogram.

In an August 2026 cross-check, ScraperAPI resolved all 47 pinned 2023 clusters: 45
counts exactly matched the earlier SerpApi snapshot and two differed by one citation.
ZenRows auto mode and basic premium-proxy tests returned CAPTCHA or `RESP001` pages.
A later test using ZenRows' full troubleshooting combination—US premium proxy,
JavaScript rendering, an 8-second wait, realistic headers and referer, and original
status reporting—did resolve a pinned cluster with the same count as SerpApi. It was
not stable across a batch: requests still encountered CAPTCHA pages and HTTP 429
responses, including after an interrupted concurrent run. ZenRows is therefore not
in the automated transport pool until a low-concurrency 47/47 verification and
content-aware retry policy succeed. The Python SDK wraps the same Fetch API and adds
retry/concurrency helpers; changing from REST to the SDK does not by itself change the
target-page protection or enabled bypass features.

ScraperAPI documentation: <https://docs.scraperapi.com/credits-and-requests>
ZenRows Fetch troubleshooting: <https://docs.zenrows.com/fetch/features/js-rendering>
