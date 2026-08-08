from secawardlens.matching import resolve_candidates
from secawardlens.models import Author, BindingStatus, CitationProvider, Identifier, Paper
from secawardlens.providers.base import ProviderPaper

VERIFIED_AT = "2026-08-07T12:00:00Z"


def paper(*, doi: str | None = None) -> Paper:
    identifiers = []
    if doi:
        identifiers.append(
            Identifier(
                scheme="doi",
                value=doi,
                source_url=f"https://doi.org/{doi}",
                verified_at=VERIFIED_AT,
            )
        )
    return Paper(
        id="ieee-sp-2023-example",
        canonical_title="A Precise Security Result",
        authors=[Author(name="Ada Lovelace"), Author(name="Grace Hopper")],
        publication_year=2023,
        venue_name="IEEE Symposium on Security and Privacy",
        identifiers=identifiers,
    )


def test_exact_doi_wins_over_a_similar_preprint() -> None:
    candidates = [
        ProviderPaper(
            external_id="W1",
            title="A Precise Security Result",
            authors=["Ada Lovelace", "Grace Hopper"],
            publication_year=2023,
            venue=None,
            doi="10.1109/example",
        ),
        ProviderPaper(
            external_id="W2",
            title="A Precise Security Result",
            authors=["Ada Lovelace", "Grace Hopper"],
            publication_year=2023,
            venue="arXiv",
            doi="10.48550/arxiv.example",
        ),
    ]
    result = resolve_candidates(
        paper=paper(doi="10.1109/example"),
        conference_id="ieee-sp",
        provider=CitationProvider.OPENALEX,
        candidates=candidates,
    )
    assert result.status == BindingStatus.AUTO_VERIFIED
    assert result.external_id == "W1"


def test_ambiguous_exact_titles_require_review() -> None:
    candidates = [
        ProviderPaper(
            external_id=value,
            title="A Precise Security Result",
            authors=["Ada Lovelace", "Grace Hopper"],
            publication_year=2023,
            venue="IEEE Symposium on Security and Privacy",
        )
        for value in ("W1", "W2")
    ]
    result = resolve_candidates(
        paper=paper(),
        conference_id="ieee-sp",
        provider=CitationProvider.OPENALEX,
        candidates=candidates,
    )
    assert result.status == BindingStatus.CANDIDATE
    assert result.method == "fuzzy_review"


def test_no_candidates_stays_pending() -> None:
    result = resolve_candidates(
        paper=paper(),
        conference_id="ieee-sp",
        provider=CitationProvider.OPENALEX,
        candidates=[],
    )
    assert result.status == BindingStatus.PENDING
    assert result.external_id is None
