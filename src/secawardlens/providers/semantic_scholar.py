from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any

import httpx

from ..models import CitationObservation, CitationProvider, CitationRetrievalService, utc_now
from ..normalization import normalize_doi
from .base import ProviderPaper
from .http import JsonApiClient


def _paper(payload: dict[str, Any]) -> ProviderPaper:
    external_ids = payload.get("externalIds") or {}
    return ProviderPaper(
        external_id=str(payload["paperId"]),
        title=str(payload.get("title") or ""),
        authors=[
            str(author["name"])
            for author in payload.get("authors", [])
            if author.get("name")
        ],
        publication_year=payload.get("year"),
        venue=str(payload.get("venue")) if payload.get("venue") else None,
        doi=normalize_doi(str(external_ids["DOI"])) if external_ids.get("DOI") else None,
        citation_count=payload.get("citationCount"),
        influential_citation_count=payload.get("influentialCitationCount"),
        raw=payload,
    )


class SemanticScholarClient(JsonApiClient):
    FIELDS = "paperId,title,authors,year,venue,externalIds,citationCount,influentialCitationCount"

    def __init__(self, api_key: str | None = None, *, client: httpx.Client | None = None) -> None:
        headers = {"User-Agent": "SecAwardLens/0.1 (citation research)"}
        if api_key:
            headers["x-api-key"] = api_key
        super().__init__(
            base_url="https://api.semanticscholar.org/graph/v1",
            headers=headers,
            # The issued key allows one request per second. A small margin avoids
            # crossing the boundary because of clock and network jitter.
            min_interval_seconds=1.25,
            client=client,
        )

    def get_paper(self, external_id: str) -> ProviderPaper:
        return _paper(self.get_json(f"/paper/{external_id}", params={"fields": self.FIELDS}))

    def get_by_doi(self, doi: str) -> ProviderPaper:
        return self.get_paper(f"DOI:{normalize_doi(doi)}")

    def title_candidate(self, title: str) -> ProviderPaper | None:
        payload = self.get_optional_json(
            "/paper/search/match", params={"query": title, "fields": self.FIELDS}
        )
        if payload is None:
            return None
        matches = payload.get("data", [])
        return _paper(matches[0]) if matches else None

    def search_title(self, title: str, *, limit: int = 5) -> list[ProviderPaper]:
        if not 1 <= limit <= 100:
            raise ValueError("Semantic Scholar search limit must be between 1 and 100")
        payload = self.get_json(
            "/paper/search",
            params={"query": title, "limit": limit, "fields": self.FIELDS},
        )
        return [_paper(item) for item in payload.get("data", [])]

    def observation(
        self,
        *,
        paper_id: str,
        external_id: str,
        retrieved_at: datetime | None = None,
    ) -> CitationObservation:
        paper = self.get_paper(external_id)
        raw_bytes = json.dumps(paper.raw, ensure_ascii=False, sort_keys=True).encode()
        return CitationObservation(
            paper_id=paper_id,
            provider=CitationProvider.SEMANTIC_SCHOLAR,
            external_id=paper.external_id,
            retrieved_at=retrieved_at or utc_now(),
            total_citations=paper.citation_count or 0,
            influential_citations=paper.influential_citation_count,
            retrieval_service=CitationRetrievalService.SEMANTIC_SCHOLAR,
            response_sha256=hashlib.sha256(raw_bytes).hexdigest(),
            request_fingerprint=f"GET /paper/{paper.external_id}?fields={self.FIELDS}",
        )
