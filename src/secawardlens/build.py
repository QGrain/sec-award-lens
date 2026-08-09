from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from .io import (
    load_awards,
    load_bindings,
    load_conferences,
    load_coverage,
    load_editions,
    load_enrichments,
    load_observations,
    load_papers,
    load_source_registry,
    stable_json,
)
from .metrics import citation_window, distribution_summary
from .models import CitationObservation
from .validation import validate_repository

SUPPORTED_CITATION_SOURCES = ("google_scholar", "openalex", "semantic_scholar")


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(stable_json(payload), encoding="utf-8")


def _observation_payload(observation: CitationObservation) -> dict[str, Any]:
    payload = observation.model_dump(mode="json")
    if observation.retrieval_service is None:
        payload.pop("retrieval_service")
    return payload


def _latest_by_source(
    observations: list[CitationObservation],
) -> dict[tuple[str, str], CitationObservation]:
    latest: dict[tuple[str, str], CitationObservation] = {}
    for item in observations:
        key = (item.paper_id, item.provider.value)
        if key not in latest or item.retrieved_at > latest[key].retrieved_at:
            latest[key] = item
    return latest


def _latest_citing_years_by_source(
    observations: list[CitationObservation],
) -> dict[tuple[str, str], CitationObservation]:
    return _latest_by_source(
        [
            item
            for item in observations
            if item.citations_by_citing_year or item.total_citations == 0
        ]
    )


