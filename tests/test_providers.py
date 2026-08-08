import httpx

from secawardlens.providers.openalex import OpenAlexClient
from secawardlens.providers.semantic_scholar import SemanticScholarClient


def test_openalex_observation_preserves_year_counts_and_digest() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/works/W1"
        return httpx.Response(
            200,
            json={
                "id": "https://openalex.org/W1",
                "display_name": "Verified Paper",
                "publication_year": 2023,
                "doi": "https://doi.org/10.1000/example",
                "cited_by_count": 7,
                "counts_by_year": [
                    {"year": 2024, "cited_by_count": 2},
                    {"year": 2025, "cited_by_count": 5},
                ],
                "authorships": [{"author": {"display_name": "Ada Lovelace"}}],
                "primary_location": {"source": None},
                "locations": [],
                "updated_date": "2026-08-01T00:00:00Z",
            },
        )

    http = httpx.Client(
        base_url="https://api.openalex.org", transport=httpx.MockTransport(handler)
    )
    with OpenAlexClient(client=http) as client:
        result = client.observation(
            paper_id="paper", external_id="W1", retrieved_at="2026-08-07T12:00:00Z"
        )
    assert result.total_citations == 7
    assert [(item.year, item.count) for item in result.citations_by_citing_year] == [
        (2024, 2),
        (2025, 5),
    ]
    assert len(result.response_sha256) == 64


def test_semantic_scholar_observation_remains_provider_specific() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "paperId": "s2-id",
                "title": "Verified Paper",
                "authors": [{"name": "Ada Lovelace"}],
                "year": 2023,
                "venue": "Example Venue",
                "externalIds": {"DOI": "10.1000/example"},
                "citationCount": 9,
                "influentialCitationCount": 2,
            },
        )

    http = httpx.Client(
        base_url="https://api.semanticscholar.org/graph/v1",
        transport=httpx.MockTransport(handler),
    )
    with SemanticScholarClient(client=http) as client:
        result = client.observation(
            paper_id="paper", external_id="s2-id", retrieved_at="2026-08-07T12:00:00Z"
        )
    assert result.provider == "semantic_scholar"
    assert result.total_citations == 9
    assert result.influential_citations == 2


def test_semantic_scholar_match_unwraps_data_list() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "data": [{
                    "paperId": "s2-match",
                    "title": "Remote Direct Memory Introspection",
                    "authors": [{"name": "Hongyi Liu"}],
                    "year": 2023,
                    "venue": "USENIX Security Symposium",
                    "externalIds": {"CorpusId": 259267288},
                    "citationCount": 7,
                    "influentialCitationCount": 1,
                }],
            },
        )

    http = httpx.Client(
        base_url="https://api.semanticscholar.org/graph/v1",
        transport=httpx.MockTransport(handler),
    )
    with SemanticScholarClient(client=http) as client:
        result = client.title_candidate("Remote Direct Memory Introspection")
    assert result is not None
    assert result.external_id == "s2-match"
    assert result.citation_count == 7


def test_semantic_scholar_ranked_search_returns_review_candidates() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/graph/v1/paper/search"
        assert request.url.params["limit"] == "5"
        return httpx.Response(
            200,
            json={
                "data": [{
                    "paperId": "s2-ranked",
                    "title": "A Candidate Paper",
                    "authors": [{"name": "Ada Lovelace"}],
                    "year": 2023,
                    "venue": "USENIX Security Symposium",
                    "externalIds": {},
                    "citationCount": 3,
                    "influentialCitationCount": 0,
                }],
            },
        )

    http = httpx.Client(
        base_url="https://api.semanticscholar.org/graph/v1",
        transport=httpx.MockTransport(handler),
    )
    with SemanticScholarClient(client=http) as client:
        results = client.search_title("A Candidate Paper")
    assert [item.external_id for item in results] == ["s2-ranked"]
