from __future__ import annotations

from collections.abc import Iterable

from .models import (
    BindingStatus,
    CandidateEvidence,
    CitationProvider,
    MatchMethod,
    Paper,
    ProviderBinding,
)
from .normalization import author_overlap, normalize_doi, normalize_title, title_similarity
from .providers.base import ProviderPaper

VENUE_ALIASES = {
    "ieee-sp": {"ieee symposium on security and privacy", "ieee s&p", "sp"},
    "usenix-security": {"usenix security symposium", "usenix security"},
    "acm-ccs": {"acm conference on computer and communications security", "ccs"},
    "ndss": {"network and distributed system security symposium", "ndss"},
}


def _venue_matches(venue: str | None, conference_id: str) -> bool:
    if not venue:
        return False
    normalized = normalize_title(venue)
    return any(alias in normalized or normalized in alias for alias in VENUE_ALIASES[conference_id])


def evidence_for(paper: Paper, candidate: ProviderPaper, conference_id: str) -> CandidateEvidence:
    year_delta = (
        abs(paper.publication_year - candidate.publication_year)
        if candidate.publication_year is not None
        else None
    )
    return CandidateEvidence(
        external_id=candidate.external_id,
        title=candidate.title,
        doi=candidate.doi,
        publication_year=candidate.publication_year,
        venue=candidate.venue,
        title_similarity=title_similarity(paper.canonical_title, candidate.title),
        author_overlap=author_overlap(
            [author.name for author in paper.authors], candidate.authors
        ),
        year_delta=year_delta,
        venue_match=_venue_matches(candidate.venue, conference_id),
    )


def _paper_doi(paper: Paper) -> str | None:
    return next(
        (
            normalize_doi(identifier.value)
            for identifier in paper.identifiers
            if identifier.scheme == "doi"
        ),
        None,
    )


def resolve_candidates(
    *,
    paper: Paper,
    conference_id: str,
    provider: CitationProvider,
    candidates: Iterable[ProviderPaper],
) -> ProviderBinding:
    scored = sorted(
        (evidence_for(paper, candidate, conference_id) for candidate in candidates),
        key=lambda item: (item.title_similarity, item.author_overlap, item.venue_match),
        reverse=True,
    )
    expected_doi = _paper_doi(paper)
    if expected_doi:
        doi_matches = [candidate for candidate in scored if candidate.doi == expected_doi]
        if len(doi_matches) == 1:
            selected = doi_matches[0]
            sane = selected.title_similarity >= 0.8 and (selected.year_delta or 0) <= 1
            if sane:
                return ProviderBinding(
                    paper_id=paper.id,
                    provider=provider,
                    external_id=selected.external_id,
                    status=BindingStatus.AUTO_VERIFIED,
                    method=MatchMethod.DOI_EXACT,
                    confidence=1.0,
                    selected_candidate=selected,
                    rejected_candidates=[item for item in scored if item != selected],
                )

    exact = [
        candidate
        for candidate in scored
        if normalize_title(candidate.title) == normalize_title(paper.canonical_title)
        and candidate.year_delta is not None
        and candidate.year_delta <= 1
        and candidate.author_overlap > 0
        and candidate.venue_match
    ]
    if len(exact) == 1:
        selected = exact[0]
        confidence = min(0.99, 0.75 + 0.2 * selected.author_overlap + 0.04)
        return ProviderBinding(
            paper_id=paper.id,
            provider=provider,
            external_id=selected.external_id,
            status=BindingStatus.AUTO_VERIFIED,
            method=MatchMethod.TITLE_EXACT,
            confidence=confidence,
            selected_candidate=selected,
            rejected_candidates=[item for item in scored if item != selected],
        )

    return ProviderBinding(
        paper_id=paper.id,
        provider=provider,
        external_id=scored[0].external_id if scored else None,
        status=BindingStatus.CANDIDATE if scored else BindingStatus.PENDING,
        method=MatchMethod.FUZZY_REVIEW if scored else None,
        confidence=scored[0].title_similarity if scored else None,
        selected_candidate=scored[0] if scored else None,
        rejected_candidates=scored[1:],
    )
