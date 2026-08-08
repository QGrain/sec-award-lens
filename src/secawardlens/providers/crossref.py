from __future__ import annotations

from typing import Any

import httpx

from ..normalization import normalize_doi
from .base import ProviderPaper
from .http import JsonApiClient


def _first(value: Any) -> str | None:
    if isinstance(value, list) and value:
        return str(value[0])
    return None


def _paper(message: dict[str, Any]) -> ProviderPaper:
    authors = [
        " ".join(part for part in [item.get("given"), item.get("family")] if part)
        for item in message.get("author", [])
    ]
    publication = message.get("published-print") or message.get("published") or {}
    year_parts = publication.get("date-parts")
    year = year_parts[0][0] if year_parts and year_parts[0] else None
    return ProviderPaper(
        external_id=normalize_doi(str(message["DOI"])),
        title=_first(message.get("title")) or "",
        authors=authors,
        publication_year=year,
        venue=_first(message.get("container-title")),
        doi=normalize_doi(str(message["DOI"])),
        citation_count=message.get("is-referenced-by-count"),
        raw=message,
    )


class CrossrefClient(JsonApiClient):
    def __init__(
        self,
        *,
        mailto: str,
        client: httpx.Client | None = None,
    ) -> None:
        super().__init__(
            base_url="https://api.crossref.org",
            headers={"User-Agent": f"SecAwardLens/0.1 (mailto:{mailto})"},
            client=client,
        )
        self.mailto = mailto

    def get_by_doi(self, doi: str) -> ProviderPaper:
        payload = self.get_json(f"/works/{normalize_doi(doi)}", params={"mailto": self.mailto})
        return _paper(payload["message"])

    def search_title(self, title: str, *, rows: int = 5) -> list[ProviderPaper]:
        payload = self.get_json(
            "/works",
            params={"query.title": title, "rows": rows, "mailto": self.mailto},
        )
        return [_paper(item) for item in payload["message"]["items"]]
