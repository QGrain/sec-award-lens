from __future__ import annotations

import difflib
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, cast

import yaml

from .build import build_site_data
from .io import (
    load_awards,
    load_editions,
    load_source_registry,
    read_yaml,
)
from .matching import evidence_for
from .models import (
    Author,
    BindingStatus,
    Identifier,
    ManualOverride,
    MatchMethod,
    Paper,
    PaperResolutionSubmission,
    ProviderBinding,
    ReviewProviderDecision,
)
from .normalization import normalize_doi
from .providers.base import ProviderPaper
from .validation import validate_repository

_TARGETS = {
    "papers": Path("data/curated/papers.yml"),
    "bindings": Path("data/curated/bindings.yml"),
    "overrides": Path("data/curated/manual_overrides.yml"),
}
_VERIFIED = {BindingStatus.AUTO_VERIFIED, BindingStatus.MANUALLY_VERIFIED}


def load_submission(path: Path) -> PaperResolutionSubmission:
    return PaperResolutionSubmission.model_validate(read_yaml(path))


def _document(root: Path, name: str) -> dict[str, Any]:
    payload = read_yaml(root / _TARGETS[name])
    if not isinstance(payload, dict):
        raise ValueError(f"invalid YAML document: {_TARGETS[name]}")
    return cast(dict[str, Any], payload)


def _records(document: dict[str, Any], key: str) -> list[dict[str, Any]]:
    value = document.get(key)
    if not isinstance(value, list):
        raise ValueError(f"expected a {key!r} list")
    return cast(list[dict[str, Any]], value)


def _upsert(records: list[dict[str, Any]], item: dict[str, Any], *keys: str) -> None:
    identity = tuple(item[key] for key in keys)
    for index, current in enumerate(records):
        if tuple(current.get(key) for key in keys) == identity:
            records[index] = item
            return
    records.append(item)


def _candidate(decision: ReviewProviderDecision) -> ProviderPaper | None:
    if not all(
        (
            decision.external_id,
            decision.candidate_title,
            decision.candidate_authors,
            decision.candidate_publication_year,
        )
    ):
        return None
    return ProviderPaper(
        external_id=decision.external_id or "",
        title=decision.candidate_title or "",
        authors=decision.candidate_authors,
        publication_year=decision.candidate_publication_year,
        venue=decision.candidate_venue,
        doi=normalize_doi(decision.candidate_doi) if decision.candidate_doi else None,
    )


def _binding(
    submission: PaperResolutionSubmission,
    decision: ReviewProviderDecision,
    paper: Paper,
    conference_id: str,
) -> ProviderBinding:
    candidate = _candidate(decision)
    evidence = evidence_for(paper, candidate, conference_id) if candidate else None
    if decision.decision == "verified":
        return ProviderBinding(
            paper_id=paper.id,
            provider=decision.provider,
            external_id=decision.external_id,
            status=BindingStatus.MANUALLY_VERIFIED,
            method=MatchMethod.MANUAL_OVERRIDE,
            confidence=decision.confidence,
            selected_candidate=evidence,
            related_version_ids=decision.related_version_ids,
            verified_by=submission.reviewer,
            verified_at=submission.reviewed_at,
            override_reason=decision.reason,
            review_notes=submission.notes,
        )
    status = {
        "ambiguous": BindingStatus.CANDIDATE,
        "rejected": BindingStatus.REJECTED,
        "not_found": BindingStatus.PENDING,
    }[decision.decision]
    return ProviderBinding(
        paper_id=paper.id,
        provider=decision.provider,
        external_id=decision.external_id,
        status=status,
        method=MatchMethod.FUZZY_REVIEW if evidence else None,
        confidence=evidence.title_similarity if evidence else None,
        selected_candidate=evidence,
        related_version_ids=decision.related_version_ids,
        verified_by=submission.reviewer,
        verified_at=submission.reviewed_at,
        review_notes=f"{decision.decision}: {decision.reason}",
    )


def _dump(document: dict[str, Any]) -> str:
    return yaml.safe_dump(document, allow_unicode=True, sort_keys=False, width=10_000)


