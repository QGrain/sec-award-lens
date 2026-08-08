# Semantic Scholar publication decision

## What “not published” means

The Python adapter is open-source code and can perform paper lookup and citation-count
retrieval. However, project automation does not call it, no Semantic Scholar paper IDs
or counts are committed under `data/`, generated site JSON lists only OpenAlex, and the
public web application displays no Semantic Scholar series.

Consequences: the site has no cross-provider comparison and does not currently use
Semantic Scholar to fill the five unresolved OpenAlex records. The project therefore
has no Semantic Scholar API uptime or rate-limit dependency. It does not affect
official award coverage or OpenAlex data. A diagnostic lookup found an exact Semantic
Scholar entity for one of the five papers, demonstrating that the providers can be
complementary; it remains unpublished pending the decision described here.

## What “pending review” means

This is a licensing and publication-policy decision, not unfinished entity-resolution
code. Semantic Scholar's API agreement grants conditional API access and display. It
also says S2 data can have separate licenses and underlying third-party content can
carry additional terms. Other published license text requires attribution/link-back
for public use and restricts sharing or commercialization in some circumstances.

SecAwardLens currently dedicates its original data files to CC0. Before placing
API-derived Semantic Scholar observations in the same downloadable repository, the
maintainer should establish that the intended static storage, GitHub redistribution,
CC0 boundary, and public display comply with the applicable agreement. This document
is project-risk guidance, not legal advice.

## Recommended maintainer action

The safest current choice is to do nothing and keep OpenAlex as the only public source.
To enable Semantic Scholar later:

1. Describe the exact use case to AI2 through the API-key/contact form: a non-commercial
   open-source static site that periodically stores and republishes paper IDs and
   citation counts.
2. Ask whether committed historical snapshots may be redistributed, what data license
   applies, and whether the required public attribution is a text link, logo, or both.
3. If approved, segregate S2-derived snapshots from CC0 original data, add the required
   license/attribution notice and `utm_source=api` link, configure a secret API key, and
   change `public_output_enabled` only in the same reviewed pull request.
4. Add independent provider bindings; do not copy OpenAlex decisions automatically or
   combine counts from the two sources.

The application should explicitly disclose the static public website and proposed
timestamped GitHub snapshots; a key approval should not be silently interpreted as
broader redistribution permission unless AI2 confirms that use.

## API key application answers

Select **Public (Free / Nonprofit)**. SecAwardLens is a public, non-commercial research
dataset and website, so `Private` would not describe the intended use.

Paste the following into the project-description field:

> SecAwardLens is a non-commercial, open-source research data and visualization project that tracks Best, Outstanding, and Distinguished Paper awards from IEEE S&P, USENIX Security, ACM CCS, and NDSS. We use official conference pages as award ground truth and use Semantic Scholar only to resolve scholarly entities and report provider-specific citation observations. We plan to use `/graph/v1/paper/search/match` during human-reviewed entity resolution, `/graph/v1/paper/{paper_id}` and preferably `/graph/v1/paper/batch` for scheduled metadata and citation-count refreshes, and potentially `/graph/v1/paper/{paper_id}/citations` to aggregate citing-paper publication years when needed. Requested fields are `paperId`, `corpusId`, `title`, `authors`, `year`, `publicationDate`, `venue`, `externalIds`, `url`, `citationCount`, and `influentialCitationCount`; citation-graph requests would request only citing-paper IDs and years. The current collection has 47 papers and will expand gradually by conference year. Requests run only in a maintainer-controlled pipeline, never from end-user browsers. Verified IDs are pinned and cached, batch requests are preferred, refreshes are scheduled rather than user-triggered, traffic is limited to one request per second, and 429/5xx responses use exponential backoff. We expect fewer than 100 requests on a normal refresh day, with explicitly capped backfill jobs. The public site will attribute Semantic Scholar and link back with `utm_source=api`. For reproducibility, we would like to retain minimal timestamped paper IDs and citation observations in a public GitHub repository; please advise if that storage requires additional written authorization or a different license arrangement.

List these planned endpoints:

```text
GET /graph/v1/paper/search/match
GET /graph/v1/paper/{paper_id}
POST /graph/v1/paper/batch
GET /graph/v1/paper/{paper_id}/citations (optional, paginated)
```

Enter **100 requests/day** for initial routine use. If the form requests peak traffic,
state that explicitly capped historical backfills may reach 500 requests/day while
still observing one request per second.

The project has successfully made unauthenticated diagnostics, enforces a one-second
minimum interval, and retries transport failures, HTTP 429, and 5xx responses with
exponential backoff. The applicant may therefore truthfully acknowledge those items,
the two-rate-plan notice, and inactive-key policy. The applicant must personally read
and accept the current API agreement. Retain a dated copy of the application and any
AI2 response before enabling `semantic_scholar.public_output_enabled`.

Official references:

- <https://www.semanticscholar.org/product/api/license>
- <https://api.semanticscholar.org/license/>
- <https://www.semanticscholar.org/product/api>
