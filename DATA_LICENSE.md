# Data license and attribution

To the extent the project maintainers hold copyright or database rights in their
original selection, normalization, and curation under `data/`, those rights are waived under the
[Creative Commons CC0 1.0 Universal dedication](https://creativecommons.org/publicdomain/zero/1.0/).

This dedication does not grant rights in third-party material. Conference names,
paper titles, author names, source-page content, DOI metadata, and citation-provider
records may be governed by their respective owners and terms. Provenance URLs and
provider identifiers are retained so downstream users can verify and attribute those
sources. Google Scholar/SerpApi, OpenAlex, and Semantic Scholar records should be
reused according to their current provider terms.

CC0 is a project choice, not a technical requirement. It does not and cannot relicense
third-party response data. Provider-derived records retain their applicable upstream
terms even when they appear next to project-authored CC0 fields in one generated JSON
document.

Current provider scope:

- Google Scholar observations retrieved through SerpApi, including counts, cluster
  identifiers, and year aggregations, are third-party records expressly excluded from
  this project's CC0 dedication. Their display does not relicense Google or SerpApi
  data, names, or services. The site labels the transport as “Google Scholar via
  SerpApi”; downstream reuse must be assessed under the applicable upstream terms.
- OpenAlex states that its dataset is CC0; OpenAlex-derived IDs, citation observations,
  topics, and affiliations may therefore be redistributed under that upstream grant.
- Reviewed Semantic Scholar paper IDs and minimal timestamped citation observations
  are displayed as a separate provider series. They are expressly excluded from this
  project's CC0 dedication and remain subject to the applicable S2 and third-party
  data terms. Raw API responses are not committed. Public displays include Semantic
  Scholar attribution, an `utm_source=api` link-back, and the requested scholarly
  citation.

The Semantic Scholar name and mark in the web footer are trademarks used solely to
provide the attribution required by the S2 API agreement; they are not covered by the
project's Apache-2.0 or CC0 grants.

The enabled scope is intentionally minimal and matches the approved Public
(Free/Nonprofit) application for this static research site. Expanding the repository
to raw S2 responses, bulk citation graphs, or other S2 datasets requires a fresh terms
review and, where uncertain, written confirmation from AI2.