def prepare_resolution(
    root: Path, submission: PaperResolutionSubmission
) -> dict[Path, str]:
    documents = {name: _document(root, name) for name in _TARGETS}
    papers = _records(documents["papers"], "papers")
    bindings = _records(documents["bindings"], "bindings")
    overrides = _records(documents["overrides"], "overrides")
    paper_record = next(
        (item for item in papers if item.get("id") == submission.paper_id), None
    )
    if paper_record is None:
        raise ValueError(
            "paper_id is not in the official award dataset; new award rows require "
            "source/parser review before using this form"
        )

    metadata = submission.metadata
    if metadata.canonical_title is not None:
        paper_record["canonical_title"] = metadata.canonical_title
    if metadata.authors is not None:
        paper_record["authors"] = [Author(name=name).model_dump() for name in metadata.authors]
    if metadata.publication_year is not None:
        paper_record["publication_year"] = metadata.publication_year
    if metadata.official_paper_url is not None:
        paper_record["official_paper_url"] = metadata.official_paper_url
    if metadata.doi and metadata.doi_source_url:
        identifiers = cast(list[dict[str, Any]], paper_record.setdefault("identifiers", []))
        identifiers[:] = [item for item in identifiers if item.get("scheme") != "doi"]
        identifiers.append(
            Identifier(
                scheme="doi",
                value=normalize_doi(metadata.doi),
                source_url=metadata.doi_source_url,
                verified_at=submission.reviewed_at,
            ).model_dump(mode="json")
        )
    metadata_sources = cast(
        list[str], paper_record.setdefault("metadata_sources", [])
    )
    for source in submission.evidence_urls:
        if source not in metadata_sources:
            metadata_sources.append(source)

    paper = Paper.model_validate(paper_record)
    awards = load_awards(root)
    editions = {edition.id: edition for edition in load_editions(root)}
    award = next((item for item in awards if item.paper_id == paper.id), None)
    if award is None:
        raise ValueError(f"paper has no award record: {paper.id}")
    conference_id = editions[award.edition_id].conference_id
    public_sources = {
        source.id: source.public_output_enabled
        for source in load_source_registry(root).citation_sources
    }

    for decision in submission.provider_decisions:
        if decision.decision == "verified" and not public_sources.get(
            decision.provider.value, False
        ):
            raise ValueError(
                f"{decision.provider.value} public output is disabled in source_registry.yml; "
                "record written authorization and enable it before applying this binding"
            )
        current = next(
            (
                ProviderBinding.model_validate(item)
                for item in bindings
                if item.get("paper_id") == paper.id
                and item.get("provider") == decision.provider.value
            ),
            None,
        )
        if current and current.status in _VERIFIED and decision.decision != "verified":
            raise ValueError(
                f"refusing to downgrade verified binding {paper.id}/{decision.provider.value}"
            )
        binding = _binding(submission, decision, paper, conference_id)
        _upsert(
            bindings,
            binding.model_dump(mode="json", exclude_none=True),
            "paper_id",
            "provider",
        )
        overrides[:] = [
            item
            for item in overrides
            if not (
                item.get("paper_id") == paper.id
                and item.get("provider") == decision.provider.value
            )
        ]
        if decision.decision == "verified":
            override = ManualOverride(
                paper_id=paper.id,
                provider=decision.provider,
                external_id=decision.external_id or "",
                reason=decision.reason,
                verified_by=submission.reviewer,
                verified_at=submission.reviewed_at,
                evidence_urls=decision.evidence_urls,
            )
            overrides.append(override.model_dump(mode="json"))
            identifiers = cast(
                list[dict[str, Any]], paper_record.setdefault("identifiers", [])
            )
            identifiers[:] = [
                item for item in identifiers if item.get("scheme") != decision.provider.value
            ]
            identifiers.append(
                Identifier(
                    scheme=decision.provider.value,
                    value=decision.external_id or "",
                    source_url=decision.candidate_url or "",
                    verified_at=submission.reviewed_at,
                ).model_dump(mode="json")
            )

    return {
        _TARGETS[name]: _dump(document) for name, document in documents.items()
    }


def _validate_prepared(root: Path, prepared: dict[Path, str]) -> None:
    with TemporaryDirectory(prefix="secawardlens-review-") as directory:
        temporary_root = Path(directory)
        shutil.copytree(root / "data", temporary_root / "data")
        for relative, content in prepared.items():
            target = temporary_root / relative
            target.write_text(content, encoding="utf-8")
        report = validate_repository(temporary_root)
        if not report.valid:
            raise ValueError("review would invalidate the dataset:\n" + "\n".join(report.errors))


def resolution_diff(root: Path, prepared: dict[Path, str]) -> str:
    chunks: list[str] = []
    for relative, content in prepared.items():
        current = (root / relative).read_text(encoding="utf-8")
        chunks.extend(
            difflib.unified_diff(
                current.splitlines(keepends=True),
                content.splitlines(keepends=True),
                fromfile=str(relative),
                tofile=str(relative),
            )
        )
    return "".join(chunks)


def apply_resolution(
    root: Path, submission: PaperResolutionSubmission, *, write: bool
) -> str:
    prepared = prepare_resolution(root, submission)
    _validate_prepared(root, prepared)
    diff = resolution_diff(root, prepared)
    if write and diff:
        for relative, content in prepared.items():
            target = root / relative
            temporary = target.with_suffix(target.suffix + ".tmp")
            temporary.write_text(content, encoding="utf-8")
            temporary.replace(target)
        build_site_data(root)
    return diff
