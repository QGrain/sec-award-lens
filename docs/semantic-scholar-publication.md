# Semantic Scholar publication decision

## Enabled scope

AI2 approved the project's Public (Free/Nonprofit) API-key application with a
cumulative limit of one request per second. The application described SecAwardLens as
a non-commercial open-source static site, identified the paper and citation fields it
would retrieve, and disclosed periodic timestamped snapshots. The approval email also
requested Semantic Scholar attribution on the site or citation of *The Semantic
Scholar Open Data Platform* in published materials.

On that basis, SecAwardLens publishes only the minimum S2-derived records needed for
the comparison view:

- independently reviewed Semantic Scholar paper IDs;
- total and influential citation counts;
- UTC retrieval timestamps, request fingerprints, and response digests.

Raw API responses, citing-paper graphs, abstracts, and bulk S2 datasets are not
committed. Routine refreshes use pinned IDs and never silently rematch a title.

## License and attribution boundary

The current product API agreement permits third-party products to access and display
S2 data subject to the agreement and the licenses accompanying the data. A separate
official API/Data agreement contains additional public-use, link-back, logo, and
sharing language. This repository therefore takes a narrow approach:

- S2-derived records are expressly outside the project's CC0 dedication;
- the site displays the Semantic Scholar name and mark;
- public links use `utm_source=api`;
- the acknowledgements and methodology cite *The Semantic Scholar Open Data
  Platform*;
- provider counts remain separate and are never added to OpenAlex or Google Scholar.

This is a project-maintenance decision, not legal advice. Retain the submitted
application and approval email outside the repository, and never commit the API key.
Before expanding to raw responses, bulk citation graphs, or a materially different
commercial use, review the then-current terms and ask AI2 for written confirmation if
the scope is uncertain.

## Operational controls

The adapter sends the key only in the `x-api-key` header, waits 1.1 seconds between
requests, and applies exponential backoff. Candidate discovery does not write data.
A maintainer compares DOI, title, authors, year, venue, and document version before an
ID is pinned. Missing entities remain visibly unavailable rather than receiving the
count of a similar paper.

Official references:

- <https://www.semanticscholar.org/product/api/license>
- <https://api.semanticscholar.org/license/>
- <https://www.semanticscholar.org/product/api>
- <https://arxiv.org/abs/2301.10140>
