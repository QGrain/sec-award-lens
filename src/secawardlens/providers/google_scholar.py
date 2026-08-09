from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

import httpx
from bs4 import BeautifulSoup

from ..models import (
    CitationObservation,
    CitationProvider,
    CitationRetrievalService,
    CitationYearCount,
    utc_now,
)
from .base import ProviderPaper
from .http import JsonApiClient

_YEAR = re.compile(r"\b(19|20)\d{2}\b")
_RESULT_COUNT = re.compile(r"(?:about\s+)?([\d,.\s]+)\s+results?", re.IGNORECASE)


class GoogleScholarTransportError(RuntimeError):
    """A sanitized transport or response error that is safe to print in CI."""


def _html_result_count(html: str) -> int:
    soup = BeautifulSoup(html, "html.parser")
    if soup.select_one("#gs_captcha_ccl, #captcha-form, .g-recaptcha"):
        raise GoogleScholarTransportError("ScraperAPI returned a Google Scholar CAPTCHA")
    if "unusual traffic" in html.lower():
        raise GoogleScholarTransportError("ScraperAPI returned a Google Scholar block page")
    node = soup.select_one("#gs_ab_md")
    text = node.get_text(" ", strip=True) if node else ""
    match = _RESULT_COUNT.search(text)
    digits = re.sub(r"\D", "", match.group(1)) if match else ""
    if not digits:
        raise GoogleScholarTransportError(
            "ScraperAPI Google Scholar response has no result count"
        )
    return int(digits)


def order_refresh_services(
    capacities: Mapping[CitationRetrievalService, int | None], required: int
) -> list[CitationRetrievalService]:
    """Prefer one service that covers the batch, then allow combined capacity."""
    if required <= 0:
        raise ValueError("required observations must be positive")
    preference = [
        service
        for service in (
            CitationRetrievalService.SERPAPI,
            CitationRetrievalService.SCRAPERAPI,
        )
        if service in capacities
    ]
    for service in preference:
        capacity = capacities[service]
        if capacity is None or capacity >= required:
            return [service, *(item for item in preference if item != service)]
    if sum(capacity or 0 for capacity in capacities.values()) >= required:
        return preference
    raise GoogleScholarTransportError(
        f"Google Scholar transports cannot cover {required} observations"
    )


def _require_success(payload: dict[str, Any]) -> None:
    if payload.get("error"):
        raise RuntimeError(f"SerpApi Google Scholar error: {payload['error']}")
    status = (payload.get("search_metadata") or {}).get("status")
    if status != "Success":
        raise RuntimeError(f"SerpApi Google Scholar search did not succeed: {status}")


def _candidate(payload: dict[str, Any]) -> ProviderPaper | None:
    inline = payload.get("inline_links") or {}
    cited_by = inline.get("cited_by") or {}
    versions = inline.get("versions") or {}
    cluster_id = cited_by.get("cites_id") or versions.get("cluster_id")
    if not cluster_id:
        # A Scholar result_id cannot be used as the stable `cites` parameter. Do not
        # create a binding that would force routine refreshes to search by title.
        return None
    publication = payload.get("publication_info") or {}
    summary = str(publication.get("summary") or "")
    year_match = _YEAR.search(summary)
    authors = [
        str(author["name"])
        for author in publication.get("authors") or []
        if author.get("name")
    ]
    return ProviderPaper(
        external_id=str(cluster_id),
        title=str(payload.get("title") or ""),
        authors=authors,
        publication_year=int(year_match.group()) if year_match else None,
        venue=summary or None,
        citation_count=int(cited_by.get("total") or 0),
        raw=payload,
    )