def build_site_data(root: Path, output: Path | None = None) -> list[Path]:
    report = validate_repository(root)
    if not report.valid:
        raise ValueError("repository validation failed:\n" + "\n".join(report.errors))

    output = output or root / "web/public/data"
    conferences = load_conferences(root)
    editions = load_editions(root)
    enrichments = load_enrichments(root)
    papers = load_papers(root)
    awards = load_awards(root)
    bindings = load_bindings(root)
    coverage = load_coverage(root)
    observations = load_observations(root)
    source_registry = load_source_registry(root)
    paper_by_id = {item.id: item for item in papers}
    conference_by_id = {item.id: item for item in conferences}
    edition_by_id = {item.id: item for item in editions}
    enrichment_by_paper = {item.paper_id: item for item in enrichments}
    latest = _latest_by_source(observations)
    latest_citing_years = _latest_citing_years_by_source(observations)
    observed_sources = {item.provider.value for item in observations}
    citation_sources = [
        item.id
        for item in source_registry.citation_sources
        if item.public_output_enabled
        and item.id in SUPPORTED_CITATION_SOURCES
        and item.id in observed_sources
    ]
    preferred_source = next(
        (item for item in SUPPORTED_CITATION_SOURCES if item in citation_sources),
        "openalex",
    )
    history: dict[tuple[str, str], list[CitationObservation]] = defaultdict(list)
    for item in observations:
        history[(item.paper_id, item.provider.value)].append(item)

    generated_at = max(
        (item.retrieved_at for item in observations),
        default=max(item.official_source.retrieved_at for item in awards),
    )
    written: list[Path] = []
    years: list[int] = []
    for year in sorted({edition.year for edition in editions}):
        years.append(year)
        year_editions = [item for item in editions if item.year == year]
        edition_ids = {item.id for item in year_editions}
        year_awards = [item for item in awards if item.edition_id in edition_ids]
        year_paper_ids = {item.paper_id for item in year_awards}
        year_generated_at = max(
            (item.retrieved_at for item in observations if item.paper_id in year_paper_ids),
            default=max(item.official_source.retrieved_at for item in year_awards),
        )
        rows: list[dict[str, Any]] = []
        for award in year_awards:
            paper = paper_by_id[award.paper_id]
            edition = edition_by_id[award.edition_id]
            enrichment = enrichment_by_paper.get(paper.id)
            citations: dict[str, dict[str, Any]] = {}
            for provider in SUPPORTED_CITATION_SOURCES:
                observation = latest.get((paper.id, provider))
                if observation is None:
                    continue
                citing_years = latest_citing_years.get((paper.id, provider))
                citations[provider] = {
                    **_observation_payload(observation),
                    "citations_first_3_years": (
                        citation_window(citing_years, paper.publication_year, 3)
                        if provider in {"openalex", "google_scholar"}
                        and citing_years is not None
                        else None
                    ),
                    "citing_years_retrieved_at": (
                        citing_years.retrieved_at.isoformat() if citing_years else None
                    ),
                }
            rows.append(
                {
                    "award": award.model_dump(mode="json"),
                    "paper": paper.model_dump(mode="json"),
                    "primary_topic": (
                        enrichment.primary_topic.model_dump(mode="json")
                        if enrichment and enrichment.primary_topic
                        else None
                    ),
                    "conference": conference_by_id[edition.conference_id].model_dump(mode="json"),
                    "citations": citations,
                }
            )
        summaries = []
        for edition in year_editions:
            conference_rows = [
                row for row in rows if row["award"]["edition_id"] == edition.id
            ]
            counts = [
                row["citations"][preferred_source]["total_citations"]
                for row in conference_rows
                if preferred_source in row["citations"]
            ]
            summaries.append(
                {
                    "edition": edition.model_dump(mode="json"),
                    "conference": conference_by_id[edition.conference_id].model_dump(mode="json"),
                    "award_count": len(conference_rows),
                    "cited_paper_count": len(counts),
                    "citation_source": preferred_source,
                    "citations": distribution_summary(counts),
                }
            )
        target = output / "years" / f"{year}.json"
        _write_json(
            target,
            {
                "schema_version": 3,
                "generated_at": year_generated_at.isoformat(),
                "year": year,
                "rows": sorted(
                    rows,
                    key=lambda row: (
                        -row["citations"].get(preferred_source, {}).get(
                            "total_citations", -1
                        ),
                        row["paper"]["canonical_title"],
                    ),
                ),
                "conference_summaries": summaries,
            },
        )
        written.append(target)

    for paper in papers:
        paper_bindings = [item for item in bindings if item.paper_id == paper.id]
        paper_awards = [item for item in awards if item.paper_id == paper.id]
        paper_generated_at = max(
            (item.retrieved_at for item in observations if item.paper_id == paper.id),
            default=max(item.official_source.retrieved_at for item in paper_awards),
        )
        target = output / "papers" / f"{paper.id}.json"
        _write_json(
            target,
            {
                "schema_version": 1,
                "generated_at": paper_generated_at.isoformat(),
                "paper": paper.model_dump(mode="json"),
                "enrichment": (
                    enrichment_by_paper[paper.id].model_dump(mode="json")
                    if paper.id in enrichment_by_paper
                    else None
                ),
                "awards": [
                    item.model_dump(mode="json") for item in paper_awards
                ],
                "bindings": [item.model_dump(mode="json") for item in paper_bindings],
                "citation_history": {
                    provider: [
                        _observation_payload(item)
                        for item in sorted(points, key=lambda point: point.retrieved_at)
                    ]
                    for (paper_id, provider), points in history.items()
                    if paper_id == paper.id
                },
            },
        )
        written.append(target)

    target = output / "index.json"
    _write_json(
        target,
        {
            "schema_version": 1,
            "generated_at": generated_at.isoformat(),
            "years": years,
            "default_year": max(years),
            "conferences": [item.model_dump(mode="json") for item in conferences],
            "coverage": [item.model_dump(mode="json") for item in coverage],
            "citation_sources": citation_sources,
            "preferred_citation_source": preferred_source,
            "methodology_url": "#/methodology",
        },
    )
    written.append(target)
    return written


def export_json_schemas(root: Path) -> list[Path]:
    from .models import (  # kept local so the build path stays lightweight
        AwardGrant,
        CitationObservation,
        Conference,
        ConferenceEdition,
        CoverageEntry,
        ManualOverride,
        Paper,
        PaperEnrichment,
        PaperResolutionSubmission,
        ProviderBinding,
        SourceRegistry,
    )

    output = root / "schemas"
    output.mkdir(parents=True, exist_ok=True)
    written = []
    for model in (
        Conference,
        ConferenceEdition,
        AwardGrant,
        Paper,
        PaperEnrichment,
        PaperResolutionSubmission,
        ProviderBinding,
        CitationObservation,
        ManualOverride,
        CoverageEntry,
        SourceRegistry,
    ):
        target = output / f"{model.__name__}.schema.json"
        target.write_text(json.dumps(model.model_json_schema(), indent=2) + "\n", encoding="utf-8")
        written.append(target)
    return written
