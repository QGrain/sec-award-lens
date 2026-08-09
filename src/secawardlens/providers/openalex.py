from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from datetime import datetime
from typing import Any

import httpx

from ..models import (
    CitationObservation,
    CitationProvider,
    CitationRetrievalService,
    CitationYearCount,
    utc_now,
)
from ..normalization import normalize_doi
from .base import ProviderPaper
from .http import JsonApiClient


def _openalex_id(value: str) -> str:
    return value.rsplit("/", 1)[-1]


def _author_names(work: dict[str, Any]) -> list[str]:
    return [
        str(authorship.get("author", {}).get("display_name"))
        for authorship in work.get("authorships", [])
        if authorship.get("author", {}).get("display_name")
    ]


def _venue(work: dict[str, Any]) -> str | None:
    source = (work.get("primary_location") or {}).get("source") or {}
    value = source.get("display_name")
    return str(value) if value else None


def _as_provider_paper(work: dict[str, Any]) -> ProviderPaper:
    doi_value = work.get("doi")
    by_year = {
        int(item["year"]): int(item["cited_by_count"])
        for item in work.get("counts_by_year", [])
        if item.get("year") is not None and item.get("cited_by_count") is not None
    }
    return ProviderPaper(
        external_id=_openalex_id(str(work["id"])),
        title=str(work.get("display_name") or work.get("title") or ""),
        authors=_author_names(work),
        publication_year=work.get("publication_year"),
        venue=_venue(work),
        doi=normalize_doi(str(doi_value)) if doi_value else None,
        citation_count=work.get("cited_by_count"),
        counts_by_year=by_year,
        updated_at=work.get("updated_date"),
        raw=work,
    )


class OpenAlexClient(JsonApiClient):
    FIELDS = (
        "id,display_name,publication_year,doi,cited_by_count,counts_by_year,"
        "authorships,primary_location,primary_topic,locations,type,updated_date,is_retracted"
    )

    def __init__(self, api_key: str | None = None, *, client: httpx.Client | None = None) -> None:
        super().__init__(
            base_url="https://api.openalex.org",
            headers={"User-Agent": "SecAwardLens/0.1 (citation research)"},
            client=client,
        )
        self.api_key = api_key

    def _params(self, **values: Any) -> dict[str, Any]:
        params = {key: value for key, value in values.items() if value is not None}
        if self.api_key:
            params["api_key"] = self.api_key
        return params

    def get_work(self, external_id: str) -> ProviderPaper:
        payload = self.get_json(
            f"/works/{_openalex_id(external_id)}", params=self._params(select=self.FIELDS)
        )
        return _as_provider_paper(payload)

    def get_by_doi(self, doi: str) -> ProviderPaper:
        payload = self.get_json(
            f"/works/doi:{normalize_doi(doi)}", params=self._params(select=self.FIELDS)
        )
        return _as_provider_paper(payload)

    def search_titles(self, titles: Iterable[str]) -> list[ProviderPaper]:
        title_list = list(dict.fromkeys(title.strip() for title in titles if title.strip()))
        if not title_list:
            return []
        if len(title_list) > 100:
            raise ValueError("OpenAlex supports at most 100 OR values per filter")
        # Quoting each OR value prevents commas in paper titles from being
        # interpreted as separators between OpenAlex filters.
        quoted_titles = [f'"{title.replace(chr(34), chr(92) + chr(34))}"' for title in title_list]
        payload = self.get_json(
            "/works",
            params=self._params(
                filter="title.search:" + "|".join(quoted_titles),
                per_page=100,
                select=self.FIELDS,
            ),
        )
        return [_as_provider_paper(item) for item in payload.get("results", [])]

    def autocomplete_title(self, title: str) -> list[ProviderPaper]:
        """Resolve free autocomplete hits to complete work records.

        OpenAlex autocomplete is useful for candidate generation when a title
        contains punctuation that interacts poorly with filter syntax. It is
        never itself treated as a match decision.
        """
        payload = self.get_json("/autocomplete/works", params=self._params(q=title))
        identifiers = [
            _openalex_id(str(item["id"]))
            for item in payload.get("results", [])
            if item.get("entity_type") == "work" and item.get("id")
        ]
        return [self.get_work(identifier) for identifier in identifiers]

    def citing_year_counts(self, external_id: str) -> dict[int, int]:
        payload = self.get_json(
            "/works",
            params=self._params(
                filter=f"cites:{_openalex_id(external_id)}", group_by="publication_year"
            ),
        )
        return {
            int(group["key"]): int(group["count"])
            for group in payload.get("group_by", [])
            if str(group.get("key", "")).isdigit()
        }

    def observation(
        self,
        *,
        paper_id: str,
        external_id: str,
        full_history: bool = False,
        retrieved_at: datetime | None = None,
    ) -> CitationObservation:
        work = self.get_work(external_id)
        by_year = self.citing_year_counts(external_id) if full_history else work.counts_by_year
        raw_bytes = json.dumps(work.raw, ensure_ascii=False, sort_keys=True).encode()
        updated_at = (
            datetime.fromisoformat(work.updated_at.replace("Z", "+00:00"))
            if work.updated_at
            else None
        )
        return CitationObservation(
            paper_id=paper_id,
            provider=CitationProvider.OPENALEX,
            external_id=work.external_id,
            retrieved_at=retrieved_at or utc_now(),
            total_citations=work.citation_count or 0,
            influential_citations=None,
            citations_by_citing_year=[
                CitationYearCount(year=year, count=count) for year, count in sorted(by_year.items())
            ],
            provider_record_updated_at=updated_at,
            retrieval_service=CitationRetrievalService.OPENALEX,
            response_sha256=hashlib.sha256(raw_bytes).hexdigest(),
            request_fingerprint=f"GET /works/{work.external_id}?select={self.FIELDS}",
        )
