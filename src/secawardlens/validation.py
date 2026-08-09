from __future__ import annotations

import math
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from .io import (
    load_awards,
    load_bindings,
    load_conferences,
    load_coverage,
    load_editions,
    load_enrichments,
    load_observations,
    load_overrides,
    load_papers,
    load_source_registry,
)
from .models import AwardGrant, BindingStatus, CitationProvider, MatchMethod
from .normalization import normalize_doi, normalize_title


@dataclass
class ValidationReport:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def valid(self) -> bool:
        return not self.errors

    def require(self, condition: bool, message: str) -> None:
        if not condition:
            self.errors.append(message)


def _duplicates(values: list[str]) -> set[str]:
    return {value for value, count in Counter(values).items() if count > 1}


def validate_repository(root: Path) -> ValidationReport:
    report = ValidationReport()
    conferences = load_conferences(root)
    editions = load_editions(root)
    papers = load_papers(root)
    enrichments = load_enrichments(root)
    awards = load_awards(root)
    bindings = load_bindings(root)
    overrides = load_overrides(root)
    coverage = load_coverage(root)
    observations = load_observations(root)
    registry = load_source_registry(root)
    public_sources = {
        item.id: item.public_output_enabled for item in registry.citation_sources
    }

    for label, values in (
        ("conference", [item.id for item in conferences]),
        ("edition", [item.id for item in editions]),
        ("paper", [item.id for item in papers]),
        ("award", [item.id for item in awards]),
    ):
        for duplicate in sorted(_duplicates(values)):
            report.errors.append(f"duplicate {label} id: {duplicate}")

    conference_ids = {item.id for item in conferences}
    edition_ids = {item.id for item in editions}
    paper_ids = {item.id for item in papers}
    paper_by_id = {item.id: item for item in papers}
    edition_by_id = {item.id: item for item in editions}
    for edition in editions:
        report.require(
            edition.conference_id in conference_ids,
            f"edition {edition.id} references missing conference {edition.conference_id}",
        )
    for award in awards:
        report.require(
            award.edition_id in edition_ids,
            f"award {award.id} references missing edition {award.edition_id}",
        )
        report.require(
            award.paper_id in paper_ids,
            f"award {award.id} references missing paper {award.paper_id}",
        )
        if award.edition_id in edition_by_id and award.paper_id in paper_ids:
            paper = paper_by_id[award.paper_id]
            report.require(
                abs(paper.publication_year - edition_by_id[award.edition_id].year) <= 1,
                f"award {award.id} has implausible publication year {paper.publication_year}",
            )
    award_keys = [f"{item.edition_id}:{item.paper_id}" for item in awards]
    for duplicate in sorted(_duplicates(award_keys)):
        report.errors.append(f"duplicate award-paper link: {duplicate}")

    normalized_titles = defaultdict(list)
    dois = defaultdict(list)
    for paper in papers:
        normalized_titles[normalize_title(paper.canonical_title)].append(paper.id)
        for identifier in paper.identifiers:
            if identifier.scheme == "doi":
                dois[normalize_doi(identifier.value)].append(paper.id)
    for title, ids in normalized_titles.items():
        if len(ids) > 1:
            report.errors.append(f"duplicate normalized title {title!r}: {', '.join(ids)}")
    for doi, ids in dois.items():
        if len(ids) > 1:
            report.errors.append(f"duplicate DOI {doi}: {', '.join(ids)}")

    enrichment_keys: list[str] = []
    for enrichment in enrichments:
        enrichment_keys.append(f"{enrichment.paper_id}:{enrichment.provider}")
        report.require(
            enrichment.paper_id in paper_ids,
            f"enrichment references missing paper {enrichment.paper_id}",
        )
        if enrichment.paper_id in paper_by_id:
            author_names = {author.name for author in paper_by_id[enrichment.paper_id].authors}
            for author in enrichment.authors:
                report.require(
                    author.author_name in author_names,
                    f"enrichment author {author.author_name!r} is not canonical for "
                    f"{enrichment.paper_id}",
                )
    for duplicate in sorted(_duplicates(enrichment_keys)):
        report.errors.append(f"duplicate paper enrichment: {duplicate}")

    binding_keys: list[str] = []
    for binding in bindings:
        binding_keys.append(f"{binding.paper_id}:{binding.provider}")
        report.require(
            binding.paper_id in paper_ids,
            f"binding references missing paper {binding.paper_id}",
        )
        if binding.status in {BindingStatus.AUTO_VERIFIED, BindingStatus.MANUALLY_VERIFIED}:
            report.require(
                bool(binding.external_id),
                f"verified binding lacks external id: {binding.paper_id}/{binding.provider}",
            )
            report.require(
                public_sources.get(binding.provider.value, False),
                f"verified binding uses a provider whose public output is disabled: "
                f"{binding.paper_id}/{binding.provider}",
            )
            if binding.provider == CitationProvider.GOOGLE_SCHOLAR:
                report.require(
                    bool(binding.external_id and binding.external_id.isdigit()),
                    "verified Google Scholar binding must use a numeric cites_id: "
                    f"{binding.paper_id}",
                )
    for duplicate in sorted(_duplicates(binding_keys)):
        report.errors.append(f"duplicate provider binding: {duplicate}")
    external_keys = [
        f"{item.provider}:{item.external_id}" for item in bindings if item.external_id
    ]
    for duplicate in sorted(_duplicates(external_keys)):
        report.errors.append(f"external entity is bound to multiple papers: {duplicate}")
    binding_by_key = {
        (item.paper_id, item.provider.value): item for item in bindings
    }
    for enrichment in enrichments:
        enrichment_binding = binding_by_key.get((enrichment.paper_id, enrichment.provider))
        report.require(
            bool(
                enrichment_binding
                and enrichment_binding.external_id == enrichment.external_id
            ),
            f"enrichment external ID disagrees with binding: {enrichment.paper_id}",
        )

    for binding in bindings:
        if binding.method == MatchMethod.DOI_EXACT:
            paper_dois = {
                normalize_doi(identifier.value)
                for identifier in paper_by_id[binding.paper_id].identifiers
                if identifier.scheme == "doi"
            }
            selected_doi = (
                normalize_doi(binding.selected_candidate.doi)
                if binding.selected_candidate and binding.selected_candidate.doi
                else None
            )
            report.require(
                selected_doi in paper_dois,
                f"DOI-exact binding lacks the selected DOI on paper {binding.paper_id}",
            )

    override_keys = {f"{item.paper_id}:{item.provider}": item for item in overrides}
    for override in overrides:
        report.require(
            override.paper_id in paper_ids,
            f"override references missing paper {override.paper_id}",
        )
    for binding in bindings:
        if binding.method and binding.method.value == "manual_override":
            key = f"{binding.paper_id}:{binding.provider}"
            report.require(key in override_keys, f"manual binding lacks override record: {key}")
            if key in override_keys:
                report.require(
                    binding.external_id == override_keys[key].external_id,
                    f"manual binding and override external IDs disagree: {key}",
                )

    coverage_ids = {item.edition_id for item in coverage}
    for edition_id in edition_ids:
        report.require(edition_id in coverage_ids, f"missing coverage record for {edition_id}")

    award_sources = {
        f"{item.conference_id}-{item.year}": item for item in registry.award_sources
    }
    awards_by_edition: dict[str, list[AwardGrant]] = defaultdict(list)
    for award in awards:
        awards_by_edition[award.edition_id].append(award)
    for edition_id in edition_ids:
        report.require(edition_id in award_sources, f"missing source registration for {edition_id}")
        registration = award_sources.get(edition_id)
        if registration:
            edition_awards = awards_by_edition[edition_id]
            report.require(
                len(edition_awards) == registration.expected_records,
                f"{edition_id} has {len(edition_awards)} awards; registry expects "
                f"{registration.expected_records}",
            )
            for award in edition_awards:
                report.require(
                    award.official_source.url == registration.url,
                    f"{award.id} source URL disagrees with registry",
                )
                report.require(
                    award.official_source.content_sha256 == registration.extracted_sha256,
                    f"{award.id} source digest disagrees with registry",
                )

    verified = {
        (item.paper_id, item.provider, item.external_id)
        for item in bindings
        if item.status in {BindingStatus.AUTO_VERIFIED, BindingStatus.MANUALLY_VERIFIED}
    }
    snapshot_keys: list[str] = []
    grouped_observations: dict[
        tuple[str, CitationProvider], list[tuple[object, int]]
    ] = defaultdict(list)
    for observation in observations:
        snapshot_keys.append(
            f"{observation.paper_id}:{observation.provider}:{observation.retrieved_at.isoformat()}"
        )
        report.require(
            (observation.paper_id, observation.provider, observation.external_id) in verified,
            "observation lacks a matching verified binding: "
            f"{observation.paper_id}/{observation.provider}/{observation.external_id}",
        )
        report.require(
            public_sources.get(observation.provider.value, False),
            f"observation uses a provider whose public output is disabled: "
            f"{observation.paper_id}/{observation.provider}",
        )
        grouped_observations[(observation.paper_id, observation.provider)].append(
            (observation.retrieved_at, observation.total_citations)
        )
        citing_years = [item.year for item in observation.citations_by_citing_year]
        report.require(
            not _duplicates([str(year) for year in citing_years]),
            f"duplicate citing year in observation for {observation.paper_id}",
        )
        citing_year_total = sum(
            item.count for item in observation.citations_by_citing_year
        )
        excess = citing_year_total - observation.total_citations
        if excess > 0:
            message = (
                "citing-year counts exceed total for "
                f"{observation.paper_id}/{observation.provider}: "
                f"{citing_year_total} > {observation.total_citations}"
            )
            # Provider totals and citing-work aggregations can be updated on
            # slightly different schedules. Preserve both returned values and
            # tolerate only a small, visible indexing drift.
            tolerance = max(2, math.ceil(observation.total_citations * 0.01))
            if excess <= tolerance:
                report.warnings.append(message)
            else:
                report.errors.append(message)
    for duplicate in sorted(_duplicates(snapshot_keys)):
        report.errors.append(f"duplicate citation observation: {duplicate}")
    for observation_key, points in grouped_observations.items():
        ordered = sorted(points)
        for previous, current in zip(ordered, ordered[1:], strict=False):
            if current[1] < previous[1]:
                report.warnings.append(
                    "citation count decreased for "
                    f"{observation_key[0]}/{observation_key[1]}: {previous[1]} -> {current[1]}"
                )

    award_papers = {item.paper_id for item in awards}
    for paper_id in sorted(paper_ids - award_papers):
        report.warnings.append(f"paper is not linked to an award: {paper_id}")
    return report
