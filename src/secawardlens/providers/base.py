from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ProviderPaper:
    external_id: str
    title: str
    authors: list[str] = field(default_factory=list)
    publication_year: int | None = None
    venue: str | None = None
    doi: str | None = None
    citation_count: int | None = None
    influential_citation_count: int | None = None
    counts_by_year: dict[int, int] = field(default_factory=dict)
    updated_at: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)

