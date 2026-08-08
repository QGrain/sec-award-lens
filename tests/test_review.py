import shutil

import pytest
import yaml

from secawardlens.io import (
    load_bindings,
    load_overrides,
    load_papers,
    repository_root,
)
from secawardlens.models import (
    BindingStatus,
    PaperResolutionSubmission,
    ReviewProviderDecision,
)
from secawardlens.review import apply_resolution

PAPER_ID = "usenix-security-2023-remote-direct-memory-introspection"


def submission(provider: str = "openalex") -> PaperResolutionSubmission:
    root = repository_root()
    paper = next(item for item in load_papers(root) if item.id == PAPER_ID)
    external_id = "W9999999999" if provider == "openalex" else "s2-review-id"
    candidate_url = (
        f"https://openalex.org/{external_id}"
        if provider == "openalex"
        else f"https://www.semanticscholar.org/paper/{external_id}"
    )
    return PaperResolutionSubmission(
        paper_id=PAPER_ID,
        reviewer="test-maintainer",
        reviewed_at="2026-08-08T12:00:00Z",
        evidence_urls=[
            "https://www.usenix.org/conference/usenixsecurity23/presentation/liu-hongyi"
        ],
        provider_decisions=[
            ReviewProviderDecision(
                provider=provider,
                decision="verified",
                external_id=external_id,
                candidate_url=candidate_url,
                candidate_title=paper.canonical_title,
                candidate_authors=[author.name for author in paper.authors],
                candidate_publication_year=2023,
                candidate_venue="USENIX Security Symposium",
                confidence=0.99,
                reason="Exact official title, author, year, and venue agreement.",
                evidence_urls=[
                    "https://www.usenix.org/conference/usenixsecurity23/presentation/liu-hongyi"
                ],
            )
        ],
    )


def test_review_form_dry_runs_then_updates_compiled_records(tmp_path) -> None:
    root = repository_root()
    shutil.copytree(root / "data", tmp_path / "data")

    diff = apply_resolution(tmp_path, submission(), write=False)
    assert "W9999999999" in diff
    before = next(item for item in load_bindings(tmp_path) if item.paper_id == PAPER_ID)
    assert before.status == BindingStatus.PENDING

    apply_resolution(tmp_path, submission(), write=True)
    after = next(item for item in load_bindings(tmp_path) if item.paper_id == PAPER_ID)
    assert after.status == BindingStatus.MANUALLY_VERIFIED
    assert after.external_id == "W9999999999"
    assert any(
        item.paper_id == PAPER_ID and item.external_id == "W9999999999"
        for item in load_overrides(tmp_path)
    )
    assert (tmp_path / f"web/public/data/papers/{PAPER_ID}.json").exists()


def test_review_form_respects_disabled_provider_publication(tmp_path) -> None:
    root = repository_root()
    shutil.copytree(root / "data", tmp_path / "data")
    registry_path = tmp_path / "data/provenance/source_registry.yml"
    registry = yaml.safe_load(registry_path.read_text())
    for source in registry["citation_sources"]:
        if source["id"] == "semantic_scholar":
            source["public_output_enabled"] = False
    registry_path.write_text(yaml.safe_dump(registry, sort_keys=False))
    with pytest.raises(ValueError, match="public output is disabled"):
        apply_resolution(tmp_path, submission("semantic_scholar"), write=False)
