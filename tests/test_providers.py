import httpx
import pytest

from secawardlens.models import CitationRetrievalService
from secawardlens.providers.google_scholar import (
    GoogleScholarClient,
    GoogleScholarTransportError,
    ScraperApiGoogleScholarClient,
    order_refresh_services,
)
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


def test_google_scholar_search_returns_only_stable_cluster_candidates() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/search.json"
        assert request.url.params["engine"] == "google_scholar"
        assert request.url.params["api_key"] == "test-key"
        assert request.url.params["q"] == '"Verified Paper"'
        return httpx.Response(
            200,
            json={
                "search_metadata": {"status": "Success"},
                "organic_results": [
                    {
                        "title": "Verified Paper",
                        "result_id": "opaque-result-id",
                        "publication_info": {
                            "summary": "A Lovelace - ACM CCS, 2023 - dl.acm.org",
                            "authors": [{"name": "Ada Lovelace"}],
                        },
                        "inline_links": {
                            "cited_by": {"total": 362, "cites_id": "123456789"}
                        },
                    },
                    {
                        "title": "Unpinned Result",
                        "result_id": "not-a-cites-id",
                        "publication_info": {"summary": "A Author - 2023"},
                    },
                ],
            },
        )

    http = httpx.Client(
        base_url="https://serpapi.com", transport=httpx.MockTransport(handler)
    )
    with GoogleScholarClient(api_key="test-key", client=http) as client:
        results = client.search_title("Verified Paper")
    assert [item.external_id for item in results] == ["123456789"]
    assert results[0].citation_count == 362
    assert results[0].publication_year == 2023


def test_google_scholar_observation_uses_pinned_cites_id_and_year_counts() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["cites"] == "123456789"
        return httpx.Response(
            200,
            json={
                "search_metadata": {"status": "Success"},
                "search_information": {"total_results": 362},
                "citations_per_year": [
                    {"year": 2023, "citations": 12},
                    {"year": 2024, "citations": 100},
                    {"year": 2025, "citations": 170},
                    {"year": 2026, "citations": 80},
                ],
                "organic_results": [],
            },
        )

    http = httpx.Client(
        base_url="https://serpapi.com", transport=httpx.MockTransport(handler)
    )
    with GoogleScholarClient(api_key="test-key", client=http) as client:
        result = client.observation(
            paper_id="paper",
            external_id="123456789",
            retrieved_at="2026-08-08T12:00:00Z",
        )
    assert result.provider == "google_scholar"
    assert result.total_citations == 362
    assert sum(item.count for item in result.citations_by_citing_year) == 362
    assert result.retrieval_service == "serpapi"
    assert "api_key" not in result.request_fingerprint


def test_google_scholar_http_error_does_not_expose_api_key() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "invalid key"})

    http = httpx.Client(
        base_url="https://serpapi.com", transport=httpx.MockTransport(handler)
    )
    with GoogleScholarClient(api_key="private-test-key", client=http) as client:
        try:
            client.search_title("Verified Paper")
        except RuntimeError as error:
            assert str(error) == "SerpApi Google Scholar request failed with HTTP 401"
            assert "private-test-key" not in str(error)
        else:
            raise AssertionError("expected a sanitized provider error")


def test_google_scholar_discovery_observation_reuses_search_count() -> None:
    payload = {
        "search_metadata": {
            "status": "Success",
            "processed_at": "2026-08-08 12:30:00 UTC",
        },
        "organic_results": [
            {
                "title": "Verified Paper",
                "publication_info": {
                    "summary": "A Lovelace - ACM CCS, 2023 - dl.acm.org",
                    "authors": [{"name": "Ada Lovelace"}],
                },
                "inline_links": {
                    "cited_by": {"total": 362, "cites_id": "123456789"}
                },
            }
        ],
    }
    http = httpx.Client(
        base_url="https://serpapi.com",
        transport=httpx.MockTransport(lambda _: httpx.Response(200, json=payload)),
    )
    with GoogleScholarClient(api_key="test-key", client=http) as client:
        candidates, response = client.search_title_with_payload("Verified Paper")
        result = client.discovery_observation(
            paper_id="paper",
            candidate=candidates[0],
            search_payload=response,
            query_title="Verified Paper",
        )
    assert result.total_citations == 362
    assert result.external_id == "123456789"
    assert result.retrieved_at.isoformat() == "2026-08-08T12:30:00+00:00"
    assert result.citations_by_citing_year == []
    assert "api_key" not in result.request_fingerprint


def test_scraperapi_observation_parses_scholar_html_and_records_transport() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/"
        assert request.url.params["api_key"] == "test-key"
        assert request.url.params["country_code"] == "us"
        assert request.url.params["max_cost"] == "25"
        assert "cites=123456789" in request.url.params["url"]
        return httpx.Response(
            200,
            text='<html><div id="gs_ab_md">About 362 results (0.04 sec)</div></html>',
        )

    http = httpx.Client(
        base_url="https://api.scraperapi.com", transport=httpx.MockTransport(handler)
    )
    with ScraperApiGoogleScholarClient(api_key="test-key", client=http) as client:
        result = client.observation(
            paper_id="paper",
            external_id="123456789",
            retrieved_at="2026-08-08T12:00:00Z",
        )
    assert result.total_citations == 362
    assert result.citations_by_citing_year == []
    assert result.retrieval_service == "scraperapi"
    assert "api_key" not in result.request_fingerprint


def test_scraperapi_capacity_uses_live_balance_and_url_cost() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/account":
            return httpx.Response(200, json={"creditsLeft": 3800})
        if request.url.path == "/account/urlcost":
            return httpx.Response(200, json={"credits": 25})
        raise AssertionError(f"unexpected path: {request.url.path}")

    http = httpx.Client(
        base_url="https://api.scraperapi.com", transport=httpx.MockTransport(handler)
    )
    with ScraperApiGoogleScholarClient(api_key="test-key", client=http) as client:
        assert client.remaining_observations() == 152


def test_scraperapi_rejects_captcha_even_when_http_status_is_200() -> None:
    html = '<html><form id="captcha-form"><div class="g-recaptcha"></div></form></html>'
    http = httpx.Client(
        base_url="https://api.scraperapi.com",
        transport=httpx.MockTransport(lambda _: httpx.Response(200, text=html)),
    )
    with (
        ScraperApiGoogleScholarClient(api_key="private-test-key", client=http) as client,
        pytest.raises(GoogleScholarTransportError, match="CAPTCHA") as caught,
    ):
        client.observation(paper_id="paper", external_id="123456789")
    assert "private-test-key" not in str(caught.value)


def test_refresh_service_order_prefers_a_transport_that_covers_the_batch() -> None:
    capacities = {
        CitationRetrievalService.SERPAPI: 20,
        CitationRetrievalService.SCRAPERAPI: 152,
    }
    assert order_refresh_services(capacities, 47)[0] == "scraperapi"
    capacities[CitationRetrievalService.SERPAPI] = 203
    assert order_refresh_services(capacities, 47)[0] == "serpapi"


def test_refresh_service_order_rejects_insufficient_combined_quota() -> None:
    with pytest.raises(GoogleScholarTransportError, match="cannot cover 47"):
        order_refresh_services(
            {
                CitationRetrievalService.SERPAPI: 20,
                CitationRetrievalService.SCRAPERAPI: 20,
            },
            47,
        )