class GoogleScholarClient(JsonApiClient):
    """Google Scholar observations obtained through SerpApi, not a Google API."""

    def __init__(self, api_key: str, *, client: httpx.Client | None = None) -> None:
        if not api_key:
            raise ValueError("a SerpApi key is required")
        self.api_key = api_key
        super().__init__(
            base_url="https://serpapi.com",
            headers={"User-Agent": "SecAwardLens/0.1 (citation research)"},
            client=client,
        )

    def _params(self, **params: Any) -> dict[str, Any]:
        return {
            "engine": "google_scholar",
            "api_key": self.api_key,
            "hl": "en",
            **params,
        }

    def _get_json(self, **params: Any) -> dict[str, Any]:
        """Call SerpApi without allowing its query-string key into error logs."""
        try:
            return self.get_json("/search.json", params=self._params(**params))
        except httpx.HTTPStatusError as error:
            raise RuntimeError(
                "SerpApi Google Scholar request failed with HTTP "
                f"{error.response.status_code}"
            ) from None
        except httpx.TransportError:
            raise RuntimeError("SerpApi Google Scholar transport failure") from None

    def remaining_observations(self) -> int:
        """Return the number of one-search observations left in the current plan."""
        try:
            payload = self.get_json("/account.json", params={"api_key": self.api_key})
        except httpx.HTTPStatusError as error:
            raise GoogleScholarTransportError(
                f"SerpApi account request failed with HTTP {error.response.status_code}"
            ) from None
        except httpx.TransportError:
            raise GoogleScholarTransportError("SerpApi account transport failure") from None
        remaining = payload.get("total_searches_left")
        if not isinstance(remaining, int) or remaining < 0:
            raise GoogleScholarTransportError("SerpApi account response has no usable quota")
        return remaining

    def search_title_with_payload(
        self, title: str, *, limit: int = 10
    ) -> tuple[list[ProviderPaper], dict[str, Any]]:
        if not 1 <= limit <= 20:
            raise ValueError("SerpApi Google Scholar limit must be between 1 and 20")
        payload = self._get_json(q=f'"{title}"', num=limit)
        _require_success(payload)
        candidates = (_candidate(item) for item in payload.get("organic_results") or [])
        return [candidate for candidate in candidates if candidate is not None], payload

    def search_title(self, title: str, *, limit: int = 10) -> list[ProviderPaper]:
        candidates, _ = self.search_title_with_payload(title, limit=limit)
        return candidates

    def discovery_observation(
        self,
        *,
        paper_id: str,
        candidate: ProviderPaper,
        search_payload: dict[str, Any],
        query_title: str,
        limit: int = 10,
        retrieved_at: datetime | None = None,
    ) -> CitationObservation:
        """Create the initial count from the reviewed title-search response.

        Routine refreshes still use the pinned numeric ``cites_id``. This method
        avoids spending a second search per paper during first-time discovery.
        """
        if not candidate.external_id.isdigit():
            raise ValueError("Google Scholar binding must be a numeric cites_id")
        if candidate.citation_count is None:
            raise RuntimeError("SerpApi candidate has no Google Scholar citation count")
        raw_bytes = json.dumps(search_payload, ensure_ascii=False, sort_keys=True).encode()
        processed_at = (search_payload.get("search_metadata") or {}).get("processed_at")
        observed_at = retrieved_at
        if observed_at is None and processed_at:
            observed_at = datetime.strptime(
                str(processed_at), "%Y-%m-%d %H:%M:%S %Z"
            ).replace(tzinfo=UTC)
        title_digest = hashlib.sha256(query_title.encode()).hexdigest()
        return CitationObservation(
            paper_id=paper_id,
            provider=CitationProvider.GOOGLE_SCHOLAR,
            external_id=candidate.external_id,
            retrieved_at=observed_at or utc_now(),
            total_citations=candidate.citation_count,
            influential_citations=None,
            citations_by_citing_year=[],
            retrieval_service=CitationRetrievalService.SERPAPI,
            response_sha256=hashlib.sha256(raw_bytes).hexdigest(),
            request_fingerprint=(
                "GET /search.json?engine=google_scholar&"
                f"q_sha256={title_digest}&num={limit}&hl=en"
            ),
        )

    def observation(
        self,
        *,
        paper_id: str,
        external_id: str,
        retrieved_at: datetime | None = None,
    ) -> CitationObservation:
        if not external_id.isdigit():
            raise ValueError("Google Scholar binding must be a numeric cites_id")
        payload = self._get_json(cites=external_id, num=20)
        _require_success(payload)
        information = payload.get("search_information") or {}
        if "total_results" not in information:
            raise RuntimeError("SerpApi response has no Google Scholar total_results")
        raw_bytes = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()
        year_counts = [
            CitationYearCount(year=int(item["year"]), count=int(item["citations"]))
            for item in payload.get("citations_per_year") or []
            if item.get("year") is not None and item.get("citations") is not None
        ]
        return CitationObservation(
            paper_id=paper_id,
            provider=CitationProvider.GOOGLE_SCHOLAR,
            external_id=external_id,
            retrieved_at=retrieved_at or utc_now(),
            total_citations=int(information["total_results"]),
            influential_citations=None,
            citations_by_citing_year=year_counts,
            retrieval_service=CitationRetrievalService.SERPAPI,
            response_sha256=hashlib.sha256(raw_bytes).hexdigest(),
            request_fingerprint=f"GET /search.json?engine=google_scholar&cites={external_id}&hl=en",
        )


