import json

from secawardlens.build import build_site_data
from secawardlens.io import (
    load_awards,
    load_bindings,
    load_enrichments,
    load_papers,
    repository_root,
)
from secawardlens.models import BindingStatus
from secawardlens.validation import validate_repository


def test_2023_release_counts_are_explicit() -> None:
    root = repository_root()
    awards = load_awards(root)
    by_edition = {edition: sum(item.edition_id == edition for item in awards) for edition in {
        "ieee-sp-2023", "usenix-security-2023", "acm-ccs-2023", "ndss-2023"
    }}
    assert by_edition == {
        "ieee-sp-2023": 12,
        "usenix-security-2023": 16,
        "acm-ccs-2023": 17,
        "ndss-2023": 2,
    }
    assert len(load_papers(root)) == 47


def test_entity_coverage_is_visible() -> None:
    bindings = load_bindings(repository_root())
    verified = [item for item in bindings if item.status in {
        BindingStatus.AUTO_VERIFIED, BindingStatus.MANUALLY_VERIFIED
    }]
    assert len(verified) == 42
    assert sum(item.status == BindingStatus.PENDING for item in bindings) == 5


def test_openalex_enrichment_stays_provider_specific() -> None:
    enrichments = load_enrichments(repository_root())
    assert len(enrichments) == 42
    assert sum(item.primary_topic is not None for item in enrichments) == 41
    assert all(item.provider == "openalex" for item in enrichments)


def test_repository_validates_and_builds(tmp_path) -> None:
    root = repository_root()
    assert validate_repository(root).valid
    written = build_site_data(root, tmp_path)
    year = json.loads((tmp_path / "years/2023.json").read_text())
    assert len(year["rows"]) == 47
    assert sum(item["primary_topic"] is not None for item in year["rows"]) == 41
    assert all("enrichment" not in item for item in year["rows"])
    assert sum("openalex" in item["citations"] for item in year["rows"]) == 42
    assert len(written) == 49
