from __future__ import annotations

from collections.abc import Iterable
from statistics import mean, median

from .models import CitationObservation


def citation_window(
    observation: CitationObservation, publication_year: int, years: int = 3
) -> int:
    end_year = publication_year + years
    return sum(
        item.count
        for item in observation.citations_by_citing_year
        if publication_year <= item.year < end_year
    )


def quartiles(values: list[float]) -> tuple[float, float]:
    ordered = sorted(values)
    if not ordered:
        raise ValueError("quartiles require at least one value")
    midpoint = len(ordered) // 2
    lower = ordered[:midpoint] or ordered
    upper = ordered[(midpoint + (len(ordered) % 2)) :] or ordered
    return float(median(lower)), float(median(upper))


def distribution_summary(values: Iterable[int | float]) -> dict[str, float | int]:
    materialized = [float(value) for value in values]
    if not materialized:
        return {"n": 0}
    q1, q3 = quartiles(materialized)
    return {
        "n": len(materialized),
        "min": min(materialized),
        "median": float(median(materialized)),
        "mean": float(mean(materialized)),
        "q1": q1,
        "q3": q3,
        "max": max(materialized),
    }
