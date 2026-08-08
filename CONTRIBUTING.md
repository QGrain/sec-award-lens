# Contributing

Data corrections are as welcome as code changes. Please keep every data change small,
reviewable, and backed by a source.

## Development checks

```bash
uv sync --all-extras
uv run ruff check .
uv run mypy
uv run pytest
uv run secawardlens data validate
uv run secawardlens schema export
uv run secawardlens build

cd web
npm ci
npm test
npm run build
```

Generated schemas and `web/public/data/` belong in the same commit as their source
data. Do not edit them by hand.

## Data pull requests

Include the official award URL and preserve the raw award label, title, and author
line exactly as displayed. Put cleaned metadata in the paper record, not in raw award
fields. A new external ID must include its matching evidence. Weak or conflicting
candidates should stay pending and be described in the pull request.

Manual overrides require a reason, reviewer name or handle, timestamp, and evidence
URL. Never replace a verified ID during routine citation refreshes.

For a missing or ambiguous provider entity, use the structured workflow in
[docs/manual-curation-workflow.md](docs/manual-curation-workflow.md).

## Adding a conference year

Treat every conference-year as an independently reviewed source cohort:

1. Add the edition and a `coverage_matrix.yml` entry with status `unresolved`.
2. Locate an organizer or sponsoring-organization source. Archive pages may aid
   discovery, but curated provenance must point to authoritative evidence.
3. Add a layout-specific parser and minimized parser fixture. Preserve raw title,
   author line, and award name.
4. Compare every extracted record with the official page. Record the expected count,
   retrieval time, parser version, and extracted-record digest.
5. Add normalized paper records without overwriting visibly different official text.
6. Confirm publisher DOIs through proceedings pages or Crossref where possible.
7. Generate OpenAlex candidates and accept only documented automatic thresholds or a
   reviewed manual override. Record related preprint/repository versions separately.
8. Leave uncertain papers pending; never create a citation observation without a
   verified provider binding.
9. Refresh citations, validate, regenerate schemas/site JSON, and inspect denominators,
   unmatched labels, ranking behavior, and provenance links.
10. Mark coverage `verified` only after confirming that the official award set is
    complete.

A missing page section must fail loudly. An empty parser result is not evidence that a
conference issued no awards. Current source layouts and known review risks are listed
in [docs/sources.md](docs/sources.md).
