from secawardlens.metrics import citation_window, distribution_summary
from secawardlens.models import CitationObservation, CitationYearCount


def observation(at: str, count: int) -> CitationObservation:
    return CitationObservation(
        paper_id="paper",
        provider="openalex",
        external_id="W1",
        retrieved_at=at,
        total_citations=count,
        citations_by_citing_year=[
            CitationYearCount(year=2023, count=2),
            CitationYearCount(year=2024, count=5),
            CitationYearCount(year=2025, count=7),
            CitationYearCount(year=2026, count=11),
        ],
        response_sha256="a" * 64,
        request_fingerprint="fixture",
    )


def test_fixed_age_window_excludes_fourth_calendar_year() -> None:
    assert citation_window(observation("2026-08-07T12:00:00Z", 25), 2023, 3) == 14


def test_distribution_reports_denominator() -> None:
    assert distribution_summary([1, 2, 9]) == {
        "n": 3,
        "min": 1.0,
        "median": 2.0,
        "mean": 4.0,
        "q1": 1.0,
        "q3": 9.0,
        "max": 9.0,
    }
