import json
import shutil
from collections import Counter

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


def test_release_counts_are_explicit() -> None:
    root = repository_root()
    awards = load_awards(root)
    expected = {
        "ieee-sp-2021": 2,
        "usenix-security-2021": 7,
        "acm-ccs-2021": 5,
        "ndss-2021": 1,
        "ieee-sp-2022": 4,
        "usenix-security-2022": 12,
        "acm-ccs-2022": 5,
        "ndss-2022": 1,
        "ieee-sp-2023": 12,
        "usenix-security-2023": 16,
        "acm-ccs-2023": 17,
        "ndss-2023": 2,
    }
    by_edition = {
        edition: sum(item.edition_id == edition for item in awards) for edition in expected
    }
    assert by_edition == expected
    assert len(load_papers(root)) == 84


def test_entity_coverage_is_visible() -> None:
    bindings = load_bindings(repository_root())
    verified = Counter(
        item.provider.value
        for item in bindings
        if item.status in {BindingStatus.AUTO_VERIFIED, BindingStatus.MANUALLY_VERIFIED}
    )
    pending = Counter(
        item.provider.value for item in bindings if item.status == BindingStatus.PENDING
    )
    assert verified == {
        "google_scholar": 84,
        "openalex": 70,
        "semantic_scholar": 81,
    }
    assert pending == {"openalex": 14, "semantic_scholar": 3}
    assert sum(item.status == BindingStatus.CANDIDATE for item in bindings) == 0


def test_openalex_enrichment_stays_provider_specific() -> None:
    enrichments = load_enrichments(repository_root())
    assert len(enrichments) == 70
    assert sum(item.primary_topic is not None for item in enrichments) == 69
    assert all(item.provider == "openalex" for item in enrichments)


def test_repository_validates_and_builds(tmp_path) -> None:
    root = repository_root()
    assert validate_repository(root).valid
    written = build_site_data(root, tmp_path)
    year_2021 = json.loads((tmp_path / "years/2021.json").read_text())
    year_2022 = json.loads((tmp_path / "years/2022.json").read_text())
    year_2023 = json.loads((tmp_path / "years/2023.json").read_text())
    index = json.loads((tmp_path / "index.json").read_text())
    assert (
        year_2021["schema_version"]
        == year_2022["schema_version"]
        == year_2023["schema_version"]
        == 3
    )
    assert len(year_2021["rows"]) == 15
    assert len(year_2022["rows"]) == 22
    assert len(year_2023["rows"]) == 47
    assert sum(item["primary_topic"] is not None for item in year_2021["rows"]) == 15
    assert sum("google_scholar" in item["citations"] for item in year_2021["rows"]) == 15
    assert sum("openalex" in item["citations"] for item in year_2021["rows"]) == 15
    assert sum("semantic_scholar" in item["citations"] for item in year_2021["rows"]) == 15
    assert sum(item["primary_topic"] is not None for item in year_2022["rows"]) == 13
    assert sum(item["primary_topic"] is not None for item in year_2023["rows"]) == 41
    assert all("enrichment" not in item for item in year_2022["rows"])
    assert sum("google_scholar" in item["citations"] for item in year_2022["rows"]) == 22
    assert sum("openalex" in item["citations"] for item in year_2022["rows"]) == 13
    assert sum("semantic_scholar" in item["citations"] for item in year_2022["rows"]) == 20
    assert sum("google_scholar" in item["citations"] for item in year_2023["rows"]) == 47
    assert sum("openalex" in item["citations"] for item in year_2023["rows"]) == 42
    assert sum("semantic_scholar" in item["citations"] for item in year_2023["rows"]) == 46
    scholar = [
        item["citations"]["google_scholar"]
        for year in (year_2021, year_2022, year_2023)
        for item in year["rows"]
        if "google_scholar" in item["citations"]
    ]
    assert all(item["citations_first_3_years"] is not None for item in scholar)
    assert all(item["citing_years_retrieved_at"] for item in scholar)
    assert index["citation_sources"] == ["google_scholar", "openalex", "semantic_scholar"]
    assert index["preferred_citation_source"] == "google_scholar"
    assert index["years"] == [2021, 2022, 2023]
    assert len(written) == 88


def test_google_scholar_default_falls_back_when_its_snapshot_is_absent(tmp_path) -> None:
    root = repository_root()
    shutil.copytree(root / "data", tmp_path / "data")
    for snapshot in (tmp_path / "data/snapshots").glob("*-google-scholar.jsonl"):
        snapshot.unlink()

    output = tmp_path / "site"
    build_site_data(tmp_path, output)
    index = json.loads((output / "index.json").read_text())
    assert index["citation_sources"] == ["openalex", "semantic_scholar"]
    assert index["preferred_citation_source"] == "openalex"


def test_social_sharing_card_is_crawler_visible_and_correctly_sized() -> None:
    root = repository_root()
    html = (root / "web/index.html").read_text()
    image_url = "https://qgrain.github.io/sec-award-lens/social-card.png"
    for marker in (
        '<link rel="canonical" href="https://qgrain.github.io/sec-award-lens/"',
        '<meta property="og:title"',
        f'<meta property="og:image" content="{image_url}"',
        '<meta name="twitter:card" content="summary_large_image"',
        f'<meta name="twitter:image" content="{image_url}"',
    ):
        assert marker in html

    image = (root / "web/public/social-card.png").read_bytes()
    assert image[:8] == b"\x89PNG\r\n\x1a\n"
    assert int.from_bytes(image[16:20]) == 1200
    assert int.from_bytes(image[20:24]) == 630