class ScraperApiGoogleScholarClient:
    """Current Scholar totals from HTML returned by ScraperAPI.

    ScraperAPI is a transport, not a separate citation source. Unlike SerpApi's
    structured Scholar response, the HTML result page does not provide the citing-year
    histogram, so these observations intentionally leave that field empty.
    """

    MAX_CREDITS_PER_REQUEST = 25
    _COST_TARGET = "https://scholar.google.com/scholar?hl=en&cites=1"

    def __init__(self, api_key: str, *, client: httpx.Client | None = None) -> None:
        if not api_key:
            raise ValueError("a ScraperAPI key is required")
        self.api_key = api_key
        self._owned_client = client is None
        self.client = client or httpx.Client(
            base_url="https://api.scraperapi.com",
            follow_redirects=True,
            timeout=120,
            headers={"User-Agent": "SecAwardLens/0.1 (citation research)"},
        )

    def close(self) -> None:
        if self._owned_client:
            self.client.close()

    def __enter__(self) -> ScraperApiGoogleScholarClient:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def _response(self, path: str, **params: Any) -> httpx.Response:
        request_params = {
            "api_key": self.api_key,
            **{name: value for name, value in params.items() if name != "url"},
        }
        if "url" in params:
            request_params["url"] = params["url"]
        try:
            response = self.client.get(path, params=request_params)
        except httpx.TransportError:
            raise GoogleScholarTransportError("ScraperAPI transport failure") from None
        if response.status_code != 200:
            raise GoogleScholarTransportError(
                f"ScraperAPI request failed with HTTP {response.status_code}"
            )
        return response

    def _json(self, path: str, **params: Any) -> dict[str, Any]:
        response = self._response(path, **params)
        try:
            payload = response.json()
        except ValueError:
            raise GoogleScholarTransportError("ScraperAPI returned invalid account JSON") from None
        if not isinstance(payload, dict):
            raise GoogleScholarTransportError("ScraperAPI returned non-object account JSON")
        return payload

    def remaining_observations(self) -> int:
        account = self._json("/account")
        cost = self._json("/account/urlcost", url=self._COST_TARGET, country_code="us")
        credits_left = account.get("creditsLeft")
        credits_per_request = cost.get("credits")
        if not isinstance(credits_left, int) or credits_left < 0:
            raise GoogleScholarTransportError(
                "ScraperAPI account response has no usable credit balance"
            )
        if not isinstance(credits_per_request, int) or credits_per_request <= 0:
            raise GoogleScholarTransportError(
                "ScraperAPI cost response has no usable request cost"
            )
        return credits_left // credits_per_request

    def observation(
        self,
        *,
        paper_id: str,
        external_id: str,
        retrieved_at: datetime | None = None,
    ) -> CitationObservation:
        if not external_id.isdigit():
            raise ValueError("Google Scholar binding must be a numeric cites_id")
        target = (
            "https://scholar.google.com/scholar?"
            f"hl=en&as_sdt=0,5&cites={external_id}"
        )
        response = self._response(
            "/",
            url=target,
            country_code="us",
            max_cost=self.MAX_CREDITS_PER_REQUEST,
        )
        raw_bytes = response.content
        return CitationObservation(
            paper_id=paper_id,
            provider=CitationProvider.GOOGLE_SCHOLAR,
            external_id=external_id,
            retrieved_at=retrieved_at or utc_now(),
            total_citations=_html_result_count(response.text),
            influential_citations=None,
            citations_by_citing_year=[],
            retrieval_service=CitationRetrievalService.SCRAPERAPI,
            response_sha256=hashlib.sha256(raw_bytes).hexdigest(),
            request_fingerprint=(
                "GET api.scraperapi.com -> scholar.google.com/scholar?"
                f"cites={external_id}&hl=en&country_code=us&max_cost=25"
            ),
        )
