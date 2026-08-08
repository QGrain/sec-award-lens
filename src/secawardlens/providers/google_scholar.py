from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from typing import Any

import httpx

from ..models import CitationObservation, CitationProvider, CitationYearCount, utc_now
from .base import ProviderPaper
from .http import JsonApiClient

_YEAR = re.compile(r"\b(19|20)\d{2}\b")


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
            response_sha256=hashlib.sha256(raw_bytes).hexdigest(),
            request_fingerprint=f"GET /search.json?engine=google_scholar&cites={external_id}&hl=en",
        )
