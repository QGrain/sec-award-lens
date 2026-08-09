# Methodology

## Scope

SecAwardLens includes paper-level **Best Paper**, **Outstanding Paper**, and
**Distinguished Paper** awards from IEEE S&P, USENIX Security, ACM CCS, and NDSS.
Raw conference terminology is preserved while those labels are normalized into a
small comparison vocabulary. Student, practical, artifact, poster, honorable
mention, test-of-time, and sponsor-specific prizes are outside the initial scope.

The initial 2023 cohort has 47 awards. It validates the end-to-end pipeline but is not
a claim that one year describes the field.

## Separation of records

An `AwardGrant` records the organizer's decision and its provenance. A `Paper`
records cleaned bibliographic metadata. A `ProviderBinding` records a reviewed
relationship between that paper and one provider entity. A `CitationObservation`
records what one provider reported at one UTC timestamp. This separation prevents a
provider correction from rewriting award history and prevents a new count from
erasing an older observation.

Provider-supplied topics and work-specific author affiliations live in a separate
`PaperEnrichment` record with provider ID and retrieval time. They improve browsing
but do not overwrite the organizer/publisher metadata. Topic labels are OpenAlex
machine classifications and affiliations can be incomplete.

## Entity resolution

The resolver evaluates candidates in this order:

1. Exact normalized DOI plus a title similarity of at least 0.8 and publication year
   within one year.
2. Exact normalized title, at least one overlapping expected author surname,
   publication year within one year, and a recognized venue alias.
3. A review candidate ranked by normalized title similarity, author overlap, year,
   and venue evidence.

Only the first two paths may automatically verify a match. Multiple otherwise-valid
exact-title candidates remain ambiguous. Manual decisions live in a separate override
file with evidence. Known preprint or repository duplicates are retained as related
version IDs and are not silently summed.

Routine refreshes select only `auto_verified` or `manually_verified` bindings and
fetch their pinned IDs directly. Search is a separate command.

## Citation observations

Google Scholar, OpenAlex, and Semantic Scholar observations are independent series.
Google Scholar is preferred in the interface once reviewed snapshots exist, but it is
obtained through a third-party retrieval service because Google provides no official
public Scholar API. SerpApi is preferred; ScraperAPI is a validated fallback for
current totals. Every observation contains the provider,
external work ID, UTC retrieval time, total citations, citations grouped by the
publication year of citing works where available, provider record update time,
retrieval service where known, response digest, and request fingerprint. Files in
`data/snapshots/` are append-only.

“Citations by citing year” is not a historical counter: later provider corrections
can alter the allocation. True counter growth comes from comparing independent
snapshots over time.

The initial Google Scholar baseline reused each reviewed title-search response to
avoid spending a second SerpApi search during discovery. Those discovery responses
contained the current total but not `citations_per_year`, so their yearly arrays are
empty. Routine SerpApi refreshes query the pinned numeric `cites_id` and populate the
yearly series when that field is returned. ScraperAPI's HTML fallback supplies only
the current total, so a fallback observation can legitimately have no yearly series.
The static comparison data derives age-window metrics from the most recent observation
that contains a citing-year series and records that series' retrieval timestamp. A
later total-only fallback therefore updates the current count without erasing an
already observed age-window metric.

## Comparisons

Current citations are useful for browsing but strongly age-dependent. The first-three-
publication-years metric sums citing-year counts in `[publication_year,
publication_year + 3)`. It enables like-age comparison once the full window has
elapsed. Partial windows must be labeled as such when newer years are added.

Conference views report `n`, matched `n`, median, mean, quartiles, observed minimum
and maximum, and the paper-level distribution. Totals are intentionally omitted from
summary cards because award
counts differ. Small samples remain visible; for example, NDSS has only two included
2023 winners, so its summary is descriptive rather than a stable conference estimate.

## Current limitations

- Google Scholar resolves 47/47, OpenAlex 42/47, and Semantic Scholar 46/47 of
  the 2023 records. Missing observations remain visibly missing per provider.
- One snapshot establishes a baseline; a genuine growth curve needs later snapshots.
- Provider citation coverage and entity merging can change retrospectively.
- Scholar generally covers more document types and often clusters repository,
  preprint, and conference versions differently; a larger count is broader, not an
  independently verified ground truth.
- SerpApi is a paid-quota, third-party parser whose response contract can change when
  Google Scholar changes its result pages. SerpApi is the preferred retrieval service;
  ScraperAPI is a current-total-only fallback and is recorded separately in provenance.
- The first Google Scholar baseline has no citing-year histogram because it was
  derived from discovery responses; this is a missing field, not a zero-valued series.
- A calendar-year window is coarser than an exact publication-date window.
- Cross-provider counts are not interchangeable and should not be combined.
