# Data layout

`curated/` is reviewed source data. Conference and edition records are shared;
award files are partitioned by conference and year; paper entities and provider
bindings are global so later years can reference the same work without duplication.

`provenance/coverage_matrix.yml` distinguishes verified coverage, partial coverage,
confirmed absence, and unresolved years. `source_registry.yml` records parser
contracts and whether provider output may be published.

`snapshots/YYYY-MM-DD-provider.jsonl` contains one `CitationObservation` per verified
paper binding. Snapshot files are append-only. Correct a fact through a new snapshot
or an explicit data-correction pull request; do not rewrite an older count merely
because a provider now reports a different value.

All files validate against the Pydantic models in `src/secawardlens/models.py`.
Generated JSON Schemas are published in `schemas/`.

Maintainers normally apply human-reviewed corrections through one structured form in
`review/submissions/`. `secawardlens review apply FORM --write` compiles that form into
the canonical paper, binding, and override files and regenerates site JSON. Community
reports enter through the GitHub Issue form and are never imported without maintainer
review.
