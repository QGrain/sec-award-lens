# Human curation workflow

SecAwardLens deliberately does not turn an ambiguous search result into a paper
binding. A missing count can mean either “the official award paper is known but this
provider has no usable entity” or “the official award record itself is incomplete.”
The review path below keeps those cases separate.

## 1. Start from a review target

Use the unresolved-entity list in `docs/sources.md` for the current queue. For an
OpenAlex target, generate fresh candidates without modifying data:

```bash
export OPENALEX_API_KEY='...'
uv run secawardlens match openalex --paper-id PAPER_ID

export S2_API_KEY='...'
uv run secawardlens match semantic-scholar --paper-id PAPER_ID

export SERPAPI_KEY='...'
uv run secawardlens match google-scholar --paper-id PAPER_ID
```

Record the paper ID. Do not invent a second ID for a conference version, preprint, or
repository copy until their relationship has been reviewed.

## 2. Search in evidence order

Collect these fields, leaving unknown values as `null` rather than guessing:

1. Official conference award page: raw award label, title, author line, and URL.
2. Official proceedings or paper page: canonical title, complete authors, affiliations,
   publication year, and paper URL.
3. Publisher/Crossref: DOI and version-of-record landing page.
4. OpenAlex: work ID, title, authors, year, venue, DOI, and any related work IDs.
5. Semantic Scholar: paper ID/Corpus ID and the same comparison fields. Generate
   candidate JSON locally with the CLI command above. It is identity-review evidence;
   only accepted, pinned IDs enter routine refreshes.
6. Google Scholar: run the local SerpApi-backed candidate command. Verify the exact
   title, authors, year, venue, and clustered versions. Accept only the numeric
   `cites_id`; an opaque `result_id` is not a refreshable binding. Do not enter a
   Scholar count as an OpenAlex or Semantic Scholar count.

For each candidate, compare DOI first, then normalized title, authors, publication
year, venue, and document version. A conference paper and a preprint can be related
without being interchangeable. If more than one entity remains plausible, submit the
case as ambiguous.

## 3. Submit one review packet

Non-code contributors should open the **Paper resolution** issue form. It is a
structured evidence intake, not a trusted data import. A maintainer reviews the issue,
then copies `data/review/paper-resolution.template.yml` to
`data/review/submissions/<paper-id>-<date>.yml` and fills in the accepted facts.

Create the submissions directory when accepting the first review packet:

```bash
mkdir -p data/review/submissions
cp data/review/paper-resolution.template.yml \
  data/review/submissions/<paper-id>-<date>.yml
```

Validate and preview the generated changes:

```bash
uv run secawardlens review validate data/review/submissions/FORM.yml
uv run secawardlens review apply data/review/submissions/FORM.yml
```

The second command is dry-run by default and prints a unified diff. After reviewing
it, apply the changes atomically and rebuild frontend JSON:

```bash
uv run secawardlens review apply data/review/submissions/FORM.yml --write
```

The script updates canonical paper metadata, provider bindings, manual overrides, and
generated site data. The accepted form remains in the PR as provenance. It currently
handles papers already present in the official award dataset. A genuinely omitted
award paper still requires award-source/parser review because that changes the
conference ground truth and expected record count.

A maintainer records an accepted decision in these authoritative files:

| Finding | File to change |
| --- | --- |
| Official award correction | `data/curated/awards/CONFERENCE/YEAR.yml` |
| Canonical title, authors, year, paper URL, DOI | `data/curated/papers.yml` |
| Accepted/rejected/pending provider entity | `data/curated/bindings.yml` |
| Human-selected non-automatic entity | `data/curated/manual_overrides.yml` |
| OpenAlex topic and author affiliations | `data/curated/paper_enrichments.yml` |
| Source completeness status | `data/provenance/coverage_matrix.yml` |

Never edit `web/public/data` by hand; it is generated. Direct edits to the three
compiled YAML files are still supported for exceptional migrations, but the review
form is the normal maintainer path.

## 4. Required decision rules

- DOI exact match still requires a sane title and year.
- A title-only match is insufficient when authors or versions disagree.
- Manual overrides must name the reviewer, UTC review time, reason, and evidence URLs.
- A provider `not_found` result stays `pending` with dated review notes; it is not a
  zero-citation paper.
- Confirmed external IDs remain pinned. Citation refresh reads the pinned ID and never
  searches again.
- A Google Scholar binding must be a numeric `cites_id` reviewed against the expected
  conference paper. Search result order and a matching snippet are not sufficient.
- OpenAlex topics are provider-assigned machine classifications, not editorial labels.
  Keep them in `paper_enrichments.yml`, separate from canonical paper metadata.
- Review forms never accept a human-entered citation count. A verified provider ID is
  refreshed through that provider; if no provider entity exists, the site displays
  unavailable rather than inventing a count or yearly history.

## 5. Validate and publish

Run the same checks used by CI:

```bash
uv run secawardlens data validate
uv run secawardlens schema export
uv run secawardlens build
uv run pytest
cd web
npm ci
npm test
npm run build
```

After the PR is reviewed and merged, the Pages workflow rebuilds the static JSON and
frontend automatically. If a newly accepted provider ID has no citation snapshot yet,
run the citation-refresh workflow; its PR adds the first immutable observation, and a
subsequent merge makes the count visible. A provider decision can be applied only while
that provider's `public_output_enabled` gate is true.
