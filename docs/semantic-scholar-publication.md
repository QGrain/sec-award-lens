# Semantic Scholar publication decision

## Current state after key approval

AI2 approved the project's API-key application with a cumulative limit of one request
per second. The adapter sends the key only in the `x-api-key` header, waits 1.1 seconds
between requests, and applies exponential backoff. A manual GitHub Action and local CLI
can now generate review candidates for the five OpenAlex-unresolved papers.

Candidate discovery is not publication: it writes no binding, count, snapshot, or site
JSON. A maintainer must compare title, authors, year, venue, DOI, and document version,
then submit the structured review form. Routine refreshes never reuse a search result
unless its ID has been accepted and pinned.

The site includes the Semantic Scholar name/logo, an API-attribution link carrying
`utm_source=api`, and a citation to *The Semantic Scholar Open Data Platform*. No S2
response data is currently committed under `data/` or displayed in the ranking.

## Why public output remains gated

This is a licensing and publication-policy decision, not unfinished entity-resolution
code. The current agreement at <https://api.semanticscholar.org/license/> requires a
Semantic Scholar link with `utm_source=api`, name/logo on public displays, and scientific
credit. It also contains restrictions on sharing API Data. A separately published May
2023 product agreement describes website attribution and provider-specific data
licenses. Because those texts are not identical, the repository applies the stricter
boundary.

SecAwardLens dedicates its original curation to CC0. Before placing API-derived S2
observations in the same downloadable repository, the maintainer should establish that
static storage, GitHub redistribution, the CC0 boundary, and public display comply with
the applicable agreement. This is project-risk guidance, not legal advice.

The submitted key application explicitly disclosed a non-commercial public static site,
periodic paper-ID/citation retrieval, and proposed timestamped GitHub snapshots. The
generic approval email confirmed the key, rate limit, and attribution requirement, but
did not answer the downloadable-snapshot question explicitly.

## Required steps before publishing S2 observations

1. Retain the submitted application and approval email outside the public repository;
   never commit the key.
2. Reply to AI2 asking whether minimal, timestamped S2 paper IDs and citation counts may
   be committed to a public GitHub repository as downloadable static JSON, and under
   which upstream terms.
3. If confirmed, keep S2-derived records outside the CC0 dedication, retain the current
   attribution/link-back, and change `public_output_enabled` in a reviewed pull request.
4. Add independently reviewed provider bindings; do not copy OpenAlex decisions or
   combine counts from the two sources.

Suggested clarification:

> Thank you for approving the SecAwardLens API key. Our application described a
> non-commercial open-source static site and proposed retaining minimal timestamped
> Semantic Scholar paper IDs and citation counts in its public GitHub repository. May
> those minimal observations be committed as downloadable static JSON, and if so,
> which S2 Data license/notice should accompany them? We will keep them outside our
> CC0 dedication and provide the required Semantic Scholar name/logo, `utm_source=api`
> link-back, and scholarly attribution.

Official references:

- <https://api.semanticscholar.org/license/>
- <https://www.semanticscholar.org/product/api/license>
- <https://www.semanticscholar.org/product/api>
- <https://arxiv.org/abs/2301.10140>
